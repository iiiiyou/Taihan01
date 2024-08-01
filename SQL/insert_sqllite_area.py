import sqlite3
import util.format_date_time as ti

s_time=ti.get_date_time()
product="abe"
area="100"

def write_sql(s_time, product, area):
    #테이블 생성 및 데이터 삽입
    conn = sqlite3.connect('C:/Users/user01/Desktop/areaDB'+s_time+'.db')
    cursor = conn.cursor()

    c_time = ti.get_date_time()

    cursor.execute("""CREATE TABLE IF NOT EXISTS area(
    s_time int, material_number text, i_time int, area int
    )""")

    cursor.execute(
        'INSERT INTO area (s_time, material_number, i_time, area) VALUES (?,?,?,?)',
        (s_time, product, c_time, area))

    conn.commit()
    conn.close()
    
write_sql(s_time, product, area)