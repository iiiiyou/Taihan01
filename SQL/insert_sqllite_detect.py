import sqlite3
import sys
sys.path.append('C:/source')
import util.format_date_time as ti

def write_sql(s_time, material_number, seq2, d_meter, type, d_time, image, area):
    conn = sqlite3.connect('C:/source/SQL/fiber')
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO detection (s_time, material_number, seq2, d_meter, type, d_time, image, area)'+
        'VALUES (?,?,?,?,?,?,?,?)',
        (s_time, material_number, seq2, d_meter, type, d_time, image, area))

    conn.commit()
    conn.close()

