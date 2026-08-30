import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from app import config

app = FastAPI(title="Razorpay AI Revenue Recovery Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo simplification: phones on the venue WiFi hit this from unpredictable IPs
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

print(f"[startup] LLM_PROVIDER={config.LLM_PROVIDER}")
if config.LLM_PROVIDER == "ollama":
    print(f"[startup] OLLAMA_MODEL={config.OLLAMA_MODEL}")
else:
    print(f"[startup] GROQ_MODEL={config.GROQ_MODEL}")


FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)
index_html = os.path.join(FRONTEND_DIST, "index.html")
has_frontend = os.path.isfile(index_html)

if has_frontend:
    # SPA client-side routes: must return index.html so React Router handles them
    @app.get("/submit")
    async def serve_submit():
        return FileResponse(index_html)

    @app.get("/dashboard")
    async def serve_dashboard():
        return FileResponse(index_html)

    @app.get("/store")
    async def serve_store():
        return FileResponse(index_html)

    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/")
    def health():
        return {"status": "ok"}
