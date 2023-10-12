import yaml
from exceptions import ConfigurationError
from strings import EXC_CONF_LOAD, EXC_CONF_BAD_VERSION, EXC_CONF_BAD_TIMEZONE_VALUE, EXC_CONF_BAD_PROMPT_VALUE
import pytz

__CONF_PATH = '/usr/local/etc/chatbot/chatbot.conf.yml'

def __parse_prompt_list(prompts: list) -> list:
  result = []
  for element in prompts:
    if not (isinstance(element, dict) and
              isinstance(element.get('role'), str) and
              isinstance(element.get('content'), str)):
        raise ConfigurationError(EXC_CONF_BAD_PROMPT_VALUE)    
    result.append({
      'role': element['role'],
      'content': element['content'],
      'condition': element.get('condition')
    })
  return result


def __parse(data: dict) -> None:
  conf = {
    'timezone': None,
    'telegram': {
      'users': [],
      'triggers': { 'keywords': [] }
    },
    'openai': {
      'model': 'gpt-3.5-turbo',
      'prompts': {
        'base': [],
        'thematic': [],
        'chat': []
      },
      'defaultMessages': {
        'error': [],
        'dailyLimitExceeded': []
      },
      'limits': {
        'daily': 10000,
        'completion': 1024
      },
      'context': {
        'history': False,
        'suppressTriggerUsername': False
      }
    }
  }

  version = data.get('version')
  timezone = data.get('timezone', 'UTC')
  telegram = data.get('telegram', {})
  telegram_triggers = telegram.get('triggers', {})
  openai = data.get('openai', {})
  openai_prompts = openai.get('prompts', {})
  openai_default_messages = openai.get('defaultMessages', {})
  openai_limits = openai.get('limits', {})
  openai_context = openai.get('context', {})

  if version != '1.0.0-alpha3':
    raise ConfigurationError(EXC_CONF_BAD_VERSION.format(data['version']))
  
  try:
    timezone = pytz.timezone(timezone)
  except pytz.UnknownTimeZoneError as e:
    raise ConfigurationError(EXC_CONF_BAD_TIMEZONE_VALUE)
  
  conf['timezone'] = timezone

  if isinstance(telegram.get('users'), list):
    conf['telegram']['users'] = telegram['users'] 

  if isinstance(telegram_triggers.get('keywords'), list):
    conf['telegram']['triggers']['keywords'] = telegram_triggers['keywords']

  if isinstance(openai.get('model'), str):
    conf['openai']['model'] = openai['model']

  if isinstance(openai_prompts.get('base'), list):
    prompt_list = __parse_prompt_list(openai_prompts['base'])
    conf['openai']['prompts']['base'] = prompt_list

  if isinstance(openai_default_messages.get('error'), str):
    errorMessages = openai_default_messages['error']
    conf['openai']['defaultMessages']['error'] = [errorMessages]

  if isinstance(openai_default_messages.get('error'), list):
    errorMessages = openai_default_messages['error']
    conf['openai']['defaultMessages']['error'] = errorMessages

  if isinstance(openai_default_messages.get('dailyLimitExceeded'), str):
    dailyLimitMsg = openai_default_messages['dailyLimitExceeded']
    conf['openai']['defaultMessages']['dailyLimitExceeded'] = [dailyLimitMsg]

  if isinstance(openai_default_messages.get('dailyLimitExceeded'), list):
    dailyLimitMsg = openai_default_messages['dailyLimitExceeded']
    conf['openai']['defaultMessages']['dailyLimitExceeded'] = dailyLimitMsg
  
  if isinstance(openai_limits.get('daily'), int):
    conf['openai']['limits']['daily'] = openai_limits['daily']

  if isinstance(openai_limits.get('completion'), int):
    conf['openai']['limits']['completion'] = openai_limits['completion']

  if isinstance(openai_prompts.get('thematic'), list):
    thematic = openai_prompts['thematic']
    for element in thematic:
      if not (isinstance(element, dict) and
              isinstance(element.get('keywords'), list) and
              isinstance(element.get('prompts'), list)):
         raise ConfigurationError(EXC_CONF_BAD_PROMPT_VALUE) 
      prompt_list = __parse_prompt_list(element['prompts'])
      thematic = { 'keywords': element['keywords'],
                   'prompts': prompt_list }
      conf['openai']['prompts']['thematic'].append(thematic)

  if isinstance(openai_prompts.get('chat'), list):
    prompt_list = __parse_prompt_list(openai_prompts['chat'])
    conf['openai']['prompts']['chat'] = prompt_list

  if isinstance(openai_context.get('history'), bool):
    conf['openai']['context']['history'] = openai_context['history']

  if isinstance(openai_context.get('suppressTriggerUsername'), bool):
    val = openai_context['suppressTriggerUsername']
    conf['openai']['context']['suppressTriggerUsername'] = val

  return conf

def __read() -> dict:
  with open(__CONF_PATH, 'r') as f:
    data = yaml.safe_load(f)
  return __parse(data)

def read() -> dict:
  try:
    return __read()
  except Exception as e:
    ce = ConfigurationError(EXC_CONF_LOAD.format(str(e)))
    ce.__traceback__ = e.__traceback__
    raise ce
