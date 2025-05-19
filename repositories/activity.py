from datetime import date
from db.session import db_conn
import logging


async def fetch_steps(day: date) -> int:
    logging.info(f"[activity] Получен запрос на шаги за дату: {day}")
    query = """
        SELECT SUM(STEPS) as steps
        FROM XIAOMI_ACTIVITY_SAMPLE
        WHERE DATE(TIMESTAMP, 'unixepoch', 'localtime') = ?
    """
    logging.debug(f"[activity] SQL: {query.strip()} | params: {day.isoformat()}")
    try:
        async with db_conn() as conn:
            async with conn.execute(query, (day.isoformat(),)) as cursor:
                row = await cursor.fetchone()
                steps = row["steps"] or 0
                if steps == 0:
                    logging.warning(f"[activity] За дату {day} не найдено шагов.")
                else:
                    logging.info(f"[activity] Найдено шагов: {steps}")
                return steps
    except Exception as e:
        logging.error(f"[activity] Ошибка SQL: {e}")
        return 0