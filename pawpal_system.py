# logic layer

from dataclasses import dataclass, field
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


@dataclass
class Task:
	title: str
	duration_minutes: int
	priority: PriorityLevel
	category: Optional[str] = None
	description: Optional[str] = None
	scheduled_minute: Optional[int] = None
	frequency: str = "daily"
	completed: bool = False
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


@dataclass
class Constraints:
	max_total_minutes: Optional[int] = None
	allowed_time_windows: List[Tuple[int, int]] = field(default_factory=list)
	priority_weights: Dict[PriorityLevel, int] = field(default_factory=dict)
	owner_preferences: Dict[str, Any] = field(default_factory=dict)

	def is_task_allowed(self, task: Task) -> bool:
		"""Return whether a task is eligible under current constraints."""
		if not task.validate():
			return False
		if task.completed:
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

	def score_task(self, task: Task, owner: Owner, pet: Pet) -> int:
		"""Compute a weighted score for task ranking."""
		base = self.priority_weights.get(task.priority, task.get_priority_score())
		bonus = 0
		preferred_categories = owner.preferences.get("preferred_categories", [])
		if task.category and task.category in preferred_categories:
			bonus += 1
		if task.pet is not None and task.pet is pet:
			bonus += 1
		return base + bonus


@dataclass
class Schedule:
	owner: Optional[Owner] = None
	pet: Optional[Pet] = None
	items: List[Tuple[int, Task]] = field(default_factory=list)
	unscheduled: List[Tuple[Task, str]] = field(default_factory=list)
	total_minutes: int = 0
	explanation: str = ""

	def add_item(self, task: Task, start_minute: int) -> bool:
		"""Add a task at a start minute if it passes validation and bounds checks."""
		if start_minute < 0 or start_minute > 1439:
			return False
		if not task.validate():
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
	) -> Schedule:
		"""Build and return a daily schedule for a specific owner-pet context."""
		schedule = Schedule(owner=owner, pet=pet)
		self._active_owner = owner
		self._active_pet = pet

		candidate_tasks = tasks if tasks else owner.get_all_tasks()
		if not candidate_tasks:
			candidate_tasks = pet.get_incomplete_tasks()

		filtered_tasks: List[Task] = []
		for task in candidate_tasks:
			if task.pet is not None and task.pet is not pet:
				continue
			if self.constraints.is_task_allowed(task):
				filtered_tasks.append(task)

		ranked_tasks = self.rank_tasks(filtered_tasks)

		max_minutes = owner.available_time_minutes
		if self.constraints.max_total_minutes is not None:
			max_minutes = min(max_minutes, self.constraints.max_total_minutes)

		start_minute = owner.preferences.get("day_start_minute", 8 * 60)
		cursor = start_minute

		for task in ranked_tasks:
			if schedule.get_total_duration() + task.duration_minutes <= max_minutes:
				added = schedule.add_item(task, cursor)
				if added:
					cursor += task.duration_minutes
				else:
					schedule.unscheduled.append((task, "Failed to add to schedule."))
			else:
				schedule.unscheduled.append((task, "Not enough available time."))

		schedule.explanation = self.explain_plan(schedule)
		self._active_owner = None
		self._active_pet = None
		return schedule

	def rank_tasks(self, tasks: List[Task]) -> List[Task]:
		"""Sort tasks by descending score, then by shorter duration and title."""
		owner = self._active_owner
		pet = self._active_pet

		def _score(task: Task) -> int:
			if owner is None or pet is None:
				return task.get_priority_score()
			return self.constraints.score_task(task, owner, pet)

		return sorted(
			tasks,
			key=lambda task: (
				-_score(task),
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