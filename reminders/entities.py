from dataclasses import dataclass

from reminders.types import timestamp


@dataclass
class Reminder:
    message: str
    due_to: timestamp
    sent: bool = False
