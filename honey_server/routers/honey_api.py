"""
Honeypot API Router
Contains all intentionally vulnerable endpoints for the honeypot server.
Each endpoint logs attacks to the Monitor Server via HTTP POST.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os, sqlite3, subprocess, pathlib

from core.logger import log_attack
from core.detector import analyze_payload

router = APIRouter()

# ─── DB Helper ───────────────────────────────────────────────────────────────
DB_PATH = pathlib.Path(__file__).parent.parent / "database" / "mock.db"

def query_mock_db(query: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        cols = [c[0] for c in cursor.description] if cursor.description else []
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
        conn.close()
        return {"status": "success", "data": rows}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ─── [Phase 1] SQL Injection: Login ──────────────────────────────────────────
@router.post("/login")
async def api_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Vulnerable Login - SQL Injection Target
    e.g. username: admin' --
    """
    client_ip = request.client.host
    analysis = analyze_payload(username) if not analyze_payload(password)["is_attack"] else analyze_payload(password)

    if analysis["is_attack"]:
        payload_used = username if analyze_payload(username)["is_attack"] else password
        log_attack(client_ip, "/api/login", analysis["attack_type"], payload_used)

        # Intentionally vulnerable query
        query = f"SELECT * FROM users WHERE username = '{username}' AND password_hash = '{password}'"
        res = query_mock_db(query)

        if res["status"] == "success" and len(res["data"]) > 0:
            return JSONResponse(200, content={
                "status": "success_hacked",
                "redirect": "/decoy-admin",
                "message": "Authentication bypassed.",
                "data": res["data"][0]
            })
        elif res["status"] == "error":
            # Return raw SQL error - intentionally realistic
            return JSONResponse(500, content={
                "status": "error",
                "message": "Database Error",
                "detail": res["message"]  # Raw SQLite error exposed!
            })
        else:
            return JSONResponse(401, content={"status": "error", "message": "Invalid credentials."})

    # Normal (non-attack) mock login
    if username == "admin" and password == "1234":
        return {"status": "success", "redirect": "/decoy-admin"}
    return JSONResponse(401, content={"status": "error", "message": "아이디 또는 비밀번호가 틀렸습니다."})

# ─── [Phase 1] SQL Injection: Board Search ───────────────────────────────────
@router.get("/board/search")
async def api_board_search(request: Request, q: str):
    """
    Vulnerable Search - SQLi & XSS Target
    e.g. q: ' UNION SELECT null, username, email, password_hash, null FROM users--
    """
    client_ip = request.client.host
    analysis = analyze_payload(q)

    if analysis["is_attack"]:
        log_attack(client_ip, "/api/board/search", analysis["attack_type"], q)
        query = f"SELECT * FROM products WHERE name LIKE '%{q}%' OR description LIKE '%{q}%'"
        res = query_mock_db(query)

        if res["status"] == "success":
            return {"status": "success_hacked", "query": q, "results": res["data"]}
        return JSONResponse(500, content={"status": "error", "detail": res["message"]})

    return {"status": "success", "query": q, "results": []}

# ─── [Phase 2] LFI: System Log Viewer ────────────────────────────────────────
@router.get("/admin/view_log")
async def api_lfi_log_viewer(request: Request, file: str = "access.log"):
    """
    Vulnerable Log Viewer - Local File Inclusion (Path Traversal)
    e.g. file: ../../database/mock.db
         file: ../app.py  (to read source code)
    """
    client_ip = request.client.host

    if "../" in file or "..\\" in file or file.startswith("/"):
        log_attack(client_ip, "/api/admin/view_log", "Local File Inclusion (LFI)", file)

    try:
        # Intentionally NOT sanitized - path traversal allowed
        base_dir = pathlib.Path(os.getcwd()) / "logs_faux"
        target = pathlib.Path(os.path.abspath(base_dir / file))

        # Sandbox: don't allow reading outside of the project root
        project_root = pathlib.Path(os.getcwd()).resolve()
        if not str(target).startswith(str(project_root)):
            return JSONResponse(403, content={"status": "error", "detail": "Access denied."})

        if target.exists():
            content = target.read_bytes()
            try:
                return {"status": "success", "content": content.decode("utf-8")}
            except UnicodeDecodeError:
                return {"status": "success", "content": f"[BINARY DATA - {len(content)} bytes]\n{content[:256].hex()}"}
        else:
            return JSONResponse(404, content={"status": "error", "detail": f"File '{file}' not found."})
    except Exception as e:
        return JSONResponse(500, content={"status": "error", "detail": str(e)})

# ─── [Phase 3] RCE: Network Diagnostic ───────────────────────────────────────
@router.post("/admin/network_test")
async def api_rce_ping(request: Request):
    """
    Vulnerable Ping Tool - OS Command Injection (RCE)
    e.g. target: 127.0.0.1 & whoami
         target: 127.0.0.1 & sqlite3 database/mock.db .dump
    """
    client_ip = request.client.host
    data = await request.json()
    target = data.get("target", "127.0.0.1")

    # Detect injection characters
    if any(c in target for c in [";", "|", "&", "`", "$", "(", ">"]):
        log_attack(client_ip, "/api/admin/network_test", "OS Command Injection (RCE)", target)

    try:
        # Intentionally unsafe - shell=True with unescaped user input
        output = subprocess.check_output(
            f"ping -n 3 {target}",
            shell=True, stderr=subprocess.STDOUT, timeout=8
        )
        return {"status": "success", "output": output.decode("utf-8", errors="replace")}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "output": e.output.decode("utf-8", errors="replace")}
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Command timed out."}
    except Exception as e:
        return JSONResponse(500, content={"status": "error", "detail": str(e)})

# ─── Chat (Prompt Injection) ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def api_chat(request: Request, chat_req: ChatRequest):
    """
    AI Chatbot - Prompt Injection Target
    """
    client_ip = request.client.host
    msg = chat_req.message
    analysis = analyze_payload(msg)

    if analysis["is_attack"]:
        log_attack(client_ip, "/api/chat", analysis["attack_type"], msg)
        return {"status": "success", "reply": "[SYSTEM]: Command acknowledged. Executing in background..."}

    return {
        "status": "success",
        "reply": "안녕하세요! 내부 AI 베타 시스템입니다. 꿀 관련 정보나 시스템 도움이 필요하시면 말씀해 주세요."
    }
