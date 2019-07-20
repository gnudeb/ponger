from dataclasses import dataclass

from .gateways import ReminderGateway, NotificationGateway, TimeSource
from .types import timestamp


@dataclass
class CreateReminderUseCase:
    reminder_gateway: ReminderGateway
    time_source: TimeSource

    def create_with_due_date(
            self, message: str, due_to: timestamp, recipient_id: int):

        self.reminder_gateway.create_reminder(
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
    reminder_gateway: ReminderGateway
    notification_gateway: NotificationGateway

    def execute(self) -> bool:
        sent_anything = False
        for reminder in self.reminder_gateway.get_due_reminders_and_mark_sent():
            self.notification_gateway.send_notification(
                message=reminder.message,
                recipient_id=reminder.recipient_id
            )
            sent_anything = True

        return sent_anything
