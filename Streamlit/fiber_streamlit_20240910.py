import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
from io import BytesIO
from datetime import date, timedelta, datetime
import os
import base64
import glob
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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
            SELECT a.s_time,
                   a.d_time,
                   a.seq2,
                   a.d_meter,
                   a.type,
                   CAST(a.material_number AS TEXT) AS material_number,
                   a.area || ' / ' || COALESCE(b.area, 1) || ' (' || ROUND((CAST(a.area AS REAL) / COALESCE(b.area, 1)) * 100, 2) || '%)' AS area,
                   FIRST_VALUE(a.image) OVER (PARTITION BY a.s_time, a.d_time, a.seq2, a.d_meter, a.type, a.material_number, a.area ORDER BY a.s_time DESC, a.seq2 DESC) AS image
              FROM detection AS a JOIN worklog AS b
                                    ON a.s_time = b.s_time
             WHERE a.s_time BETWEEN ? AND ?
             GROUP BY a.s_time, a.d_time, a.seq2, a.d_meter, a.type, a.material_number, a.area
             ORDER BY a.s_time DESC, a.seq2 DESC
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
    for col in df.select_dtypes([object]):
        df[col] = df[col].apply(lambda x: clean_string(str(x)))
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

def image_to_base64(image_path):
    """이미지를 base64 문자열로 변환"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# CSS 스타일 정의
st.markdown("""
    <style>
    .small-text {
        font-size: 14px; /* 텍스트 크기 */
        margin-top: -15px; /* 위쪽 공백 줄이기 */   
        margin-bottom: 0px; /* 아래쪽 공백 최소화 */
    }
    .small-title {
        font-size: 20px; /* 제목 텍스트 크기 */
        margin-top: -50px; /* 제목 위쪽 공백 최대한 줄이기 */
        margin-bottom: 10px; /* 제목 아래쪽 공백 최소화 */
        text-align: center; /* 가운데 정렬 */
    }
    .responsive-image {
        max-width: 100%;
        height: auto;
    }
    .image-container {
        text-align: center;
    }
    .caption {
        margin-top: 5px;
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# Streamlit 앱
st.markdown("<h2 class='small-title'>불량품 탐지 데이터 조회</h2>", unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6, col7 = st.columns([0.4, 1.0, 0.4, 1.0, 1.0, 0.5, 0.5])

with col1:
    st.markdown("<small class='small-text'>조회일자:</small>", unsafe_allow_html=True)

with col2:
    start_date = st.date_input("조회 시작일", value=date.today(), label_visibility="collapsed")

with col3:
    st.markdown("<small class='small-text'>유형 선택:</small>", unsafe_allow_html=True)

with col4:
    type_filter = st.selectbox("유형 선택", ["전체", "defect", "area"], index=0, label_visibility="collapsed")

end_date = start_date + timedelta(days=1)
start_date_int = int(start_date.strftime("%Y%m%d%H%M%S"))
end_date_int = int(end_date.strftime("%Y%m%d%H%M%S"))
start_date_str = start_date.strftime("%Y%m%d")

folder_name = r"C:\source\sql"
db_folder = os.path.join(folder_name)

rows, col_names = fetch_data(start_date_int, end_date_int, db_folder)
if rows:
    df = pd.DataFrame(rows, columns=col_names)
else:
    df = pd.DataFrame(columns=["s_time", "d_time", "seq2", "d_meter", "type", "material_number", "area", "image"])

with col6:
    st.markdown(
       f"<small class='small-text'>데이터 건수:</small>",
        unsafe_allow_html=True
    )

with col7:
    st.markdown(
    f"<small class='small-text'>{len(df)}</small>",
        unsafe_allow_html=True
    )

df.columns = ["불량검출시작시간", "불량검출시간", "순번", "발견지점", "유형", "제조번호", "넓이", "이미지"]

if type_filter == "defect":
    df = df[df["유형"] == "defect"]
elif type_filter == "area":
    df = df[df["유형"] == "area"]

if not df.empty:
    excel_file = to_excel(df)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"data_{current_time}.xlsx"
    
    with col5:
        st.download_button(
            label="Excel 다운로드",
            data=excel_file,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=True)
gb.configure_column("불량검출시작시간", width=130)
gb.configure_column("불량검출시간", width=130)
gb.configure_column("순번", width=30)
gb.configure_column("발견지점", width=80)
gb.configure_column("유형", width=50)
gb.configure_column("제조번호", width=120)
gb.configure_column("넓이", width=100)
gb.configure_column("이미지", width=150)

gb.configure_selection(selection_mode="single", use_checkbox=True)

grid_options = gb.build()

grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    height=400,
    theme='streamlit',
    enable_enterprise_modules=False,
    fit_columns_on_grid_load=True,
)

selected_row = grid_response['selected_rows'] if grid_response['selected_rows'] is not None else []

# 선택된 이미지의 이름과 경로를 확인하고 처리하는 부분 수정
with st.container():
    if len(selected_row) > 0:  # 선택된 행이 있는 경우에만 처리
        selected_data = pd.DataFrame(selected_row).iloc[0]  # 첫 번째 선택된 행 데이터
        
        # 유형에 따라 폴더 경로 설정
        if selected_data["유형"] == "defect":
            image_folder = os.path.join(r"C:\image", start_date_str, "box")
            origin_folder = os.path.join(r"C:\image", start_date_str, "original")
        elif selected_data["유형"] == "area":
            image_folder = os.path.join(r"C:\image", start_date_str, "area_box")
            origin_folder = os.path.join(r"C:\image", start_date_str, "area_original")
        else:
            image_folder = None
            origin_folder = None

        # 선택된 행에서 불량검출시간 값을 사용해 image_pk를 설정
        st.session_state['image_pk'] = selected_data["불량검출시간"]

        if image_folder:
            # 이미지 이름에서 경로를 제거하고 파일명만 추출
            image_filename = os.path.basename(selected_data['이미지'])  # 파일명만 추출

            # 선택된 이미지의 이름에서 숫자 부분을 제외한 공통 부분 추출 (예: "0_" 부분 제외)
            if image_filename.startswith(('0_', '1_', '2_')):
                image_base_name = image_filename[2:]  # 첫 두 글자(숫자 + _) 제거
            else:
                image_base_name = image_filename  # 숫자로 시작하지 않는 경우 원래 이름 사용

            # 0_, 1_, 2_로 시작하는 모든 이미지를 가져옴 (box 폴더에서)
            search_pattern = os.path.join(image_folder, f"[0-2]_{image_base_name}")

            image_paths = sorted(glob.glob(search_pattern))

            if image_paths:
                col1, col2, col3 = st.columns(3)  # 3개의 이미지를 표시하기 위한 칼럼 생성
                
                # 각 칼럼에 이미지를 하나씩 표시 (box 폴더의 이미지)
                for col, image_path in zip([col1, col2, col3], image_paths):
                    with col:
                        if os.path.exists(image_path):
                            img_base64 = image_to_base64(image_path)
                            st.markdown(
                                f'<div class="image-container">'
                                f'<img src="data:image/png;base64,{img_base64}" class="responsive-image" />'
                                f'<div class="caption">불량품이미지 ({selected_data["유형"]})  {os.path.basename(image_path)}</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                            
                            # original 폴더에서 동일한 이름의 이미지 찾기
                            original_image_path = os.path.join(origin_folder, os.path.basename(image_path))

                            if os.path.exists(original_image_path):
                                original_img_base64 = image_to_base64(original_image_path)
                                st.markdown(
                                    f'<div class="image-container">'
                                    f'<img src="data:image/png;base64,{original_img_base64}" class="responsive-image" />'
                                    f'<div class="caption">원본이미지 ({selected_data["유형"]})  {os.path.basename(original_image_path)}</div>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                            else:
                                st.error(f"원본 이미지 파일이 존재하지 않습니다: {original_image_path}")
                        else:
                            st.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
            else:
                # 0_, 1_, 2_로 시작하는 이미지가 없을 경우 기본 이미지명으로 검색
                search_pattern = os.path.join(image_folder, image_base_name)
                image_paths = sorted(glob.glob(search_pattern))

                if image_paths:
                    col1, col2, col3 = st.columns(3)  # 3개의 이미지를 표시하기 위한 칼럼 생성

                    # 각 칼럼에 이미지를 하나씩 표시 (box 폴더의 이미지)
                    for col, image_path in zip([col1, col2, col3], image_paths):
                        with col:
                            if os.path.exists(image_path):
                                img_base64 = image_to_base64(image_path)
                                st.markdown(
                                    f'<div class="image-container">'
                                    f'<img src="data:image/png;base64,{img_base64}" class="responsive-image" />'
                                    f'<div class="caption">불량품이미지 ({selected_data["유형"]})  {os.path.basename(image_path)}</div>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                                
                                # original 폴더에서 동일한 이름의 이미지 찾기
                                original_image_path = os.path.join(origin_folder, os.path.basename(image_path))

                                if os.path.exists(original_image_path):
                                    original_img_base64 = image_to_base64(original_image_path)
                                    st.markdown(
                                        f'<div class="image-container">'
                                        f'<img src="data:image/png;base64,{original_img_base64}" class="responsive-image" />'
                                        f'<div class="caption">원본이미지 ({selected_data["유형"]})  {os.path.basename(original_image_path)}</div>'
                                        f'</div>',
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.error(f"원본 이미지 파일이 존재하지 않습니다: {original_image_path}")
                            else:
                                st.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
                else:
                    st.error("기본 이미지 파일도 찾을 수 없습니다.")
    else:
        st.session_state['image_url'] = None
        st.session_state['origin_image_url'] = None
        st.session_state['image_pk'] = None 
