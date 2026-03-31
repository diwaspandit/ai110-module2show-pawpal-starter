# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
=> Classes (Owner, Pet, Task, Schedule, Schedule, Scheduler)

- What classes did you include, and what responsibilities did you assign to each?
=> My core system consists of of 6 classes: Owner and Pet to represent user data, Task represents care activitires, Schedule represent daily plan, Scheduler contains the algorithm, Constraints manages scheduling rules.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
=> Yes. I refined the original UML to make relationships and data types safer. I linked `Schedule` to both `Owner` and `Pet` so each generated plan clearly belongs to one owner-pet context. I also updated `Task.priority` from a raw string to a `PriorityLevel` enum (`low`, `medium`, `high`) to avoid invalid values and reduce bugs when ranking tasks. Finally, I changed schedule time fields from free-form strings to minute-based integers so future conflict-checking and sorting logic is easier to implement reliably.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
=> The scheduler considers owner available time, optional max total scheduled minutes, task priority, task duration, recurring due status (`once`/`daily`/`weekly`), allowed time windows, blocked/preferred categories, and overlap avoidance.

=> I prioritized constraints in this order: (1) validity and due status, (2) hard time limits, (3) overlap/conflict safety, then (4) quality ranking (score-per-minute + anti-starvation). This order kept plans feasible first, then optimized usefulness.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
=> One tradeoff is that the scheduler uses a greedy priority-and-score-per-minute approach instead of a global optimizer (like full-day dynamic programming). It picks the next best task that fits, which is simple and fast, but it may miss a theoretically perfect combination in edge cases.

=> This is reasonable for this scenario because PawPal+ is an interactive planning assistant where responsiveness and understandable behavior matter more than mathematically optimal packing. The greedy logic is easier to explain to users, easier to debug, and still produces practical daily plans under normal time constraints.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
=> I used VS Code Copilot Chat for phased support: UML-to-code mapping, method stub generation, edge-case brainstorming, unit-test drafting, and targeted UI cleanup in Streamlit.

=> The most effective Copilot features were: inline completion for repetitive dataclass/method patterns, chat-driven test-case generation, and quick refactor suggestions when method names changed.

=> The most helpful prompts were specific and constraint-based, such as: “add tests for daily recurrence and conflict detection” or “use Scheduler methods in app.py display logic without changing domain behavior.”

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
=> I rejected a suggestion to keep `Task.priority` as a plain string and use ad-hoc comparisons everywhere. I kept `PriorityLevel` as an enum to preserve type safety and reduce invalid states.

=> I verified choices by running `python -m pytest`, checking behavior-focused tests (sorting, recurrence, conflicts), and confirming no regressions in the Streamlit flow.

=> I also modified an AI suggestion that duplicated near-identical tests; I merged intent into cleaner, non-redundant coverage to keep the suite maintainable.

**c. Session strategy and architecture ownership**

- How did using separate chat sessions for different phases help you stay organized?
- What did you learn about being the “lead architect” with AI tools?
=> Separate chat sessions by phase (design, core logic, testing, UI/docs) reduced context drift and made decisions traceable. Each session had a clear goal and acceptance criteria.

=> I learned that AI is strongest as a rapid implementation partner, but system coherence still depends on human architecture decisions. Being the lead architect meant enforcing class boundaries, naming consistency, and test-driven verification instead of accepting every fast suggestion.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?
=> I tested task completion state, add/remove flows, time sorting (`HH:MM` and scheduled minute), filtering (pet/completion), recurring next-task creation, conflict detection (same pet and cross-pet), ranking behavior, and allowed-window placement.

=> These tests were important because they cover both happy paths and high-risk edge logic where silent scheduling mistakes are most likely.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
=> Confidence is high: 5/5 for current scope, supported by 16 passing tests and consistent app behavior.

=> Next edge cases: invalid time strings in user input, boundary times (00:00/23:59), ties with identical score density, daylight-saving/date rollover effects for recurrence, and very large task lists for performance.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
=> I am most satisfied with the alignment between UML, domain code, tests, and Streamlit demo. The scheduler behavior is explainable and test-backed.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
=> I would add persistent storage, richer recurrence rules (custom intervals), and optional optimization mode for better global packing when needed.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
=> The key takeaway is that AI accelerates implementation, but architecture quality comes from deliberate constraint ordering, explicit domain models, and disciplined verification.
