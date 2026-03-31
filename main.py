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
	dog.add_task(
		Task(
			title="Morning walk",
			duration_minutes=30,
			priority=PriorityLevel.HIGH,
			category="walk",
			description="Neighborhood walk before work",
		)
	)
	dog.add_task(
		Task(
			title="Breakfast",
			duration_minutes=15,
			priority=PriorityLevel.MEDIUM,
			category="feeding",
			description="Serve morning meal",
		)
	)
	cat.add_task(
		Task(
			title="Medication",
			duration_minutes=10,
			priority=PriorityLevel.HIGH,
			category="meds",
			description="Daily allergy medication",
		)
	)
	cat.add_task(
		Task(
			title="Play session",
			duration_minutes=20,
			priority=PriorityLevel.LOW,
			category="enrichment",
			description="Interactive toy play",
		)
	)

	constraints = Constraints(max_total_minutes=90)
	scheduler = Scheduler(constraints=constraints)

	print("=" * 52)
	print("              TODAY'S SCHEDULE")
	print("=" * 52)
	print(f"Owner: {owner.name}")
	print(f"Daily time budget: {owner.available_time_minutes} minutes")

	for pet in owner.pets:
		print_schedule_for_pet(pet, scheduler)

	print("\nDone.")


if __name__ == "__main__":
	main()

