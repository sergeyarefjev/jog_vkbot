from vkbottle import GroupEventType
from vkbottle.bot import Message, MessageEvent, rules
from vkbottle.tools import LoopWrapper, EMPTY_KEYBOARD
from create_bot import bot
from database.db import Database
from datetime import datetime, timezone, timedelta
import keyboards.all_keyboards as kb
from handlers.menu import help_by_finish_date_summary
import random
import numpy as np
from handlers.menu import control_hour, control_minute, control_second


count_jog_in_week_treshold = 2
count_jog_in_month_treshold = 7

@bot.loop_wrapper.interval(seconds=90)
async def test_task():
    print(f"✅ Планировщик работает! {datetime.now()}")
    print(f"UTC now: {datetime.now(timezone.utc)}")



#На 3 часа назад, так как в Москве +3
@bot.loop_wrapper.timer(hours=18, minutes=20)
async def notice_long_ago():
    async with Database() as db:
        users_id, last_jogs, statuses = await db.take_all_user_last_jog_and_status()
        for user_id, last_jog, status in zip(users_id, last_jogs, statuses):
            if 14 > (last_jog - datetime.now()).day > 2 and status > 1:
                await bot.api.messages.send(
                    peer_id=user_id,
                    message="Думаю, что сегодня можно было бы совершить легкую пробежку! Тебе не кажется?",
                    random_id=0,
                    keyboards=kb.jog_notice_kb()
                )
            elif (last_jog - datetime.now()).day >= 14:
                status_new = -1
                await db.update_long_ago(user_id, status_new)
            else:
                if status >= 0:
                    status_new = status + 1
                    await db.update_long_ago(user_id, status_new)


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"notice": "yes"})
)
async def notice_long_age_true(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id = event.peer_id,
        message="Супер, отличный план!",
        random_id=0,
        keyboard=EMPTY_KEYBOARD()
    )


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"notice": "no"})
)
async def notice_long_age_false(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message="Ну ничего, тогда в следующий раз",
        random_id=0,
        keyboard=EMPTY_KEYBOARD()
    )

@bot.loop_wrapper.timer(hours=18, minutes=25)
async def happy_birthday():
    print("here")
    async with Database() as db:
       user_ids, birthdays, date_joins = await db.all_user_id_birthday_datejoin()
    for user_id, bdate, date_join in zip(user_ids, birthdays, date_joins):
        if bdate.day == datetime.now().date().day and bdate.month == datetime.now().date().month:
            days = (datetime.now().date() - date_join).days
            await bot.api.messages.send(
                peer_id=user_id,
                random_id=0,
                message=random.choice(["Уррраааа, ура ура ура!!!!!! Поздравляем тебя с днем рождения! Желаем всего тебе самого крутого"
                        f" и исполнения твоих желаний! А также, мы тебе очень благодарны, что ты с нами уже {days} дней"
                        f" без тебя, мы бы были не такими дружелюбными! Еще раз с праздником тебя 🔥❤️❤️❤️🔥",
                                       "Так так, кто у нас тут сегодня именниник??? Правильно, это ты☀️ Поздравляем"
                                       " тебя с праздником и желаем всего самого самого наилучшего❤️."
                                       "Пусть в твоей жизни будет много любви и счастья!!! А еще, спасибо тебе большое,"
                                       f" за то время, что ты с нами провел {days} дней между прочим, как бы"
                                       f"достаточно много, без тебя мы бы не стали теми, кем являемся сейчас! "
                                       f"Поздравляем тебя🔥❤️❤️🔥"])
            )

@bot.loop_wrapper.timer(hours=15)
async def summary():
    time_now = datetime.now()
    if time_now.weekday() == 0:
        text = "Итак, это ваш еженедельный отчет!"
        last_week = time_now - timedelta(days=7)
        async with Database() as db:
            user_ids = await db.all_user_id()
        for user_id in user_ids:
            async with Database() as db:
                distance_time_pace_diffgain = np.array(await db.distance_time_pace_diffgain_from_start_to_finish(user_id,
                                                                                                  last_week, time_now))
            if distance_time_pace_diffgain.shape[0] >= count_jog_in_week_treshold:
                text += f"Общее количество пробежек на этой неделе: {distance_time_pace_diffgain.shape[0]}\n"
                distance = distance_time_pace_diffgain[:, 1]
                text += f"Преодоленное растояние: {np.sum([d for d in distance if d is not None])}"
                time_jog = distance_time_pace_diffgain[:, 2]
                time_jog = np.sum([t.hour * 3600 + t.minute * 60 + t.second for t in time_jog if t is not None])
                hour = int(time_jog // 3600)
                minute = int(time_jog // 60) - hour * 60
                second = time_jog - 60 * minute - 3600 * hour
                text += f"Время, проведенное во время пробежек:"
                if hour != 0: text += f" {hour} {await control_hour(hour)}"
                if minute != 0: text += f" {minute} {await control_minute(minute)}"
                if second != 0: text += f" {second} {await control_second(second)}"
                text += "\n"
                pace = distance_time_pace_diffgain[:, 3]
                text += f"Средний темп за эти пробежки: {np.mean([p for p in pace if p is not None])}\n"
                await bot.api.messages.send(
                    peer_id=user_id,
                    message=text,
                    random_id=0
                )

    if time_now.day == 1:
        if time_now.month != 1:
            last_month = datetime(year=time_now.year, month=time_now.month-1, day=1, hour=12)
        else:
            last_month = datetime(year=time_now.year-1, month=12, day=1, hour=12)
        async with Database() as db:
            user_ids = await db.all_user_id()
        for user_id in user_ids:
            async with Database() as db:
                distance_time_pace_diffgain = np.array(await db.distance_time_pace_diffgain_from_start_to_finish(user_id,
                                                                                                  last_week, time_now))
                if distance_time_pace_diffgain.shape[0] >= count_jog_in_month_treshold:
                    text = await help_by_finish_date_summary(user_id, start_date=last_month, finish_date=time_now)

                    await bot.api.messages.send(
                        peer_id=user_id,
                        message=text.replace("В этот период", "За последний месяц"),
                        random_id=0
                    )
