from dataclasses import dataclass

from .types import timestamp


@dataclass
class Reminder:
    message: str
    due_to: timestamp
    recipient_id: int
    sent: bool = False

    def mark_sent(self) -> 'Reminder':
        self.sent = True
        return self
