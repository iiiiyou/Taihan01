import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
from io import BytesIO
from datetime import date, datetime, timedelta
import os
import base64
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# 페이지 설정
st.set_page_config(layout="wide")

def clean_string(s):
    return ''.join(i for i in s if ord(i) >= 32 and ord(i) < 127)

# @st.cache_data(ttl=60)
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
            SELECT distinct a.s_time,
                   a.d_time,
                   a.seq2,
                   a.d_meter,
                   a.type,
                   CAST(a.material_number AS TEXT) AS material_number,
                   a.area,--  || ' / ' || COALESCE(b.area, 1) || ' (' || ROUND((CAST(a.area AS REAL) / COALESCE(b.area, 1)) * 100, 2) || '%)' AS area,
                   image
             FROM detection AS a JOIN worklog AS b
                                 ON a.s_time = b.s_time
            WHERE a.s_time BETWEEN ? AND ?
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
    # 문자열 열의 불법 문자를 제거
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
st.title("불량품 탐지 데이터 조회")

# 좁은 간격을 위한 칼럼 설정
col1, col2, col3, col4, col5, col6, col7 = st.columns([0.4, 1.0, 0.4, 1.0, 1.0, 0.5, 0.5])

# 조회일자
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

# 유형 선택
with col3:
    st.markdown("### 유형 선택:")
with col4:
    type_filter = st.selectbox("유형 선택", ["전체", "defect", "area"], index=0, label_visibility="collapsed")
  
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

# 폴더 경로 설정
folder_name = r"C:\source\sql"
db_folder = os.path.join(folder_name)

# 데이터 로드
rows, col_names = fetch_data(start_date_int, end_date_int, db_folder)
if rows:
    df = pd.DataFrame(rows, columns=col_names)
else:
    df = pd.DataFrame(columns=["s_time", "d_time", "seq2", "d_meter", "type", "material_number", "area", "image"])  # 빈 데이터프레임에 기본 컬럼 추가

with col6:
    st.markdown(
        f"<h4 style='text-align: right; display: inline-block; padding-right: 10px;'>데이터 건수:</h4>",
        unsafe_allow_html=True
    )

with col7:
    st.markdown(
    f"<h4 style='text-align: right; display: inline-block;'>{len(df)}</h4>",
    unsafe_allow_html=True
    )

# 컬럼명을 변경
df.columns = ["불량검출시작시간", "불량검출시간", "순번", "발견지점", "유형", "제조번호", "넓이", "이미지"]

# 유형 필터링 적용
if type_filter == "defect":
    df = df[df["유형"] == "defect"]
elif type_filter == "area":
    df = df[df["유형"] == "area"]

# Excel 다운로드 버튼
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

# AgGrid 설정
gb = GridOptionsBuilder.from_dataframe(df)

# 기본 컬럼 설정
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=True)

# 컬럼 너비 설정
gb.configure_column("불량검출시작시간", width=130)
gb.configure_column("불량검출시간", width=130)
gb.configure_column("순번", width=30)
gb.configure_column("발견지점", width=80)
gb.configure_column("유형", width=50)
gb.configure_column("제조번호", width=120)
gb.configure_column("넓이", width=100)
gb.configure_column("이미지", width=150)

# 선택 모드 설정 (체크박스)
gb.configure_selection(selection_mode="single", use_checkbox=True)

grid_options = gb.build()

# AgGrid를 사용하여 데이터프레임 표시
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    height=400,
    theme='streamlit',
    enable_enterprise_modules=False,
    fit_columns_on_grid_load=True,
)

# 선택된 행 가져오기
selected_row = grid_response['selected_rows'] if grid_response['selected_rows'] is not None else []

# 하단에 이미지를 표시
# 하단에 이미지를 표시
# 하단에 이미지를 표시
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

        # 이미지 경로 설정
        st.session_state['image_url'] = os.path.join(image_folder, selected_data["이미지"]) if image_folder else None
        
        # st.session_state['image_url'] 값이 유효한지 확인
        if st.session_state['image_url']:
            # 경로에서 날짜 정보 추출하기 위해 슬래시 `/`로 분리
            split_image_url = st.session_state['image_url'].split("/")
            origin_folder = st.session_state['image_url'].replace("box", "original")

            # 분리한 경로에 충분한 요소가 있는지 확인
            if len(split_image_url) >= 4:  # 경로에서 네 번째 요소가 날짜라고 가정
                image_date_str = split_image_url[2]  # 세 번째 요소에 날짜
                image_box_folder = split_image_url[3]  # 세 번째 요소에 폴더값
                
                try:
                    image_date = datetime.strptime(image_date_str, "%Y%m%d")
                    #modified_image = selected_data['이미지'].replace('box', 'Original')
 
                    # 먼저 동일 날짜의 original 폴더에서 이미지 찾기
                    original_image_url = selected_data['이미지'].replace('box', 'Original')

                    # 동일 날짜의 original 폴더에 이미지가 있는지 확인
                    image_base_path = os.path.join(origin_folder, f"{original_image_url.split('.')[0]}")  # 기본 경로 설정

                    if (os.path.exists(f"{image_base_path.split('.')[0]}-0.jpg") or
                        os.path.exists(f"{image_base_path.split('.')[0]}-1.jpg") or
                        os.path.exists(f"{image_base_path.split('.')[0]}-2.jpg")):
                        #st.write(f"Process: 1") 
                        # 이미지가 있는 경우 해당 경로 저장
                        st.session_state['origin_image_url'] = original_image_url
                    else:
                        # 동일 날짜에 이미지가 없는 경우 하루 전 날짜로 변경
                        previous_date = image_date - timedelta(days=1)
                        previous_date_str = previous_date.strftime("%Y%m%d")

                        # 하루 전 날짜의 original 폴더 경로 생성
                        previous_image_base_path = os.path.join(origin_folder, selected_data['이미지'].replace('box', 'Original').replace(image_date_str, previous_date_str))
                        
                        #st.write(f"Process: 2")   
                        # 하루 전 날짜의 original 폴더에 이미지가 있는지 확인
                        if (os.path.exists(f"{previous_image_base_path.split('.')[0]}-0.jpg") or
                            os.path.exists(f"{previous_image_base_path.split('.')[0]}-1.jpg") or
                            os.path.exists(f"{previous_image_base_path.split('.')[0]}-2.jpg")):
                            #st.write(f"Process: 3") 
                            
                            # 하루 전 날짜 이미지가 있는 경우 해당 경로 저장
                            st.session_state['origin_image_url'] = previous_image_base_path
                        else:
                            # 이미지가 없는 경우 None 설정
                            st.session_state['origin_image_url'] = None
                            #st.write(f"Process: 4")  
 
                    #st.write(f"original_image_url: {original_image_url}")
                    #st.write(f"original_image_url: {st.session_state['origin_image_url'] }")
                                                                               
                    # 먼저 동일 날짜의 original 폴더에서 이미지 찾기
                    if st.session_state['origin_image_url']:
                        original_image_urls = [
                        os.path.join(origin_folder, f"{st.session_state['origin_image_url'].split('.')[0]}-0.jpg"),
                        os.path.join(origin_folder, f"{st.session_state['origin_image_url'].split('.')[0]}-1.jpg"),
                        os.path.join(origin_folder, f"{st.session_state['origin_image_url'].split('.')[0]}-2.jpg"),
                    ]
                    else:
                        st.error("원본 이미지 파일이 존재하지 않습니다")
                        
                except ValueError as e:
                    st.error(f"날짜 변환 오류: {e}")
            else:
                st.error("경로에 날짜 정보를 찾을 수 없습니다.")

        st.session_state['image_pk'] = f'{selected_data["불량검출시간"]}'

        # 이미지 크기 조정 및 표시
        if st.session_state['image_url']:
            col1, col2, col3, col4 = st.columns(4)  # 4개의 컬럼 생성
            
            with col1:
                if os.path.exists(st.session_state['image_url']):
                    img_base64 = image_to_base64(st.session_state['image_url'])
                    st.markdown(
                        f'<div class="image-container">'
                        f'<img src="data:image/png;base64,{img_base64}" class="responsive-image" />'
                        f'<div class="caption">box</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.error(f"이미지 파일이 존재하지 않습니다: {st.session_state['image_url']}")

            for i in range(3):
                with [col2, col3, col4][i]:  # 두 번째, 세 번째, 네 번째 컬럼 사용
                    if st.session_state['origin_image_url']:
                        if original_image_urls[i] and os.path.exists(original_image_urls[i]):
                            origin_img_base64 = image_to_base64(original_image_urls[i])
                            st.markdown(
                                f'<div class="image-container">'
                                f'<img src="data:image/png;base64,{origin_img_base64}" class="responsive-image" />'
                                f'<div class="caption">camera-{i}</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.error(f"원본 이미지 파일이 존재하지 않습니다: {original_image_urls[i]}")
                    else:
                        st.error("원본 이미지 파일이 존재하지 않습니다.")
    else:
        # 이미지가 선택되지 않은 경우 아무것도 표시하지 않음
        st.session_state['image_url'] = None
        st.session_state['origin_image_urls'] = []
        st.session_state['image_pk'] = None