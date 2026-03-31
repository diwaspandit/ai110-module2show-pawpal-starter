# testing ground to verify logic works in terminal before integrating with UI

from pawpal_system import (
	Constraints,
	Owner,
	Pet,
	PriorityLevel,
	Scheduler,
	Task,
)


def minute_to_hhmm(minute: int) -> str:
	hours = minute // 60
	mins = minute % 60
	return f"{hours:02d}:{mins:02d}"


def print_schedule_for_pet(pet: Pet, scheduler: Scheduler) -> None:
	if pet.owner is None:
		print(f"\nNo owner assigned for {pet.name}.")
		return

	schedule = scheduler.generate_daily_plan(
		owner=pet.owner,
		pet=pet,
		tasks=pet.get_incomplete_tasks(),
	)

	print(f"\n🐾 {pet.name} ({pet.species.title()})")
	print("-" * 52)
	if not schedule.items:
		print("No scheduled tasks.")
	else:
		for start_minute, task in schedule.items:
			start = minute_to_hhmm(start_minute)
			end = minute_to_hhmm(start_minute + task.duration_minutes)
			category = task.category or "general"
			print(
				f"{start} - {end}  |  {task.title:<18} "
				f"| {task.priority.value.upper():<6} | {category}"
			)

	if schedule.unscheduled:
		print("\nUnscheduled:")
		for task, reason in schedule.unscheduled:
			print(f"  - {task.title}: {reason}")

	print(f"\nTotal planned time: {schedule.get_total_duration()} minutes")
	print(f"Summary: {schedule.get_explanation()}")


def print_sorted_tasks_for_pet(pet: Pet, scheduler: Scheduler) -> None:
	"""Show tasks sorted by HH:MM time using Scheduler.sort_by_time."""
	print(f"\nSorted tasks for {pet.name} (by time):")
	print("-" * 52)
	ordered = scheduler.sort_by_time(pet.tasks)
	for task in ordered:
		time_label = task.time if task.time is not None else "(no time)"
		status = "done" if task.completed else "open"
		print(
			f"{time_label:>7}  |  {task.title:<18} "
			f"| {task.priority.value.upper():<6} | {status}"
		)


def print_filtered_task_views(owner: Owner, scheduler: Scheduler) -> None:
	"""Show filtered task lists by completion status and pet name."""
	all_tasks = owner.get_all_tasks()

	incomplete = scheduler.filter_tasks_by_completion_or_pet_name(
		all_tasks,
		completed=False,
	)
	mochi_only = scheduler.filter_tasks_by_completion_or_pet_name(
		all_tasks,
		pet_name="Mochi",
	)

	print("\nFiltered view: incomplete tasks")
	print("-" * 52)
	for task in incomplete:
		pet_name = task.pet.name if task.pet is not None else "Unknown"
		print(f"- {task.title} ({pet_name})")

	print("\nFiltered view: tasks for Mochi")
	print("-" * 52)
	for task in mochi_only:
		status = "done" if task.completed else "open"
		print(f"- {task.title} ({status})")


def print_conflict_warnings(owner: Owner, scheduler: Scheduler) -> None:
	"""Print lightweight conflict warnings for overlapping task times."""
	warnings = scheduler.detect_scheduling_conflicts(owner.get_all_tasks())
	print("\nConflict detection")
	print("-" * 52)
	if not warnings:
		print("No time conflicts detected.")
		return
	for warning in warnings:
		print(f"⚠️  {warning}")


def main() -> None:
	# Owner
	owner = Owner(
		name="Jordan",
		available_time_minutes=120,
		preferences={"day_start_minute": 7 * 60},
	)

	# Pets
	dog = Pet(name="Mochi", species="dog", age=4)
	cat = Pet(name="Luna", species="cat", age=2)
	owner.add_pet(dog)
	owner.add_pet(cat)

	# Tasks (at least three, with different times/durations)
	# Intentionally added out of chronological order to test sort_by_time().
	dog.add_task(
		Task(
			title="Breakfast",
			duration_minutes=15,
			priority=PriorityLevel.MEDIUM,
			time="08:00",
			category="feeding",
			description="Serve morning meal",
		)
	)
	dog.add_task(
		Task(
			title="Morning walk",
			duration_minutes=30,
			priority=PriorityLevel.HIGH,
			time="07:30",
			category="walk",
			description="Neighborhood walk before work",
		)
	)
	cat.add_task(
		Task(
			title="Play session",
			duration_minutes=20,
			priority=PriorityLevel.LOW,
			time="18:00",
			category="enrichment",
			description="Interactive toy play",
		)
	)
	cat.add_task(
		Task(
			title="Medication",
			duration_minutes=10,
			priority=PriorityLevel.HIGH,
			time="07:30",
			category="meds",
			description="Daily allergy medication",
		)
	)

	# Mark one task complete to demonstrate completion filtering.
	cat.tasks[1].mark_complete()

	constraints = Constraints(max_total_minutes=90)
	scheduler = Scheduler(constraints=constraints)

	print("=" * 52)
	print("              TODAY'S SCHEDULE")
	print("=" * 52)
	print(f"Owner: {owner.name}")
	print(f"Daily time budget: {owner.available_time_minutes} minutes")

	for pet in owner.pets:
		print_sorted_tasks_for_pet(pet, scheduler)

	print_filtered_task_views(owner, scheduler)
	print_conflict_warnings(owner, scheduler)

	for pet in owner.pets:
		print_schedule_for_pet(pet, scheduler)

	print("\nDone.")


if __name__ == "__main__":
	main()

