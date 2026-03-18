"""
Honeypot Server - EC2 Instance (Port 8080)
Intentionally vulnerable internal-looking system.
Attacker discovers this via port scan of the main server's IP.
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import uvicorn, os

from routers import honey_pages, honey_api

app = FastAPI(
    title="Honey Internal Dev System",
    description="Legacy internal management portal. Vulnerable by design (honeypot).",
    version="0.9.beta",
    # Hide docs from automated scanners (Swagger is still available - a lure)
    docs_url="/api-docs",
    redoc_url=None
)

app.include_router(honey_pages.router)
app.include_router(honey_api.router, prefix="/api")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[Honeypot Server] Starting on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
