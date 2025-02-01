import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import timedelta, datetime, time

# Function to parse time into hours as a float
def parse_time(time_str):
    try:
        h, m = map(int, time_str.split(":"))
        if 0 <= h < 24 and 0 <= m < 60:
            return h + m / 60.0
        else:
            st.error("Invalid time format: Hours must be between 0-23 and minutes between 0-59.")
            return 0
    except ValueError:
        st.error("Invalid time format. Please use HH:MM.")
        return 0

# Backend Functions for Optimum Recommendations
def calculate_sleep_time(fixed_obligations):
    # Find the earliest start time and latest end time from obligations
    if not fixed_obligations:
        return None, None
    start_times = [datetime.strptime(obligation[1], "%H:%M").time() for obligation in fixed_obligations]
    end_times = [datetime.strptime(obligation[2], "%H:%M").time() for obligation in fixed_obligations]
    earliest_start = min(start_times)
    latest_end = max(end_times)
    
    # Calculate sleep time (8 hours before latest end time)
    bedtime = datetime.combine(datetime.today(), latest_end) - timedelta(hours=8)
    wake_up_time = datetime.combine(datetime.today(), earliest_start)
    return wake_up_time.time(), bedtime.time()

def schedule_meals(wake_up_time, bedtime, num_meals):
    total_time = datetime.combine(datetime.today(), bedtime) - datetime.combine(datetime.today(), wake_up_time)
    interval = total_time / (num_meals + 1)
    meal_times = [datetime.combine(datetime.today(), wake_up_time) + interval * (i + 1) for i in range(num_meals)]
    return [meal.time() for meal in meal_times]

def schedule_workout(free_slots, workout_duration):
    for slot in free_slots:
        if slot[1] - slot[0] >= workout_duration:
            return (slot[0], slot[0] + workout_duration)
    return None

def calculate_free_slots(fixed_obligations, wake_up_time, bedtime):
    free_slots = []
    fixed_obligations.sort()  # Sort by start time
    previous_end = datetime.combine(datetime.today(), wake_up_time)
    for obligation in fixed_obligations:
        obligation_start = datetime.combine(datetime.today(), datetime.strptime(obligation[1], "%H:%M").time())
        obligation_end = datetime.combine(datetime.today(), datetime.strptime(obligation[2], "%H:%M").time())
        if obligation_start > previous_end:
            free_slots.append((previous_end, obligation_start))
        previous_end = obligation_end
    if previous_end < datetime.combine(datetime.today(), bedtime):
        free_slots.append((previous_end, datetime.combine(datetime.today(), bedtime)))
    return free_slots

# Color coding for activities
colors = {
    "Work": 'red',
    "Home": 'green',
    "Trans": '#B61515',
    "Sleep": '#AB10B4',
    "Meal": '#FFA500',
    "Workout": '#0000FF',
}

# Initialize schedule and custom color data
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = []
if 'custom_colors' not in st.session_state:
    st.session_state['custom_colors'] = {}

st.title("Weekly Schedule Plot Generator")

# Manual Planner
col1, col2, col3, col4 = st.columns(4)
with col1:
    day = st.selectbox("Day", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
with col2:
    start_time = st.time_input("Start Time", value=None, key="start")
with col3:
    duration = st.number_input("Duration (hours)", min_value=0.5, max_value=12.0, step=0.5, value=1.0, key="duration")
with col4:
    activity = st.selectbox("Activity", list(colors.keys()) + ["Custom Activity"])

if activity == "Custom Activity":
    custom_activity = st.text_input("Custom Activity Name")
    activity_color = st.color_picker("Pick a Color", value="#0000FF")
    if custom_activity and activity_color:
        if custom_activity not in st.session_state['custom_colors']:
            st.session_state['custom_colors'][custom_activity] = activity_color
        elif st.session_state['custom_colors'][custom_activity] != activity_color:
            st.session_state['custom_colors'][custom_activity] = activity_color
else:
    custom_activity = activity_color = None

# Add to schedule
if st.button("Add to Schedule"):
    if custom_activity and activity_color:
        activity = custom_activity  # Use the custom activity

    if start_time and duration:
        start_time_str = start_time.strftime("%H:%M")
        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = start_datetime + timedelta(hours=duration)
        end_time_str = end_datetime.time().strftime("%H:%M")
        st.session_state['schedule'].append((day, start_time_str, end_time_str, activity))
        st.success(f"Added: {day} from {start_time_str} to {end_time_str} as {activity}")
    else:
        st.error("Please enter valid start time and duration.")

# Optimum Recommendations Panel
st.sidebar.header("Optimum Recommendations")
if st.session_state['schedule']:
    if st.sidebar.button("Recommend Sleep Timing"):
        wake_up_time, bedtime = calculate_sleep_time(st.session_state['schedule'])
        if wake_up_time and bedtime:
            st.sidebar.write(f"**Recommended Sleep Timing:** {wake_up_time.strftime('%H:%M')} - {bedtime.strftime('%H:%M')}")
        else:
            st.sidebar.write("Unable to recommend sleep timing. Add more obligations.")

    num_meals = st.sidebar.number_input("Number of Meals per Day", min_value=1, max_value=6, value=3)
    if st.sidebar.button("Recommend Meal Timing"):
        wake_up_time, bedtime = calculate_sleep_time(st.session_state['schedule'])
        if wake_up_time and bedtime:
            meal_times = schedule_meals(wake_up_time, bedtime, num_meals)
            st.sidebar.write("**Recommended Meal Times:**")
            for i, meal_time in enumerate(meal_times):
                st.sidebar.write(f"Meal {i+1}: {meal_time.strftime('%H:%M')}")

    workout_days = st.sidebar.number_input("Workout Days per Week", min_value=1, max_value=7, value=3)
    if st.sidebar.button("Recommend Workout Timing"):
        wake_up_time, bedtime = calculate_sleep_time(st.session_state['schedule'])
        if wake_up_time and bedtime:
            free_slots = calculate_free_slots(st.session_state['schedule'], wake_up_time, bedtime)
            workout_time = schedule_workout(free_slots, timedelta(minutes=60))  # Default 60-minute workout
            if workout_time:
                st.sidebar.write(f"**Recommended Workout Time:** {workout_time[0].strftime('%H:%M')} - {workout_time[1].strftime('%H:%M')}")
            else:
                st.sidebar.write("No available slot for workout.")
        else:
            st.sidebar.write("Unable to recommend workout timing. Add more obligations.")

# Display current schedule with edit and delete buttons
if st.session_state['schedule']:
    st.subheader("Current Schedule")
    for index, entry in enumerate(st.session_state['schedule']):
        color_display = st.session_state['custom_colors'].get(entry[3], colors.get(entry[3], 'blue'))
        st.write(f"{index + 1}. {entry[0]}: {entry[1]} to {entry[2]} - {entry[3]} ({color_display})")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"Edit {index + 1}", key=f"edit_button_{index}"):
                st.session_state['edit_index'] = index
                st.session_state['edit_entry'] = entry  # Store the entry being edited
        with col2:
            def delete_entry(index):
                del st.session_state['schedule'][index]
                st.success("Entry deleted!")
                st.rerun()
            if st.button(f"Delete {index + 1}", key=f"delete_button_{index}", on_click=delete_entry, args=(index,)):
                 pass

# If an entry is selected for editing
if 'edit_index' in st.session_state:
    st.subheader("Edit Entry")
    edit_day = st.selectbox("Day", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], index=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].index(st.session_state['edit_entry'][0]), key="edit_day")
    edit_start_time = st.time_input("Start Time", value=datetime.strptime(st.session_state['edit_entry'][1], "%H:%M").time(), key="edit_start_time")
    edit_duration = st.number_input("Duration (hours)", min_value=0.5, max_value=12.0, step=0.5, value=1.0, key="edit_duration")
    edit_activity = st.selectbox("Activity", list(colors.keys()) + ["Custom Activity"], index=list(colors.keys()).index(st.session_state['edit_entry'][3]) if st.session_state['edit_entry'][3] in colors else len(colors), key="edit_activity")

    if st.button("Update Entry", key="update_button"):
        start_datetime = datetime.combine(datetime.today(), edit_start_time)
        end_datetime = start_datetime + timedelta(hours=edit_duration)
        end_time_str = end_datetime.time().strftime("%H:%M")
        updated_entry = (edit_day, edit_start_time.strftime("%H:%M"), end_time_str, edit_activity)

        st.session_state['schedule'][st.session_state['edit_index']] = updated_entry
        del st.session_state['edit_index']  # Clear edit state
        del st.session_state['edit_entry']
        st.success("Entry updated!")
        st.rerun()

# Plot schedule
if st.session_state['schedule']:
    day_labels = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][::-1]
    day_indices = {day: i for i, day in enumerate(day_labels)}

    fig, ax = plt.subplots(figsize=(14, 6))

    for day, start, end, status in st.session_state['schedule']:
        start_time = parse_time(start)
        end_time = parse_time(end)
        duration = end_time - start_time if end_time > start_time else (24 - start_time + end_time)
        color = st.session_state['custom_colors'].get(status, colors.get(status, 'blue'))

        ax.broken_barh([(start_time, duration)], (day_indices[day] - 0.4, 0.8), facecolors=color)
        ax.text(
            start_time + duration / 2,
            day_indices[day],
            f"{status}\n{duration:.1f}h",
            ha='center', va='center',
            fontsize=9, color='white', weight='bold'
        )

    # Format the plot
    ax.set_yticks(range(len(day_labels)))
    ax.set_yticklabels(day_labels)
    ax.set_xticks(range(0, 25, 3))
    ax.set_xticklabels([f"{i}:00" for i in range(0, 25, 3)])
    ax.set_xlim(0, 24)
    ax.set_xlabel("Time of Day")
    ax.set_title("Weekly Schedule")

    grid_linestyle = st.selectbox("Grid Line Style", ['-', '--', '-.', ':'])
    grid_alpha = st.slider("Grid Line Transparency", 0.1, 1.0, 0.5)
    plt.grid(True, linestyle=grid_linestyle, alpha=grid_alpha)

    # Display plot
    st.pyplot(fig)

    # Option to download the schedule as an image
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    st.download_button(
        label="Download Schedule as Image",
        data=buf,
        file_name="schedule_plot.png",
        mime="image/png",
    )
    buf.close()