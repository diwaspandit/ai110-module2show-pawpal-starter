# logic layer

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class PriorityLevel(str, Enum):
	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"


@dataclass
class Owner:
	name: str
	available_time_minutes: int
	preferences: Dict[str, Any] = field(default_factory=dict)
	pets: List["Pet"] = field(default_factory=list)
    
	def get_available_time(self) -> int:
		"""Return the owner's available minutes for the day."""
		return self.available_time_minutes

	def get_preferences(self) -> Dict[str, Any]:
		"""Return the owner's scheduling preferences."""
		return self.preferences

	def add_pet(self, pet: "Pet") -> None:
		"""Attach a pet to this owner and set the reverse relationship."""
		if pet not in self.pets:
			self.pets.append(pet)
		pet.owner = self

	def get_all_tasks(self) -> List["Task"]:
		"""Collect and return tasks from all pets owned by this owner."""
		all_tasks: List[Task] = []
		for pet in self.pets:
			all_tasks.extend(pet.tasks)
		return all_tasks


@dataclass
class Pet:
	name: str
	species: str
	age: Optional[int] = None
	special_needs: Optional[str] = None
	owner: Optional[Owner] = None
	tasks: List["Task"] = field(default_factory=list)

	def get_care_needs(self) -> List[str]:
		"""Return a sorted list of care categories needed by this pet."""
		needs = {task.category for task in self.tasks if task.category}
		if self.special_needs:
			needs.add("special_needs")
		return sorted(list(needs))

	def get_owner(self) -> Optional[Owner]:
		"""Return the owner associated with this pet, if any."""
		return self.owner

	def add_task(self, task: "Task") -> None:
		"""Add a task to this pet and set the task's pet reference."""
		if task not in self.tasks:
			self.tasks.append(task)
		task.pet = self

	def remove_task(self, task: "Task") -> None:
		"""Remove a task from this pet and clear its pet reference."""
		if task in self.tasks:
			self.tasks.remove(task)
		if task.pet is self:
			task.pet = None

	def get_incomplete_tasks(self) -> List["Task"]:
		"""Return tasks for this pet that are not completed."""
		return [task for task in self.tasks if not task.completed]

	def get_tasks_by_status(self, completed: bool = False) -> List["Task"]:
		"""Return pet tasks filtered by completion status."""
		return [task for task in self.tasks if task.completed is completed]


@dataclass
class Task:
	title: str
	duration_minutes: int
	priority: PriorityLevel
	due_date: Optional[date] = None
	time: Optional[str] = None
	category: Optional[str] = None
	description: Optional[str] = None
	scheduled_minute: Optional[int] = None
	frequency: str = "daily"
	completed: bool = False
	last_completed_day: Optional[int] = None
	skip_streak: int = 0
	pet: Optional[Pet] = None

	def validate(self) -> bool:
		"""Validate task fields and ensure values are within supported ranges."""
		if not self.title or not self.title.strip():
			return False
		if self.duration_minutes <= 0:
			return False
		if not isinstance(self.priority, PriorityLevel):
			return False
		if self.frequency not in {"once", "daily", "weekly"}:
			return False
		if self.due_date is not None and not isinstance(self.due_date, date):
			return False
		if self.time is not None:
			parts = self.time.split(":")
			if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
				return False
			hours = int(parts[0])
			minutes = int(parts[1])
			if not (0 <= hours <= 23 and 0 <= minutes <= 59):
				return False
		if self.scheduled_minute is not None and not (0 <= self.scheduled_minute <= 1439):
			return False
		return True

	def get_priority_score(self) -> int:
		"""Map the task's priority enum to a numeric score."""
		priority_map: Dict[PriorityLevel, int] = {
			PriorityLevel.HIGH: 3,
			PriorityLevel.MEDIUM: 2,
			PriorityLevel.LOW: 1,
		}
		return priority_map[self.priority]

	def mark_complete(self) -> None:
		"""Mark this task as completed."""
		self.completed = True

	def mark_incomplete(self) -> None:
		"""Mark this task as not completed."""
		self.completed = False

	def increment_skip_streak(self) -> None:
		"""Increase skip counter when a due task cannot be scheduled."""
		self.skip_streak += 1

	def reset_skip_streak(self) -> None:
		"""Reset skip counter once a task is scheduled/completed."""
		self.skip_streak = 0

	def mark_complete_for_day(self, day_index: int) -> None:
		"""Mark this task complete and record the day index for recurring logic."""
		self.completed = True
		self.last_completed_day = day_index

	def is_due_on_day(self, day_index: int = 0) -> bool:
		"""Return whether this task is due on a given day index."""
		if self.frequency == "once":
			return not self.completed
		if self.frequency == "daily":
			return self.last_completed_day != day_index
		if self.frequency == "weekly":
			if self.last_completed_day is None:
				return True
			return (day_index - self.last_completed_day) >= 7
		return not self.completed


@dataclass
class Constraints:
	max_total_minutes: Optional[int] = None
	allowed_time_windows: List[Tuple[int, int]] = field(default_factory=list)
	priority_weights: Dict[PriorityLevel, int] = field(default_factory=dict)
	owner_preferences: Dict[str, Any] = field(default_factory=dict)

	def is_task_allowed(self, task: Task, day_index: int = 0) -> bool:
		"""Return whether a task is eligible under current constraints."""
		if not task.validate():
			return False
		if not task.is_due_on_day(day_index):
			return False
		blocked_categories = self.owner_preferences.get("blocked_categories", [])
		if task.category and task.category in blocked_categories:
			return False
		return True

	def remaining_time(self, schedule: "Schedule") -> int:
		"""Return remaining schedulable minutes for the given schedule."""
		if self.max_total_minutes is not None:
			limit = self.max_total_minutes
		elif schedule.owner is not None:
			limit = schedule.owner.available_time_minutes
		else:
			limit = 0
		return max(limit - schedule.get_total_duration(), 0)

	def score_task(self, task: Task, owner: Owner, pet: Pet) -> float:
		"""Compute a weighted score for task ranking."""
		base = float(self.priority_weights.get(task.priority, task.get_priority_score()))
		bonus = 0
		preferred_categories = owner.preferences.get("preferred_categories", [])
		if task.category and task.category in preferred_categories:
			bonus += 1
		if task.pet is not None and task.pet is pet:
			bonus += 1
		anti_starvation_bonus = min(task.skip_streak, 5)
		return base + bonus + anti_starvation_bonus


@dataclass
class Schedule:
	owner: Optional[Owner] = None
	pet: Optional[Pet] = None
	items: List[Tuple[int, Task]] = field(default_factory=list)
	unscheduled: List[Tuple[Task, str]] = field(default_factory=list)
	total_minutes: int = 0
	explanation: str = ""

	def has_conflict(self, start_minute: int, duration_minutes: int) -> bool:
		"""Return whether a proposed time range overlaps an existing item."""
		end_minute = start_minute + duration_minutes
		for existing_start, existing_task in self.items:
			existing_end = existing_start + existing_task.duration_minutes
			if start_minute < existing_end and end_minute > existing_start:
				return True
		return False

	def add_item(self, task: Task, start_minute: int) -> bool:
		"""Add a task at a start minute if it passes validation and bounds checks."""
		if start_minute < 0 or start_minute > 1439:
			return False
		if not task.validate():
			return False
		if start_minute + task.duration_minutes > 1440:
			return False
		if self.has_conflict(start_minute, task.duration_minutes):
			return False
		task.scheduled_minute = start_minute
		self.items.append((start_minute, task))
		self.items.sort(key=lambda pair: pair[0])
		self.total_minutes += task.duration_minutes
		return True

	def remove_item(self, task: Task) -> None:
		"""Remove a scheduled task and update schedule totals."""
		for idx, (_, current_task) in enumerate(self.items):
			if current_task is task:
				self.total_minutes = max(self.total_minutes - current_task.duration_minutes, 0)
				self.items.pop(idx)
				current_task.scheduled_minute = None
				break

	def get_total_duration(self) -> int:
		"""Recalculate and return total planned duration in minutes."""
		self.total_minutes = sum(task.duration_minutes for _, task in self.items)
		return self.total_minutes

	def get_explanation(self) -> str:
		"""Return the human-readable summary of schedule decisions."""
		return self.explanation

	def is_feasible(self) -> bool:
		"""Return whether the schedule fits within the owner's available time."""
		if self.owner is None:
			return False
		return self.get_total_duration() <= self.owner.available_time_minutes


class Scheduler:
	def __init__(self, constraints: Optional[Constraints] = None) -> None:
		"""Initialize a scheduler with optional constraints and run context."""
		self.constraints = constraints if constraints is not None else Constraints()
		self._active_owner: Optional[Owner] = None
		self._active_pet: Optional[Pet] = None

	def generate_daily_plan(
		self,
		owner: Owner,
		pet: Pet,
		tasks: List[Task],
		day_index: int = 0,
		include_completed: bool = False,
	) -> Schedule:
		"""Build and return a daily schedule for a specific owner-pet context."""
		schedule = Schedule(owner=owner, pet=pet)
		self._active_owner = owner
		self._active_pet = pet

		candidate_tasks = tasks if tasks else owner.get_all_tasks()
		if not candidate_tasks:
			candidate_tasks = pet.get_incomplete_tasks()

		filtered_tasks = self.filter_tasks(
			tasks=candidate_tasks,
			pet=pet,
			status="all" if include_completed else "incomplete",
			day_index=day_index,
		)
		filtered_tasks = [
			task for task in filtered_tasks if self.constraints.is_task_allowed(task, day_index=day_index)
		]

		ranked_tasks = self.rank_tasks(filtered_tasks)

		max_minutes = owner.available_time_minutes
		if self.constraints.max_total_minutes is not None:
			max_minutes = min(max_minutes, self.constraints.max_total_minutes)

		start_minute = owner.preferences.get("day_start_minute", 8 * 60)
		cursor = start_minute

		for task in ranked_tasks:
			if schedule.get_total_duration() + task.duration_minutes <= max_minutes:
				slot = self._find_slot_for_task(schedule, task, cursor, owner)
				added = schedule.add_item(task, slot) if slot is not None else False
				if added:
					task.reset_skip_streak()
					cursor = max(cursor, slot + task.duration_minutes)
				else:
					task.increment_skip_streak()
					schedule.unscheduled.append((task, "Failed to add to schedule."))
			else:
				task.increment_skip_streak()
				schedule.unscheduled.append((task, "Not enough available time."))

		schedule.explanation = self.explain_plan(schedule)
		self._active_owner = None
		self._active_pet = None
		return schedule

	def mark_task_complete(self, task: Task, completed_on: Optional[date] = None) -> Optional[Task]:
		"""Mark task complete and create next recurring instance for daily/weekly tasks."""
		completion_date = completed_on if completed_on is not None else date.today()
		task.completed = True

		if task.frequency not in {"daily", "weekly"}:
			return None

		next_delta = timedelta(days=1 if task.frequency == "daily" else 7)
		next_task = Task(
			title=task.title,
			duration_minutes=task.duration_minutes,
			priority=task.priority,
			due_date=completion_date + next_delta,
			time=task.time,
			category=task.category,
			description=task.description,
			frequency=task.frequency,
			completed=False,
		)

		if task.pet is not None:
			task.pet.add_task(next_task)

		return next_task

	def _find_slot_for_task(
		self,
		schedule: Schedule,
		task: Task,
		earliest_start: int,
		owner: Owner,
	) -> Optional[int]:
		"""Find earliest non-conflicting start minute, respecting allowed windows."""
		windows = self.constraints.allowed_time_windows
		if not windows:
			windows = [(owner.preferences.get("day_start_minute", 8 * 60), 24 * 60)]

		for window_start, window_end in sorted(windows, key=lambda window: window[0]):
			candidate = max(window_start, earliest_start)
			while candidate + task.duration_minutes <= window_end:
				if not schedule.has_conflict(candidate, task.duration_minutes):
					return candidate

				next_candidate = candidate + 1
				for existing_start, existing_task in schedule.items:
					existing_end = existing_start + existing_task.duration_minutes
					if candidate < existing_end and (candidate + task.duration_minutes) > existing_start:
						next_candidate = max(next_candidate, existing_end)
				candidate = next_candidate

		return None

	def sort_tasks_by_time(self, tasks: List[Task]) -> List[Task]:
		"""Return tasks sorted by scheduled minute, with unscheduled tasks last."""
		return self.sort_by_time(tasks)

	def sort_by_time(self, tasks: List[Task]) -> List[Task]:
		"""Sort tasks by `time` in HH:MM format using a lambda key."""
		return sorted(
			tasks,
			key=lambda task: (
				task.time is None and task.scheduled_minute is None,
				(
					(int(task.time.split(":")[0]) * 60 + int(task.time.split(":")[1]))
					if task.time is not None
					else task.scheduled_minute if task.scheduled_minute is not None else 10**9
				),
				task.title.lower(),
			),
		)

	def detect_scheduling_conflicts(self, tasks: List[Task]) -> List[str]:
		"""Return lightweight warnings for tasks that overlap in time."""
		warnings: List[str] = []
		timed_tasks: List[Tuple[int, int, Task]] = []

		for task in tasks:
			start_minute: Optional[int] = None
			if task.time is not None:
				if not task.validate():
					continue
				hours, minutes = task.time.split(":")
				start_minute = int(hours) * 60 + int(minutes)
			elif task.scheduled_minute is not None:
				start_minute = task.scheduled_minute

			if start_minute is None:
				continue

			end_minute = start_minute + task.duration_minutes
			timed_tasks.append((start_minute, end_minute, task))

		timed_tasks.sort(key=lambda entry: entry[0])

		for idx, (start_a, end_a, task_a) in enumerate(timed_tasks):
			for start_b, end_b, task_b in timed_tasks[idx + 1 :]:
				if start_b >= end_a:
					break
				if start_a < end_b and start_b < end_a:
					pet_a = task_a.pet.name if task_a.pet is not None else "Unknown pet"
					pet_b = task_b.pet.name if task_b.pet is not None else "Unknown pet"
					conflict_time = f"{start_b // 60:02d}:{start_b % 60:02d}"
					warnings.append(
						f"Conflict: '{task_a.title}' ({pet_a}) overlaps with "
						f"'{task_b.title}' ({pet_b}) around {conflict_time}."
					)

		return warnings

	def filter_tasks(
		self,
		tasks: List[Task],
		pet: Optional[Pet] = None,
		status: str = "incomplete",
		day_index: int = 0,
	) -> List[Task]:
		"""Filter tasks by pet association, due recurrence, and completion status."""
		filtered: List[Task] = []

		for task in tasks:
			if pet is not None and task.pet is not None and task.pet is not pet:
				continue

			if not task.is_due_on_day(day_index):
				continue

			effective_completed = task.completed
			if task.frequency in {"daily", "weekly"} and task.is_due_on_day(day_index):
				effective_completed = False

			if status == "incomplete" and effective_completed:
				continue
			if status == "completed" and not effective_completed:
				continue

			filtered.append(task)

		return filtered

	def filter_tasks_by_completion_or_pet_name(
		self,
		tasks: List[Task],
		completed: Optional[bool] = None,
		pet_name: Optional[str] = None,
	) -> List[Task]:
		"""Filter tasks by completion status and/or pet name."""
		filtered: List[Task] = []
		normalized_pet_name = pet_name.strip().lower() if pet_name is not None else None

		for task in tasks:
			if completed is not None and task.completed is not completed:
				continue

			if normalized_pet_name is not None:
				if task.pet is None or task.pet.name.lower() != normalized_pet_name:
					continue

			filtered.append(task)

		return filtered

	def rank_tasks(self, tasks: List[Task]) -> List[Task]:
		"""Sort tasks by descending score-per-minute, then by shorter duration and title."""
		owner = self._active_owner
		pet = self._active_pet

		def _score(task: Task) -> float:
			if owner is None or pet is None:
				return float(task.get_priority_score() + min(task.skip_streak, 5))
			return self.constraints.score_task(task, owner, pet)

		def _density(task: Task) -> float:
			return _score(task) / max(task.duration_minutes, 1)

		return sorted(
			tasks,
			key=lambda task: (
				-_density(task),
				task.duration_minutes,
				task.title.lower(),
			),
		)

	def explain_plan(self, schedule: Schedule) -> str:
		"""Generate a concise explanation of scheduled and skipped tasks."""
		planned = len(schedule.items)
		skipped = len(schedule.unscheduled)
		total = schedule.get_total_duration()
		owner_name = schedule.owner.name if schedule.owner else "owner"
		pet_name = schedule.pet.name if schedule.pet else "pet"
		return (
			f"Planned {planned} task(s) for {pet_name} under {owner_name} in {total} minutes. "
			f"Skipped {skipped} task(s) due to constraints or time limits."
		)