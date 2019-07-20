from dataclasses import dataclass

from .gateways import EntityGateway, NotificationGateway, TimeSource
from .types import timestamp


@dataclass
class CreateReminderUseCase:
    entity_gateway: EntityGateway
    time_source: TimeSource

    def create_with_due_date(
            self, message: str, due_to: timestamp, recipient_id: int):

        self.entity_gateway.create_reminder(
            message=message, due_to=due_to, recipient_id=recipient_id
        )

    def create_with_interval(
            self, message: str, interval: int, recipient_id: int):

        due_to: int = self.time_source.now() + interval
        self.create_with_due_date(
            message=message,
            due_to=due_to,
            recipient_id=recipient_id
        )


@dataclass
class SendDueRemindersUseCase:
    entity_gateway: EntityGateway
    notification_gateway: NotificationGateway

    def execute(self) -> bool:
        sent_anything = False
        for reminder in self.entity_gateway.get_due_reminders_and_mark_sent():
            self.notification_gateway.send_notification(
                message=reminder.message,
                recipient_id=reminder.recipient_id
            )
            sent_anything = True

        return sent_anything
