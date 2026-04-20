from vkbottle import CtxStorage, GroupEventType
from vkbottle.bot import Message, MessageEvent, rules
from vkbottle.dispatch.dispenser import BaseStateGroup
from vkbottle.tools import EMPTY_KEYBOARD, Keyboard
from create_bot import bot
import keyboards.all_keyboards as kb
from database.db import Database
from datetime import datetime, timedelta, time
from operator import or_
from functools import reduce

import numpy as np
from handlers.menu import control_hour, control_minute, control_second

ctx = CtxStorage()
ctx_self_choice = CtxStorage()

class jog_info(BaseStateGroup):
    start_time = datetime.now()
    finish_time = datetime.now() + timedelta(hours=1)
    jog_id = 0
    name_jog = "name_jog"
    caption_jog = "caption_jog"
    distance = 1
    time_jog = time()
    calories = 2
    average_heart_rate = 3
    max_heart_rate = 4
    average_pace = time(hour=1)
    max_pace = time(hour=2)
    min_height = 5
    max_height = 6
    shoes = ""
    temperature = 7
    wind_speed = 8
    end = 9

class self_choice(BaseStateGroup):
    choice_data = 0
    start_fill_later = 1

async def get_shoes_keyboard(user_id):
    return await kb.kb_shoes(user_id, skip_somthing="skip_shoes")

list_state = [jog_info.name_jog, jog_info.caption_jog, jog_info.distance, jog_info.calories,
              jog_info.average_heart_rate, jog_info.max_heart_rate, jog_info.average_pace, jog_info.max_pace,
              jog_info.min_height, jog_info.max_height, jog_info.shoes, jog_info.temperature, jog_info.wind_speed]
#name_current_state, next_state, keyboard, type_trans, in_text
state_config = {
    "jog_info:name_jog": ("name_jog", jog_info.caption_jog,
                        kb.jog_skip_something("skip_caption"), None, "заметку о тренировке"),
    "jog_info:caption_jog": ("caption_jog", jog_info.distance, EMPTY_KEYBOARD, None, "дистанцию в км"),
    "jog_info:1": ("distance", jog_info.time_jog, kb.self_auto_time_jog(), "float",
                        "время пробежки, если хотите указать его сами (формат: ЧЧ:ММ:СС) или мы его посчитаем, "
                        "как время между нажатием кнопок"),

    "jog_info:2": ("calories", jog_info.average_heart_rate,
                        kb.jog_skip_something("skip_average_heart_rate"), "float",
                        "средний пульс на пробежке"),
    "jog_info:3": ("average_heart_rate", jog_info.max_heart_rate,
                                  kb.jog_skip_something("skip_max_heart_rate"), "int",
                                  "максимальный пульс во время пробежки"),
    "jog_info:4": ("max_heart_rate", jog_info.average_pace,
                              kb.jog_skip_something("skip_average_pace"), "int",
                              "средний темп во время пробежки (формат ММ:СС)"),
    "jog_info:01:00:00": ("average_pace", jog_info.max_pace,
                            kb.jog_skip_something("skip_max_pace"), "time",
                            "максимальный темп во время пробежки (формат ММ:СС)"),
    "jog_info:02:00:00": ("max_pace", jog_info.min_height,
                        kb.jog_skip_something("skip_min_height"), "time",
                        "минимальную высоту, которую вы посетили за пробежку"),
    "jog_info:5": ("min_height", jog_info.max_height,
                          kb.jog_skip_something("skip_max_height"), "float",
                          "максимальную высоту, которую вы посетили за пробежку"),
    "jog_info:6": ("max_height", jog_info.shoes,
                          get_shoes_keyboard, "float",
                          "обувь, в которой вы провели сегодняшнюю тренировку"),
    "jog_info:": ("shoes", jog_info.temperature,
                     kb.jog_skip_something("skip_temperature"), None,
                     "температуру, которая вас сопровождала во время пробежки"),
    "jog_info:7": ("temperature", jog_info.wind_speed,
                           kb.jog_skip_something("skip_wind_speed"), "int",
                           "скорость ветра во время тренировки в м/с"),
    "jog_info:8": ("wind_speed", jog_info.end,
                   EMPTY_KEYBOARD, "int", "ничего, на этом закончили")
}

skip_config = {
    "skip_name": (kb.jog_skip_something("skip_caption"), jog_info.caption_jog,
                  "Супер, напиши заметку к этой пробежку"),
    "skip_caption": (EMPTY_KEYBOARD, jog_info.distance,
                     "Так так, отлично, напиши дистанцию в км за эту пробежку"),
    "skip_calories": (kb.jog_skip_something("skip_average_heart_rate"), jog_info.average_heart_rate,
                      "Отлично, напиши средний пульс"),
    "skip_average_heart_rate": (kb.jog_skip_something("skip_max_heart_rate"), jog_info.max_heart_rate,
                            "Итак, напиши максимальный пульс"),
    "skip_max_heart_rate": (kb.jog_skip_something("skip_average_pace"), jog_info.average_pace,
                            'Идем дальше, напиши средний темп в формате "ММ:СС"'),
    "skip_average_pace": (kb.jog_skip_something("skip_max_pace"), jog_info.max_pace,
                          'А теперь - максимальный темп в формате "ММ:СС"'),
    "skip_max_pace": (kb.jog_skip_something("skip_min_height"), jog_info.min_height,
                      "Угу, сейчас - минимальную высоту за пробежку"),
    "skip_min_height": (kb.jog_skip_something("skip_max_height"), jog_info.max_height,
                        "Прекрасно, теперь - максимальную высоту за пробежку"),
    "skip_max_height": (get_shoes_keyboard, jog_info.shoes,
                        "И теперь - обувь, в которой вы провели эту тренировку"),
    "skip_shoes": (kb.jog_skip_something("skip_temperature"), jog_info.temperature,
                   "А сейчас напиши температуру во время пробежки"),
    "skip_temperature": (kb.jog_skip_something("skip_wind_speed"), jog_info.wind_speed,
                         "И последний вопрос, напиши скорость ветра во время тренировки"),
    "skip_wind_speed": (EMPTY_KEYBOARD, jog_info.end, "На этом регистрация этой тренировки кончилась")
}


rules_list = [rules.PayloadRule({"jog": key}) for key in skip_config.keys()]
combined_rule = reduce(or_, rules_list)


async def remind_goals(user_id):
    async with Database() as db:
        await db.initialize_active_goal(user_id, datetime.now())
        goals = await db.get_active_goals(user_id)
        if len(goals) > 0:
            text = "Ваши цели и прогресс в них:\n"
        else:
            text = "Главное меню\n"
        for goal in goals:
            distance_time_pace_diffgain = np.array(await db.distance_time_pace_diffgain_from_start_to_finish(
                user_id, goal[1], goal[2]))
            if len(distance_time_pace_diffgain) == 0:
                continue
            if goal[-2] is not None:
                diff_gain = distance_time_pace_diffgain[:, 4]
                percent_diff_gain = round(np.sum([df for df in diff_gain if df is not None]) / goal[-2], 2)
                count_active_bar = round(percent_diff_gain * 10)
                text += (f"Преодолеть разность высот в {goal[-2]} м, вы ее выполнили на: "
                         f"{'█' * count_active_bar}{'░' * (10 - count_active_bar)} {int(percent_diff_gain * 100)}/100 %\n")
            elif goal[-3] is not None:
                time_jog = distance_time_pace_diffgain[:, 2]
                percent_time_jog = round(np.sum([t.hour * 3600 + t.minute * 60 + t.second
                                           for t in time_jog if t is not None]) / goal[-3], 2)
                count_active_bar = round(percent_time_jog * 10)
                text += f"Общее время:"
                hour = int(goal[-3]//3600)
                minute = int(goal[-3] // 60) - hour * 60
                second = goal[-3] - 3600 * hour - minute * 60
                if hour != 0:
                    text += f" {hour} {await control_hour(hour)}"
                if minute != 0:
                    text += f" {minute} {await control_minute(minute)}"
                if second != 0:
                    text += f" {second} {await control_second(second)} "
                text += (f", Вы ее выполнили на {'█' * count_active_bar}{'░' * (10 - count_active_bar)} "
                         f"{int(percent_time_jog * 100)}/100 %\n")
            elif goal[-4] is not None:
                distance = distance_time_pace_diffgain[:, 1]
                percent_distance = round(np.sum([d for d in distance if d is not None]) / goal[-4], 2)
                count_active_bar = round(percent_distance * 10)
                text += (f"Дистанция: {goal[-4]} км, Вы ее выполнили на {'█' * count_active_bar}"
                         f"{'░' * (10 - count_active_bar)} {int(percent_distance * 100)}/100 %\n")
            elif goal[-5] is not None:
                count_jog = distance_time_pace_diffgain.shape[0]
                percent_jog = round(count_jog / goal[-5], 2)
                count_active_bar = round(percent_jog * 10)
                text += (f"Количество пробежек: {goal[-5]}, Вы ее выполнили на {'█' * count_active_bar}"
                         f"{'░' * (10 - count_active_bar)} {int(percent_jog) * 100}/100 %\n")
        if len(goals) > 0:
            text += "Сегодняшняя пробежка должна принести хорошие результаты, для этих целей!"
    return text

async def clear_ctx(ctx_):
    list_name = ["user_id","jog_id","start_time","finish_time", "name_jog","caption_jog",
    "distance","time_jog", "calories", "average_heart_rate","max_heart_rate",
    "average_pace","max_pace","min_height", "max_height", "shoes","temperature", "wind_speed", "self_choice", "start_fill"]
    for key in list_name:
        if ctx.contains(key):
            ctx.delete(key)

@bot.on.message(text=["/main"])
async def main_message(message: Message):
    await clear_ctx(ctx)
    await clear_ctx(ctx_self_choice)
    text = await remind_goals(message.from_id)
    await message.answer(text, keyboard=kb.main_kb())


@bot.on.message(text=["Начать пробежку"])
async def start_jog(message: Message):
    ctx.set("start_time", datetime.now())
    await message.answer("Отлично, поехали!", keyboard=kb.jog_continue())
    await bot.state_dispenser.set(message.from_id, jog_info.finish_time)
    async with Database() as db:
        jog_id = await db.take_last_jog_id(message.from_id)
        jog_id += 1
    ctx.set("user_id", message.from_id)
    ctx.set("jog_id", jog_id)

@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"jog": "end"})
)
async def notice_long_age_true(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id = event.peer_id,
        message="Молодец, отличная пробежка! Хочешь заполнить анкету по этой пробежке?",
        random_id=0,
        keyboard=kb.jog_form()
    )
    ctx.set("finish_time", datetime.now())


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"jog": "fill"})
)
async def start_fill_form(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Назови как-нибудь эту тренировку",
        keyboard=kb.jog_skip_name(),
        random_id=0
    )
    await bot.state_dispenser.set(event.peer_id, jog_info.name_jog)


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"jog": "then"})
)
async def fill_later(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        random_id=0,
        message='Хорошо, тогда чтобы внести данные о тренировке, просто в разделе "Заполнить информацию о пробежке"'
                ' введи дату сегодняшней пробежки.',
        keyboard=EMPTY_KEYBOARD
    )
    async with Database() as db:
        await db.insert_date_id([ctx.get("user_id"), ctx.get("jog_id"),
                                 ctx.get("start_time"), ctx.get("finish_time")])


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"jog_time_choice": "self"})
)
async def self_time(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Хорошо, жду ответа",
        keyboard=EMPTY_KEYBOARD,
        random_id=0
    )

@bot.on.message(state=jog_info.time_jog)
async def self_time_fill(message: Message):
    try:
        ctx.set("time_jog", datetime.strptime(message.text, "%H:%M:%S").time())
        await message.answer("Отлично, теперь введи калории", keyboard=kb.jog_skip_something("skip_calories"))
        await bot.state_dispenser.set(message.from_id, jog_info.calories)
    except:
        await message.answer("Введи, пожалуйста, в обещанном формате")

@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"jog_time_choice": "auto"})
)
async def auto_time(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Отлично, теперь напиши калории, которые ты потратил на пробежке",
        keyboard=kb.jog_skip_something("skip_calories"),
        random_id=0
    )
    td = ctx.get("finish_time") - ctx.get("start_time")
    seconds = int(td.total_seconds())
    h = seconds // 3600
    m = (seconds - h * 3600) // 60
    s = seconds - h * 3600 - m * 60
    ctx.set("time_jog", time(hour=h, minute=m, second=s))
    await bot.state_dispenser.set(event.peer_id, jog_info.calories)


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadContainsRule({"shoes": "shoe"})
)
async def shoe(event: MessageEvent):
    ctx.set("shoes", event.object.payload["button_text"])
    await bot.state_dispenser.set(event.peer_id, jog_info.temperature)
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        random_id=0,
        message="Отлично, теперь введи температуру во время пробежки",
        keyboard=kb.jog_skip_something("skip_temperature")
    )


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    combined_rule
)
async def skip_something(event: MessageEvent):
    current_name = event.object.payload.get("jog")
    keyboard, next_state, text = skip_config[current_name]

    if isinstance(keyboard, Keyboard) or keyboard == EMPTY_KEYBOARD:
        kbd = keyboard
    else:
        coro = keyboard(event.peer_id)
        kbd = await coro
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message=text,
        keyboard=kbd,
        random_id=0
    )
    await bot.state_dispenser.set(event.peer_id, next_state)
    if next_state == jog_info.end:
        await end()



@bot.on.message(state=list_state)
async def dialog(message: Message):
    current_state = (await bot.state_dispenser.get(message.from_id)).state
    name_current_state, next_state, keyboard, type_trans, in_text = state_config[f"{current_state}"]

    try:
        if type_trans is None:
            ctx.set(name_current_state, message.text)
        elif type_trans == "time":
            ctx.set(name_current_state, datetime.strptime(message.text, '%M:%S'))
        elif type_trans == "float":
            ctx.set(name_current_state, float(message.text.replace(',', '.')))
        elif type_trans == "int":
            ctx.set(name_current_state, int(message.text))

        await bot.state_dispenser.set(message.from_id, next_state)
        if isinstance(keyboard, Keyboard) or keyboard == EMPTY_KEYBOARD:
            await message.answer(f"Отлично, теперь введите {in_text}",
                                 keyboard=keyboard)
        else:
            coro = keyboard(message.from_id)
            kbd = await coro
            await message.answer(f"Отлично, теперь введите {in_text}",
                                 keyboard=kbd)
        if next_state == jog_info.end:
            await end()
    except ValueError:
        await message.answer("Введите по образцу, пожалуйста")


async def end():
    if ctx.get("average_pace") is None:
        minute = ctx.get("time_jog").second / 60 + ctx.get("time_jog").minute + ctx.get("time_jog").hour * 60
        pace = minute / ctx.get("distance")
        pace_minute = pace // 1
        pace_second = (pace % 1) * 60
        ctx.set("average_pace", time(hour=0, minute=int(pace_minute), second=int(pace_second)))
    data = [ctx.get("user_id"), ctx.get("jog_id"), ctx.get("start_time"), ctx.get("finish_time"),
            ctx.get("name_jog"), ctx.get("caption_jog"), ctx.get("distance"), ctx.get("time_jog"),
            ctx.get("calories"), ctx.get("average_heart_rate"), ctx.get("max_heart_rate"),
            ctx.get("average_pace"), ctx.get("max_pace"), ctx.get("min_height"), ctx.get("max_height"),
            ctx.get("shoes"), ctx.get("temperature"), ctx.get("wind_speed")]
    async with Database() as db:
        if ctx_self_choice.get("start_fill_later"):
            print("here")
            await db.update_data_to_jogging(data + [ctx.get("user_id"), ctx.get("start_time")])
        else:
            await db.insert_data_to_jogging(data)
            await db.update_long_ago(ctx.get("user_id"), 0)


@bot.on.message(text=["Заполнить информацию о пробежке"])
async def fill_info(message: Message):
    await message.answer("Информацию о какой пробежке будем заполнять?",
                         keyboard=kb.date_jog_choice())

@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"date": "last"})
)
async def last_jog(event: MessageEvent):
    async with (Database() as db):
        (user_id, jog_id, start_time, finish_time, name_jog, caption_jog,
         distance, time_jog, calories, average_heart_rate, max_heart_rate, average_pace, max_pace,
         min_height, max_height, shoes, temperature, wind_speed) = await db.take_last_jog_data(event.peer_id)
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        random_id=0,
        message=f"Хорошо, сейчас мы заполним информацию о твоей последней тренировке"
                f", которая состоялась: {start_time.date()}\n Напиши название этой тренировки.",
        keyboard=kb.jog_skip_something("skip_name")
    )
    await bot.state_dispenser.set(event.peer_id, jog_info.name_jog)
    ctx_self_choice.set("start_fill_later", True)
    ctx.set("user_id", user_id); ctx.set("jog_id", jog_id); ctx.set("start_time", start_time)
    ctx.set("finish_time", finish_time); ctx.set("name_jog", name_jog); ctx.set("caption_jog", caption_jog)
    ctx.set("distance", distance); ctx.set("time_jog", time_jog); ctx.set("calories", calories)
    ctx.set("average_heart_rate", average_heart_rate); ctx.set("max_heart_rate", max_heart_rate)
    ctx.set("average_pace", average_pace); ctx.set("max_pace", max_pace); ctx.set("min_height", min_height)
    ctx.set("max_height", max_height); ctx.set("shoes", shoes); ctx.set("temperature", temperature)
    ctx.set("wind_speed", wind_speed)

@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"date": "self"})
)
async def choice_data(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        random_id=0,
        message="Так так, тогда напиши дату в следующем сообщении в формате ГГГГ-ММ-ДД",
        keyboard=EMPTY_KEYBOARD
    )
    await bot.state_dispenser.set(event.peer_id, self_choice.choice_data)
    ctx_self_choice.set("self_choice", True)
    ctx_self_choice.set("start_fill_later", True)

@bot.on.message(state=self_choice.choice_data)
async def choice_data(message: Message):
    try:
        async with Database() as db:
            jogs = await db.take_several_jog_by_data(message.from_id,
                                               datetime.strptime(message.text, "%Y-%m-%d"))
            await message.answer("Какую именно пробежку?", keyboard=kb.time_jog_choice(jogs))
    except ValueError:
        await message.answer("Введите дату в обещанном формате, пожалуйста")


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadContainsRule({"time": "choice"})
)
async def jog_choice_full(event: MessageEvent):
    jog = event.object.payload["jog_time"]
    jog = datetime.fromisoformat(jog)
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        random_id=0,
        message="Хорошо, теперь дай название этой тренировке",
        keyboard=kb.jog_skip_something("skip_name")
    )
    await bot.state_dispenser.set(event.peer_id, jog_info.name_jog)
    async with Database() as db:
        (user_id, jog_id, start_time, finish_time, name_jog, caption_jog,
         distance, time_jog, calories, average_heart_rate, max_heart_rate, average_pace, max_pace,
         min_height, max_height, shoes, temperature, wind_speed) = await db.take_by_datetime_jog(event.peer_id, jog)

    ctx.set("user_id", user_id); ctx.set("jog_id", jog_id); ctx.set("start_time", start_time)
    ctx.set("finish_time", finish_time); ctx.set("name_jog", name_jog); ctx.set("caption_jog", caption_jog)
    ctx.set("distance", distance); ctx.set("time_jog", time_jog); ctx.set("calories", calories)
    ctx.set("average_heart_rate", average_heart_rate); ctx.set("max_heart_rate", max_heart_rate)
    ctx.set("average_pace", average_pace); ctx.set("max_pace", max_pace); ctx.set("min_height", min_height)
    ctx.set("max_height", max_height); ctx.set("shoes", shoes); ctx.set("temperature", temperature)
    ctx.set("wind_speed", wind_speed)

@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"time": "non"})
)
async def non_jog_choice(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        random_id=0,
        message="Хорошо, ошибся, с кем не бывает, введи дату еще раз!",
        keyboard=kb.date_jog_choice()
    )
