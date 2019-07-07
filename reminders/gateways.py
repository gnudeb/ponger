from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Collection

from reminders.entities import Reminder
from reminders.types import timestamp


class TimeSource(ABC):

    @abstractmethod
    def now(self) -> timestamp:
        pass


@dataclass
class EntityGateway(ABC):
    time_source: TimeSource = None

    @abstractmethod
    def create_reminder(self, message: str, due_to: timestamp):
        pass

    @abstractmethod
    def get_due_reminders_and_mark_sent(self) -> Collection[Reminder]:
        pass


class NotificationGateway(ABC):

    def send_notification(self, message: str):
        pass
