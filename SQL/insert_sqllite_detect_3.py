import sqlite3
import sys
sys.path.append('C:/source')
import util.format_date_time as ti

def write_sql(s_time, material_number, seq2, d_meter, type, d_time, image, area):
    conn = sqlite3.connect('C:/source/SQL/fiber.db', isolation_level=None)
    conn.execute('PRAGMA journal_mode = WAL')
    conn.execute('PRAGMA synchronous = OFF')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS detection (
    s_time int, material_number text, seq2 int, d_meter int, type text, d_time int, image text, area int
    )""")

    cursor.execute(
        'INSERT INTO detection (s_time, material_number, seq2, d_meter, type, d_time, image, area)'+
        'VALUES (?,?,?,?,?,?,?,?)',
        (s_time, material_number, seq2, d_meter, type, d_time, image, area))

    conn.close()

