import unittest
from dataclasses import dataclass, field
from typing import List

from reminders import CreateReminderUseCase, SendDueRemindersUseCase, TimeSource, timestamp, EntityGateway, Reminder, \
    NotificationGateway


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


class TestReminders(unittest.TestCase):

    def setUp(self):
        self.time_source = ArtificialTimeSource()
        self.notification_gateway = StubNotificationGateway()
        entity_gateway = InMemoryEntityGateway(
            time_source=self.time_source
        )
        self.create = CreateReminderUseCase(
            entity_gateway=entity_gateway,
            time_source=self.time_source
        )
        self.send = SendDueRemindersUseCase(
            entity_gateway=entity_gateway,
            notification_gateway=self.notification_gateway
        )

    def test_reminder_is_not_sent_immediately(self):
        self._given_reminder(interval=60)

        self._when_time_is_advanced_by(seconds=1)

        self._then_no_notification_have_been_sent()

    def test_reminder_is_not_sent_second_before_due(self):
        self._given_reminder(interval=60)

        self._when_time_is_advanced_by(seconds=59)

        self._then_no_notification_have_been_sent()

    def test_reminder_is_sent_right_on_time(self):
        self._given_reminder(interval=60)

        self._when_time_is_advanced_by(seconds=60)

        self._then_notifications_have_been_sent()

    def test_reminders_with_different_intervals(self):
        self._given_reminder(message="Hi", interval=30)
        self._given_reminder(message="Hello", interval=60)

        self._when_time_is_advanced_by(seconds=45)

        self._then_particular_notification_have_been_sent(message="Hi")
        self._then_particular_notification_have_not_been_sent(message="Hello")

    def test_reminder_is_sent_only_once(self):
        self._given_reminder(interval=30)

        self._when_time_is_advanced_by(seconds=60)

        self._then_notifications_have_been_sent(amount=1)

        self._when_time_is_advanced_by(seconds=1)

        self._then_no_notification_have_been_sent()

    def _given_reminder(self, message: str = "", interval: int = 60):
        self.create.create_with_interval(message=message, interval=interval)

    def _when_time_is_advanced_by(self, seconds: int):
        self.notification_gateway.forget_sent_notifications()
        self.time_source.advance_by(seconds=seconds)
        self.send.execute()

    def _then_no_notification_have_been_sent(self):
        self.assertFalse(self.notification_gateway.has_notifications())

    def _then_notifications_have_been_sent(self, amount: int = None):
        if amount is None:
            self.assertTrue(self.notification_gateway.has_notifications())
        else:
            self.assertEqual(len(self.notification_gateway), amount)

    def _then_particular_notification_have_been_sent(self, message: str):
        self.assertIn(message, self.notification_gateway)

    def _then_particular_notification_have_not_been_sent(self, message: str):
        self.assertNotIn(message, self.notification_gateway)


if __name__ == '__main__':
    unittest.main()
