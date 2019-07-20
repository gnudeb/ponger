import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from sys import argv
from threading import Thread
from time import sleep
from typing import List, Tuple

from telegram.ext import Updater, MessageHandler, CallbackContext
from telegram import Update, Bot
from telegram.ext.filters import Filters

from reminders.entities import Reminder
from reminders.gateways import TimeSource, NotificationGateway, ReminderGateway
from reminders.types import timestamp
from reminders.usecases import CreateReminderUseCase, SendDueRemindersUseCase


class PythonTimeSource(TimeSource):

    def now(self) -> timestamp:
        return int(datetime.now().timestamp())


@dataclass
class TelegramNotificationGateway(NotificationGateway):
    telegram_bot: Bot

    def send_notification(self, message: str, recipient_id: int):
        self.telegram_bot.send_message(chat_id=recipient_id, text=message)


@dataclass
class InMemoryReminderGateway(ReminderGateway):
    _reminders: List[Reminder] = field(default_factory=list)

    def create_reminder(
            self, message: str, due_to: timestamp, recipient_id: int):
        self._reminders.append(Reminder(message, due_to, recipient_id))

    def get_due_reminders_and_mark_sent(self) -> List[Reminder]:
        expired_reminders = filter(self._is_reminder_expired, self._reminders)
        unsent_reminders = filter(lambda r: not r.sent, expired_reminders)
        return list(map(Reminder.mark_sent, unsent_reminders))

    def _is_reminder_expired(self, reminder: Reminder) -> bool:
        return self.time_source.now() >= reminder.due_to


@dataclass
class Ponger:
    bot: Bot
    create: CreateReminderUseCase
    send: SendDueRemindersUseCase
    logger: logging.Logger
    _send_interval: int = field(default=1, init=False)
    _running: bool = field(default=False, init=False)

    def handle_message(self, update: Update, context: CallbackContext):
        message: str = update.message.text
        self.logger.debug(f"Ponger got message '{message}'!")

        self.create.create_with_interval(
            message=message,
            interval=self._extract_interval_from_message(message),
            recipient_id=update.message.chat_id,
        )

        self._update_interval()

    @staticmethod
    def _extract_interval_from_message(message) -> int:
        try:
            return int(message.split(" ")[0])
        except ValueError:
            return 1

    def start(self):
        self._ping_sender(threaded=True)

    def stop(self):
        self.logger.debug("Initiating ponger shutdown...")
        self._running = False

    def _ping_sender(self, threaded=False):
        if threaded:
            Thread(target=self._ping_sender).start()
            return
        self._running = True
        while self._running:
            self.logger.debug(f"Initiating notification sending...")

            sent_anything: bool = self.send.execute()
            self._update_interval(sent_anything)

            self.logger.debug(
                f"Ponger sleeping for {self._send_interval} seconds..."
            )
            sleep(self._send_interval)

        self.logger.debug("Ponger thread has ended")

    def _update_interval(self, sent_anything: bool = True):
        if sent_anything:
            self._send_interval = 1
        else:
            self._send_interval = min(3, self._send_interval + 1)


class PongerConfiguration(ABC):
    @property
    @abstractmethod
    def bot_token(self):
        pass


@dataclass
class CommandLinePongerConfiguration(PongerConfiguration):
    logger: logging.Logger
    _bot_token: str = field(init=False)

    def __post_init__(self):
        try:
            _, self._bot_token = argv
        except ValueError:
            # TODO: maybe more graceful error handling?
            self.logger.error("Expected one argument: bot token")
            sys.exit(-1)

    @property
    def bot_token(self):
        return self._bot_token


if __name__ == '__main__':

    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        level=logging.DEBUG,
    )

    logger = logging.getLogger(__name__)

    configuration: PongerConfiguration = CommandLinePongerConfiguration(
        logger=logger.getChild("configuration")
    )

    updater = Updater(
        token=configuration.bot_token,
        use_context=True
    )

    time_source: TimeSource = PythonTimeSource()
    notification_gateway: NotificationGateway = \
        TelegramNotificationGateway(telegram_bot=updater.bot)
    reminder_gateway: ReminderGateway = InMemoryReminderGateway(
        time_source=time_source
    )

    ponger = Ponger(
        bot=updater.bot,
        create=CreateReminderUseCase(
            reminder_gateway=reminder_gateway,
            time_source=time_source,
        ),
        send=SendDueRemindersUseCase(
            reminder_gateway=reminder_gateway,
            notification_gateway=notification_gateway,
        ),
        logger=logger.getChild("ponger")
    )

    updater.dispatcher.add_handler(MessageHandler(
        filters=Filters.text,
        callback=ponger.handle_message,
    ))

    ponger.start()
    updater.start_polling()
    updater.idle()
    ponger.stop()
