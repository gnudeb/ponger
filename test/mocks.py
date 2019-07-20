from dataclasses import dataclass, field
from typing import List

from reminders.gateways import NotificationGateway, TimeSource
from reminders.types import timestamp


@dataclass
class StubNotificationGateway(NotificationGateway):
    sent_notifications: List[str] = field(default_factory=list)

    def __len__(self):
        return len(self.sent_notifications)

    def __contains__(self, item) -> bool:
        if isinstance(item, str):
            return item in self.sent_notifications
        return False

    def send_notification(self, message: str, recipient_id: int):
        self.sent_notifications.append(message)

    def has_notifications(self) -> bool:
        return len(self.sent_notifications) > 0

    def forget_sent_notifications(self):
        self.sent_notifications.clear()


@dataclass
class ArtificialTimeSource(TimeSource):
    current_time: timestamp = 0

    def now(self) -> timestamp:
        return self.current_time

    def advance_by(self, seconds: int):
        self.current_time += seconds
