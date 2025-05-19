from datetime import date, timedelta
from repositories import activity, sleep, weight


async def daily_report(day: date):
    steps = await activity.fetch_steps(day)
    sleep_data = await sleep.fetch_sleep(day)
    weight_now, weight_delta = await weight.fetch_weight(day)
    goals = None

    return {
        "date": day.isoformat(),
        "sleep": sleep_data,
        "activity": {"steps": steps},
        "weight": {"weight_kg": weight_now, "delta_kg": weight_delta},
        "goals": goals,
    }