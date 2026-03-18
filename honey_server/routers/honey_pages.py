"""
Honeypot Page Router
Serves the legacy-styled HTML pages for the honeypot server.
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/board", response_class=HTMLResponse)
async def board_page(request: Request):
    return templates.TemplateResponse("board.html", {"request": request})

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@router.get("/decoy-admin", response_class=HTMLResponse)
async def decoy_admin(request: Request):
    # This page is reached after SQLi bypass
    return templates.TemplateResponse("decoy_admin.html", {"request": request})
