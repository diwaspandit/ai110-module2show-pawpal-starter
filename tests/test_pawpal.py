from pawpal_system import Constraints, Owner, Pet, PriorityLevel, Schedule, Scheduler, Task


def test_task_mark_complete_updates_status() -> None:
	task = Task(
		title="Medication",
		duration_minutes=10,
		priority=PriorityLevel.HIGH,
	)

	assert task.completed is False
	task.mark_complete()
	assert task.completed is True


def test_add_task_to_pet_increases_task_count() -> None:
	pet = Pet(name="Mochi", species="dog")
	starting_count = len(pet.tasks)

	task = Task(
		title="Morning walk",
		duration_minutes=20,
		priority=PriorityLevel.MEDIUM,
	)

	pet.add_task(task)

	assert len(pet.tasks) == starting_count + 1


def test_sort_tasks_by_time_orders_scheduled_before_unscheduled() -> None:
	scheduler = Scheduler()

	task_late = Task(
		title="Evening walk",
		duration_minutes=20,
		priority=PriorityLevel.MEDIUM,
		scheduled_minute=18 * 60,
	)
	task_early = Task(
		title="Breakfast",
		duration_minutes=10,
		priority=PriorityLevel.HIGH,
		scheduled_minute=8 * 60,
	)
	task_unscheduled = Task(
		title="Brush coat",
		duration_minutes=15,
		priority=PriorityLevel.LOW,
	)

	ordered = scheduler.sort_tasks_by_time([task_late, task_unscheduled, task_early])

	assert [task.title for task in ordered] == ["Breakfast", "Evening walk", "Brush coat"]


def test_filter_tasks_by_pet_and_status() -> None:
	owner = Owner(name="Jordan", available_time_minutes=120)
	dog = Pet(name="Mochi", species="dog")
	cat = Pet(name="Luna", species="cat")
	owner.add_pet(dog)
	owner.add_pet(cat)

	dog_task = Task(
		title="Dog walk",
		duration_minutes=25,
		priority=PriorityLevel.HIGH,
	)
	cat_task = Task(
		title="Cat feeding",
		duration_minutes=10,
		priority=PriorityLevel.MEDIUM,
	)
	dog_completed = Task(
		title="Dog meds",
		duration_minutes=5,
		priority=PriorityLevel.HIGH,
		frequency="once",
		completed=True,
	)

	dog.add_task(dog_task)
	dog.add_task(dog_completed)
	cat.add_task(cat_task)

	scheduler = Scheduler(Constraints(max_total_minutes=60))
	filtered = scheduler.filter_tasks(owner.get_all_tasks(), pet=dog, status="incomplete")

	assert [task.title for task in filtered] == ["Dog walk"]


def test_daily_recurring_task_is_due_next_day() -> None:
	task = Task(
		title="Daily meds",
		duration_minutes=10,
		priority=PriorityLevel.HIGH,
		frequency="daily",
	)

	task.mark_complete_for_day(day_index=0)

	assert task.is_due_on_day(day_index=0) is False
	assert task.is_due_on_day(day_index=1) is True


def test_schedule_conflict_detection_blocks_overlapping_tasks() -> None:
	owner = Owner(name="Jordan", available_time_minutes=60)
	pet = Pet(name="Mochi", species="dog")
	schedule = Schedule(owner=owner, pet=pet)

	first = Task(title="Walk", duration_minutes=30, priority=PriorityLevel.HIGH)
	second = Task(title="Feeding", duration_minutes=20, priority=PriorityLevel.MEDIUM)

	assert schedule.add_item(first, start_minute=8 * 60) is True
	assert schedule.add_item(second, start_minute=8 * 60 + 15) is False


def test_rank_tasks_uses_score_per_minute() -> None:
	owner = Owner(name="Jordan", available_time_minutes=120)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)

	long_high = Task(
		title="Long high",
		duration_minutes=60,
		priority=PriorityLevel.HIGH,
	)
	short_medium = Task(
		title="Short medium",
		duration_minutes=10,
		priority=PriorityLevel.MEDIUM,
	)
	pet.add_task(long_high)
	pet.add_task(short_medium)

	scheduler = Scheduler()
	ranked = scheduler.generate_daily_plan(owner=owner, pet=pet, tasks=pet.tasks).items

	assert ranked[0][1].title == "Short medium"


def test_anti_starvation_bonus_prioritizes_skipped_task() -> None:
	owner = Owner(name="Jordan", available_time_minutes=120)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)

	frequently_skipped = Task(
		title="Skipped low",
		duration_minutes=10,
		priority=PriorityLevel.LOW,
		skip_streak=5,
	)
	not_skipped_high = Task(
		title="Fresh high",
		duration_minutes=30,
		priority=PriorityLevel.HIGH,
	)
	pet.add_task(frequently_skipped)
	pet.add_task(not_skipped_high)

	scheduler = Scheduler()
	ranked = scheduler.generate_daily_plan(owner=owner, pet=pet, tasks=pet.tasks).items

	assert ranked[0][1].title == "Skipped low"


def test_time_window_placement_respects_allowed_windows() -> None:
	owner = Owner(
		name="Jordan",
		available_time_minutes=120,
		preferences={"day_start_minute": 7 * 60},
	)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)

	pet.add_task(Task(title="Walk", duration_minutes=30, priority=PriorityLevel.HIGH))
	pet.add_task(Task(title="Feed", duration_minutes=30, priority=PriorityLevel.MEDIUM))

	scheduler = Scheduler(
		Constraints(
			max_total_minutes=120,
			allowed_time_windows=[(8 * 60, 9 * 60)],
		)
	)
	schedule = scheduler.generate_daily_plan(owner=owner, pet=pet, tasks=pet.tasks)

	assert len(schedule.items) == 2
	assert schedule.items[0][0] == 8 * 60
	assert schedule.items[1][0] == 8 * 60 + 30