import sqlite3
import sys
sys.path.append('C:/source')
import util.format_date_time as ti

def write_sql(s_time, product):
    conn = sqlite3.connect('C:/source/SQL/fiber')
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO worklog (s_time, material_number)'+
        'VALUES (?,?)',
        (s_time, product))

    conn.commit()
    conn.close()