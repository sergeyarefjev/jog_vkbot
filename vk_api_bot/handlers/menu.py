import io

from vkbottle import GroupEventType, CtxStorage, PhotoMessageUploader
from vkbottle.bot import Message, Blueprint, rules, MessageEvent
from database.db import Database
from vkbottle.tools import EMPTY_KEYBOARD
from vkbottle.dispatch.dispenser import BaseStateGroup
import keyboards.all_keyboards as kb
from datetime import datetime, timedelta, time, date
from create_bot import bot

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
from math import floor, ceil


menu_router = Blueprint("menu_router")
menu_router.labeler.vbml_ignore_case = True

ctx = CtxStorage()
ctx_summary = CtxStorage()

class goal_distance(BaseStateGroup):
    count_running = -1
    distance = -2
    all_time = -3
    all_height = -4
    start_time = 1
    finish_time = 2

class summary_date(BaseStateGroup):
    start_date = 0
    finish_date = 1

one = [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44]
two = [1, 21, 31, 41]
async def control_hour(hour):
    if hour == 1:
        return "час"
    elif hour in [2, 3, 4]:
        return "часа"
    else:
        return "часов"
async def control_minute(minute):
    if minute in one:
        return "минуты"
    elif minute in two:
        return "минуту"
    else:
        return "минут"
async def control_second(second):
    if second in one:
        return "секунды"
    elif second in two:
        return "секунду"
    else:
        return "секунд"
async def pace_to_speed(pace):
    seconds_on_km = int(pace.second) + int(pace.minute) * 60
    km_on_hour = 1 / seconds_on_km * 3600
    return km_on_hour
async def real_to_y_day(real):
    years = real // 1
    days = round((real - years) * 365.25)
    return (years, days)

async def check_bmi(bmi):
    if bmi <= 16:
        return "Выраженный дефицит массы тела"
    elif 16 < bmi <= 18.5:
        return "Недостаточная масса тела"
    elif 18.5 < bmi <= 25:
        return "Норма"
    elif 25 < bmi <= 30:
        return "Избыточная масса тела (предожирение)"
    elif 30 < bmi <= 35:
        return "Ожирение первой степени"
    elif 35 < bmi <= 40:
        return "Ожирение второй степени"
    elif bmi > 40:
        return "Ожирение третей степени"


@menu_router.on.message(text=["BMI"])
async def bmi_message(message: Message):
    async with Database() as db:
        weight = await db.take_weight(message.from_id)
        height = await db.take_height(message.from_id)

    bmi = weight / (height / 100)**2
    await message.answer(f"Ваш индекс массы тела: {bmi:.2f}")
    await message.answer(f"Ваше состояние: {await check_bmi(bmi)}")

@menu_router.on.message(text=["Личные данные"])
async def personal_data(message: Message):
    async with Database() as db:
        data = await db.take_user_info(message.from_id)
        user_info = (await message.ctx_api.users.get(user_ids=f"{message.from_id}"))[0]
        text = f"Вот ваши личные данные, {user_info.first_name} {user_info.last_name}:\n"
        text += f"Ваш вес: {data[2]}\n"
        text += f"Ваш рост: {data[3]}\n"
        text += f"Бегом вы занимаетесь около: {data[5]} лет\n"
        rows = await db.shoe_distance(message.from_id)
        text += f"Ваши самые долгоживущие кроссовки: {rows[0][0]}, их пробег уже: {rows[0][1]} км\n"


        await message.answer(text)


@menu_router.on.message(text=["Обувь"])
async def shoes_data(message: Message):
    async with Database() as db:
        data = await db.take_user_info(message.from_id)
        text = "Ответ по вашей обуви:\n"
        shoes = data[6]
        rows_group = await db.shoe_distance(message.from_id)
        for row in rows_group:
            if row[0] in shoes:
                text += f"У кроссовок {row[0]} уже пробег {row[1]} км\n"
        text += "В среднем рекоммендуется менять кроссовки каждые 700-1000 км"
        await message.answer(text)


@menu_router.on.message(text=["Достижения"])
async def achivments_data(message: Message):
    async with Database() as db:
        data = await db.take_user_info(message.from_id)
        user_info = (await message.ctx_api.users.get(user_ids=f"{message.from_id}"))[0]
        text = f"{user_info.first_name}, вот ваши достижения:\n"
        count_jog = await db.count_jog(message.from_id)
        text += f"Общее количество ваших пробежек {count_jog}\n"
        max_distance = await db.max_distance(message.from_id)
        text += (f"Ваша самая длинная пробежка состоялась"
                 f" {max_distance[0].date()} и целых {max_distance[1]} км\n")
        max_time = await db.max_time(message.from_id)
        hour = max_time[1].hour
        minute = max_time[1].minute
        second = max_time[1].second
        if hour == 0:
            text += (f"Ваша самая длительная пробежка состоялась {minute} "
                     f"{(await control_minute(minute))} "
                     f"и {second} {(await control_second(second))}"
                     f" (хороший результат) и прошла она {max_time[0].date()}\n")
        else:
            text += (f"Ваша самая длительная пробежка состоялась {hour} "
                     f"{(await control_hour(hour))}, {minute} {(await control_minute(minute))},"
                     f"{second} {(await control_second(second))} и прошла она {max_time[0].date()}\n")
        min_pace = await db.min_pace(message.from_id)
        text += (f"Самый лучший ваш зафиксированный темп: {min_pace.minute}:{min_pace.second}, то есть аж "
                 f"{(await pace_to_speed(min_pace)):.1f} км/ч, это очень круто!\n")
        text += (f"Самая большая разница высот, преодоленная во время пробежки:"
                 f" {(await db.max_diff_height(message.from_id))} м\n")
        text += (f"Ваш средний темп за все время:"
                 f" {str((await db.average_pace(message.from_id))).split('.')[0][3:]}\n")
        text += (f"За все время вы преодолели: {await db.all_distance(message.from_id):.2f} км, "
                 f"впечатляющий результат!\n")
        text += (f"Вы добились всех этих достижений за: {(await real_to_y_day(data[5]))[0]} year и "
                 f"{(await real_to_y_day(data[5]))[1]} day")
        await message.answer(text)


#"Хочу поставить новую цель"
@menu_router.on.message(text=["Цели"])
async def goals_message(message: Message):
    await message.answer("Отлично, вы хотите поставить новую цель, или посмотреть на успехи в текущих,"
                         " а может быть вас интересуют ваши уже выполненные цели?",
                         keyboard=kb.goal_kb())

@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"goal": "new_goal"})
)
async def create_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Отлично, выбери тип цели, которую хочешь поставить",
        random_id=0,
        keyboard=kb.goal_choose()
    )


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"goal": "count_jog_goal"})
)
async def count_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Отлично, тогда нужно выбрать количество пробежек и время на выполнение цели."
                "Начнем с количества. Сколько пробежек ты хочешь провести?",
        random_id=0
    )
    ctx.set("user_id", event.peer_id)
    await bot.state_dispenser.set(event.peer_id, goal_distance.count_running)

@menu_router.on.message(state=goal_distance.count_running)
async def count_running_goal(message: Message):
    try:
        ctx.set("count_running", int(message.text))
        await bot.state_dispenser.set(message.from_id, goal_distance.start_time)
        await message.answer("Отлично, теперь напиши, когда ты планируешь начать покарять свою цель.",
                             keyboard=kb.goal_start_time())
    except ValueError:
        await message.answer("Введите количество пробежек в виде натурального числа, пожалуйста")


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"goal": "distance_jog_goal"})
)
async def distance_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Супер, тогда нужно определиться с дистанцией, которую ты хочешь преодолеть, и со временем,"
             " которое ты планируешь на это потратить. Сколько километор ты планируешь пробежать?",
        random_id=0
    )
    ctx.set("user_id", event.peer_id)
    await bot.state_dispenser.set(event.peer_id, goal_distance.distance)

@menu_router.on.message(state=goal_distance.distance)
async def distance_goal(message: Message):
    try:
        if message.text.find(','):
            f = float(message.text.replace(',', '.'))
        else:
            f = float(message.text)
        ctx.set("distance", f)
        await bot.state_dispenser.set(message.from_id, goal_distance.start_time)
        await message.answer("Отлично, теперь напиши, когда ты планируешь начать покарять свою цель.",
                             keyboard=kb.goal_start_time())
    except ValueError:
        await message.answer("Введите дистанцию в виде вещественного числа, пожалуйста")


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"goal": "time_jog_goal"})
)
async def time_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Так так, прекрасно, тогда напиши, сколько времени ты хочешь суммарно провести "
                "на пробежках (например 15 часов 30 минут или в формате 'Ч:М:С')",
        random_id=0
    )
    ctx.set("user_id", event.peer_id)
    await bot.state_dispenser.set(event.peer_id, goal_distance.all_time)


@menu_router.on.message(state=goal_distance.all_time)
async def time_goal(message: Message):
    try:
        if message.text.find(":") == -1:
            hour_idx = message.text.find(" час")
            hour = message.text[:hour_idx].split(" ")[-1]
            minute_idx = message.text.find(" мин")
            minute = message.text[:minute_idx].split(" ")[-1]
            second_idx = message.text.find(" сек")
            second = message.text[:second_idx].split(" ")[-1]
            if hour_idx == -1:
                hour = 0
            if minute_idx == -1:
                minute = 0
            if second_idx == -1:
                second = 0
        else:
            hour = message.text[:message.text.rfind(":")]
            minute = message.text[message.text.rfind(":"):message.text.lfind(":")]
            second = message.text[message.text.lfind(":"):]
        hour, minute, second = int(hour), int(minute), int(second)
        second = second + minute * 60 + hour * 3600
        ctx.set("all_time", second)
        await message.answer("Отлично, теперь определимся с началом цели", keyboard=kb.goal_start_time())
        await bot.state_dispenser.set(message.from_id, goal_distance.start_time)
    except ValueError:
        await message.answer("Пожалуйста, введи более аккуратно время")


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"goal": "height_jog_goal"})
)
async def height_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Прекрасно, теперь скажи какую разность высот ты хочешь преодолеть в метрах?",
        random_id=0
    )
    ctx.set("user_id", event.peer_id)
    await bot.state_dispenser.set(event.peer_id, goal_distance.all_height)

@menu_router.on.message(state=goal_distance.all_height)
async def distance_goal(message: Message):
    try:
        if message.text.find(','):
            f = float(message.text.replace(',', '.'))
        else:
            f = float(message.text)
        ctx.set("all_height", f)
        await bot.state_dispenser.set(message.from_id, goal_distance.start_time)
        await message.answer("Отлично, теперь напиши, когда ты планируешь начать покарять свою цель.",
                             keyboard=kb.goal_start_time())
    except ValueError:
        await message.answer("Введите высоту в виде вещественного числа, пожалуйста")

@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    (rules.PayloadRule({"goal_start": "now"}) |
            rules.PayloadRule({"goal_start": "next_week"})|
            rules.PayloadRule({"goal_start": "next_month"}))
)
async def time_start_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Хорошо, теперь давай определимся сколько времени тебе понадобится на эту цель",
        keyboard=kb.goal_finish_time(),
        random_id=0
    )
    if event.object.payload.get("goal_start") == "now":
        ctx.set("start_time", datetime.now())
    elif event.object.payload.get("goal_start") == "next_week":
        today = datetime.now()
        days_before_monday = (7 - today.weekday()) % 7
        next_monday = today + timedelta(days=days_before_monday)
        ctx.set("start_time", next_monday.replace(hour=0, minute=0, second=0))
    else:
        today = datetime.now()
        ctx.set("start_time", today.replace(month=today.month + 1))
    await bot.state_dispenser.set(event.peer_id, goal_distance.finish_time)


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"goal_start": "self"})
)
async def time_start_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Хорошо, жду вашего сообщения!",
        random_id=0
    )
    await bot.state_dispenser.set(event.peer_id, goal_distance.start_time)


@menu_router.on.message(state=goal_distance.start_time)
async def time_start_goal(message: Message):
    try:
        ctx.set("start_time", datetime.strptime(message.text, "%Y-%m-%d").date())
        await bot.state_dispenser.set(message.from_id, goal_distance.finish_time)
        await message.answer("Супер, перейдем к выбору продолжительности цели!",
                             keyboard=kb.goal_finish_time())
    except ValueError:
        await message.answer("Введи дату в обещанном формате, пожалуйста")


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    (rules.PayloadRule({"goal_finish": "week"}) |
            rules.PayloadRule({"goal_finish": "month"}) |
            rules.PayloadRule({"goal_finish": "year"}) |
            rules.PayloadRule({"goal_finish": "inf"}))
)
async def time_finish_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message=("Отлично, цель поставлена! Буду отслеживать ваш прогресс, если вам станет интересно,"
                                 'то о своих успехах можете посмотреть их в разделе "Цели"'),
        random_id=0
    )
    if event.object.payload.get("goal_finish") == "week":
        ctx.set("finish_time", ctx.get("start_time") + timedelta(days=7))
    elif event.object.payload.get("goal_finish") == "month":
        from calendar import monthrange
        year = datetime.now().year
        month = datetime.now().month
        ctx.set("finish_time",
                ctx.get("start_time") + timedelta(days=monthrange(year, month)[1]))
    elif event.object.payload.get("goal_finish") == "year":
        year = datetime.now().year
        ctx.set("finish_time", ctx.get("start_time") +
                timedelta(days=(date(year, 12, 31) - date(year, 1, 1)).days + 1))
    else:
        ctx.set("finish_time", datetime.now() + timedelta(days=365 * 150))
    await processing_distance_goal(event.peer_id)


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"goal_finish": "self"})
)
async def time_finish_goal(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Так точно, жду вашего сообщения!",
        random_id=0
    )


@menu_router.on.message(state=goal_distance.finish_time)
async def time_finish_goal(message: Message):
    try:
        if datetime.strptime(message.text, "%Y-%m-%d").date() > ctx.get("start_time").date():
            ctx.set("finish_time", datetime.strptime(message.text, "%Y-%m-%d").date())
            await processing_distance_goal(message.from_id)
            await message.answer("Отлично, цель поставлена! Буду отслеживать ваш прогресс, если вам станет интересно,"
                                 'то о своих успехах можете посмотреть их в разделе "Цели"')
        else:
            raise ValueError
    except ValueError:
        await message.answer("Введи дату по-нормальному, пожалуйста")

async def keys_ctx_goal():
    keys = []
    for key in ["user_id", "start_time", "finish_time", "count_running", "distance", "all_time", "all_height"]:
        if ctx.get(key) is not None:
            keys.append(key)
    return keys
async def processing_distance_goal(user_id):
    async with Database() as db:
        data = (ctx.get("user_id"), ctx.get("start_time"), ctx.get("finish_time"), ctx.get("count_running"),
                ctx.get("distance"), ctx.get("all_time"), ctx.get("all_height"))
        await db.insert_goal(data)
    await bot.state_dispenser.delete(user_id)
    for key in (await keys_ctx_goal()):
        ctx.delete(key)


#"Хочу посмотреть свои результаты"
@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"goal": "check_goal"})
)
async def check_goal(event: MessageEvent):
    async with Database() as db:
        await db.initialize_active_goal(event.peer_id, datetime.now())
        active_goals = await db.get_active_goals(event.peer_id)
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Так так, посмотрим, что у нас с целями, ах вот же, на данный момент поставлены следующие цели:",
        random_id=0,
        keyboard=kb.active_goals(active_goals)
    )

async def create_figure(event: MessageEvent, type_goal, goal):
    async with Database() as db:
        if type_goal == "count_jog":
            time_jog_cumulative_sum = np.array(await db.take_cumulative_sum_count_jog(event.peer_id, goal[1], goal[2]))
        elif type_goal == "time":
            time_jog_cumulative_sum = np.array(await db.take_cumulative_sum_time_distance_diffgain(
                                    event.peer_id, goal[1], goal[2], "time"))
            df = pd.DataFrame({'a' : time_jog_cumulative_sum[:, 1]})
            time_jog_cumulative_sum[:, 1] = df['a'].dt.seconds + df['a'].dt.days * 3600 * 24
        elif type_goal == "distance":
            time_jog_cumulative_sum = np.array(await db.take_cumulative_sum_time_distance_diffgain(
                                    event.peer_id, goal[1], goal[2], "distance"))
        else:
            time_jog_cumulative_sum = np.array(await db.take_cumulative_sum_time_distance_diffgain(
                                    event.peer_id, goal[1], goal[2], "diff_gain"))

        help = await db.max_start_to_finish(event.peer_id, goal[1], goal[2])
        if help is not None:
            max_avg_pace, max_max_pace, max_distance, max_time, max_diff_gain = help
        else:
            max_avg_pace, max_max_pace, max_distance, max_time, max_diff_gain = None, None, None, None, None
    if len(time_jog_cumulative_sum) > 0:
        time_jog, cumulative_sum = time_jog_cumulative_sum[:, 0], time_jog_cumulative_sum[:, 1]
        fig = plt.figure(figsize=(12, 8))
        gs = plt.GridSpec(2, 2, figure=fig)
        ax_1 = fig.add_subplot(gs[0, :])
        ax_2 = fig.add_subplot(gs[1, 1])
        ax_3 = fig.add_subplot(gs[1, 0])

        ax_1.step(time_jog, cumulative_sum, where="post")
        ax_1.scatter(time_jog, cumulative_sum, s=5)
        ax_1.set_title("Прогресс в достижении цели")
        if type_goal == "count_jog":
            ax_1.plot(time_jog, [goal[3] for _ in range(len(time_jog))], '--', color='red')
            ax_1.set_ylabel("Количество пробежек")
            percent_complite = cumulative_sum[-1] / goal[3] * 100
        elif type_goal == "distance":
            ax_1.plot(time_jog, [goal[4] for _ in range(len(time_jog))], '--', color='red')
            ax_1.set_ylabel("Дистанция пробежек")
            percent_complite = cumulative_sum[-1] / goal[4] * 100
        elif type_goal == "time":
            ax_1.plot(time_jog, [goal[5] for _ in range(len(time_jog))], '--', color='red')
            ax_1.set_ylabel("Общее время пробежек")
            step = goal[5] / 5
            ax_1.set_yticks([step * i for i in range(6)])
            percent_complite = cumulative_sum[-1] / goal[5] * 100
        else:
            ax_1.plot(time_jog, [goal[6] for _ in range(len(time_jog))], '--', color='red')
            ax_1.set_ylabel("Разность высот")
            percent_complite = cumulative_sum[-1] / goal[6] * 100

        color_red = plt.cm.Reds(0.5)
        color_green = plt.cm.Greens(0.7)
        ax_2.pie([percent_complite, 100 - percent_complite],
                labels=["Пройдено", "Осталось"],
                startangle=90,
                counterclock=False,
                autopct='%1.1f%%',
                colors=[color_green, color_red])
        ax_2.set_title("Диаграмма вашего прогресса")

        ax_3.axis('off')
        ax_3.text(0, 1, f"Самый большой темп за время достижения цели: {max_max_pace}")
        ax_3.text(0, 0.9, f"Самый высокий средний темп за пробежку: {max_avg_pace}")
        ax_3.text(0, 0.8, f"Самая длинная пробежка: {max_distance} км")
        ax_3.text(0, 0.7, f"Самая длительная пробежка: {max_time}")
        ax_3.text(0, 0.6, f"Самый высокий преодаленный перепад высот: {max_diff_gain} м")
        ax_3.text(0, 0.5, f"Дата постановки цели: {goal[1].strftime('%Y:%m:%d')}")
        if goal[2].replace(tzinfo=None) < datetime(year=2125, month=1, day=1, hour=1, minute=1, second=1):
            ax_3.text(0, 0.4, f"Дата окончания цели: {goal[2].strftime('%Y:%m:%d')}")
            ax_3.text(0, 0.3, f"Осталось дней для выполнения цели: {(goal[2] - goal[1]).days}")
        else:
            ax_3.text(0, 0.4, f"Это бессрочная цель, поэтому у вас еще много времени")

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        photo_uploader = PhotoMessageUploader(bot.api)
        photo = await photo_uploader.upload(
            file_source=buf,
            peer_id=event.peer_id
        )
        return photo
    else:
        return False

@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadContainsRule({"goal": "diff_gain"}) |
    rules.PayloadContainsRule({"goal": "time"}) |
    rules.PayloadContainsRule({"goal": "distance"}) |
    rules.PayloadContainsRule({"goal": "count_jog"})
)
async def goals(event: MessageEvent):
    type_goal = event.object.payload["goal"]
    start_goal = event.object.payload["start_time"] #Этого хватит, так как в базе хранится datetime, а не date
    async with Database() as db:
        goal = await db.get_goal_by_start_time(event.peer_id, start_goal)
    photo = await create_figure(event, type_goal, goal)

    if not isinstance(photo, bool):
        await event.ctx_api.messages.send(
            peer_id=event.peer_id,
            random_id=0,
            attachment=photo,
            message="Вот на каком этапе ваша цель"
        )
    else:
        await event.ctx_api.messages.send(
            peer_id=event.peer_id,
            random_id=0,
            message="Не удалось подвести итоги этой цели, возможно вы еще"
                    " не провели ни одну пробежку, с момента постановки цели"
        )


@bot.on.message(text=["Последняя сводка"])
async def last_jog_summary(message: Message):
    text = ""
    async with Database() as db:
        jog = await db.take_last_jog_data(message.from_id)
    text += jog[4]
    text += "\n" + jog[5]
    text += f"\nТренировка началась — {jog[2].strftime(format='%Y-%m-%d %H:%M')}"

    text += f"\nПреодоленное расстояние: {jog[6]} км и длилась она: "
    if jog[7].hour != 0:
        text +=  f"{jog[7].hour} {await control_hour(jog[7].hour)} "
    if jog[7].minute != 0:
        text += f"{jog[7].minute} {await control_minute(jog[7].minute)}"
    if jog[7].second != 0:
        text += f" {jog[7].second} {await control_second(jog[7].second)}"

    text += f"\nА средний темп составил: {jog[11].strftime(format='%M:%S')}"
    if jog[12] != time(hour=0, minute=0, second=0) and jog[12] is not None:
        text += f"\nМаксимальный темп во время пробежки: {jog[12].strftime(format='%M:%S')}"
    if jog[14] - jog[13] != 0 and jog[14] is not None and jog[13] is not None:
        text += f"\nСуммарный подьем: {np.abs(jog[14] - jog[13])}"
    if jog[15] != 'Не выбран' and jog[15] is not None:
        text += f"\nВы бегали в кроссовках: {jog[15]}"
    if jog[16] != 0 and jog[16] is not None:
        text += f"\nПробежка проводилась при температуре {jog[16]}C°"
    if jog[17] != 0 and jog[17] is not None:
        text += f"\nСкорость ветра во время пробежки: {jog[17]} м/с"
    if jog[8] != 0 and jog[8] is not None:
        text += f"\nКоличество сожженных каллорий: {jog[8]}"
    if jog[9] != 0 and jog[9] is not None:
        text += f"\nСредняя частота сердцебиений: {jog[9]}"
    if jog[10] != 0 and jog[10] is None:
        text += f"\nМаксимальная частота сердцебиений: {jog[10]}"

    async with Database() as db:
        text += (f"\nЭта пробежка была длиннее, чем "
                 f"{await db.take_percent_worse_jog(message.from_id, jog[6], 'distance')}% тренировок")
        text += (f"\nТемп на этой пробежке был лучше чем на: "
                 f"{await db.take_percent_worse_jog(message.from_id, jog[11], 'average_pace')}%")
        text += f"\nЭто была пробежка уже под номером: {await db.count_jog(message.from_id)}."
        text += "\nВы большой молодец, продолжай в том же духе!!!"
    await message.answer(text)


@bot.on.message(text=["Отчет"])
async def summary(message: Message):
    await message.answer("Введите дату, начиная с которой вы хотите посмотреть отчет (в формате YYYY-MM-DD)")
    await bot.state_dispenser.set(message.from_id, summary_date.start_date)

@bot.on.message(state=summary_date.start_date)
async def start_date_summary(message: Message):
    try:
        await message.answer("Хорошо, теперь введите дату, до которой вы хотите посмотреть отчет, в том же формате")
        ctx_summary.set("start_date", datetime.strptime(message.text, '%Y-%m-%d'))
        await bot.state_dispenser.set(message.from_id, summary_date.finish_date)

    except ValueError:
        await message.answer("Введите дату еще раз в требуемом формате, скорее всего вы допустили ошибку")

async def start_time_distance_time_pace_diffgain_split(start_distance_time_pace_diffgain):
    start_time, distance, time_jog, pace, diff_gain = [], [], [], [], []
    for row in start_distance_time_pace_diffgain:
        start_time.append(row[0])
        distance.append(row[1])
        if row[2] is not None:
            time_jog.append(row[2].minute + row[2].second / 60 + row[2].hour * 60)
        else:
            time_jog.append(None)
        if row[3] is not None:
            pace.append(row[3].minute + row[3].second / 60)
        else:
            pace.append(None)
        diff_gain.append(row[4])
    return start_time, np.array(distance), np.array(time_jog), np.array(pace), np.array(diff_gain)

async def create_figure_summary(start_distance_time_pace, user_id):
    start_time, distance, time_jog, pace, _ = await start_time_distance_time_pace_diffgain_split(start_distance_time_pace)


    fig, ax = plt.subplots(nrows=3, ncols=1)
    #plt.figure(figsize=(12, 9))

    ax[0].plot(start_time, distance, marker='.')
    ax[0].set_ylabel("Дистанция\n в км")
    not_none_distance = [d for d in distance if d is not None]
    mean_distance = np.mean(not_none_distance)
    ax[0].plot(start_time, [mean_distance for _ in range(len(start_time))], '--', color="red", label=["Среднее"])
    ax[0].legend()
    step = (ceil(max(not_none_distance)) - floor(min(not_none_distance))) / 3
    ax[0].set_yticks([round(floor(min(not_none_distance)) + step * i, 1) for i in range(4)])
    ax[0].xaxis.set_major_locator(MaxNLocator(4))

    ax[1].plot(start_time, time_jog, marker='+')
    ax[1].set_ylabel("Время пробежки\n в минутах")
    not_none_time = [t for t in time_jog if t is not None]
    mean_time_jog = np.mean(not_none_time)
    ax[1].plot(start_time, [mean_time_jog for _ in range(len(start_time))], '--', color='green', label=["Среднее"])
    ax[1].legend()
    step = (ceil(max(not_none_time)) - floor(min(not_none_time))) / 3
    ax[1].set_yticks([round(floor(min(not_none_time)) + step * i, 1) for i in range(4)])
    ax[1].xaxis.set_major_locator(MaxNLocator(4))


    ax[2].plot(start_time, pace, marker='*')
    ax[2].set_ylabel("Средний темп\n за пробежку")
    not_none_pace = [p for p in pace if p is not None]
    mean_pace = np.mean(not_none_pace)
    ax[2].plot(start_time, [mean_pace for _ in range(len(start_time))], '--', color='purple', label=["Среднее"])
    ax[2].legend()
    step = (ceil(max(not_none_pace)) - floor(min(not_none_pace))) / 3
    #ax[2].set_yticks([round(ceil(min(not_none_pace) + step * i), 1) for i in range(4)])
    ax[2].yaxis.set_major_locator(MaxNLocator(4))
    ax[2].xaxis.set_major_locator(MaxNLocator(4))


    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    photo_uploader = PhotoMessageUploader(bot.api)
    photo = await photo_uploader.upload(
        file_source=buf,
        peer_id=user_id
    )
    return photo

async def help_by_finish_date_summary(user_id, message=None, start_date=None, finish_date=None):
    """
    Обязательно либо message, либо start_date и finish_date
    """
    try:
        if start_date is None and finish_date is None:
            start_date = ctx_summary.get("start_date")
            finish_date = datetime.strptime(message.text, "%Y-%m-%d")
            ctx_summary.set("finish_date", finish_date)

        text = ""
        async with Database() as db:
            print(start_date, finish_date)
            max_avg_pace, max_max_pace, max_distance, max_time, max_diff_gain = await db.max_start_to_finish(
                                                                user_id, start_date, finish_date)
            start_distance_time_pace = await db.distance_time_pace_diffgain_from_start_to_finish(user_id,
                                                                                  start_date, finish_date)

        if len(start_distance_time_pace) > 0:
            photo = await create_figure_summary(start_distance_time_pace, user_id)

            if max_avg_pace is not None:
                text += f"В этот период ваш максимальный средний темп за все пробежки был: {max_avg_pace.strftime('%M:%S')}\n"
            if max_max_pace is not None:
                text += f"А максимальный темп из всех пробежек: {max_max_pace.strftime('%M:%S')}\n"
            if max_distance is not None:
                text += f"Самая длинная пробежка составила: {max_distance} км\n"
            if max_time is not None:
                text += "А самая долгая пробежка была: "
                if max_time.hour != 0:
                    text += f"{max_time.hour} {await control_hour(max_time.hour)} "
                if max_time.minute != 0:
                    text += f"{max_time.minute} {await control_minute(max_time.minute)} "
                if max_time.second != 0:
                    text += f"{max_time.second} {await control_second(max_time.second)} "
                text += "\n"
            if max_diff_gain is not None:
                text += f"И максимальная разница высот за пробежку: {max_diff_gain} м"
            await bot.api.messages.send(
                peer_id=user_id,
                attachment=photo,
                random_id=0
            )
            if message is not None:
                await bot.api.messages.send(
                    peer_id=user_id,
                    message=text + "\nМожет быть вам интересно посмотреть что-то поподробнее?",
                    keyboard=kb.progress_keyboard(),
                    random_id=0)
        else:
            await bot.api.messags.send(
                peer_id=user_id,
                message="В указаном диапазоне нет ни одной пробежки",
                random_id=0
            )
        return text
    except Exception:
        await bot.api.messages.send(
            peer_id=user_id,
            message="Извините, произошла ошибка",
            keyboard=kb.menu_kb(),
            random_id=0)

@bot.on.message(state=summary_date.finish_date)
async def finish_date_summary(message: Message):
    await help_by_finish_date_summary(message.from_id, message=message)


async def take_a_b_max_min(arr_1, arr_2, length):
    """
    arr_1 -- x
    arr_2 -- y
    length -- length arr_with_none
    """
    arr_1_without_none = []
    arr_2_without_none = []
    for i in range(length):
        if arr_1[i] is not None and arr_2[i] is not None:
            arr_1_without_none.append(arr_1[i])
            arr_2_without_none.append(arr_2[i])
    arr_1_without_none = np.array(arr_1_without_none)
    a, b = np.polyfit(arr_1_without_none, arr_2_without_none, deg=1)
    min_arr_1 = np.min(arr_1_without_none)
    max_arr_1 = np.max(arr_1_without_none)
    return a, b, max_arr_1, min_arr_1


async def progress_pace_figure(start_distance_time_pace, user_id):
    start_time, distance, time_jog, pace, _ = await start_time_distance_time_pace_diffgain_split(start_distance_time_pace)

    if len(pace) >= 20:
        fig, ax = plt.subplots(ncols=1, nrows=3, figsize=(16, 16))
    else:
        fig, ax = plt.subplots(ncols=1, nrows=2, figsize=(16, 16))

    ax[0].scatter(distance, pace, s=40)
    ax[0].set_title("Зависимость темпа от дистанции пробежки")
    ax[0].set_ylabel("Темп")
    ax[0].set_xlabel("Дистанция, км")
    a_dis, b_dis, max_dis, min_dis = await take_a_b_max_min(distance, pace, len(pace))
    ax[0].plot([min_dis, max_dis],
               [a_dis * min_dis, a_dis * max_dis] + b_dis, '--', label=["Тренд"], color="red", dashes=[2,2])
    ax[0].legend()

    ax[1].scatter(time_jog, pace, s=40)
    ax[1].set_title("Зависимость темпа от времени пробежки")
    ax[1].set_ylabel("Темп")
    ax[1].set_xlabel("Время, мин")
    a_time, b_time, max_time, min_time = await take_a_b_max_min(time_jog, pace, len(pace))
    ax[1].plot([min_time, max_time], [a_time * min_time, a_time * max_time] + b_time,
               '--', label=["Тренд"], color="purple")
    ax[1].legend()
    if len(pace) >= 20:
        nbins = len(pace) // 3
        ax[2].set_title("Гистаграмма вашего темпа")
        ax[2].hist([p for p in pace if p is not None], alpha=0.5, color='red', rwidth=0.9, bins=nbins)

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    photo_uploader = PhotoMessageUploader(bot.api)
    photo = await photo_uploader.upload(
        file_source=buf,
        peer_id=user_id
    )
    return photo, a_dis, a_time



@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"progress": "pace"})
)
async def progress_pace(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Отлично, сейчас покажем вашу статистику по темпу поконкретнее!",
        random_id=0
    )
    start_date = ctx_summary.get("start_date")
    finish_date = ctx_summary.get("finish_date")
    #ctx_summary.delete("start_date")
    #ctx_summary.delete("finish_date")
    text = ""
    async with Database() as db:
        start_distance_time_pace = await db.distance_time_pace_diffgain_from_start_to_finish(event.peer_id,
                                                                                    start_date, finish_date)
    photo, a_dis, a_time = await progress_pace_figure(start_distance_time_pace, event.peer_id)
    if round(a_dis, 3) > 0:
        text += (f"Ваш темп имеет положительный тренд относительно дистанции, а именно {a_dis:.3f} мин/км.\n"
                 f"Это говорит о том, что вы начинаете быстрее бегать при определенной дистанции!\n")
    elif round(a_dis, 3) == 0:
        text += "Ваш темп, относительно дальности пробежки, не менялся за это время, ты показываешь уверенную стабильность.\n"
    else:
        text += (f"Тренд вашего темпа отрицательный относительно дистанции ({-a_dis:.3f} мин/км).\n"
                 f"Это говорит о том, что вы либо теряете форму, а значит нужно постараться увеличить тренировки,"
                 f' либо вы просто в этот промежуток больше себя берегли и занимались некой "реабилитацией", что тоже хорошо\n')
    if round(a_time, 3) > 0:
        text += (f"Относительно времени пробежки ваш темп растет, а именно {a_time:.3f} мин/мин.\n"
                 f"Это значит, что вы бегаете быстрее, при том же времени пробежки, это очень круто!")
    elif round(a_time, 3) == 0:
        text += ("Ваш темп, относительно времени пробежки, не менялся за это время, а это значит, что вы обладаете"
                 " высокой стабильностью.\n")
    else:
        text += (f"Ваш темп относительно времени пробежки упал на {-a_time:.3f} мин/мин, это значит, что нужно поднажать"
                 f" немножко (но вам виднее, на самом деле, обязательно думайте о своем здоровье:) )")
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message=text,
        attachment=photo,
        random_id=0
    )
    await bot.state_dispenser.delete(event.peer_id)


async def progress_distance_figure(start_distance_time_pace, user_id):
    start_time, distance, time_jog, pace, diff_gain = await start_time_distance_time_pace_diffgain_split(
        start_distance_time_pace)

    if len(distance) >= 20:
        fig, ax = plt.subplots(ncols=1, nrows=3, figsize=(16, 16))
    else:
        fig, ax = plt.subplots(ncols=1, nrows=2, figsize=(16, 16))

    pace_mean = np.mean([p for p in pace if p is not None])
    ax[0].scatter(time_jog, distance, s=40)
    ax[0].set_ylabel("Дистанция, км")
    ax[0].set_xlabel("Время, мин")
    a_time, b_time, max_time, min_time = await take_a_b_max_min(time_jog, distance, len(distance))
    ax[0].plot([min_time, max_time], [a_time * min_time, a_time * max_time] + b_time, '--', color='purple', label=["Тренд"])
    ax[0].set_title(f"Средний темп: {pace_mean//1}:{pace_mean%1 * 100} мин/км")
    ax[0].legend()

    ax[1].scatter(diff_gain, distance, s=40)
    ax[1].set_ylabel("Дистанция, км")
    ax[1].set_xlabel("Разность высот, м")
    a_diff_gain, b_diff_gain, max_diff_gain, min_diff_gain = await take_a_b_max_min(diff_gain, distance, len(distance))
    ax[1].plot([min_diff_gain, max_diff_gain],
               [a_diff_gain * min_diff_gain, a_diff_gain * max_diff_gain] + b_diff_gain, '--', color='green', label=["Тренд"])
    ax[1].legend()

    if len(distance) >= 20:
        distance_without_none = np.array([d for d in distance if d is not None])
        thresholds = [0, 5, 10, 21.1, 42.2, np.inf]
        labels = ["Короткие", "Средние", "Длинные", "Полумарафон+", "Марафон+"]
        split_distance = []
        for i in range(len(thresholds) - 1):
            split_distance.append(np.sum((thresholds[i] < distance_without_none)
                                         & (distance_without_none <= thresholds[i + 1])))
        labels_true, distance_count_true = [], []
        for label, distance in zip(labels, split_distance):
            if distance > 0:
                labels_true.append(label)
                distance_count_true.append(distance)

        wedges, _, _ = ax[2].pie(distance_count_true,
                                 labels=labels_true,
                                 autopct='%1.1f%%',
                                 center=(1, 0))
        for w in wedges:
            w.set_alpha(0.8)
        legend_labels = []
        if "Короткие" in labels_true: legend_labels.append("Короткие: 0 — 5 км")
        if "Средние" in labels_true: legend_labels.append("Средние: 5 — 10 км")
        if "Длинные" in labels_true: legend_labels.append("Длинные: 10 — 21.1 км")
        if "Полумарафон+" in labels_true: legend_labels.append("Полумарафон+ 21.1 — 42.2 км")
        if "Марафон+" in labels_true: legend_labels.append("Маранфон+ 42.2 км <")
        ax[2].legend(wedges, legend_labels, loc="center right", bbox_to_anchor=(0, 0.5))

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    photo_uploader = PhotoMessageUploader(bot.api)
    photo = await photo_uploader.upload(
        file_source=buf,
        peer_id=user_id
    )
    return photo, a_time, a_diff_gain, pace_mean


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"progress": "distance"})
)
async def progress_distance(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Супер, сейчас соберу статистику по дистанции поподробнее!!!",
        random_id=0
    )
    start_date = ctx_summary.get("start_date")
    finish_date = ctx_summary.get("finish_date")
   # ctx_summary.delete("start_date")
   # ctx_summary.delete("finish_date")
    text = ""
    async with Database() as db:
        start_distance_time_pace = await db.distance_time_pace_diffgain_from_start_to_finish(event.peer_id,
                                                                                    start_date, finish_date)
    photo, a_time, a_diff_gain, pace_mean = await progress_distance_figure(start_distance_time_pace, event.peer_id)
    text += f"Ваш средний темп за это время — {int(pace_mean//1)}:{round(pace_mean%1 * 100)} мин/км\n"
    if round(a_diff_gain, 2) > 0:
        text += (f"Тренд дальности ваших пробежек в зависимости от преодоленной разности высот: {a_diff_gain:.2f}.\n"
                 f"Это значит, что дальность ваших пробежек с большим перепадом высот больше, возможно вам "
                 f"стоит подумать над тем, как прокладывать маршруты, возможно вы часто бегаете на спуск, "
                 f"что облегчает пробежки")
    elif round(a_diff_gain, 2) == 0:
        text += (f"Изменение дистанции от разности высот не значительное, это хороший знак, значит вы легко переносите"
                 f"увеличение или уменьшение высоты.")
    else:
        text += (f"Тренд дальности ваших пробежек относительно преодоленной разности высот отрицательный: {a_diff_gain:.2f}."
                 f"Это нормально, если вы бегаете в горки")

    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message=text,
        attachment=photo,
        random_id=0
    )
    await bot.state_dispenser.delete(event.peer_id)
#Тут копипаст жесткий (говнокод)
async def progress_time_figure(start_distance_time_pace, user_id):
    start_time, distance, time_jog, pace, diff_gain = await start_time_distance_time_pace_diffgain_split(
        start_distance_time_pace)

   # if len(distance) >= 20:
    #    fig, ax = plt.subplots(ncols=1, nrows=3, figsize=(16, 16))

    fig, ax = plt.subplots(ncols=1, nrows=2, figsize=(16, 16))

    pace_mean = np.mean([p for p in pace if p is not None])
    ax[0].scatter(distance, time_jog, s=40)
    ax[0].set_xlabel("Дистанция, км")
    ax[0].set_ylabel("Время, мин")
    a_distance, b_distance, max_distance, min_distance = await take_a_b_max_min(distance, time_jog, len(time_jog))
    ax[0].plot([min_distance, max_distance], [a_distance * min_distance, a_distance * max_distance]
               + b_distance, '--', color='purple', label=["Тренд"])
    ax[0].set_title(f"Средний темп: {int(pace_mean//1)}:{int(pace_mean%1 * 100)} мин/км")
    ax[0].legend()

    ax[1].scatter(diff_gain, time_jog, s=40)
    ax[1].set_ylabel("Время, мин")
    ax[1].set_xlabel("Разность высот, м")
    a_diff_gain, b_diff_gain, max_diff_gain, min_diff_gain = await take_a_b_max_min(diff_gain, time_jog, len(time_jog))
    ax[1].plot([min_diff_gain, max_diff_gain],
               [a_diff_gain * min_diff_gain, a_diff_gain * max_diff_gain] + b_diff_gain, '--', color='green', label=["Тренд"])
    ax[1].legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    photo_uploader = PhotoMessageUploader(bot.api)
    photo = await photo_uploader.upload(
        file_source=buf,
        peer_id=user_id
    )
    return photo, a_distance, a_diff_gain, pace_mean



@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"progress": "time"})
)
async def progress_time(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Супер, сейчас соберу статистику по времени поподробнее!!!",
        random_id=0
    )
    start_date = ctx_summary.get("start_date")
    finish_date = ctx_summary.get("finish_date")
    #ctx_summary.delete("start_date")
    #ctx_summary.delete("finish_date")
    text = ""
    async with Database() as db:
        start_distance_time_pace = await db.distance_time_pace_diffgain_from_start_to_finish(event.peer_id,
                                                                                    start_date, finish_date)
    photo, a_distance, a_diff_gain, pace_mean = await progress_time_figure(start_distance_time_pace, event.peer_id)
    text += f"Ваш средний темп за это время — {int(pace_mean // 1)}:{round(pace_mean % 1 * 100)} мин/км\n"
    if round(a_diff_gain, 2) > 0:
        text += (f"Тренд продолжительности ваших пробежек в зависимости от преодоленной разности высот: {a_diff_gain:.2f}.\n"
                 f"Это значит, что время ваших пробежек с большим перепадом высот больше, возможно вам "
                 f"стоит подумать над тем, как прокладывать маршруты, возможно вы часто бегаете на спуск, "
                 f"что облегчает пробежки")
    elif round(a_diff_gain, 2) == 0:
        text += (f"Изменение времени от разности высот не значительное, это хороший знак, значит вы легко переносите"
                 f"увеличение или уменьшение высоты.")
    else:
        text += (
            f"Тренд времени ваших пробежек относительно преодоленной разности высот отрицательный: {a_diff_gain:.2f}."
            f"Это нормально, если вы бегаете в горки")

    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message=text,
        attachment=photo,
        random_id=0
    )
    await bot.state_dispenser.delete(event.peer_id)


@menu_router.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"progress": "nothing"})
)
async def progress_nothing(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Хорошо, тогда вернемся в меню",
        keyboard=kb.menu_kb(),
        random_id=0
    )
    ctx_summary.delete("start_date")
    ctx_summary.delete("finish_date")
    await bot.state_dispenser.delete(event.peer_id)
