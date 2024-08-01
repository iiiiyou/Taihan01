import sqlite3
import util.format_date_time as ti

def write_sql(s_time, e_time):
    conn = sqlite3.connect('fiber.db')
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE worklog (e_time)'+
        'VALUES (?)'+
        'where s_time = ' + s_time + '',
        ())

    conn.commit()
    conn.close()

