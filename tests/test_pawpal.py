from pawpal_system import Pet, PriorityLevel, Task


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