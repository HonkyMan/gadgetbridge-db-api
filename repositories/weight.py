from datetime import date, datetime, timedelta, time
from db.session import db_conn
from core.config import get_settings
import logging

async def fetch_weight(day: date) -> tuple[float | None, float | None]:
    settings = get_settings()
    min_weight = settings.min_my_weight
    max_weight = settings.max_my_weight

    logging.info(f"[weight] Получен запрос на вес за дату: {day}, диапазон: {min_weight}-{max_weight}")
    
    day_start = datetime.combine(day, time(0, 0))
    day_end = datetime.combine(day, time(23, 59, 59, 999000))
    start_ts = int(day_start.timestamp() * 1000)  # теперь миллисекунды
    end_ts = int(day_end.timestamp() * 1000)
    
    logging.debug(f"[weight] SQL диапазон: {start_ts} - {end_ts}")
    
    try:
        async with db_conn() as conn:
            logging.debug(f"[weight] Запрос к MI_SCALE_WEIGHT_SAMPLE: {start_ts} - {end_ts}")
            query = '''
                SELECT * FROM MI_SCALE_WEIGHT_SAMPLE
                WHERE TIMESTAMP >= ? AND TIMESTAMP <= ?
                AND WEIGHT_KG >= ? AND WEIGHT_KG <= ?
                ORDER BY TIMESTAMP DESC
            '''
            async with conn.execute(query, (start_ts, end_ts, min_weight, max_weight)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    logging.warning(f"[weight] Нет измерений веса за дату {day}")
                else:
                    logging.info(f"[weight] Найдено измерений веса: {len(rows)}")
    except Exception as e:
        logging.error(f"[weight] Ошибка SQL: {e}")
        rows = []
    if not rows:
        return None, None
    
    weight_now = rows[0]["WEIGHT_KG"]
    prev_day = day - timedelta(days=1)
    prev_start = datetime.combine(prev_day, time(0, 0))
    prev_end = datetime.combine(prev_day, time(23, 59, 59, 999000))
    prev_start_ts = int(prev_start.timestamp() * 1000)
    prev_end_ts = int(prev_end.timestamp() * 1000)
    
    logging.debug(f"[weight] SQL диапазон (предыдущий день): {prev_start_ts} - {prev_end_ts}")
    
    try:
        async with db_conn() as conn:
            logging.debug(f"[weight] Запрос к MI_SCALE_WEIGHT_SAMPLE (предыдущий день): {prev_start_ts} - {prev_end_ts}")
            query_prev = '''
                SELECT * FROM MI_SCALE_WEIGHT_SAMPLE
                WHERE TIMESTAMP >= ? AND TIMESTAMP <= ?
                AND WEIGHT_KG >= ? AND WEIGHT_KG <= ?
                ORDER BY TIMESTAMP DESC
            '''
            async with conn.execute(query_prev, (prev_start_ts, prev_end_ts, min_weight, max_weight)) as cursor:
                prev_rows = await cursor.fetchall()
                if not prev_rows:
                    logging.warning(f"[weight] Нет измерений веса за предыдущий день {prev_day}")
                else:
                    logging.info(f"[weight] Найдено измерений веса за предыдущий день: {len(prev_rows)}")
    except Exception as e:
        logging.error(f"[weight] Ошибка SQL (предыдущий день): {e}")
        prev_rows = []
    weight_prev = prev_rows[0]["WEIGHT_KG"] if prev_rows else None
    weight_delta = weight_now - weight_prev if weight_prev is not None else None
    return weight_now, weight_delta
