import environment
import redis
from datetime import datetime

class Storage():
  def __init__(self, configuration: dict) -> None:
    self.__redis_db = environment.get_redis_db()
    self.__redis_charset = environment.get_redis_charset()
    self.__redis_host = environment.get_redis_host()
    self.__redis_namespace = environment.get_redis_namespace()
    self.__redis_password = environment.get_redis_password()
    self.__redis_port = environment.get_redis_port()
    self.__timezone = configuration['timezone']
  
  def __get_redis_connection(self) -> redis.Redis:
    return redis.Redis(str(self.__redis_host),
                        int(self.__redis_port),
                        int(self.__redis_db),
                        str(self.__redis_password))

  def __get_daily_token_usage_key(self) -> str:
    current_date = datetime.now(self.__timezone).strftime("%Y-%m-%d")
    return f'{self.__redis_namespace}:stats:token_usage_{current_date}'
  
  def get_daily_token_usage(self) -> int:
    conn = self.__get_redis_connection()
    value_bytes = conn.get(self.__get_daily_token_usage_key())
    conn.close()
    if value_bytes == None: return 0
    return int(value_bytes.decode(self.__redis_charset))
  
  def set_daily_token_usage(self, value: int) -> None:
    key = self.__get_daily_token_usage_key()
    conn = self.__get_redis_connection()
    conn.set(key, str(value).encode(self.__redis_charset))
    conn.close()