import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
from io import BytesIO
from datetime import date, datetime, timedelta
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
                d_meter,
                image
            FROM detection
            WHERE s_time BETWEEN ? AND ?
            ORDER BY s_time, seq2 DESC
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
    processed_data = output.getvalue()
    return processed_data

# Streamlit 앱
st.title("불량품 탐지 데이터 조회")

# 조회일자, 달력, Excel 다운로드 버튼을 타이틀 우측에 배치
col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

with col1:
    st.markdown("### 조회일자:")

with col2:
    start_date = st.date_input("조회 시작일", value=date.today(), label_visibility="collapsed")
    
    # 현재 세션 상태의 시작일자와 비교하여 변경이 있을 때만 이미지 초기화
    if 'last_start_date' not in st.session_state or st.session_state['last_start_date'] != start_date:
        st.session_state['image_url'] = None
        st.session_state['origin_image_url'] = None
        st.session_state['image_pk'] = None
        st.session_state['image_load_error'] = False
        st.session_state['last_start_date'] = start_date

# 날짜를 정수로 변환
end_date = start_date + timedelta(days=1)
start_date_int = int(start_date.strftime("%Y%m%d%H%M%S"))
end_date_int = int(end_date.strftime("%Y%m%d%H%M%S"))
start_date_str = start_date.strftime("%Y%m%d")
end_date_str = end_date.strftime("%Y%m%d")

# 폴더 경로 설정
folder_name = r"C:\source\sql"
db_folder = os.path.join(folder_name)  
image_folder = os.path.join(r"C:\image", start_date_str, "box")
origin_folder = os.path.join(r"C:\image", start_date_str, "original")

# 데이터 로드
rows, col_names = fetch_data(start_date_int, end_date_int, db_folder)
if rows:
    df = pd.DataFrame(rows, columns=col_names)
else:
    df = pd.DataFrame()

# Excel 다운로드 버튼
if not df.empty:
    excel_file = to_excel(df)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"data_{current_time}.xlsx"
    
    with col4:
        st.download_button(
            label="Excel 다운로드",
            data=excel_file,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# DataFrame과 관련된 스타일을 설정
st.markdown("""
    <style>
    .main .block-container {
        max-width: 85%;
        padding-left: 5%;
        padding-right: 5%;
    }
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
        color: blue.
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)

# 항목명 추가 (불량이미지 항목을 히든으로 처리)
column_names = ["시작시간", "순번", "유형", "제품번호", "넓이", "검출지점", "불량품이미지"]
header_cols = st.columns([6, 2, 3, 5, 3, 6, 17])  # 불량이미지 열 제외

for col, name in zip(header_cols, column_names):
    col.markdown(f"**{name}**")

# 데이터가 없으면 메시지 출력
if df.empty:
    st.warning("해당 기간에 데이터가 존재하지 않습니다.")
else:
    # 데이터 출력 및 버튼 추가 (불량이미지 열은 제외)
    for i, row in df.iterrows():
        cols = st.columns([6, 2, 3, 5, 3, 6, 17])  # 불량이미지 열 제외, 버튼 열 추가
        for col, val in zip(cols[:-1], row[:-1]):  # 불량이미지 데이터는 제외
            col.write(val)
        # 버튼 추가
        button_col = cols[-1]
        if button_col.button(f'이미지 보기 ({row["s_time"]} {row["seq2"]})', key=f'button_{i}'):
            try:
                image_path = os.path.join(image_folder, row["image"])
                origin_image_path = os.path.join(origin_folder, os.path.basename(row["image"]))
                
                st.session_state['image_url'] = image_path
                st.session_state['origin_image_url'] = origin_image_path
                st.session_state['image_pk'] = f'{row["s_time"]} {row["seq2"]}'
                st.session_state['image_load_error'] = False
            except Exception as e:
                st.session_state['image_load_error'] = True
                st.session_state['image_load_error_msg'] = "이미지 경로에 오류가 있습니다. 확인 후 다시 이용하시기 바랍니다!"

    st.markdown('</div>', unsafe_allow_html=True)

# 하단에 이미지를 표시하거나 숨깁니다.
with st.container():
    # 이미지가 클릭되었을 때만 이미지를 표시하도록 수정
    if st.session_state['image_url'] and st.session_state['origin_image_url'] and st.session_state['image_pk']:
        if st.session_state['image_load_error']:
            st.error(st.session_state['image_load_error_msg'])
        else:
            try:
                col1, col2 = st.columns(2)
                
                # 좌측에 기존 이미지 표시
                with col1:
                    if os.path.exists(st.session_state['image_url']):  # 파일 존재 확인
                        img = Image.open(st.session_state['image_url'])
                        st.image(img, caption=f"불량품이미지 (box)  {st.session_state['image_pk']}", use_column_width=True)
                    else:
                        st.error(f"이미지 파일이 존재하지 않습니다: {st.session_state['image_url']}")
                
                # 우측에 원본 이미지 표시
                with col2:
                    if os.path.exists(st.session_state['origin_image_url']):  # 파일 존재 확인
                        origin_img = Image.open(st.session_state['origin_image_url'])
                        st.image(origin_img, caption=f"원본이미지 (origin)  {st.session_state['image_pk']}", use_column_width=True)
                    else:
                        st.error(f"원본 이미지 파일이 존재하지 않습니다: {st.session_state['origin_image_url']}")

            except Exception as e:
                st.error("이미지를 로드하는 데 오류가 발생했습니다. 파일 경로를 확인하세요.")
    else:
        # 이미지가 클릭되지 않았거나 이미지 URL이 없는 경우에는 아무것도 표시하지 않음
        st.session_state['image_url'] = None
        st.session_state['origin_image_url'] = None
        st.session_state['image_pk'] = None
