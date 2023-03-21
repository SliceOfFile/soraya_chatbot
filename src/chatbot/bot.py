import random
import soraya_slog as logger
from common import exc_to_dict, str_includes
from datetime import datetime
from openai import ChatCompletion
from storage import Storage
from strings import *
from telegram import Message, Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes
from tenacity import retry, wait_exponential, stop_after_attempt

class Bot():
  def __init__(self,
               id: int,
               first_name: str,
               username: str,
               configuration: dict,
               storage: Storage,
               ) -> None:
    self.__id = id
    self.__first_name = first_name
    self.__username = username
    self.__configuration = configuration
    self.__storage = storage

  def __parse_condition(self, update: Update, condition: str) -> bool:
    if condition == 'HAS_USER_USERNAME':
      return isinstance(update.effective_user.username, str)
    if condition == 'HAS_BOT_USERNAME':
      return isinstance(self.__username, str)
    return True

  def __get_time_variables(self) -> tuple[str, str, str]:
    timezone = self.__configuration['timezone']
    now = datetime.now(timezone)
    current_time = now.strftime('%H:%M')
    current_date = now.strftime('%Y-%m-%d')
    return str(timezone), current_time, current_date

  def __parse_content(self, update: Update, content: str) -> str:
    timezone, current_time, current_date = self.__get_time_variables()
    return content.format(BOT_FIRSTNAME=str(self.__first_name),
                          CURRENT_DATE=current_date,
                          CURRENT_TIME=current_time,
                          TIMEZONE=timezone,
                          BOT_USERNAME=str(self.__username),
                          USER_FIRSTNAME=str(update.effective_user.first_name),
                          USER_USERNAME=str(update.effective_user.username))

  def __build_prompts_get_parsed(self,
                                 update: Update,
                                 prompt: dict) -> dict | None:
    valid_roles = ['system', 'assistant', 'user']

    if prompt.get('role') not in valid_roles:
      return None
    
    if not isinstance(prompt.get('content'), str):
      return None

    if not self.__parse_condition(update, prompt.get('condition')):
      return None
    
    content = self.__parse_content(update, prompt['content'])
    return { 'role': prompt['role'], 'content': content }

  def __build_prompts_common(self,
                             update: Update,
                             prompts: dict) -> list[dict]:
    result = []
    for element in prompts:
      parsed = self.__build_prompts_get_parsed(update, element)
      if isinstance(parsed, dict):
        result.append(parsed)
    return result

  def __build_prompts_thematic(self, update: Update) -> list[dict]:
    message_text = update.effective_message.text
    thematic = self.__configuration['openai']['prompts']['thematic']
    result = []

    for element in thematic:
      for word in element['keywords']:
        if str_includes(message_text, word):
          built = self.__build_prompts_common(update, element['prompts'])
          result.extend(built)
          break
    
    return result

  def __build_prompts_history(self, update: Update) -> list[dict]:
    bot_id = self.__id
    reply_to = update.effective_message.reply_to_message
    result = []

    if not isinstance(reply_to, Message):
      return result
    
    role = 'assistant' if reply_to.from_user.id == bot_id else 'user'
    content = reply_to.text

    if isinstance(content, str):
      result.append({ 'role': role, 'content': content })

    return result

  def __build_prompts(self, update: Update) -> list[dict]:
    use_history = self.__configuration['openai']['context']['history']
    base_prompts = self.__configuration['openai']['prompts']['base']
    chat_prompts = self.__configuration['openai']['prompts']['chat']
    result = []

    result.extend(self.__build_prompts_common(update, base_prompts))
    result.extend(self.__build_prompts_thematic(update))
    result.extend(self.__build_prompts_common(update, chat_prompts))

    if use_history:
      result.extend(self.__build_prompts_history(update))

    content = self.__filter_message_text(update.effective_message.text)
    result.append({ 'role': 'user', 'content': content})

    return result
  
  def __should_reply(self, update: Update) -> bool:
    raw_keywords = self.__configuration['telegram']['triggers']['keywords']
    keywords = [self.__parse_content(update, word) for word in raw_keywords]
    chat = update.effective_chat
    message = update.effective_message

    if chat.type == ChatType.PRIVATE:
      return True
        
    if (message.reply_to_message is not None and
        message.reply_to_message.from_user.id == self.__id):
      return True

    for element in keywords:
      if str_includes(message.text, element):
        return True
    
    return False
  
  def __filter_message_text(self, message_text: str) -> str:
    return message_text[:280]

  def __filter_reply_text(self, reply_text: str) -> str:
    return reply_text
  
  @retry(wait=wait_exponential(multiplier=1, min=6, max=16),
         stop=stop_after_attempt(8),
         reraise=True)
  def __create_chat_completion(self,
                               update: Update,
                               messages: list[dict],
                               max_tokens: int) -> dict:
    model = self.__configuration['openai']['model']
    user_id = update.effective_user.id
    return ChatCompletion.create(model=model,
                                 messages=messages,
                                 max_tokens=max_tokens,
                                 user=str(user_id))

  async def __handler_message(
      self, update: Update, context: ContextTypes.DEFAULT_TYPE
  ) -> tuple[list, dict, str]:
    max_tokens = self.__configuration['openai']['limits']['completion']
    messages = self.__build_prompts(update)

    chat_completion = self.__create_chat_completion(update,
                                                    messages,
                                                    max_tokens)
    
    reply_text = chat_completion['choices'][0]['message']['content']
    return messages, chat_completion, self.__filter_reply_text(reply_text)

  async def handler_message(self,
                            update: Update,
                            context: ContextTypes.DEFAULT_TYPE) -> None:
    c_openai = self.__configuration['openai']
    message = None

    try:
      daily_limit = c_openai['limits']['daily']
      s = self.__storage
      message = update.effective_message.to_dict()
      
      if not self.__should_reply(update):
        return
      
      current_token_usage = s.get_daily_token_usage()
      
      if daily_limit > 0 and current_token_usage >= daily_limit:
        reply_text = None
        limit_messages = c_openai['defaultMessages']['dailyLimitExceeded']

        if len(limit_messages) > 0:
          reply_text = random.choice(limit_messages)
          await update.message.reply_text(reply_text)

        logger.info(LOG_HANDLER_DAILY_TOKEN_LIMIT, {
          'message': message,
          'reply': { 'text': reply_text },
          'stats': { 'daily_token_usage': current_token_usage }
        })

        return
      
      handler_response = await self.__handler_message(update, context)
      prompts, chat_completion, reply_text = handler_response

      await update.message.reply_text(reply_text)

      total_tokens = int(chat_completion['usage']['total_tokens'])
      updated_token_usage = current_token_usage + total_tokens

      s.set_daily_token_usage(updated_token_usage)

      logger.info(LOG_HANDLER_MESSAGE_REPLY, {
        'prompts': prompts,
        'chat_completion': chat_completion,
        'message': message,
        'reply': { 'text': reply_text },
        'stats': { 'daily_token_usage': updated_token_usage }
      })

    except Exception as e:
      reply_text = None
      error_reply_list = c_openai['defaultMessages']['error']

      if len(error_reply_list) > 0:
        reply_text = random.choice(error_reply_list)
        try:
          await update.message.reply_text(reply_text)
        except Exception as e:
          reply_text = None
          pass

      error_message = LOG_HANDLER_MESSAGE_ERROR
      logger.error(error_message, { 'message': message,
                                    'reply': { 'text': reply_text },
                                    'exception': exc_to_dict(e) })