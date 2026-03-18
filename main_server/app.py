"""
Main Server - EC2 Public-facing server (Port 80)
Premium honey store website. Clean & secure.
Includes subtle discovery anchors (HTTP header, robots.txt, HTML comment) to guide attackers toward the honeypot.
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response, HTMLResponse
import uvicorn, os

app = FastAPI(
    title="Honey Premium Store",
    description="Official public site for Honey Premium Natural Farm.",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

# ─── Discovery Anchor Middleware ────────────────────────────────────────────
# Leaking the honeypot address via HTTP header – a subtle hint for curious attackers
@app.middleware("http")
async def add_discovery_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Dev-Instance"] = "internal-dev.local:8080"
    response.headers["X-Powered-By"] = "Honey/1.0 (TomcatLegacy/8.5)"  # Fake tech stack
    return response

# ─── Routes ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/robots.txt")
async def robots():
    """
    Discovery Anchor: robots.txt hints at legacy dev server on port 8080.
    """
    content = (
        "User-agent: *\n"
        "Disallow: /admin/\n"
        "Disallow: /internal/\n"
        "Disallow: /internal-dev/\n"
        "\n"
        "# TODO: legacy customer portal – to be decommissioned\n"
        "# Temp staging: port 8080 (internal-dev.honey.local)\n"
    )
    return Response(content=content, media_type="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    print(f"[Main Server] Starting on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
