from logging import error

MESSAGE_ERROR = 'Сообщение не отправлено'
HOMEWORK_LIST_ERROR = 'Данные не в формате list'
HOMEWORK_DICT_ERROR = 'Данные не в формате dict}'
HOMEWORK_KEY_ERROR = 'В ответе нет ключа homework_name и/или status'
PARSE_STATUS_ERROR = 'Не известный статус проверки'
SERVER_PROBLEMS = 'Сервер прилег, а ты вставай и разбирайся'
RESPONSE_ERROR = 'В ответе на запрос произошла ошибка'


class BotErrors(Exception):
    """базовый класс для всех исключений."""
    pass


class MessageError(BotErrors):
    """сообщение не отправлено."""
   

class ResponseError(BotErrors):
    """Ошибка запроса."""


class ServerError(BotErrors):
    """Ошибка подключения к серверу."""


class HomeworkListError(BotErrors):
    """данные не в формате list."""


class HomeworkKeyError(TypeError):
    """ошибка ключа запроса."""


class ParseStatusError(BotErrors):
    """не известный статус."""


class HomeworkDictError(BotErrors):
    """данные не в формате dict."""
