from datetime import datetime
from database import get_db


def start_using_desk(name, desk_id):
    if name.strip() == "":
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        desk = conn.execute(
            "SELECT * FROM desks WHERE id = ?",
            (desk_id,)
        ).fetchone()

        if desk and desk["user_name"] is None:
            conn.execute(
                "UPDATE desks SET user_name = ? WHERE id = ?",
                (name, desk_id)
            )

            conn.execute("""
                INSERT INTO history (user_name, desk_id, start_time)
                VALUES (?, ?, ?)
            """, (name, desk_id, now))


def release_desk(desk_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        desk = conn.execute(
            "SELECT * FROM desks WHERE id = ?",
            (desk_id,)
        ).fetchone()

        if desk and desk["user_name"]:
            conn.execute("""
                UPDATE history
                SET end_time = ?
                WHERE desk_id = ? AND user_name = ? AND end_time IS NULL
            """, (now, desk_id, desk["user_name"]))

            conn.execute(
                "UPDATE desks SET user_name = NULL WHERE id = ?",
                (desk_id,)
            )


def get_dashboard_data():
    with get_db() as conn:
        desks = conn.execute("SELECT * FROM desks").fetchall()
        raw_history = conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT 20"
        ).fetchall()

    history = _build_history_with_duration(raw_history)
    analysis = _build_weekday_hour_analysis(raw_history)
    summary = _build_summary(desks, raw_history)

    return {
        "desks": desks,
        "history": history,
        "analysis": analysis,
        "summary": summary
    }


def _build_history_with_duration(raw_history):
    history_with_duration = []

    for h in raw_history:
        start = h["start_time"]
        end = h["end_time"]

        if start and end:
            start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
            minutes = int((end_dt - start_dt).total_seconds() / 60)
            duration_str = f"{minutes}分"
        else:
            duration_str = "使用中"

        history_with_duration.append({
            "user_name": h["user_name"],
            "desk_id": h["desk_id"],
            "start_time": start,
            "end_time": end,
            "duration": duration_str
        })

    return history_with_duration


# 🔥 混雑カード用ロジック（ここが新）
def _build_weekday_hour_analysis(raw_history):
    weekday_hour_counts = {}
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    for h in raw_history:
        if h["start_time"]:
            dt = datetime.strptime(h["start_time"], "%Y-%m-%d %H:%M:%S")
            key = (dt.weekday(), dt.hour)
            weekday_hour_counts[key] = weekday_hour_counts.get(key, 0) + 1

    busy_threshold = 3
    medium_threshold = 2

    day_to_levels = {i: [] for i in range(7)}

    for (wd, hour), count in weekday_hour_counts.items():
        if count >= busy_threshold:
            level = "混雑"
        elif count >= medium_threshold:
            level = "やや混雑"
        else:
            continue

        day_to_levels[wd].append((hour, level))

    analysis = []

    for wd in range(7):
        items = sorted(day_to_levels[wd])
        if not items:
            continue

        start = items[0][0]
        prev = items[0][0]
        current_level = items[0][1]

        for hour, level in items[1:]:
            if hour == prev + 1 and level == current_level:
                prev = hour
            else:
                analysis.append({
                    "day": weekdays[wd],
                    "start_hour": start,
                    "end_hour": prev + 1,
                    "level": current_level
                })
                start = hour
                prev = hour
                current_level = level

        analysis.append({
            "day": weekdays[wd],
            "start_hour": start,
            "end_hour": prev + 1,
            "level": current_level
        })

    return analysis


def _build_summary(desks, raw_history):
    using_count = sum(1 for d in desks if d["user_name"])
    free_count = len(desks) - using_count
    total_usage_count = len(raw_history)

    finished_records = [h for h in raw_history if h["start_time"] and h["end_time"]]

    if finished_records:
        total_minutes = 0
        for h in finished_records:
            start_dt = datetime.strptime(h["start_time"], "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(h["end_time"], "%Y-%m-%d %H:%M:%S")
            total_minutes += int((end_dt - start_dt).total_seconds() / 60)

        avg_minutes = total_minutes // len(finished_records)
    else:
        avg_minutes = 0

    return {
        "using_count": using_count,
        "free_count": free_count,
        "total_usage_count": total_usage_count,
        "avg_minutes": avg_minutes
    }