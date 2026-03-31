import streamlit as st
from pawpal_system import Constraints, Owner, Pet, PriorityLevel, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# Persist domain objects across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time_minutes=120)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

if not st.session_state.owner.pets:
    st.session_state.owner.add_pet(Pet(name="Mochi", species="dog"))

if "selected_pet_index" not in st.session_state:
    st.session_state.selected_pet_index = 0

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner + Pets")
owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
available_time = st.number_input(
    "Available time today (minutes)",
    min_value=1,
    max_value=1440,
    value=st.session_state.owner.available_time_minutes,
)

st.session_state.owner.name = owner_name
st.session_state.owner.available_time_minutes = int(available_time)

species_options = ["dog", "cat", "other"]

with st.form("add_pet_form"):
    new_pet_name = st.text_input("New pet name", value="")
    new_pet_species = st.selectbox("New pet species", species_options, index=0)
    add_pet_clicked = st.form_submit_button("Add pet")

if add_pet_clicked:
    if new_pet_name.strip():
        new_pet = Pet(name=new_pet_name.strip(), species=new_pet_species)
        st.session_state.owner.add_pet(new_pet)
        st.session_state.selected_pet_index = len(st.session_state.owner.pets) - 1
        st.success(f"Added pet: {new_pet.name}")
    else:
        st.error("Please enter a pet name.")

pet_names = [f"{pet.name} ({pet.species})" for pet in st.session_state.owner.pets]
selected_label = st.selectbox(
    "Select pet",
    pet_names,
    index=min(st.session_state.selected_pet_index, len(pet_names) - 1),
)
st.session_state.selected_pet_index = pet_names.index(selected_label)
selected_pet = st.session_state.owner.pets[st.session_state.selected_pet_index]

st.caption(f"Active pet: {selected_pet.name} ({selected_pet.species})")

st.markdown("### Tasks")
st.caption("Add tasks to the selected pet using your core classes.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk", key="task_title")
with col2:
    duration = st.number_input(
        "Duration (minutes)", min_value=1, max_value=240, value=20, key="task_duration"
    )
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="task_priority")

col4, col5 = st.columns(2)
with col4:
    category = st.text_input("Category", value="walk", key="task_category")
with col5:
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=1, key="task_frequency")

if st.button("Add task"):
    new_task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=PriorityLevel(priority),
        category=category or None,
        frequency=frequency,
    )
    if new_task.validate():
        selected_pet.add_task(new_task)
        st.success(f"Added task '{new_task.title}' to {selected_pet.name}.")
    else:
        st.error("Task data is invalid. Check title, duration, priority, and frequency.")

st.markdown("#### Task View")
view_filter = st.selectbox(
    "Completion filter",
    ["all", "incomplete", "completed"],
    index=0,
)

if selected_pet.tasks:
    all_pet_tasks = st.session_state.scheduler.filter_tasks_by_completion_or_pet_name(
        st.session_state.owner.get_all_tasks(),
        pet_name=selected_pet.name,
    )

    if view_filter == "completed":
        filtered_tasks = st.session_state.scheduler.filter_tasks_by_completion_or_pet_name(
            all_pet_tasks,
            completed=True,
        )
    elif view_filter == "incomplete":
        filtered_tasks = st.session_state.scheduler.filter_tasks_by_completion_or_pet_name(
            all_pet_tasks,
            completed=False,
        )
    else:
        filtered_tasks = all_pet_tasks

    sorted_tasks = st.session_state.scheduler.sort_by_time(filtered_tasks)

    st.success(f"Showing {len(sorted_tasks)} sorted task(s) for {selected_pet.name}.")
    st.table(
        [
            {
                "title": task.title,
                "time": task.time or "--",
                "scheduled_minute": task.scheduled_minute if task.scheduled_minute is not None else "--",
                "duration_minutes": task.duration_minutes,
                "priority": task.priority.value,
                "category": task.category or "--",
                "frequency": task.frequency,
                "completed": task.completed,
            }
            for task in sorted_tasks
        ]
    )

    conflict_warnings = st.session_state.scheduler.detect_scheduling_conflicts(
        st.session_state.owner.get_all_tasks()
    )
    if conflict_warnings:
        st.warning("Scheduling conflicts detected:")
        for warning in conflict_warnings:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts detected.")
else:
    st.info(f"No tasks yet for {selected_pet.name}. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a plan using your Scheduler and Constraints classes.")

max_total_minutes = st.number_input(
    "Constraint: max scheduled minutes",
    min_value=1,
    max_value=1440,
    value=min(120, st.session_state.owner.available_time_minutes),
)


def minute_to_hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"

if st.button("Generate schedule"):
    st.session_state.scheduler = Scheduler(Constraints(max_total_minutes=int(max_total_minutes)))
    schedule = st.session_state.scheduler.generate_daily_plan(
        owner=st.session_state.owner,
        pet=selected_pet,
        tasks=selected_pet.get_incomplete_tasks(),
    )

    if schedule.items:
        st.success("Schedule generated successfully.")
        st.write(f"Today's schedule for {selected_pet.name}:")
        st.table(
            [
                {
                    "start": minute_to_hhmm(start_minute),
                    "end": minute_to_hhmm(start_minute + task.duration_minutes),
                    "task": task.title,
                    "priority": task.priority.value,
                    "category": task.category,
                }
                for start_minute, task in schedule.items
            ]
        )
    else:
        st.warning("No tasks could be scheduled with current constraints.")

    if schedule.unscheduled:
        st.write("Unscheduled tasks:")
        st.table(
            [
                {"task": task.title, "reason": reason}
                for task, reason in schedule.unscheduled
            ]
        )

    st.info(schedule.get_explanation())
