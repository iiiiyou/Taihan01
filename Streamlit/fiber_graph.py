import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from matplotlib import font_manager

# 페이지 설정
st.set_page_config(layout="wide")

# 한글 폰트 설정 (폰트 경로를 확인 필요)
font_path = 'C:\\Windows\\Fonts\\malgun.ttf'  # Windows의 경우
# font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'  # Linux의 경우
font_prop = font_manager.FontProperties(fname=font_path)

def fetch_data(start_date_str, end_date_str, db_folder):
    data = []
    col_names = None

    # 폴더가 존재하는지 확인하고, 로그에 경로 출력
    if not os.path.exists(db_folder):
        st.write(f"지정된 경로가 존재하지 않습니다: {db_folder}")
        return data, col_names

   # st.write(f"데이터베이스 폴더: {db_folder}")

    for db_file in os.listdir(db_folder):
        if db_file.endswith(".db"):
            db_path = os.path.join(db_folder, db_file)
            #st.write(f"읽는 데이터베이스 파일: {db_path}")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            query = """
            SELECT s_time, i_time, area
            FROM area
            WHERE i_time BETWEEN ? AND ?
            """
            #st.write(f"SQL 쿼리: {query} (파라미터: {start_date_str}, {end_date_str})")
            cur.execute(query, (start_date_str, end_date_str))
            rows = cur.fetchall()
            #st.write(f"조회된 데이터 수: {len(rows)}")
            if rows:
                if col_names is None:
                    col_names = [description[0] for description in cur.description]
                data.extend(rows)
            conn.close()
    return data, col_names

def plot_area_graph(df):
    # Convert i_time to datetime
    df['i_time'] = pd.to_datetime(df['i_time'], format='%Y%m%d%H%M%S', errors='coerce')  # Adjust this format if necessary
    df = df.dropna(subset=['i_time'])  # Drop rows with invalid datetime
    df = df.sort_values('i_time')
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['i_time'], df['area'], marker='o', linestyle='-', color='b')

    # Formatting for X-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=1))  # Show ticks every minute
    plt.xlabel('시간', fontproperties=font_prop)  # X-axis label
    plt.ylabel('넓이', fontproperties=font_prop)  # Y-axis label
    plt.title('시간에 따른 넓이그래프', fontproperties=font_prop)  # Title of the graph
    plt.xticks(rotation=45, fontproperties=font_prop)
    plt.grid(True)
    plt.tight_layout()
    st.pyplot(plt)

# Streamlit 앱
st.title("일자별 Cable 넓이 현황")

# 조회일자 입력
start_date = st.date_input("조회 시작일", value=datetime.today(), label_visibility="collapsed")
end_date = start_date + timedelta(days=1)

# 날짜를 문자열로 변환
start_date_str = start_date.strftime("%Y%m%d%H%M%S")  # Adding time part
end_date_str = (end_date - timedelta(seconds=1)).strftime("%Y%m%d%H%M%S")  # Subtracting 1 second for end date

# 입력일로부터 입력월과 일자 폴더 경로 생성
folder_name = r"C:\areaDB"
input_month = start_date.strftime("%Y%m")
db_folder = os.path.join(folder_name, input_month, start_date.strftime("%Y%m%d"))

# 로그 출력
#st.write(f"조회 시작일: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
#st.write(f"조회 종료일: {(end_date - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')}")
#st.write(f"데이터베이스 폴더 경로: {db_folder}")

# 데이터 로드
rows, col_names = fetch_data(start_date_str, end_date_str, db_folder)
if rows:
    df = pd.DataFrame(rows, columns=col_names)
else:
    df = pd.DataFrame(columns=["s_time", "i_time", "area"])

# 그래프 그리기
if not df.empty:
    plot_area_graph(df)
else:
    st.write("해당 날짜에 대한 데이터가 없습니다.")
