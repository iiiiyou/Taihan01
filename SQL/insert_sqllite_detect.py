import sqlite3
import util.format_date_time as ti

def write_sql(s_time, product, c_time, calculated_number, ):
    conn = sqlite3.connect('fiber.db')
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO dimension (s_time, material_number, seq2, d_meter, type, d_time, image, area)'+
        'VALUES (?,?,?,?,?,?,?,?)',
        (s_time, product, ))

    conn.commit()
    conn.close()

