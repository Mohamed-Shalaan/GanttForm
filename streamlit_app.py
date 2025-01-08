import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO

# Function to parse time into hours as a float
def parse_time(time_str):
    h, m = map(int, time_str.split(":"))
    return h + m / 60.0

# Color coding for activities
colors = {
    "At Work": 'red',
    "HomeXBusiness": 'green',
    "Trans.2.W": '#B61515',
    "Trans.2.H": '#288057',
    "Sleep": '#AB10B4',
}

# Initialize schedule and custom color data
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = []
if 'custom_colors' not in st.session_state:
    st.session_state['custom_colors'] = {}

st.title("Weekly Schedule Plot Generator")

# User inputs
col1, col2, col3 = st.columns(3)
with col1:
    day = st.selectbox("Day", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
with col2:
    start_time = st.text_input("Start Time (HH:MM)", value="00:00")
with col3:
    end_time = st.text_input("End Time (HH:MM)", value="01:00")
activity = st.selectbox("Activity", list(colors.keys()) + ["Custom Activity"])
custom_activity, activity_color = None, None
if activity == "Custom Activity":
    custom_activity = st.text_input("Custom Activity Name")
    activity_color = st.color_picker("Pick a Color", value="#0000FF")

# Add to schedule
if st.button("Add to Schedule"):
    if custom_activity and activity_color:
        # Check if custom activity is already in custom_colors
        if custom_activity not in st.session_state['custom_colors']:
            st.session_state['custom_colors'][custom_activity] = activity_color
        else:
            # Update the color if it differs
            if st.session_state['custom_colors'][custom_activity] != activity_color:
                st.session_state['custom_colors'][custom_activity] = activity_color
        activity = custom_activity  # Use the custom activity

    # Add the activity to the schedule
    st.session_state['schedule'].append((day, start_time, end_time, activity))
    st.success(f"Added: {day} from {start_time} to {end_time} as {activity}")

# Display current schedule
if st.session_state['schedule']:
    st.subheader("Current Schedule")
    for entry in st.session_state['schedule']:
        color_display = st.session_state['custom_colors'].get(entry[3], colors.get(entry[3], 'blue'))
        st.write(f"{entry[0]}: {entry[1]} to {entry[2]} - {entry[3]} ({color_display})")

    # Plot schedule
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
    plt.grid(True, linestyle='--', alpha=0.5)

    st.pyplot(fig)

    # Add download button
    buf = BytesIO()
    fig.savefig(buf, format="png")
    st.download_button(
        label="Download Schedule as Image",
        data=buf.getvalue(),
        file_name="weekly_schedule.png",
        mime="image/png"
    )

# Clear schedule button
if st.button("Clear Schedule"):
    st.session_state['schedule'] = []
    st.session_state['custom_colors'] = {}
    st.success("Schedule cleared!")
