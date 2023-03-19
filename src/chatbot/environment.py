import os

def get_telegram_token() -> str:
  return os.environ['TELEGRAM_TOKEN']

def get_redis_db() -> str:
  return os.environ['REDIS_DB']

def get_redis_charset() -> str:
  return os.environ['REDIS_CHARSET']

def get_redis_host() -> str:
  return os.environ['REDIS_HOST']

def get_redis_namespace() -> str:
  return os.environ['REDIS_NAMESPACE']

def get_redis_password() -> str:
  return os.environ['REDIS_PASSWORD']

def get_redis_port() -> str:
  return os.environ['REDIS_PORT']