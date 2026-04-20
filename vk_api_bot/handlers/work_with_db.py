import aiohttp
import psycopg
from vkbottle import GroupEventType
from vkbottle.bot import Blueprint, Message, MessageEvent, rules
from vkbottle.tools import EMPTY_KEYBOARD
from vkbottle.dispatch.dispenser import BaseStateGroup
import keyboards.all_keyboards as kb
from database.db import Database
from create_bot import bot

bd_router = Blueprint("bd_router")
bd_router.labeler.vbml_ignore_case = True

class CSV(BaseStateGroup):
    zeopoxa = 0


@bd_router.on.message(text=["/csv"])
async def csv_greet(message: Message):
    await message.answer("Вы хотите загрузить данные о своих пробежках из csv файла?",
                         keyboard=kb.csv_question())


@bd_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"zeopoxa_csv_question": "yes"})
)
async def yes_zeopoxa_csv_fill(event: MessageEvent):
    if event.payload["zeopoxa_csv_question"] == "yes":
        await bot.state_dispenser.set(event.peer_id, CSV.zeopoxa)
    await bot.api.messages.send(
        peer_id=event.peer_id,
        message="Супер, тогда скинь csv файл с твоими пробежками.",
        random_id=0
    )


@bd_router.on.message(state=CSV.zeopoxa)
async def csv_fill(message: Message):
    attachment = message.attachments[0]
    f_name = attachment.doc.title
    if f_name.endswith(".csv"):
        file_url = attachment.doc.url
        async with Database() as db:
            await db.copy_csv_zeopoxa(file_url, message.from_id)
            await message.answer("Данные занесы в базу данных успешно!",
                                 keyboard=EMPTY_KEYBOARD)
    else:
        await message.answer("Скиньте именно csv файл, пожалуйста.",
                             keyboard=EMPTY_KEYBOARD)

@bd_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"csv_question": "no"}))
async def no_csv_fill(event: MessageEvent):
    await bot.api.messages.send(
        peer_id=event.peer_id,
        message="Хорошо, тогда возвращаемся в меню.",
        random_id=0,
        keyboard=kb.menu_kb())
