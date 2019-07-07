from dataclasses import dataclass, field
from typing import List

from reminders.entities import Reminder
from reminders.gateways import EntityGateway, NotificationGateway, TimeSource
from reminders.types import timestamp


@dataclass
class InMemoryEntityGateway(EntityGateway):
    _reminders: List[Reminder] = field(default_factory=list)

    def create_reminder(self, message: str, due_to: int):
        self._reminders.append(Reminder(message, due_to))

    def get_due_reminders_and_mark_sent(self) -> List[Reminder]:
        expired_reminders = filter(self._is_reminder_expired, self._reminders)
        unsent_reminders = filter(lambda r: not r.sent, expired_reminders)
        return list(map(self.mark_reminder_sent, unsent_reminders))

    def are_expired_reminders_present(self) -> bool:
        for reminder in self._reminders:
            if self._is_reminder_expired(reminder):
                return True
        return False

    def mark_reminder_sent(self, reminder: Reminder) -> Reminder:
        reminder.sent = True
        return reminder

    def _is_reminder_expired(self, reminder: Reminder) -> bool:
        return self.time_source.now() >= reminder.due_to


@dataclass
class StubNotificationGateway(NotificationGateway):
    sent_notifications: List[str] = field(default_factory=list)

    def __len__(self):
        return len(self.sent_notifications)

    def __contains__(self, item) -> bool:
        if isinstance(item, str):
            return item in self.sent_notifications
        return False

    def send_notification(self, message: str):
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