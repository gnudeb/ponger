from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Collection

timestamp = int


class TimeSource(ABC):

    @abstractmethod
    def now(self) -> timestamp:
        pass


class BuiltInTimeSource(TimeSource):

    def now(self) -> int:
        return int(datetime.now().timestamp())


@dataclass
class Reminder:
    message: str
    due_to: timestamp
    sent: bool = False


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


@dataclass
class CreateReminderUseCase:
    entity_gateway: EntityGateway
    time_source: TimeSource

    def create_with_due_date(self, message: str, due_to: timestamp):
        self.entity_gateway.create_reminder(
            message=message, due_to=due_to
        )

    def create_with_interval(self, message: str, interval: int):
        due_to: int = self.time_source.now() + interval
        self.create_with_due_date(message=message, due_to=due_to)


@dataclass
class SendDueRemindersUseCase:
    entity_gateway: EntityGateway
    notification_gateway: NotificationGateway

    def execute(self):
        for reminder in self.entity_gateway.get_due_reminders_and_mark_sent():
            self.notification_gateway.send_notification(
                message=reminder.message
            )


