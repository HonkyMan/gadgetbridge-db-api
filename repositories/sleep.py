from datetime import date, datetime, timedelta, time
from db.session import db_conn
import logging

async def fetch_sleep(day: date) -> dict:
    logging.info(f"[sleep] Получен запрос на сон за дату: {day}")
    # Определяем временной диапазон: с 18:00 предыдущего дня до 18:00 текущего дня
    start_dt = datetime.combine(day - timedelta(days=1), time(18, 0))
    end_dt = datetime.combine(day, time(18, 0))
    start_ts = int(start_dt.timestamp() * 1000)  # теперь секунды
    end_ts = int(end_dt.timestamp() * 1000)
    logging.debug(f"[sleep] SQL диапазон: {start_ts} - {end_ts}")
    try:
        async with db_conn() as conn:
            logging.debug(f"[sleep] Запрос к XIAOMI_SLEEP_TIME_SAMPLE: {start_ts} - {end_ts}")
            # Получаем агрегированные данные из XIAOMI_SLEEP_TIME_SAMPLE
            query_time = '''
                SELECT * FROM XIAOMI_SLEEP_TIME_SAMPLE
                WHERE TIMESTAMP >= ? AND TIMESTAMP < ?
                ORDER BY TIMESTAMP ASC
            '''
            async with conn.execute(query_time, (start_ts, end_ts)) as cursor:
                time_samples = await cursor.fetchall()
                if not time_samples:
                    logging.warning(f"[sleep] Нет сессий сна за период {start_ts} - {end_ts}")
                else:
                    logging.info(f"[sleep] Найдено сессий сна: {len(time_samples)}")

            logging.debug(f"[sleep] Запрос к XIAOMI_SLEEP_STAGE_SAMPLE: {start_ts} - {end_ts}")
            # Получаем фазы сна из XIAOMI_SLEEP_STAGE_SAMPLE
            query_stage = '''
                SELECT * FROM XIAOMI_SLEEP_STAGE_SAMPLE
                WHERE TIMESTAMP >= ? AND TIMESTAMP < ?
                ORDER BY TIMESTAMP ASC
            '''
            async with conn.execute(query_stage, (start_ts, end_ts)) as cursor:
                stage_samples = await cursor.fetchall()
                if not stage_samples:
                    logging.warning(f"[sleep] Нет фаз сна за период {start_ts} - {end_ts}")
                else:
                    logging.info(f"[sleep] Найдено фаз сна: {len(stage_samples)}")
    except Exception as e:
        logging.error(f"[sleep] Ошибка SQL: {e}")
        time_samples = []
        stage_samples = []
    # Агрегируем данные
    sleep_info = {
        "total_sessions": len(time_samples),
        "sessions": [],
        "stages": [],
    }

    for row in time_samples:
        sleep_info["sessions"].append({
            "timestamp": row["TIMESTAMP"],
            "wakeup_time": row["WAKEUP_TIME"],
            "is_awake": row["IS_AWAKE"],
            "total_duration": row["TOTAL_DURATION"],
            "deep_sleep_duration": row["DEEP_SLEEP_DURATION"],
            "light_sleep_duration": row["LIGHT_SLEEP_DURATION"],
            "rem_sleep_duration": row["REM_SLEEP_DURATION"],
            "awake_duration": row["AWAKE_DURATION"],
        })

    for row in stage_samples:
        sleep_info["stages"].append({
            "timestamp": row["TIMESTAMP"],
            "stage": row["STAGE"],
        })

    return sleep_info