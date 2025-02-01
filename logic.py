from datetime import datetime, timedelta, time
import json
import os

# Load data from JSON file
def load_data():
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return {"schedule": [], "custom_colors": {}}

# Save data to JSON file
def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

# Function to parse time into hours as a float
def parse_time(time_str):
    try:
        h, m = map(int, time_str.split(":"))
        if 0 <= h < 24 and 0 <= m < 60:
            return h + m / 60.0
        else:
            return 0
    except ValueError:
        return 0

# Calculate sleep time
def calculate_sleep_time(schedule):
    if not schedule:
        return None, None
    end_times = [datetime.strptime(entry[2], "%H:%M").time() for entry in schedule]
    latest_end = max(end_times)
    bedtime = datetime.combine(datetime.today(), latest_end) - timedelta(hours=8)
    wake_up_time = bedtime + timedelta(hours=8)
    return wake_up_time.time(), bedtime.time()

# Schedule meals
def schedule_meals(schedule, wake_up_time, bedtime, num_meals):
    day_schedule = [entry for entry in schedule if entry[0] == "Monday"]  # Example: Use Monday's schedule
    day_schedule.sort(key=lambda x: datetime.strptime(x[1], "%H:%M"))
    free_slots = []
    previous_end = datetime.combine(datetime.today(), wake_up_time)
    for entry in day_schedule:
        start_time = datetime.combine(datetime.today(), datetime.strptime(entry[1], "%H:%M").time())
        end_time = datetime.combine(datetime.today(), datetime.strptime(entry[2], "%H:%M").time())
        if start_time > previous_end:
            free_slots.append((previous_end, start_time))
        previous_end = end_time
    if previous_end < datetime.combine(datetime.today(), bedtime):
        free_slots.append((previous_end, datetime.combine(datetime.today(), bedtime)))
    meal_times = []
    if free_slots:
        total_time = sum((slot[1] - slot[0]).total_seconds() for slot in free_slots)
        interval = total_time / (num_meals + 1)
        current_time = datetime.combine(datetime.today(), wake_up_time)
        for _ in range(num_meals):
            current_time += timedelta(seconds=interval)
            meal_times.append(current_time.time())
    return meal_times

# Schedule workout
def schedule_workout(schedule, workout_duration):
    day_schedule = [entry for entry in schedule if entry[0] == "Monday"]  # Example: Use Monday's schedule
    day_schedule.sort(key=lambda x: datetime.strptime(x[1], "%H:%M"))
    free_slots = []
    previous_end = datetime.combine(datetime.today(), time(0, 0))
    for entry in day_schedule:
        start_time = datetime.combine(datetime.today(), datetime.strptime(entry[1], "%H:%M").time())
        end_time = datetime.combine(datetime.today(), datetime.strptime(entry[2], "%H:%M").time())
        if start_time > previous_end:
            free_slots.append((previous_end, start_time))
        previous_end = end_time
    if previous_end < datetime.combine(datetime.today(), time(23, 59)):
        free_slots.append((previous_end, datetime.combine(datetime.today(), time(23, 59))))
    for slot in free_slots:
        if (slot[1] - slot[0]) >= timedelta(minutes=workout_duration):
            return (slot[0], slot[0] + timedelta(minutes=workout_duration))
    return None