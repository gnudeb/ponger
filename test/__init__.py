import unittest

from reminders.usecases import CreateReminderUseCase, SendDueRemindersUseCase
from .mocks import StubNotificationGateway, \
    ArtificialTimeSource
from bot import InMemoryEntityGateway


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

    def test_reminders_can_be_sent_out_of_order(self):
        self._given_reminder(message="A", interval=60)
        self._given_reminder(message="B", interval=30)

        self._when_time_is_advanced_by(seconds=45)

        self._then_particular_notification_have_been_sent(message="B")

        self._when_time_is_advanced_by(seconds=45)

        self._then_particular_notification_have_been_sent(message="A")

    def _given_reminder(self, message: str = "", interval: int = 60):
        self.create.create_with_interval(
            message=message,
            interval=interval,
            recipient_id=1,
        )

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
