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
    fifteen_minutes_ago = now - timedelta(minutes=15)
    future = [i for i in instances if i[0] >= fifteen_minutes_ago]
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
    instances.sort(key=lambda x: x[0])
    last_reload = time.time()

    while True:
        now = datetime.now()

        # reload JSON and instances every 60s to pick up edits and day changes
        if time.time() - last_reload > 60:
            try:
                bosses = load_bosses(JSON_FILE)
                instances = generate_instances(bosses, days_ahead=8)
                instances.sort(key=lambda x: x[0])
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
        # collect unique boss names keeping order
        names = []
        seen = set()
        for dt, name, tstr in entries:
            if name not in seen:
                names.append(name)
                seen.add(name)
        display_names = ", ".join(names)

        # Tooltip
        unique_times = sorted(list(set(i[0] for i in instances)))
        current_time_idx = -1
        try:
            current_time_idx = unique_times.index(next_dt)
        except ValueError:
            pass

        tooltip_lines = []
        if current_time_idx > 0:
            prev_time = unique_times[current_time_idx-1]
            boss_names = ", ".join(sorted(list(set(i[1] for i in instances if i[0] == prev_time))))
            tooltip_lines.append(f"Prev: {boss_names} at {prev_time.strftime('%H:%M')}")

        for i in range(3): # Current and next 2
            idx = current_time_idx + i
            if idx > -1 and idx < len(unique_times):
                time_entry = unique_times[idx]
                boss_names = ", ".join(sorted(list(set(j[1] for j in instances if j[0] == time_entry))))
                
                line = f"{time_entry.strftime('%H:%M')}: {boss_names}"

                if idx == current_time_idx:
                    if delta < timedelta(seconds=0):
                        tooltip_lines.append(f"NOW: {line}")
                    else:
                        tooltip_lines.append(f"Next: {line}")
                else:
                    tooltip_lines.append(f"      {line}")
        
        tooltip = "\n".join(tooltip_lines)

        # Text
        if delta < timedelta(seconds=0):
            despawn_countdown_delta = timedelta(minutes=15) + delta
            countdown = format_duration(despawn_countdown_delta)
            text = f"{display_names} despawns in {countdown}"
        else:
            countdown = format_duration(delta)
            text = f"{display_names} {countdown}"

        print(json.dumps({"text": text, "tooltip": tooltip}))
        sys.stdout.flush()

        # sleep until next second boundary for smoother countdown
        time.sleep(1 - (time.time() % 1))


if __name__ == "__main__":
    main()
