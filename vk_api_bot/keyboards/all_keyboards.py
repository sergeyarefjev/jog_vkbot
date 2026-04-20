from vkbottle.tools import Keyboard, Text, OpenLink, Callback
from database.db import Database
from datetime import time


def menu_kb():
    kb = Keyboard()
    kb.add(Text("Личные данные"))
    kb.add(Text("Последняя сводка"))
    kb.add(Text("Отчет"))
    kb.row()
    kb.add(Text("Достижения"))
    kb.add(Text("Цели"))
    kb.add(Text("Обувь"))
    kb.row()
    kb.add(Text("BMI"))
    return kb


def main_kb():
    kb = Keyboard()
    kb.add(Text("Начать пробежку"))
    kb.row()
    kb.add(Text("Заполнить информацию о пробежке"))
    kb.row()
    kb.add(Text("Соревнование!!!"))
    kb.row()
    kb.add(Text("Выйти в меню"))
    return kb

def date_jog_choice():
    kb=Keyboard(inline=True)
    kb.add(Callback(
        label="Последняя",
        payload={"date": "last"}
    ))
    kb.row()
    kb.add(Callback(
        label="Напишу дату сам",
        payload={"date": "self"}
    ))
    return kb

def time_jog_choice(jogs: list):
    kb = Keyboard(inline=True)
    for jog in jogs:
        data = jog[0].replace(tzinfo=None).replace(microsecond=0)
        print("jog[0]")
        print(data)
        kb.add(Callback(
            label=f"{data.strftime('%Y-%m-%d %H:%M:%S')}",
            payload={"time": "choice", "jog_time": f"{jog[0]}"}
        ))
        kb.row()
    kb.add(Callback(
        label="Не, не та дата",
        payload={"time": "non"}
    ))
    return kb

def jog_continue():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Закончить пробежку",
        payload={"jog" : "end"}
    ))
    return kb

def jog_form():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Да, давай заполню сейчас",
        payload={"jog": "fill"}
    ))
    kb.row()
    kb.add(Callback(
        label="Не, давай потом заполню",
        payload={"jog": "then"}
    ))
    return kb

def jog_skip_name():
    kb=Keyboard(inline=True)
    kb.add(Callback(
        label="Пропустить",
        payload={"jog": "skip_name"}
    ))
    return kb

def jog_skip_something(skip_something):
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Пропустить",
        payload={"jog": skip_something}
    ))
    return kb

def self_auto_time_jog():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Напишу сам в формате чч:мм:сс",
        payload={"jog_time_choice": "self"}
    ))
    kb.row()
    kb.add(Callback(
        label="Не, возьмем из разности",
        payload={"jog_time_choice": "auto"}
    ))
    return kb

async def kb_shoes(user_id, skip_somthing):
    kb = Keyboard(inline=True)
    async with Database() as db:
        shoes = await db.take_shoes(user_id)
    for shoe in shoes:
        kb.add(Callback(
            label=shoe,
            payload={"shoes": "shoe", "button_text": shoe}
        ))
        kb.row()
    kb.add(Callback(
        label="Пропустить",
        payload={"jog": skip_somthing}
    ))
    return kb


def links_kb():
    kb = Keyboard(inline=True)
   # kb.add(OpenLink("t.me/serliver", "Тг Сергея Арефьева"))
    #kb.row()
    #kb.add(OpenLink("t.me/Anikeeva00", "Тг любимки Сергея Арефьева"))
    #kb.row()
    kb.add(OpenLink("https://github.com/sergeyarefjev", "GitHub Сергея Арефьева"))
    kb.row()
    kb.add(OpenLink("https://vk.com/lithiumohno", "Вк Сергея Арефьева"))
    return kb


def save_kb():
    kb = Keyboard(inline=True)

    kb.add(Callback(
        label="Хочу перезаписать!",
        payload={"users": "overwrite"}
    ))

    kb.row()
    kb.add(Callback(
        label="Нет, оставь, как есть.",
        payload={"users": "nothing"}
    ))
    return kb


def csv_question():
    kb = Keyboard(inline=True)

    kb.add(Callback(
        label="Да, именно так (мои данные из zeopoxa)",
        payload={"zeopoxa_csv_question": "yes"}
    ))
    kb.row()

    kb.add(Callback(
        label="Нет, я ошибся",
        payload={"csv_question": "no"}
    ))
    return kb


def gender_kb():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Мужчина",
        payload={"gender": "male"}
    ))
    kb.row()
    kb.add(Callback(
        label="Женщина",
        payload={"gender": 'female'}
    ))
    return kb


def goal_kb():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Хочу поставить новую цель!",
        payload={"goal": "new_goal"}
    ))
    kb.row()
    kb.add(Callback(
        label="Хочу посмотреть свои результаты",
        payload={"goal": "check_goal"}
    ))
    kb.row()
    kb.add(Callback(
        label="Хочу посмотреть все цели",
        payload={"goal": "all_goal"}
    ))
    return kb

def goal_choose():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Количество пробежек",
        payload={"goal": "count_jog_goal"}
    ))
    kb.row()
    kb.add(Callback(
        label="Дистанция",
        payload={"goal": "distance_jog_goal"}
    ))
    kb.row()
    kb.add(Callback(
        label="Время",
        payload={"goal": "time_jog_goal"}
    ))
    kb.row()
    kb.add(Callback(
        label="Изменение высоты",
        payload={"goal": "height_jog_goal"}
    ))
    return kb

def goal_start_time():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Сейчас",
        payload={"goal_start": "now"}
    ))
    kb.row()
    kb.add(Callback(
        label="Со следующей недели",
        payload={"goal_start": "next_week"}
    ))
    kb.row()
    kb.add(Callback(
        label="Со следующего месяца",
        payload={"goal_start": "next_month"}
    ))
    kb.row()
    kb.add(Callback(
        label="Напишу сам, формат (ГГГГ-ММ-ДД)",
        payload={"goal_start": "self"}
    ))
    return kb

def goal_finish_time():
    kb = Keyboard(inline=True)
    kb.add(Callback(
            label="Неделя",
            payload={"goal_finish": "week"}
        )
    )
    kb.row()
    kb.add(Callback(
        label="Месяц",
        payload={"goal_finish": "month"}
    ))
    kb.row()
    kb.add(Callback(
        label="Год",
        payload={"goal_finish": "year"}
    ))
    kb.row()
    kb.add(Callback(
        label="Бессрочная цель",
        payload={"goal_finish": "inf"}
    ))
    kb.row()
    kb.add(Callback(
        label="Напишу сам, формат (ГГГГ-ММ-ДД)",
        payload={"goal_finish": "self"}
    ))
    return kb


def active_goals(goals):
    kb = Keyboard(inline=True)
    for goal in goals:
        if goal[-2] is not None:
            kb.add(Callback(
                label=f"Разность высот {goal[-2]} м",
                payload={"goal": "diff_gain", "start_time": f"{goal[1]}"}
            ))
        elif goal[-3] is not None:
            hour = goal[-3] // 3600
            minute = (goal[-3] - hour * 3600) // 60
            second = goal[-3] - hour * 3600 - minute * 60
            kb.add(Callback(
                label=f"Время {hour}:{minute}:{second}",
                payload={"goal": "time", "start_time": f"{goal[1]}"}
            ))
        elif goal[-4] is not None:
            kb.add(Callback(
                label=f"Дистанция {goal[-4]} км",
                payload={"goal": "distance", "start_time": f"{goal[1]}"}
            ))
        elif goal[-5] is not None:
            kb.add(Callback(
                label=f"Кол-во пробежек {goal[-5]}",
                payload={"goal": "count_jog", "start_time": f"{goal[1]}"}
            ))
        else:
            kb.add(Callback(
                label="Вернуться назад",
                payload={"goal": "back"}
            ))
        kb.row()

    return kb


def jog_notice_kb():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Да, сегодня обязательно постараюсь пробежаться!",
        payload={"notice": "yes"}
    ))
    kb.row()
    kb.add(Callback(
        label="Не, давай не сегодня ",
        payload={"notice": "no"}
    ))
    return kb

def competition_kb():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Расстояние",
        payload={"competition": "distance"}
    ))
    kb.row()
    kb.add(Callback(
        label="Длительность",
        payload={"competition": "time"}
    ))
    kb.row()
    kb.add(Callback(
        label="Назад",
        payload={"competition": "back"}
    ))
    return kb

def progress_keyboard():
    kb = Keyboard(inline=True)
    kb.add(Callback(
        label="Темп",
        payload={"progress": "pace"}
    ))
    kb.row()
    kb.add(Callback(
        label="Дистанция",
        payload={"progress": "distance"}
    ))
    kb.row()
    kb.add(Callback(
        label="Время",
        payload={"progress": "time"}
    ))
    kb.row()
    kb.add(Callback(
        label="Нет, спасибо",
        payload={"progress": "nothing"}
    ))

    return kb