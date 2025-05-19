from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import summary
from core.config import get_settings
import logging

app = FastAPI(title="Gadgetbridge Health API")

settings = get_settings()
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(message)s')

@app.middleware("http")
async def log_requests(request, call_next):
    logging.info(f"HTTP {request.method} {request.url}")
    response = await call_next(request)
    if response.status_code >= 500:
        logging.error(f"Response {response.status_code} for {request.method} {request.url}")
    elif response.status_code >= 400:
        logging.warning(f"Response {response.status_code} for {request.method} {request.url}")
    else:
        logging.info(f"Response {response.status_code} for {request.method} {request.url}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # при необходимости сузить
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summary.router)

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/health", tags=["Health"])
async def healthcheck():
    """
    Healthcheck: проверяет доступность БД.
    """
    from db.session import db_conn
    try:
        async with db_conn() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ok", "db": "available"}
    except Exception as e:
        logging.error(f"Healthcheck DB error: {e}")
        return {"status": "fail", "db": "unavailable"}

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Shutting down server, закрытие соединений с БД (если требуется)")
    # Если появятся глобальные соединения или пул, закрывайте их здесь
    # Сейчас используется только async with db_conn(), поэтому ничего закрывать не требуется