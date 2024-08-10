import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
from io import BytesIO
from datetime import date, datetime, timedelta
import requests
import os

# 페이지 설정
st.set_page_config(layout="wide")

def clean_string(s):
    return ''.join(i for i in s if ord(i) >= 32 and ord(i) < 127)

def fetch_data(start_date, end_date, db_folder):
    data = []
    col_names = None

    # 주어진 폴더 내 모든 DB 파일을 탐색
    for db_file in os.listdir(db_folder):
        if db_file.endswith(".db"):
            db_path = os.path.join(db_folder, db_file)
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            query = """
            SELECT distinct s_time, 
                seq2,
                type,
                CAST(material_number AS TEXT) AS material_number,
                area,
                d_time,
                image
            FROM detection
            WHERE s_time BETWEEN ? AND ?
            order by d_time desc
            """
            cur.execute(query, (start_date, end_date))
            rows = cur.fetchall()
            if rows:
                if col_names is None:
                    col_names = [description[0] for description in cur.description]
                data.extend(rows)
            conn.close()
    return data, col_names

def to_excel(df):
    # 문자열 열의 불법 문자를 제거합니다.
    for col in df.select_dtypes([object]):
        df[col] = df[col].apply(lambda x: clean_string(str(x)))
        
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()
    processed_data = output.getvalue()
    return processed_data

# Streamlit 앱
st.title("불량품 탐지 데이터 조회")

# 날짜 입력 필드
col1, col2, col3, col4 = st.columns(4)
start_date = col1.date_input("조회일자", value=date.today())
end_date = start_date + timedelta(days=1)

# 날짜를 정수로 변환
# start_date_int =20240803152416
start_date_int = int(start_date.strftime("%Y%m%d%H%M%S"))
end_date_int = int(end_date.strftime("%Y%m%d%H%M%S"))

# 폴더 경로 입력 필드
# db_folder = "d:\python"
# image_folder = "C:\image\20240804"
# db_folder = st.text_input("DB 파일이 저장된 폴더 경로", value=".")
# image_folder = st.text_input("이미지 파일이 저장된 폴더 경로", value=".")
# folder_name = start_date.strftime("%Y%m%d")
folder_name = r"C:\source\sql"
db_folder = os.path.join(folder_name)  
image_folder = r"C:\image\20240810"   #db에 경로없이 이미지만 있는 경우

# 폴더 존재 여부 확인
if not os.path.exists(db_folder):
    st.error(f"DB 폴더 ({db_folder})가 존재하지 않습니다.")
else:
    # 데이터프레임 생성
    rows, col_names = fetch_data(start_date_int, end_date_int, db_folder)
    if rows:
        df = pd.DataFrame(rows, columns=col_names)
    else:
        st.warning("해당 기간에 데이터가 존재하지 않습니다.")
        df = pd.DataFrame()

    # 엑셀 파일로 다운로드 버튼 추가
    if not df.empty:
        excel_file = to_excel(df)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"data_{current_time}.xlsx"
        col4.download_button(
            label="Excel 다운로드",
            data=excel_file,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # 전체 컨테이너의 너비를 조정하는 스타일 적용
    st.markdown("""
        <style>
        .main .block-container {
            max-width: 85%;
            padding-left: 5%;
            padding-right: 5%;
        }
        </style>
        """, unsafe_allow_html=True)

    # 데이터프레임 출력 및 버튼 추가
    st.markdown("""
        <style>
        .dataframe-container {
            max-height: 600px;
            overflow-y: scroll;
            border: 1px solid #ccc;
        }
        .dataframe-container thead th {
            position: sticky;
            top: 0;
            background-color: #f0f0f0;
            text-align: center;
        }
        .dataframe-container th, .dataframe-container td {
            text-align: center;
        }
        .dataframe-container a {
            text-decoration: none;
            color: blue;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)

    # 데이터 출력 및 버튼 추가
    columns_widths = [6, 2, 3, 5, 3, 6, 20]
    for i, row in df.iterrows():
        cols = st.columns(columns_widths + [17])  # 마지막 열에 버튼 열 추가
        for col, val in zip(cols[:-1], row):  # 마지막 열은 버튼이 들어갈 자리
            if col == cols[-2]:  # 불량품이미지 열
                col.markdown(val, unsafe_allow_html=True)
            else:
                col.write(val)
        # 버튼 추가
        button_col = cols[-1]
        if button_col.button(f'이미지 보기 ({row["s_time"]} {row["seq2"]})', key=f'button_{i}'):
            try:
                image_path = os.path.join(image_folder, row["image"])
                # st.write(image_path)
                st.session_state['image_url'] = image_path
                st.session_state['image_pk'] = f'{row["s_time"]} {row["seq2"]}'
            except Exception as e:
                st.error("이미지 경로에 오류가 있습니다. 확인 후 다시 이용하시기 바랍니다!")

    st.markdown('</div>', unsafe_allow_html=True)

    # 하단에 이미지를 표시하거나 숨깁니다.
    with st.container():
        if 'image_url' in st.session_state and 'image_pk' in st.session_state:
            image_url = st.session_state['image_url']
            try:
                img = Image.open(image_url)
                st.image(img, caption=f"불량품이미지  {st.session_state['image_pk']}", use_column_width=True)
            except Exception as e:
                st.error("이미지를 로드하는 데 오류가 발생했습니다. 파일 경로를 확인하세요.")
