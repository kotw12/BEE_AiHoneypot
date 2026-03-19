"""
Monitor Server - EC2 Instance (Port 9000)
SOC dashboard / attack log aggregator.
Receives log data from the Honeypot server, visualizes it, and generates AI reports.
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn, os, pathlib, secrets, re

app = FastAPI(
    title="Honey SOC Monitor",
    description="Security Operations Center - Internal Monitoring Dashboard",
    version="1.0.0",
    docs_url=None, redoc_url=None  # No public API docs for monitor
)

templates = Jinja2Templates(directory="templates")
security = HTTPBasic()

# ─── Configuration ──────────────────────────────────────────────────────────
SOC_USER = os.environ.get("SOC_USER", "soc_admin")
SOC_PASS = os.environ.get("SOC_PASS", "changeme_in_env")
LOG_SECRET = os.environ.get("LOG_SECRET", "honey_internal_secret")

# 읽기/쓰기 동일한 경로를 바라보도록 설정 (.log 확장자)
LOG_FILE_PATH = pathlib.Path(os.environ.get("LOG_FILE", "honey_attack.log")).resolve()

# ─── Basic Auth for SOC Dashboard ───────────────────────────────────────────
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_user = secrets.compare_digest(credentials.username, SOC_USER)
    is_correct_pass = secrets.compare_digest(credentials.password, SOC_PASS)
    if not (is_correct_user and is_correct_pass):
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"}, detail="Unauthorized")
    return credentials.username

# ─── Routes ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(authenticate)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/api/logs")
async def get_logs(user: str = Depends(authenticate)):
    """
    Reads attack logs from the shared .log file using Regex.
    """
    if not LOG_FILE_PATH.exists():
        return []

    # 텍스트 파일 전체 읽기
    with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # 줄바꿈이 포함된 페이로드도 최대한 안전하게 잡도록 정규표현식 개선
    pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d{3})?) - WARNING - \[ATTACK DETECTED\] IP: (.*?) \| Endpoint: (.*?) \| Type: (.*?) \| Payload: ([\s\S]*?)(?=\r?\n\d{4}-\d{2}-\d{2}|\Z)"
    matches = re.findall(pattern, content)
    
    logs = [{
        "timestamp": m[0].strip(),
        "ip": m[1].strip(),
        "endpoint": m[2].strip(),
        "type": m[3].strip(),
        "payload": m[4].strip()
    } for m in matches]

    logs.reverse() # 최신 로그가 먼저 오도록 뒤집기
    return logs

@app.post("/api/ingest")
async def ingest_log(request: Request):
    """
    Log ingestion endpoint - Honeypot server POSTs attack events here.
    """
    shared_secret = request.headers.get("X-Log-Secret", "")
    if shared_secret != LOG_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    
    # 텍스트(.log) 포맷으로 문자열을 조립하여 저장합니다.
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(
            f"{data.get('timestamp', 'N/A')} - WARNING - [ATTACK DETECTED] "
            f"IP: {data.get('ip', '?')} | "
            f"Endpoint: {data.get('endpoint', '?')} | "
            f"Type: {data.get('type', '?')} | "
            f"Payload: {data.get('payload', '')}\n"
        )
        
    return {"status": "ok"}

@app.get("/api/ai-report")
async def ai_report(user: str = Depends(authenticate)):
    """
    Calls OpenAI to generate a security analysis report from the current logs.
    """
    from openai import AsyncOpenAI
    logs_data = await get_logs(user)

    if not logs_data:
        return JSONResponse(status_code=200, content={"status": "no_data", "message": "분석할 공격 로그가 없습니다."})

    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # 토큰 초과 방지를 위해 페이로드 길이를 100자로 제한하고 최근 30개만 분석합니다.
    log_summary = "\n".join([f"[{l['timestamp']}] {l['ip']} → {l['endpoint']} ({l['type']}): {str(l['payload'])[:100]}" for l in logs_data[:30]])

    prompt = f"""You are a cybersecurity analyst. Analyze the following honeypot attack logs and provide:
1. 공격 유형 및 빈도 요약 (Summary of attack types and frequency)
2. 주요 위협 행위자 IP 및 공격 패턴 (Top threat actors and patterns)
3. 공격자 수준 평가 (Assessment of attacker sophistication level)
4. 권장 대응 방안 (Recommended mitigations)

Attack Logs:
{log_summary}

Respond in Korean. Use markdown formatting."""

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        report = completion.choices[0].message.content
        return {"status": "success", "report": report}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"AI 분석 중 오류가 발생했습니다: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    print(f"[Monitor Server] Starting on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)