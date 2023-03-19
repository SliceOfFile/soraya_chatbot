import soraya_slog as logger
import sys
import traceback
from strings import LOG_PANIC
import re

def str_includes(string: str, search: str) -> bool:
  pattern = r'\b{}\b'.format(re.escape(search.lower()))
  return re.search(pattern, string.lower()) is not None

def exc_to_dict(e: Exception) -> dict:
  extracted = traceback.extract_tb(e.__traceback__)
  traceback_list = []

  for element in extracted:
    traceback_list.append({ 'filename': element.filename,
                            'name': element.name,
                            'position': { 'line': element.lineno,
                                         'column': element.colno } })

  return { 'name': type(e).__name__,
           'message': str(e),
           'traceback': traceback_list }

def panic(e: Exception) -> None:
  logger.critical(LOG_PANIC, { 'exception': exc_to_dict(e) })
  sys.exit(1)