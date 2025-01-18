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
}

# Initialize schedule and custom color data
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = []
if 'custom_colors' not in st.session_state:
    st.session_state['custom_colors'] = {}
if 'planning_mode' not in st.session_state:
     st.session_state['planning_mode'] = 'Fully Manual Planner'

st.title("Weekly Schedule Plot Generator")

# Option for AI-assisted planning
planning_mode = st.radio("Select Planning Mode", ("Fully Manual Planner", "AI Assisted"))

# Clear the schedule when planning modes are changed, also re-initialise custom colors
if st.session_state.get('planning_mode') != planning_mode:
        st.session_state['schedule'] = []
        st.session_state['custom_colors'] = {}
        st.session_state['planning_mode'] = planning_mode

if planning_mode == "AI Assisted":
    st.subheader("AI-Assisted Schedule")
    wake_time = st.time_input("Wake-up Time")
    work_hours = st.slider("Work Duration (hours)", 4, 12, 8)
    transport_duration = st.slider("Commute Time (hours)", 0.5, 3.0, 1.0)
    sleep_goal = st.slider("Sleep Duration (hours)", 4, 10, 7)

    if wake_time:
        wake_datetime = datetime.combine(datetime.today(), wake_time)
        breakfast_time = (wake_datetime + timedelta(minutes=30)).time().strftime("%H:%M")
        lunch_time = (wake_datetime + timedelta(hours=work_hours // 2)).time().strftime("%H:%M")
        dinner_time = (wake_datetime + timedelta(hours=work_hours + transport_duration + 1)).time().strftime("%H:%M")
        sleep_time = (wake_datetime + timedelta(hours=sleep_goal)).time().strftime("%H:%M")

        st.session_state['schedule'] = [
            ("Monday", wake_time.strftime("%H:%M"), sleep_time, "Sleep"),
            ("Monday", breakfast_time, lunch_time, "Home"),
            ("Monday", lunch_time, dinner_time, "Work"),
            ("Monday", dinner_time, sleep_time, "Trans"),
        ]
        st.success("AI-assisted schedule generated!")

else:
    # Manual user inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        day = st.selectbox("Day", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
    with col2:
        start_time = st.time_input("Start Time", value=None, key="start")
    with col3:
        end_time = st.time_input("End Time", value=None, key="end")
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

        if start_time and end_time:
            start_time_str = start_time.strftime("%H:%M")
            end_time_str = end_time.strftime("%H:%M")
            st.session_state['schedule'].append((day, start_time_str, end_time_str, activity))
            st.success(f"Added: {day} from {start_time_str} to {end_time_str} as {activity}")
        else:
            st.error("Please enter valid start and end times.")

# Display current schedule with edit and delete buttons
if st.session_state['schedule']:
    st.subheader("Current Schedule")
    for index, entry in enumerate(st.session_state['schedule']):
        color_display = st.session_state['custom_colors'].get(entry[3], colors.get(entry[3], 'blue'))
        st.write(f"{index + 1}. {entry[0]}: {entry[1]} to {entry[2]} - {entry[3]} ({color_display})")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"Edit {index + 1}"):
                st.session_state['edit_index'] = index
                st.session_state['edit_entry'] = entry  # Store the entry being edited
        with col2:
            if st.button(f"Delete {index + 1}"):
                del st.session_state['schedule'][index]
                st.success("Entry deleted!")
                st.rerun()

# If an entry is selected for editing
if 'edit_index' in st.session_state:
    st.subheader("Edit Entry")
    edit_day = st.selectbox("Day", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], index=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].index(st.session_state['edit_entry'][0]))
    edit_start_time = st.time_input("Start Time", value=st.session_state['edit_entry'][1])
    edit_end_time = st.time_input("End Time", value=st.session_state['edit_entry'][2])
    edit_activity = st.selectbox("Activity", list(colors.keys()) + ["Custom Activity"], index=list(colors.keys()).index(st.session_state['edit_entry'][3]) if st.session_state['edit_entry'][3] in colors else len(colors))

    if st.button("Update Entry"):
        updated_entry = (edit_day, edit_start_time.strftime("%H:%M"), edit_end_time.strftime("%H:%M"), edit_activity)
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