#!/usr/bin/env python3
import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

JSON_FILE = str(Path(__file__).resolve().parent / "timers.json")
DATE_FMT = "%Y-%m-%dT%H:%M:%S"


def load_bosses(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_instances(bosses, days_ahead=7):
    now = datetime.now()
    instances = []
    for day_offset in range(0, days_ahead + 1):
        date = (now + timedelta(days=day_offset)).date()
        weekday = date.isoweekday()  # 1=Mon ..7=Sun matches your JSON
        date_str = date.isoformat()
        for boss in bosses:
            for t in boss.get("times", []):
                if weekday in t.get("days", []):
                    dt_str = f"{date_str}T{t['time']}:00"
                    try:
                        dt = datetime.fromisoformat(dt_str)
                    except Exception:
                        continue
                    instances.append((dt, boss.get("name", ""), t["time"]))
    return instances


def find_next(instances):
    now = datetime.now()
    future = [i for i in instances if i[0] >= now]
    if not future:
        return None
    future.sort(key=lambda x: x[0])
    next_dt = future[0][0]
    same = [i for i in future if i[0] == next_dt]
    return next_dt, same


def format_duration(td):
    total = int(td.total_seconds())
    if total < 0:
        total = 0
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    try:
        bosses = load_bosses(JSON_FILE)
    except Exception as e:
        print("Error loading JSON")
        print(f"tooltip:Failed to load {JSON_FILE}: {e}")
        sys.exit(1)

    # Pre-generate instances once and refresh each minute in case of day rollover / JSON changes
    instances = generate_instances(bosses, days_ahead=8)
    last_reload = time.time()

    while True:
        now = datetime.now()

        # reload JSON and instances every 60s to pick up edits and day changes
        if time.time() - last_reload > 60:
            try:
                bosses = load_bosses(JSON_FILE)
                instances = generate_instances(bosses, days_ahead=8)
            except Exception:
                pass
            last_reload = time.time()

        nxt = find_next(instances)
        if not nxt:
            print("No upcoming spawns?!")
            sys.stdout.flush()
            time.sleep(5)
            continue

        next_dt, entries = nxt
        delta = next_dt - now
        countdown = format_duration(delta)

        # collect unique boss names keeping order
        names = []
        seen = set()
        tooltip_lines = []
        for dt, name, tstr in entries:
            if name not in seen:
                names.append(name)
                seen.add(name)
            tooltip_lines.append(f"{name} — {tstr}")

        display_names = ", ".join(names)
        tooltip = "\n".join(tooltip_lines)

        print(json.dumps({"text": f"{display_names} {countdown}", "tooltip": tooltip}))
        sys.stdout.flush()

        # sleep until next second boundary for smoother countdown
        time.sleep(1 - (time.time() % 1))


if __name__ == "__main__":
    main()
