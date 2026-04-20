from create_bot import bot
from vkbottle.bot import Blueprint, Message, MessageEvent, rules
from vkbottle.dispatch.dispenser import BaseStateGroup
from vkbottle import CtxStorage, GroupEventType
import keyboards.all_keyboards as kb
from datetime import datetime
from database.db import Database
from vkbottle.tools import EMPTY_KEYBOARD


start_router = Blueprint("start_router")
start_router.labeler.vbml_ignore_case = True

class Form_user(BaseStateGroup):
    user_id = 0
    gender = 'male'
    weight = 1
    height = 2
    birthday = datetime.now()
    run_time = 3
    shoes = ""
    date_join = 4


ctx = CtxStorage()

@start_router.on.message(text=["/start", "Старт", "старт"])
async def start_message(message: Message):
    user = (await bot.api.users.get(user_ids=f"{message.from_id}"))[0]
    name = user.first_name
    await message.answer(f'Привет {name}!\nЯ - твой помощник в мире бега, а именно - Runing_Bot\n' +
                         'Сейчас нужно будет пройти небольшой' +
                         ' опрос для того, чтобы я лучше мог вам помочь в дальнейшем.\n' +
                         'Давай начнем с твоего пола. Выбери кто ты.\n\n',keyboard=kb.gender_kb())
    await bot.state_dispenser.set(message.from_id, Form_user.gender)
    ctx.set("user_id", message.from_id)
    ctx.set("date_join", datetime.now().date())
    async with Database() as db:
        await db.input_long_ago(message.from_id, 0)


@start_router.on.message(text=["/menu", "меню", "выйти в меню"])
async def menu_message(message: Message):
   # await bot.state_dispenser.delete(message.from_id)
    await message.answer("Держите ваше меню!", keyboard=kb.menu_kb())


@start_router.on.message(text=["/start_love"])
async def love_message(message: Message):
   # await bot.state_dispenser.delete(message.from_id)
    await message.answer("Привет! Я люблю Машу Аникееву(временно Аникееву"
                         ", в планах ей не долго осталось быть Аникеевой)", keyboard=EMPTY_KEYBOARD)


@start_router.on.message(text=["Я тоже люблю Машу Аникееву", "Вообще-то, я люблю Машу Аникееву"])
async def about_me_message(message: Message):
  #  await bot.state_dispenser.delete(message.from_id)
    await message.answer("Оу, видимо вы - Сергей Арефьев", keyboard=EMPTY_KEYBOARD)


@start_router.on.message(text=["/links"])
async def links_message(message: Message):
   # await bot.state_dispenser.delete(message.from_id)
    await message.answer("Вот некоторые полезные ссылки", keyboard=kb.links_kb())

@start_router.on.raw_event(GroupEventType.MESSAGE_EVENT,
                           MessageEvent,
                        rules.PayloadRule({"gender": "male"}))
async def male_message(event: MessageEvent):
    ctx.set("gender", "male")
    await bot.api.messages.send(
        peer_id=event.peer_id,
        message="Хорошо, теперь перейдем к твоему весу. Напиши сколько ты весишь в кг",
        keyboard=EMPTY_KEYBOARD,
        random_id=0
    )
    await bot.state_dispenser.set(event.peer_id, Form_user.weight)

@start_router.on.raw_event(GroupEventType.MESSAGE_EVENT,
                           MessageEvent,
                        rules.PayloadRule({"gender": "female"}))
async def female_message(event: MessageEvent):
    ctx.set("gender", "female")
    await bot.api.messages.send(
        peer_id=event.peer_id,
        message="Хорошо, теперь перейдем к твоему весу. Напиши сколько ты весишь в кг",
        keyboard=EMPTY_KEYBOARD,
        random_id=0
    )
    await bot.state_dispenser.set(event.peer_id, Form_user.weight)

@start_router.on.message(state=Form_user.weight)
async def weight_message(message: Message):
    w = message.text
    if w.isdigit():
        if 0 <= int(w) <= 150:
            await bot.state_dispenser.set(message.from_id, Form_user.height)
            ctx.set("weight", int(w))
            await message.answer("Супер, теперь отправь свой рост в сантиметрах")
        else:
            await message.answer("Ну что за бред, напиши свой настоящий вес")
    else:
        await message.answer("Нет нет нет, отправьте свой вес, пожалуйста, в цифрах")


@start_router.on.message(state=Form_user.height)
async def height_message(message: Message):
    h = message.text
    if h.isdigit():
        if 0 <= int(h) <= 235:
            await message.answer('Отлично, отправь, пожалуйста, '
                                 'свою дату рождения в формате "YYYY-MM-DD""')
            await bot.state_dispenser.set(message.from_id, Form_user.birthday)
            ctx.set("height", int(h))
        else:
            await message.answer("Не высоковат ли ты??? Напиши честно свой рост")
    else:
        await message.answer("Ненене, в цифрах пожалуйста")


def is_date(data, fmt="%Y-%m-%d"):
    try:
        datetime.strptime(data, fmt)
        return True
    except ValueError:
        return False


@start_router.on.message(state=Form_user.birthday)
async def birthday_message(message: Message):
    b = message.text
    if is_date(b):
        if datetime.now() > datetime.strptime(b, "%Y-%m-%d") > datetime(1926, 1, 1):
            await message.answer("Так-так, осталось чуть-чуть, "
                                 "скажи сколько лет ты занимаешься бегом")
            await bot.state_dispenser.set(message.from_id, Form_user.run_time)
            ctx.set("birthday", datetime.strptime(b, "%Y-%m-%d"))
        else:
            await message.answer("Не староват ли ты???")
    else:
        await message.answer("Введи аккуратнее свою дату рождения, "
                             "посмотри еще раз на формат")


def is_float(text):
    try:
        float(text)
        return True
    except ValueError:
        return False


@start_router.on.message(state=Form_user.run_time)
async def runtime_message(message: Message):
    rt = message.text
    if is_float(rt) and float(rt) < (datetime.now() - ctx.get("birthday")).days / 365.25:
        await message.answer("Молодец, остался последний вопрос. Напиши про свою обувь."
                             " А именно название кроссовок, их имя или все то, что к тебя с ними ассоциируется."
                             " Это нужно, чтобы отслеживать их ресурс и указывать их при пробежке."
                             " Если кроссовок несколько, то напиши их через запятую")
        await bot.state_dispenser.set(message.from_id, Form_user.shoes)
        ctx.set("run_time", float(rt))
    else:
        await message.answer("Введи пожалуйста сколько ты занимаешся бегом по-честному")


@start_router.on.message(state=Form_user.shoes)
async def shoes_message(message: Message):
    await bot.state_dispenser.set(message.from_id, Form_user.shoes)
    ctx.set("shoes", message.text)
    await message.answer("Всё всё всё, отстаю от тебя, ты большой молодец. Спасибо, что рассказал о себе!")
    await bot.state_dispenser.delete(message.from_id)

    user_id = ctx.get("user_id")
    async with Database() as db:
        in_db = await db.check_id(user_id)
        if not in_db:
            data_insert = (ctx.get("user_id"), ctx.get("gender"), ctx.get("weight"), ctx.get("height"),
                           ctx.get("birthday"), ctx.get("run_time"), ctx.get("shoes"), ctx.get("date_join"))
            await db.insert_user(data_insert)

            await message.answer(("Поздравляю, теперь вы зарегистрированы в базе данных!"
                                  "Примите к сведению, что:\n"
                                  'Если вы захотите внести сведения о пробежке, то введите "/main",\n' +
                                  'Если вы захотите посмотреть меню, то введите "/menu"\n' +
                                  'Если вы хотите посмотреть полезные ссылки, то введите /links\n' +
                                  'Если вы хотите загрузить данные о пробежках, то введите /csv\n'
                                  ))
        else:
            await message.answer("Вы уже есть в базе данных. Хотите перезаписать данные?",
                                 keyboard=kb.save_kb())


@start_router.on.raw_event(GroupEventType.MESSAGE_EVENT,
                           MessageEvent,
                           rules.PayloadRule({"users": "overwrite"}))
async def overwrite_message(event: MessageEvent):
    async with Database() as db:
        await db.delete_user(ctx.get("user_id"))
        data_insert = (ctx.get("user_id"), ctx.get("gender"), ctx.get("weight"), ctx.get("height"),
                       ctx.get("birthday"), ctx.get("run_time"), ctx.get("shoes"), ctx.get("date_join"))
        await db.insert_user(data_insert)
        await bot.api.messages.send(peer_id=event.peer_id,
                                    message="Вы успешно поменяли свои данные!", random_id=0)
        ctx.delete("user_id"), ctx.delete("gender"), ctx.delete("weight"), ctx.delete("height"),
        ctx.delete("birthday"), ctx.delete("run_time"), ctx.delete("shoes"), ctx.delete("date_join")


@start_router.on.raw_event(GroupEventType.MESSAGE_EVENT,
                           MessageEvent,
                        rules.PayloadRule({"users": "nothing"}))
async def nothing_message(event: MessageEvent):
    await bot.api.messages.send(peer_id=event.peer_id,
                                message="Хорошо, хорошо. Пусть всё останется как есть.", random_id=0)