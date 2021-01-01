from configLoader import cfg
import telegrampy
from telegrampy.ext import commands
from utils import *
from datetime import datetime

bot = commands.Bot(cfg.tg_token)
queue = Queue()
user_based_history = {}
chat_based_history = {}

history = user_based_history if cfg.history == "user" else chat_based_history


def get_command_text(txt):
    """Возвращает пользовательский текст после /команды или пустоту"""
    r = txt.split(' ', 1)
    return r[1][0:1024] if len(r) > 1 else ''


def get_reply_text(msg):
    """Возвращает текст пересланного (отвеченного) сообщения или пустоту"""
    return msg._data['reply_to_message']['text'][0:1024] if 'reply_to_message' in msg._data else ''


def process_msg(func):
    """Декоратор первичного обработчика сообщения, отвечает за контроль доступа и логи"""
    async def default_msg_handler(ctx):
        if func.__name__.endswith('dialog_former'):
            print('new msg from @{} ({}) in {} ({})'.format(
                ctx.author.name, ctx.author.id, ctx.chat.title or 'private messages', ctx.chat.id))
        if (cfg.use_whitelist and ctx.chat.id in cfg.whitelist) or (not cfg.use_whitelist):
            await func(ctx)

    return default_msg_handler


@process_msg
async def user_based_dialog_former(msg):
    """Формирует чат для ввода в gpt, на основе истории диалога с пользователем"""
    if not msg.content or len(msg.content) < 1 or msg.content[0] == '/':
        return
    msg.content = filter_symbol(msg.content, ":", " ")
    user_history = add_to_user_history(msg, history)
    start_text = 'Сейчас {} год. Я - {}. Встретил{} я человека, по имени {}. Решили поболтать.\n'.format(
        datetime.now().year, cfg.role, ending[cfg.rod],
        translit(msg.author.first_name).capitalize())
    dialog_text = ''
    offset = 0
    while len(start_text + dialog_text) > 1024 or offset == 0:
        dialog_text = ''
        for item in user_history[offset:]:
            if item[1] == 1:
                dialog_text += 'Человек: "' + item[0] + '".\n'
            else:
                dialog_text += 'Я: "' + item[0] + '".\n'
        dialog_text += 'Я: "'
        offset += 1
    ctx = commands.Context('nocommand', bot=bot, message=msg, author=msg.author, chat=msg.chat)
    queue.add_to(queue.build_item(start_text + dialog_text, ctx, historic_response_parser), msg.author.id)


@process_msg
async def chat_based_dialog_former(msg):
    """Формирует чат для ввода в gpt, на основе истории диалога в беседе"""
    if not msg.content or len(msg.content) < 1 or msg.content[0] == '/':
        return
    msg.content = filter_symbol(msg.content, ":", " ")
    chat_history = add_to_chat_history(msg, history)
    start_text = 'Сейчас {} год. Я - {}. Я решил{} поболтать с людьми.\n'.format(
        datetime.now().year, cfg.role, ending[cfg.rod])
    dialog_text = ''
    offset = 0
    while len(start_text + dialog_text) > 1024 or offset == 0:
        dialog_text = ''
        for item in chat_history[offset:]:
            if item[1] != 0:
                dialog_text += item[2] + ': "' + item[0] + '".\n'
            else:
                dialog_text += 'Я: "' + item[0] + '".\n'
        dialog_text += 'Я: "'
        offset += 1
    ctx = commands.Context('nocommand', bot=bot, message=msg, author=msg.author, chat=msg.chat)
    queue.add_to(queue.build_item(start_text + dialog_text, ctx, historic_response_parser), msg.author.id)


bot.on_message = user_based_dialog_former if cfg.history == 'user' else chat_based_dialog_former


@bot.command(name='reset')
@process_msg
async def tg_reset(ctx):
    """Чистит историю диалога с пользователем"""
    history[ctx.author.id if cfg.history == "user" else ctx.chat.id] = []
    #TODO: ограничить возможность очистки истории чата только для админов чата
    return


@bot.command(name='word')
@process_msg
async def tg_word(ctx):
    """Формирует текст для ввода в gpt, цель которого - отгадать слово"""
    req_text = get_command_text(ctx.message.content)
    if req_text == '' or req_text == ' ':
        return
    req_text = filter_symbol(add_dot(req_text), '"', "''")
    queue.add_to(
        queue.build_item(
            'ЗАДАЧА: "Отгадать слово." ОПИСАНИЕ: "' + req_text.capitalize() +
            '". ОТВЕТ: "', ctx, rage_response_parser, -0.02), ctx.author.id)


@bot.command(name='rage')
@process_msg
async def tg_rage(ctx):
    """Формирует текст для ввода в gpt, цель которого - получить яростный ответ"""
    req_text = get_command_text(ctx.message.content).capitalize()
    if req_text == '' or req_text == ' ':
        req_text = 'Ты жалкий мерзавец, дуралей и профан! Я таких как ты терпеть не могу!'
    req_text = filter_symbol(req_text, '"', "''")
    queue.add_to(
        queue.build_item(
            'Идя ночью по улице, какой-то незнакомый пьяный тип подошёл к тебе и сказал: "'
            + req_text +
            '", на что ты решил поставить его на место, и разозлившись, в ярости ответил ему: "',
            ctx, rage_response_parser), ctx.author.id)


@bot.command(name='translate')
@process_msg
async def tg_translate(ctx):
    """Формирует текст для ввода в gpt, цель которого - перевести текст с английского"""
    req_text = get_command_text(ctx.message.content).capitalize()
    if req_text == '' or req_text == ' ':
        return
    req_text = filter_symbol(filter_symbol(req_text, ';', " "), ":", " ")
    queue.add_to(
        queue.build_item(
            'en: Dog; ru: Собака;; en: Today I decided; ru: Сегодня я решил;; en: They will come back soon. We need to catch the fish!; ru: Они скоро вернутся. Нам нужно поймать рыбу!;; en: The king of the castle wants to see you.; ru: Король замка хочет тебя видеть.;; en: She ordered to feed that cat; ru: Она приказала накормить того кота;; en: Where are you from, stranger?; ru: Откуда ты, странник?;; en: '
            + req_text + '; ru:', ctx, translator_response_parser),
        ctx.author.id)


@bot.command(name='continue')
@process_msg
async def tg_continue(ctx):
    """Продолжает текст на основе текста из пересланного сообщения"""
    queue.add_to(queue.build_item(get_reply_text(ctx.message), ctx), ctx.author.id)


@bot.command(name='gpt')
@process_msg
async def tg_gpt(ctx):
    """Ввод сырого текста в gpt"""
    queue.add_to(queue.build_item(get_command_text(ctx.message.content), ctx), ctx.author.id)


@bot.command(name=cfg.stop_command)
@process_msg
async def tg_stop(ctx):
    """Остановка бота"""
    if ctx.author.id == cfg.admin_id:
        queue.queue.insert(0, queue.build_item(cfg.stop_command, ctx))