import asyncio
import re

translitDict = {
    'eng': 'qwertyuiopasdfghjklzxcvbnm',
    'ru': 'квертиуиопасдфжхжклзкцвбнм'
}
ending = {'m': '', 'j': 'а', 's': 'о'}


def translit(input_text):
    """Удаляет непонятные символы и транслитит английский текст на кириллицу (🚲)"""
    output = []
    input_text = re.sub('[^a-zA-ZА-Яа-яёЁ_ \-]+', '', input_text)
    input_text = input_text.lower().replace('x', 'ks').replace(
        'j', 'dj').replace('sh', 'ш').replace('zh', 'ж').replace('ch', 'ч')
    for char in input_text:
        output.append(
            char.translate(
                str.maketrans(translitDict.get('eng'),
                              translitDict.get('ru'))))
    return ''.join(output)


def add_dot(txt):
    """Добавляет точку к тексту, если её там нет"""
    return txt + '.' if txt[-1] != '.' else txt


def filter_symbol(string, symbol, alternative):
    """Заменяет символы, которые могут искривить ввод, пока что тут обычный реплейс"""
    return string.replace(symbol, alternative)


class Queue:
    """Очередь сообщений"""
    def __init__(self, max_in_queue_per_user=10):
        self.queue = []
        self.limits = {}
        self.max_per_user = max_in_queue_per_user
        
    def activate(self, loop=False):
        """Вызывается из нового созданого event-loop'a чтобы не конфликтовать с тележной либой, обнуляет фьючер (🏒)"""
        if loop:
            self.loop = loop
        self.not_empty = asyncio.Future()

    @asyncio.coroutine
    def _trigger(self):
        """Существует для установки результата фьючера о наличии сообщения из правильного event-loop'a (🏒)"""
        if len(self.queue) > 0:
            self.not_empty.set_result(True)
            
    def pull_the_trigger(self):
        """Обёртка для функции _trigger"""
        asyncio.run_coroutine_threadsafe(self._trigger(), self.loop)

    def build_item(self, text, ctx, responseParser=None, pOffset=0):
        return (text, ctx.message.reply, ctx.chat.send_action, ctx.author.id,
                ctx.chat.id, asyncio.get_event_loop(), responseParser, pOffset)

    async def get_item(self):
        if len(self.queue) == 0:
            await self.not_empty
            self.activate()
        return self.queue.pop(0) if len(self.queue) > 0 else ""

    def add_to(self, item, user):
        if item[0] == '':
            return
        if user not in self.limits:
            self.limits[user] = 1
        else:
            self.limits[user] += 1
        if self.limits[user] <= self.max_per_user:
            self.queue.append(item)
            self.pull_the_trigger()


def cut_extra_stuff(txt):
    """Вырезает артефакты"""
    extra = txt.find('\n\n\n')
    return txt[0:extra] if extra != -1 else txt


async def delay(func, sec, *args):
    await asyncio.sleep(sec)
    await func(*args)


def add_to_user_history(msg, history):
    if msg.author.id in history:
        history[msg.author.id].append((msg.content, 1))
        if len(history[msg.author.id]) > 16:
            history[msg.author.id].pop(0)
            history[msg.author.id].pop(0)
    else:
        history[msg.author.id] = [(msg.content, 1)]
    return history[msg.author.id]


def add_to_chat_history(msg, history):
    if msg.chat.id in history:
        history[msg.chat.id].append(
            (msg.content, msg.author.id,
             translit(msg.author.first_name).capitalize()))
        if len(history[msg.chat.id]) > 16:
            history[msg.chat.id].pop(0)
            history[msg.chat.id].pop(0)
    else:
        history[msg.chat.id] = [(msg.content, msg.author.id,
                                 translit(msg.author.first_name).capitalize())]
    return history[msg.chat.id]


def translator_response_parser(txt):
    return txt[0:txt.find(';')]


def rage_response_parser(txt):
    return txt[0:txt.find('"')]


def historic_response_parser(txt, uid, history):
    resp = rage_response_parser(txt).replace('Человек:', '')
    history[uid].append((resp, 0))
    return resp
