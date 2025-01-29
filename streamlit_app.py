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

# Color coding for activities
colors = {
    "Work": 'red',
    "Home": 'green',
    "Trans": '#B61515',
    "Sleep": '#AB10B4',
    "Meals": '#FFA500',
    "Personal Time": '#87CEEB'
}

# Initialize schedule and custom color data
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = []
if 'custom_colors' not in st.session_state:
    st.session_state['custom_colors'] = {}
if 'planning_mode' not in st.session_state:
     st.session_state['planning_mode'] = 'Fully Manual Planner'

st.title("Weekly Schedule Plot Generator")

# Option for planning mode, AI mode is removed for now
planning_mode = st.radio("Select Planning Mode", ("Fully Manual Planner",))

# Clear the schedule when planning modes are changed, also re-initialise custom colors
if st.session_state.get('planning_mode') != planning_mode:
        st.session_state['schedule'] = []
        st.session_state['custom_colors'] = {}
        st.session_state['planning_mode'] = planning_mode

# Manual user inputs
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
    edit_duration = st.number_input("Duration (hours)", min_value=0.5, max_value=12.0, step=0.5, value=float(parse_time(st.session_state['edit_entry'][2]) - parse_time(st.session_state['edit_entry'][1])), key = "edit_duration")
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

# Recommend sleep and meal times
def recommend_sleep_and_meals(schedule):
    recommended_schedule = []
    for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
        occupied_times = [(parse_time(start), parse_time(end)) for d, start, end, _ in schedule if d == day]
        occupied_times.sort()

        # Sleep recommendation (7-9 hours per night)
        sleep_start = 23
        sleep_end = sleep_start + 8  # Assume 8 hours of sleep
        while any(sleep_start <= start < sleep_end or sleep_start < end <= sleep_end for start, end in occupied_times):
            sleep_start -= 1
            sleep_end = sleep_start + 8
        if sleep_start >= 0 and sleep_end <= 24:
            recommended_schedule.append((day, f"{sleep_start}:00", f"{sleep_end % 24}:00", "Sleep"))

        # Meal recommendation (3 meals per day)
        meal_times = [8, 13, 19]  # Breakfast, Lunch, Dinner
        for meal_time in meal_times:
            if all(not (meal_time <= start < meal_time + 1 or meal_time < end <= meal_time + 1) for start, end in occupied_times):
                recommended_schedule.append((day, f"{meal_time}:00", f"{meal_time + 1}:00", "Meals"))

    return recommended_schedule

# Generate personal time
def generate_personal_time(schedule):
    personal_time_schedule = []
    for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
        occupied_times = [(parse_time(start), parse_time(end)) for d, start, end, _ in schedule if d == day]
        occupied_times.sort()

        free_time = [(0, 24)]
        for start, end in occupied_times:
            new_free_time = []
            for f_start, f_end in free_time:
                if start > f_start:
                    new_free_time.append((f_start, start))
                if end < f_end:
                    new_free_time.append((end, f_end))
            free_time = new_free_time

        for f_start, f_end in free_time:
            if f_end - f_start >= 0.5:  # Minimum duration of 30 minutes
                personal_time_schedule.append((day, f"{int(f_start)}:{int((f_start - int(f_start)) * 60):02d}", f"{int(f_end)}:{int((f_end - int(f_end)) * 60):02d}", "Personal Time"))

    return personal_time_schedule

# Add recommendations to the schedule
if st.button("Recommend Sleep and Meals"):
    recommended_schedule = recommend_sleep_and_meals(st.session_state['schedule'])
    personal_time_schedule = generate_personal_time(st.session_state['schedule'] + recommended_schedule)
    st.session_state['schedule'].extend(recommended_schedule + personal_time_schedule)
    st.success("Recommended sleep, meals, and personal time added!")

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