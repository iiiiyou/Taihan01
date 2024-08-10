import sqlite3
import sys
sys.path.append('C:/source')
import util.format_date_time as ti


def write_sql1(s_time):
    conn = sqlite3.connect('C:/source/SQL/fiber.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS worklog (
    s_time int, material_number text, e_time int, area int
    )""")

    cursor.execute(
        'INSERT INTO worklog (s_time)'+
        'VALUES (?)',
        (s_time,))

    conn.commit()
    conn.close()


def write_sql2(s_time, product):
    conn = sqlite3.connect('C:/source/SQL/fiber.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS worklog (
    s_time int, material_number text, e_time int, area int
    )""")

    cursor.execute(
        'INSERT INTO worklog (s_time, material_number)'+
        'VALUES (?,?)',
        (s_time, product))

    conn.commit()
    conn.close()

def write_sql3(s_time, area):
    
    conn = sqlite3.connect('C:/source/SQL/fiber.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS worklog (
    s_time int, material_number text, e_time int, area int
    )""")
    
    cursor.execute(
        'INSERT INTO worklog (s_time, area)'+
        'VALUES (?,?)',
        (s_time, area))

    conn.commit()
    conn.close()

    