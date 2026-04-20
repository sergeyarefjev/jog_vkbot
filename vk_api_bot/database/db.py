from psycopg_pool import AsyncConnectionPool
from decouple import config
import pandas as pd
from io import StringIO


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = AsyncConnectionPool(
            conninfo=config("CONNINFO"),
            min_size=3,
            max_size=10
        )
        await self.pool.open()
        await self.pool.wait()
        print("Connect is successfull")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("Disconnect is successfull")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    #work with "users"
    async def check_id(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE user_id = %s", [user_id])
                rows = await cur.fetchall()
                if len(rows) == 0:
                    return False
                else:
                    return True

    async def insert_user(self, data):
        """
        data - list: len(data) = 8
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO users (user_id, gender, weight, height, birthday, run_time, shoes, date_join)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, data)

    async def delete_user(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                DELETE FROM users
                WHERE user_id = %s
                """, [user_id])

    async def all_user_id_birthday_datejoin(self):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                        SELECT user_id, birthday, date_join FROM users
                """)
                rows = await cur.fetchall()
        return rows

    async def all_user_id(self):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT DISTINCT user_id FROM users
                """)
                rows = await cur.fetchall()
        return rows

    async def take_weight(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT weight FROM users
                WHERE user_id = %s
                """, [user_id])
                row = await cur.fetchone()
        return row[0]

    async def take_height(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT height FROM users
                WHERE user_id = %s
                """, [user_id])
                row = await cur.fetchone()
        return row[0]

    async def take_user_info(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE user_id = %s", [user_id])
                row = await cur.fetchone()
        return row

    async def take_shoes(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT shoes FROM users WHERE user_id =%s", [user_id])
                shoes = (await cur.fetchone())[0].split(',')
        return shoes

    #work with "jogging"

    async def take_by_lr_from_user(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT start_jog, distance, time, average_pace, max_height, min_height FROM jogging
                WHERE user_id = %s
                ORDER BY start_jog
                """, [user_id])
                rows = await cur.fetchall()
        return rows

    async def shoe_distance(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT shoes, SUM(distance)::NUMERIC(5, 1) FROM jogging
                GROUP BY shoes
                ORDER BY 2 DESC
                """)
                rows = await cur.fetchall()
        return rows

    async def max_distance(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT start_jog, distance FROM jogging
                    WHERE user_id = %s
                    ORDER BY distance DESC
                    LIMIT 1
                """, [user_id])
                row = await cur.fetchone()
        return row

    async def max_time(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT start_jog, time FROM jogging
                    WHERE user_id = %s
                    ORDER BY time DESC
                    LIMIT 1
                """, [user_id])
                row = await cur.fetchone()
        return row

    async def count_jog(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM jogging WHERE user_id = %s", [user_id])
                length = (await cur.fetchone())[0]
        return length

    async def min_pace(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                                    SELECT max_pace AS min_pace FROM jogging
                                    WHERE max_pace > '00:00:00'::TIME AND user_id = %s
                                    ORDER BY max_pace 
                                    LIMIT 1
                                  """,
                                  [user_id])
                pace = (await cur.fetchone())[0]
        return pace

    async def max_diff_height(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT max_height - min_height AS diff FROM jogging
                WHERE user_id = %s
                ORDER BY diff DESC
                LIMIT 1
                """, [user_id])
                diff = (await cur.fetchone())[0]
        return diff

    async def average_pace(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT AVG(average_pace) FROM jogging WHERE user_id = %s
                                   """, [user_id])
                avg_pace = (await cur.fetchone())[0]
        return avg_pace

    async def all_distance(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT SUM(distance) FROM jogging WHERE user_id = %s",
                                  [user_id])
                all_distance = (await cur.fetchone())[0]
        return all_distance

    async def take_all_user_last_jog(self):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                        SELECT j.user_id, MIN(j.finish_jog), ss.notice_long_ago FROM jogging j
                        LEFT JOIN setting_status ss
                        ON j.user_id = ss.user_id
                        GROUP BY j.user_id, ss.notice_long_ago
                """)
                rows = await cur.fetchall()
        return rows

    async def take_last_jog_id(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT MAX(jog_id) FROM jogging WHERE user_id=%s", [user_id])
                row = (await cur.fetchone())[0]
        return row

    async def take_last_jog_data(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                                    SELECT * FROM jogging 
                                    WHERE user_id = %s
                                    ORDER BY start_jog DESC
                                    LIMIT 1
                                  """, [user_id])
                row = (await cur.fetchone())
        return row

    async def take_percent_worse_jog(self, user_id, value, mark):
        if mark == "distance":
            text = "distance <= %s"
        elif mark == "average_pace":
            text = "average_pace >= %s"
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM jogging), 1) FROM jogging
                    WHERE user_id = %s AND 
                """ + text, [user_id, value])
                percent = (await cur.fetchone())[0]
        return percent

    async def take_last_p_pace(self, user_id, p):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT average_pace FROM jogging
                    WHERE user_id = %s
                    ORDER BY start_jog DESC
                    LIMIT %s
                """, [user_id, p])
                rows = await cur.fetchall()
        return rows

    async def take_last_q_diff_gain(self, user_id, q):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT max_height - min_height as diff_gain FROM jogging
                    WHERE user_id = %s
                    ORDER BY start_jog DESC
                    LIMIT %s 
                """, [user_id, q])
                rows = await cur.fetchall()
        return rows

    async def take_several_jog_by_data(self, user_id, data):
        async with self.pool.connection() as conn:
            print("here")
            async with conn.cursor() as cur:
                await cur.execute("""
                SELECT start_jog FROM jogging
                WHERE user_id = %s AND start_jog::DATE = %s
                """, [user_id, data])
                rows = (await cur.fetchall())
        return rows

    async def take_by_datetime_jog(self, user_id, jog_time):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                                    SELECT * FROM jogging
                                    WHERE user_id = %s AND start_jog = %s
                                  """, [user_id, jog_time])
                row = (await cur.fetchone())
        return row

    async def take_cumulative_sum_count_jog(self, user_id, start_time, finish_time):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT start_jog, COUNT(*) 
                    OVER(PARTITION BY user_id ORDER BY start_jog ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                    FROM jogging
                    WHERE user_id = %s AND
                    start_jog > %s AND
                    finish_jog < %s
                """, [user_id, start_time, finish_time])
                rows = await cur.fetchall()
        return rows

    async def take_cumulative_sum_time_distance_diffgain(self, user_id, start_time, finish_time, type_goal):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                if type_goal == "time":
                    text = "SELECT start_jog, SUM(COALESCE(time, '00:00:00'::TIME))"
                elif type_goal == "distance":
                    text = "SELECT start_jog, SUM(COALESCE(distance, 0))"
                elif type_goal == "diff_gain":
                    text = "SELECT start_jog, SUM(COALESCE(ABS(max_height - min_height), 0))"
                await cur.execute(text + """
                    OVER(PARTITION BY user_id ORDER BY start_jog ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                    FROM jogging
                    WHERE user_id = %s AND
                    start_jog > %s AND
                    finish_jog < %s
                """, [user_id, start_time, finish_time])
                rows = await cur.fetchall()
        return rows

    async def max_start_to_finish(self, user_id, start_time, finish_time):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    WITH HELP_MAX AS(
                        SELECT user_id, MIN(max_pace) AS max_pace FROM jogging
                        WHERE user_id = %s AND start_jog >= %s AND finish_jog <= %s AND max_pace != '00:00:00'::TIME 
                        GROUP BY user_id
                    ),
                    
                    HELP_AVG AS(
                        SELECT user_id, MIN(average_pace) AS average_pace FROM jogging
                        WHERE user_id = %s AND start_jog >= %s AND finish_jog <= %s AND average_pace != '00:00:00'::TIME
                        GROUP BY user_id
                    ),
                    
                    HELP_OTHER AS(
                        SELECT user_id, MAX(distance) AS distance, MAX(time) AS time, 
                        MAX(max_height - min_height) AS diff_gain FROM jogging
                        WHERE user_id = %s AND start_jog >= %s AND finish_jog <= %s
                        GROUP BY user_id
                    )
                    
                    SELECT a.average_pace, m.max_pace, o.distance, o.time, o.diff_gain FROM HELP_MAX m
                        JOIN HELP_AVG a
                        ON m.user_id = a.user_id
                            JOIN HELP_OTHER o
                            ON m.user_id = o.user_id
                """, [user_id, start_time, finish_time, user_id, start_time, finish_time,
                      user_id, start_time, finish_time])
                row = await cur.fetchone()
        return row

    async def distance_time_pace_diffgain_from_start_to_finish(self, user_id, start_date, finish_date):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                        SELECT start_jog, NULLIF(distance, 0), NULLIF(time, '00:00:00'::TIME), 
                        NULLIF(average_pace, '00:00:00'::TIME), NULLIF(max_height - min_height, 0) FROM jogging
                        WHERE user_id = %s AND start_jog > %s AND finish_jog < %s
                        ORDER BY start_jog
                """, [user_id, start_date, finish_date])
                rows = await cur.fetchall()
        return rows

    async def insert_data_to_jogging(self, data):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO jogging
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, data)

    async def insert_date_id(self, data):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO jogging (user_id, jog_id, start_jog, finish_jog)
                    VALUES (%s, %s, %s, %s)
                """, data)

    async def update_data_to_jogging(self, data):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE jogging
                    SET user_id = %s,
                    jog_id = %s,
                    start_jog = %s,
                    finish_jog = %s,
                    name_jog = %s,
                    caption_jog = %s,
                    distance = %s,
                    time = %s,
                    calories = %s,
                    average_heart_rate = %s,
                    max_heart_rate = %s,
                    average_pace = %s,
                    max_pace = %s,
                    min_height = %s,
                    max_height = %s,
                    shoes = %s,
                    temperature = %s,
                    wind_speed = %s
                    WHERE user_id = %s AND start_jog=%s;
                """, data)

    async def set_fmt(self, series):
        """
        series - Series with str data format -- dd-MM-YYYY
        """
        day = series.str[:2]
        month = series.str[3:5]
        year = series.str[6:]
        return year + month + day

    async def change_comma_to_point(self, series):
        return series.apply(lambda x: x[:x.find(',')] + '.' + x[x.find(',') + 1:]
                            if x.find(',') != -1 else x)

    async def copy_csv_zeopoxa(self, file_path, user_id):
        df_csv = pd.read_csv(file_path, dtype=str)
        df = pd.DataFrame()
        df["user_id"] = [user_id for _ in range(len(df_csv))]
        df["jog_id"] = df_csv["id"]
        df["start_jog"] = await self.set_fmt(df_csv["Даты (dd-MM-yy)"]) + " " + df_csv["Время начала"]
        df["finish_jog"] = await self.set_fmt(df_csv["Даты (dd-MM-yy)"]) + " " + df_csv["Остановить время"]
        df["name_jog"] = df_csv["Заглавие"]
        df["caption_jog"] = df_csv["Заметка"]
        df["distance"] = await self.change_comma_to_point(df_csv["Расстояние (км)"])
        df["time"] = df_csv["Длительность"]
        df["calories"] = await self.change_comma_to_point(df_csv["Калории"])
        df["average_heart_rate"] = df_csv["Сред Частота сердцебиения"]
        df["max_heart_rate"] = df_csv["Mакс Частота сердцебиения"]
        df["average_pace"] = df_csv["Средний темп (мин/км)"].apply(lambda x: "00:" + x) #Так как формат
        df["max_pace"] = df_csv["Mаксимальный темп (мин/км)"].apply(lambda x: "00:" + x) #в csv MM:SS
        df["min_height"] = await self.change_comma_to_point(df_csv["Мин Высота (м)"])
        df["max_height"] = await self.change_comma_to_point(df_csv["Mакс Высота (м)"])
        df["shoes"] = df_csv["Oбувь"]
        df["temperature"] = df_csv["Температура (C)"]
        df["wind_speed"] = df_csv["Скорость ветра км/ч"]
        buffer = StringIO()
        df.to_csv(buffer, index=False, header=False)
        buffer.seek(0)
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                CREATE TABLE HELP_TABLE
                (LIKE jogging INCLUDING DEFAULTS)
                """)

                async with cur.copy("""
                COPY HELP_TABLE FROM STDIN WITH CSV
                """) as copy:
                    await copy.write(buffer.read())
                await cur.execute("""
                INSERT INTO jogging
                SELECT * FROM HELP_TABLE
                WHERE NOT EXISTS(
                    SELECT 1 FROM jogging
                    WHERE jogging.user_id = HELP_TABLE.user_id AND jogging.jog_id = HELP_TABLE.jog_id
                )
                """)
                await cur.execute(
                    "DROP TABLE HELP_TABLE"
                )

    #work with goal
    async def insert_goal(self, data):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO goal
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, data)

    async def get_active_goals(self, user_id):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT * FROM goal
                    WHERE user_id = %s AND status = True
                """, [user_id])
                rows = await cur.fetchall()
        return rows

    async def get_goal_by_start_time(self, user_id, start_time):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT * FROM goal
                    WHERE user_id = %s AND start_time = %s
                """, [user_id, start_time])
                row = await cur.fetchone()
        return row

    async def initialize_active_goal(self, user_id, now_time):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE goal
                    SET status = False
                    WHERE user_id = %s AND (start_time > %s OR finish_time < %s)
                """, [user_id, now_time, now_time])


    #work with setting_status
    async def input_long_ago(self, user_id, status):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                            INSERT INTO setting_status (user_id, notice_long_ago)
                            SELECT %s, %s
                            WHERE NOT EXISTS (SELECT 1 FROM setting_status WHERE user_id = %s);
                        """, [user_id, status, user_id])

    async def update_long_ago(self, user_id, status):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                UPDATE setting_status
                SET notice_long_ago = %s
                WHERE user_id = %s
                """, [status, user_id])

