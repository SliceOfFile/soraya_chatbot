import conf
import soraya_slog as logger
import environment
from bot import Bot
from common import panic
from telegram import User
from telegram.ext import Application, MessageHandler, filters as f
from strings import LOG_APPLICATION_CREATE
from storage import Storage
import asyncio

def get_chat_filter_parameters(configuration: dict) -> tuple[list[int],
                                                             list[str]]:
  chat_id = []
  username = []
  for element in configuration['telegram']['users']:
    if isinstance(element, int):
      chat_id.append(element)
      continue
    if isinstance(element, str):
      username.append(element)
      continue
    raise ValueError(f'Bad chat ID or username: "{element}"')
  return (chat_id, username)

def get_me(application: Application) -> User:
  loop = asyncio.get_event_loop()
  result = loop.run_until_complete(application.updater.bot.get_me())
  return result

def main():
  configuration = conf.read()
  chat_id, username = get_chat_filter_parameters(configuration)
  token = environment.get_telegram_token()
  application = Application.builder().token(token).build()
  storage = Storage(configuration)
  
  me = get_me(application)
  bot = Bot(me.id, me.first_name, me.username, configuration, storage)

  serializable_configuration = dict(configuration)
  serializable_configuration['timezone'] = str(configuration['timezone'])
  logger.info(LOG_APPLICATION_CREATE, {
    'configuration': serializable_configuration
  })

  filters_type = f.UpdateType.MESSAGE & f.TEXT & ~f.FORWARDED & ~f.COMMAND
  filters_users = f.Chat(chat_id) | f.Chat(username=username)
  filters = filters_type & filters_users

  application.add_handler(MessageHandler(filters, bot.handler_message))
  application.run_polling()

try:
  main()
except Exception as e:
  panic(e)