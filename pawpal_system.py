# logic layer

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Owner:
	name: str
	available_time_minutes: int
	preferences: Dict[str, Any] = field(default_factory=dict)

	def get_available_time(self) -> int:
		pass

	def get_preferences(self) -> Dict[str, Any]:
		pass


@dataclass
class Pet:
	name: str
	species: str
	age: Optional[int] = None
	special_needs: Optional[str] = None
	owner: Optional[Owner] = None

	def get_care_needs(self) -> List[str]:
		pass

	def get_owner(self) -> Optional[Owner]:
		pass


@dataclass
class Task:
	title: str
	duration_minutes: int
	priority: str
	category: Optional[str] = None

	def validate(self) -> bool:
		pass

	def get_priority_score(self) -> int:
		pass


@dataclass
class Constraints:
	max_total_minutes: Optional[int] = None
	allowed_time_windows: List[Tuple[str, str]] = field(default_factory=list)
	priority_weights: Dict[str, int] = field(default_factory=dict)
	owner_preferences: Dict[str, Any] = field(default_factory=dict)

	def is_task_allowed(self, task: Task) -> bool:
		pass

	def remaining_time(self, schedule: "Schedule") -> int:
		pass

	def score_task(self, task: Task, owner: Owner, pet: Pet) -> int:
		pass


@dataclass
class Schedule:
	items: List[Tuple[str, Task]] = field(default_factory=list)
	total_minutes: int = 0
	explanation: str = ""

	def add_item(self, task: Task, start_time: str) -> bool:
		pass

	def remove_item(self, task: Task) -> None:
		pass

	def get_total_duration(self) -> int:
		pass

	def get_explanation(self) -> str:
		pass

	def is_feasible(self, owner: Owner) -> bool:
		pass


class Scheduler:
	def __init__(self, constraints: Optional[Constraints] = None) -> None:
		self.constraints = constraints if constraints is not None else Constraints()

	def generate_daily_plan(
		self,
		owner: Owner,
		pet: Pet,
		tasks: List[Task],
	) -> Schedule:
		pass

	def rank_tasks(self, tasks: List[Task]) -> List[Task]:
		pass

	def explain_plan(self, schedule: Schedule) -> str:
		pass