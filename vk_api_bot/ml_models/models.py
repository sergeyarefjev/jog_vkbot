import joblib
from vkbottle.bot import Message, MessageEvent, rules
from vkbottle.dispatch.dispenser import BaseStateGroup
from vkbottle import CtxStorage, GroupEventType
from vkbottle.tools import EMPTY_KEYBOARD
from create_bot import bot
import keyboards.all_keyboards as kb
from database.db import Database

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from datetime import datetime, time, date
import xgboost
from decouple import config

"""
В качестве моделей предсказания темпа выбран XGBRegressor (см в ноутбуке)
если количество пробежек < change_koef, то выбирается модель, обученная на многих людях, 
то есть это некое усреднение по всем бегунам (ну не по всем, конечно же, но по многим), 
а если количество пробежек > change_koef, то обучается персональная модель для каждого пользователя
Модель будет именно обучаться, а не храниться, потому что пользователь будет не перед каждой пробежкой 
пользоваться этой функцией, а при хранении модели, ее все-равно нужно будет дообучать или полностью переобучать,
так как она устаревает (во многом это все же сделано для упрощения)
"""

change_koef = 150
delta_d = 0.5
delta_t = 3

class type_goal(BaseStateGroup):
    distance = 0
    time = 1

ctx = CtxStorage()

@bot.on.message(text=["Соревнование!!!"])
async def competition(message: Message):
    await message.answer("Отлично, этот режим работает следующим образом.\n"
                         "Ты ставишь цель на тренировку следующего типа:\n"
                         "— Пробежать определенную дистанцию\n"
                         "— Пробежать какое-то определенное время\n"
                         "После постановки одной из этих целей, я выбираю тебе противника, который пробежит"
                         " с такой же целью до тебя. А твоей задаче будет превзойти его результат.\n"
                         "Готов? Если готов, то выбирай ниже, что хочешь ввести", keyboard=kb.competition_kb())

async def create_data_by_model(user_id, p, q):
    async with Database() as db:
        data_arr = np.array(await db.take_by_lr_from_user(user_id))
        gender = (await db.take_user_info(user_id))[1]
    data = pd.DataFrame()
    data["gender"] = np.ones(data_arr.shape[0]) if gender == "male" else np.zeros(data_arr.shape[0])
    data["month"] = pd.to_datetime(data_arr[:, 0], format="%Y-%m-%d %H:%M:%S%z")
    # Вообще, я думаю, что во всех адекватных приложениях
    # (и при добавлении через бота) пропусков в start jog не должно быть, но мало ли
    mask = data["month"].isna()
    idx = data.index[mask]
    data.drop(idx, inplace=True)
    data["month"] = (data["month"].dt.month - 1).astype(int)
    data["distance"] = data_arr[:, 1]
    data["time"] = pd.to_datetime(data_arr[:, 2], format="%H:%M:%S")
    data["time"] = data["time"].dt.minute + data["time"].dt.hour * 60 + data["time"].dt.second / 60
    data["pace"] = pd.to_datetime(data_arr[:, 3], format="%H:%M:%S")
    data["pace"] = data["pace"].dt.hour * 60 + data["pace"].dt.minute + data["pace"].dt.second / 60
    data["diff_gain"] = data_arr[:, 4].astype(float) - data_arr[:, 5].astype(float)
    data_help = pd.DataFrame(np.eye(12)[data["month"].values])
    data = pd.concat([data_help, data], axis=1)
    for i in range(p):
        data[f"pace_{i + 1}_shift"] = data["pace"].shift(i + 1)
        if data[f"pace_{i + 1}_shift"] is None:
            data[f"pace_{i + 1}_shift"] = 0
    for j in range(q):
        data[f"diff_gain_{j + 1}_shift"] = data["diff_gain"].shift(j + 1)
        if data[f"diff_gain_{j + 1}_shift"] is None:
            data[f"diff_gain_{j + 1}_shift"] = 0


    mask_all = np.sum(np.array([data[column].isna() for column in data.columns]).T, axis=1)
    mask_all = np.where(mask_all > 0, True, False)

    idx_all = data.index[mask_all]
    data.drop(idx_all, inplace=True)
    data.columns = data.columns.astype(str)
    data.drop(columns=["month", "diff_gain"], inplace=True)
    return data

async def fit_model(user_id, model, p, q, drop_=["time"], load=True):
    """
    user_id: int - user id
    model: model (поддерживает fit)
    p: int (количество лагов темпа)
    q: int (количество лагов разности высоты)
    drop: "time" or "distance" (что выкинуть)
    """
    try:
        data = await create_data_by_model(user_id, p=p, q=q)
        if len(data) < change_koef:
            return False
        if not load:
            scaler, data_columns = await take_scaler_and_columns(user_id, p=p, drop_=drop_, q=q, load=load)
            data_x = scaler.transform(data.drop(columns=data_columns))
        else:
            data_columns = await take_scaler_and_columns(user_id, p=p, q=q, drop_=drop_, load=load)
            data_x = data.drop(columns=data_columns)
        data_x = pd.DataFrame(data_x, columns=data_columns)
        model.fit(data_x.values, data["pace"].values)
        return model

    except ValueError:
        print('Скорее всего было переданно в drop_ не "time", а "distance"')


async def take_scaler_and_columns(user_id, p, q, drop_=["time"], load=True):
    if load:
        backbone = ["gender", "pace", "pace_lag_1",
                "pace_lag_2", "pace_lag_3", "pace_lag_4", "pace_lag_5",
                "pace_lag_6", "pace_lag_7", "pace_lag_8", "pace_lag_9", "pace_lag_10"]
        if drop_ == ["time"]:
            return ["distance"] + backbone
        else:
            return ["time"] + backbone
    else:
        data = await create_data_by_model(user_id, p=p, q=q)
        columns = data.columns
        use_columns = [c for c in columns if c not in ["pace"] + drop_]
        scaler = StandardScaler()
        scaler.fit(data.drop(columns=["pace"] + drop_))
        return scaler, use_columns


async def take_last_type_pace(user_id, val, type_feature="distance"):
    """
    type_feature = "distance" | "time
    """
    async with Database() as db:
        data = np.array(await db.take_by_lr_from_user(user_id))
    if type_feature == "distance":
        delta = delta_d
        data = data[:, [1, 3]]
    else:
        delta = delta_t
        data = np.array([[d[2].minute + d[2].second/60 + d[2].hour*60, d[3]] for d in data])

    for j in range(len(data) - 1, -1, -1):
        if np.abs(val - data[j, 0]) < delta:
            return data[j, 1].minute + data[j, 1].second/60 + data[j, 1].hour*60
    return np.mean([d.minute + d.second/60 + d.hour*60 for d in date[:, 1]])

async def construct_data_lr(message: Message, p: int, q=1, this="distance", drop_=["time"], load=True):
    async with (Database() as db):
        data_user_info = await db.take_user_info(message.from_id)
        gender = data_user_info[1]
        age = date.today().year - data_user_info[4].year
        if (date.today().month < data_user_info[4].month or
           (date.today().month == data_user_info[4].month and date.today().day < data_user_info[4].day)):
            age -= 1
        user_last_p_pace = np.array((await db.take_last_p_pace(message.from_id, p)))
        user_last_p_pace = np.concatenate(user_last_p_pace) if p > 0 else user_last_p_pace
        user_last_p_pace = np.array([p if p is not None else 0 for p in user_last_p_pace])
        user_last_q_diff_gain = np.array(await db.take_last_q_diff_gain(message.from_id, q))
        user_last_q_diff_gain = np.concatenate(user_last_q_diff_gain) if q > 0 else user_last_q_diff_gain
        user_last_q_diff_gain = np.array([d if d is not None else 0 for d in user_last_q_diff_gain])
    gender = 1 if gender == "male" else 0
    month = datetime.now().month
    if this == "distance":
        value = float(message.text.replace(',', '.'))
        drop_here = drop_ + ["time"]
    else:
        value = datetime.strptime(message.text, "%H:%M:%S")
        value = value.hour * 60 + value.minute + value.second / 60
        drop_here = drop_ + ["distance"]

    if not load:
        scaler, data_columns = await take_scaler_and_columns(message.from_id, p, q=q, drop_=drop_here, load=load)
        data_help = np.eye(12)[month - 1]
        data = np.array([gender, value] + [
            user_last_p_pace[i].minute + user_last_p_pace[i].second / 60 + user_last_p_pace[i].hour * 60
            for i in range(p)] + [user_last_q_diff_gain[j] for j in range(q)])
        data = np.concatenate([data_help, data])
        data = scaler.transform(data.reshape(1, -1))
    else:
        data_columns = await take_scaler_and_columns(message.from_id, p, q=q, drop_=drop_here, load=load)
        last_feature_val = await take_last_type_pace(message.from_id, value, type_feature=this)
        if age < 34:
            age_group = [1, 0, 0]
        elif age >= 35 and age < 54:
            age_group = [0, 1, 0]
        else:
            age_group = [0, 0, 1]

        data = np.array([value, gender] +
            [user_last_p_pace[i].minute + user_last_p_pace[i].second / 60 + user_last_p_pace[i].hour * 60
            for i in range(p)] + [last_feature_val] + age_group
        ).reshape(1, -1)
    return data

@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"competition": "distance"})
)
async def distance_competition(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        random_id=0,
        message="Хорошо, тогда введите в следующем сообщении дистанцию, которую планируете покорить в км.",
        keyboard=EMPTY_KEYBOARD
    )
    await bot.state_dispenser.set(event.peer_id, type_goal.distance)

@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadRule({"competition": "time"})
)
async def time_competition(event: MessageEvent):
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        random_id=0,
        message="Отлично, тогда напиши время, которое ты хочешь уделить этой пробежке, в формате ЧЧ:ММ:СС",
        keyboard=EMPTY_KEYBOARD
    )
    await bot.state_dispenser.set(event.peer_id, type_goal.time)
@bot.on.message(state=[type_goal.distance, type_goal.time])
async def distance_competition(message: Message):
    try:
        if (await bot.state_dispenser.get(message.from_id)).state == "type_goal:0":
            print("one")
            drop_ = ["time"]
            this = "distance"
        else:
            print("two")
            drop_ = ["distance"]
            this = "time"
        async with Database() as db:
            count_jog = await db.count_jog(message.from_id)
        model = True
        if count_jog > change_koef:
            # будем считать, что это достаточно оптимальные alpha и p (это рассматривалось в ноутбуке)
            p = 10
            q = 1
            alpha = 1
            drop_columns = []
            model = await fit_model(message.from_id, Ridge(alpha=alpha), p=p, q=q, drop_=drop_ + drop_columns)
        if count_jog <= change_koef or not model:
            p = 10
            q = 0
            if this == "distance":
                drop_ = drop_ + ["last_time_jog_pace"]
                model = joblib.load(config("PATH_MODEL_DISTANCE"))
            else:
                drop_ = drop_ + ["last_distance_pace"]
                model = joblib.load(config("PATH_MODEL_TIME"))
            drop_columns = []
            q=0
        data = await construct_data_lr(message, p=10, q=q, this=this, drop_=drop_columns)
        pace_predict = model.predict(data)[0]
        minute = pace_predict // 1
        hour = minute // 60
        minute = minute % 60
        second = (pace_predict % 1) * 60
        pace = time(hour=int(hour), minute=int(minute), second=int(second))
        if this == "distance":
            await message.answer(f"Итак, твой противник пробежал {message.text} км с темпом: {pace}.\n"
                                f"Сможешь ли ты превзойти этот результат???", keyboard=kb.main_kb())
        else:
            await message.answer(f"Что ж, твой противник пробежал твое время с темпом: {pace}.\n"
                                 f"Сможешь ли ты превзойти этот результат???", keyboard=kb.main_kb())
        await bot.state_dispenser.delete(message.from_id)

    except ValueError:
        await message.answer("Введите дистанцию в виде вещественного числа")