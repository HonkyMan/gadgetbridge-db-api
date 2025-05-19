from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response
import time

from services.aggregation import daily_report
from core.config import get_settings

router = APIRouter(prefix="/summary", tags=["Summary"])

settings = get_settings()
rate_limit_cache = {}


def api_key_auth(x_api_key: str | None = Header(None)):
    """
    Проверка API-ключа, передаваемого в заголовке x-api-key.
    Возвращает 401, если ключ не совпадает с ожидаемым.
    """
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail=f"Invalid API key; key: {x_api_key}")


def validate_day(day: str) -> date:
    """
    Валидирует строку даты в формате YYYY-MM-DD.
    Возвращает объект date или выбрасывает HTTP 422 при ошибке.
    """
    try:
        return date.fromisoformat(day)
    except Exception:
        raise HTTPException(status_code=422, detail=f"Некорректный формат даты: {day}. Ожидается YYYY-MM-DD.")


@router.get(
    "/daily",
    dependencies=[Depends(api_key_auth)],
    response_description="Агрегированные данные по активности, сну и весу за выбранную дату",
    responses={
        200: {
            "description": "Успешный ответ с агрегированными данными",
            "content": {
                "application/json": {
                    "example": {
                        "date": "2024-05-18",
                        "sleep": {
                            "total_sessions": 1,
                            "sessions": [
                                {
                                    "timestamp": 1747426920000,
                                    "wakeup_time": 1747455180000,
                                    "is_awake": 1,
                                    "total_duration": 471,
                                    "deep_sleep_duration": 150,
                                    "light_sleep_duration": 250,
                                    "rem_sleep_duration": 71,
                                    "awake_duration": 0
                                }
                            ],
                            "stages": [
                                {"timestamp": 1747426920000, "stage": 3},
                                {"timestamp": 1747431960000, "stage": 4}
                            ]
                        },
                        "activity": {"steps": 12345},
                        "weight": {"weight_kg": 109.0, "delta_kg": 0.5},
                        "goals": None
                    }
                }
            }
        },
        401: {"description": "Неверный API-ключ"},
        422: {"description": "Некорректный формат даты"},
        404: {"description": "Нет данных за выбранную дату"},
        500: {"description": "Внутренняя ошибка сервера"}
    }
)
async def get_daily_report(request: Request, response: Response, day: str = Query(..., description="Дата в формате YYYY-MM-DD, например: 2024-05-18"), x_api_key: str = Header(None)):
    """
    Получить агрегированные данные по активности, сну и весу за выбранную дату.

    **Пример запроса:**
    ```
    GET /summary/daily?day=2024-05-18
    Header: x-api-key: ВАШ_КЛЮЧ
    ```
    **Пример успешного ответа:**
    ```json
    {
        "date": "2024-05-18",
        "sleep": {"total_sessions": 1, "sessions": [...], "stages": [...]},
        "activity": {"steps": 12345},
        "weight": {"weight_kg": 109.0, "delta_kg": 0.5},
        "goals": null
    }
    ```
    """
    # Rate limit по IP
    RATE_LIMIT = settings.rate_limit
    ip = request.client.host
    now = int(time.time())
    window = now // 60
    key = f"{ip}:{window}"
    count = rate_limit_cache.get(key, 0)
    if count >= RATE_LIMIT:
        response.headers["Retry-After"] = "60"
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Попробуйте позже.")
    rate_limit_cache[key] = count + 1
    try:
        day_obj = validate_day(day)
        result = await daily_report(day_obj)
        if not result:
            raise HTTPException(status_code=404, detail="Нет данных за выбранную дату")
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
