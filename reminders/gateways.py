from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Collection

from .entities import Reminder
from .types import timestamp


class TimeSource(ABC):

    @abstractmethod
    def now(self) -> timestamp:
        pass


@dataclass
class ReminderGateway(ABC):
    time_source: TimeSource = None

    @abstractmethod
    def create_reminder(
            self, message: str, due_to: timestamp, recipient_id: int):
        pass

    @abstractmethod
    def get_due_reminders_and_mark_sent(self) -> Collection[Reminder]:
        pass


class NotificationGateway(ABC):

    def send_notification(self, message: str, recipient_id: int):
        pass
