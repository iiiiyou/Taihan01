import streamlit as st
import sqlite3
import pandas as pd
import os
from zipfile import ZipFile
from utils.style import load_css
import shutil
import numpy as np
import cv2

def brighten_image(image, brightness):
    """
    이미지의 밝기를 조정합니다.
    
    Parameters:
    -----------
    image : numpy.ndarray
        입력 이미지 (BGR 형식)
    brightness : int
        밝기 조정값 (-100 ~ 100)
        - 양수: 밝게
        - 음수: 어둡게
        - 0: 원본 유지
    
    Returns:
    --------
    numpy.ndarray
        밝기가 조정된 이미지
    """
    if image is None:
        return None
    
    # brightness가 0이면 원본 그대로 반환
    if brightness == 0:
        return image.copy()
    
    # 이미지를 0-1 범위로 정규화
    img_float = image.astype(np.float32) / 255.0
    
    # 밝기 조정: -100~100 -> 0.2~3.0 (곱셈 방식)
    if brightness > 0:
        brightness_factor = 1.0 + (brightness / 100.0) * 2.0  # 0~100 -> 1.0~3.0
    else:
        brightness_factor = 1.0 + (brightness / 100.0) * 0.8  # -100~0 -> 0.2~1.0
    
    img_float = img_float * brightness_factor
    
    # 0-1 범위로 클리핑하고 0-255로 변환
    img_float = np.clip(img_float, 0, 1)
    return (img_float * 255).astype(np.uint8)

def save_brightened_image(input_path, output_path, brightness):
    """
    이미지를 밝기 조절하여 저장합니다.
    
    Parameters:
    -----------
    input_path : str
        원본 이미지 경로
    output_path : str
        저장할 이미지 경로
    brightness : int
        밝기 조정값 (-100 ~ 100)
    
    Returns:
    --------
    bool
        성공 여부
    """
    if not os.path.exists(input_path):
        return False
    
    # 이미지 읽기
    img = cv2.imread(input_path)
    if img is None:
        return False
    
    # 밝기 조절
    if brightness != 0:
        img = brighten_image(img, brightness)
    
    # 출력 디렉토리가 없으면 생성
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 이미지 저장
    success = cv2.imwrite(output_path, img)
    return success
# CSS 스타일 정의
st.markdown("""
    <style>
    /* 타이틀 위의 공백 제거 */
    .main .block-container {
        padding-top: 0rem;  /* 여백을 줄이려면 값을 줄임 */
    }
    .block-container {
        padding-top: 2rem;
        margin-top: 0rem;
    }
    </style>
""", unsafe_allow_html=True)

# Streamlit UI
st.title("불량 검출 보고서 압축 파일 생성")

# 밝기 조절 슬라이더 추가
brightness = st.slider(
    "[순서1] 이미지 밝기 조절",
    min_value=-100,
    max_value=100,
    value=0,
    step=5,
    help="압축 파일에 포함될 이미지의 밝기를 조절합니다. -100(어둡게) ~ 100(밝게)"
)

selected_date = st.text_input("[순서2] 검출 일자 (YYYYMMDD):")
load_css()

if selected_date and len(selected_date) == 8 and selected_date.isdigit():
    # Query database
    conn = sqlite3.connect("C:/source/SQL/fiber.db")
    query = f'''SELECT
        s_time as "시작시간", 
        material_number as "제품번호", 
        seq2 as "순번", 
        d_meter as "감지거리", 
        type as "종류", 
        d_time as "감지시간", 
        image  
        FROM detection WHERE s_time LIKE '{selected_date}%'
        '''
    df = pd.read_sql_query(query, conn)
    df['image_2'] = df['image'].str.replace('/box/', '/Original/')
    conn.close()

    if df.empty:
        st.warning("No data found for the selected date.")
    else:
        # HTML generation
        html_filename = f"{selected_date}.htm"
        image_base_folder = "C:/image"
        zip_filename = f"{selected_date}_report.zip"

        html_content = "<html><head><title>검출보고서</title></head><body>"
        html_content += f"<h2>검출 일자: {selected_date}</h2><table border='1' cellspacing='0' cellpadding='5'>"
        html_content += "<tr>" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"
            
        for _, row in df.iterrows():
            html_content += "<tr>"
            for col in df.columns:
                if col == "image" or col == "image_2":  # 두 이미지 열 모두 처리
                    image_path = row[col]
                    image_name = os.path.basename(image_path)
                    # 폴더 구조 유지를 위해 상대 경로 사용
                    if 'box' in image_path:
                        rel_path = f"box/{image_name}"
                    else:
                        rel_path = f"Original/{image_name}"
                        
                    html_content += (
                        f"<td>"
                        f"<a href='{rel_path}' target='_blank'>"
                        f"<img src='{rel_path}' alt='thumbnail' width='100' height='100'>"
                        f"</a></td>"
                    )
                else:
                    html_content += f"<td>{row[col]}</td>"
            html_content += "</tr>"

        html_content += "</table></body></html>"

        # Save HTML file
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Create ZIP archive
        temp_image_folder = f"temp_{selected_date}"
        os.makedirs(temp_image_folder, exist_ok=True)
        
        with ZipFile(zip_filename, 'w') as zipf:
            zipf.write(html_filename)

            # C:/image 폴더에서 selected_date로 시작하는 모든 폴더 찾기
            if os.path.exists(image_base_folder):
                for folder_name in os.listdir(image_base_folder):
                    folder_path = os.path.join(image_base_folder, folder_name)
                    
                    # 폴더이면서 selected_date로 시작하는 경우
                    if os.path.isdir(folder_path) and folder_name.startswith(selected_date):
                        # 해당 폴더 안의 모든 파일과 하위 폴더를 ZIP에 추가
                        for root, dirs, files in os.walk(folder_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # 이미지 파일인 경우 밝기 조절 적용
                                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                                    # C:/image 기준 상대 경로 계산
                                    arcname = os.path.relpath(file_path, image_base_folder)
                                    
                                    # 임시 폴더에 밝기 조절된 이미지 저장
                                    temp_file_path = os.path.join(temp_image_folder, arcname)
                                    
                                    if save_brightened_image(file_path, temp_file_path, brightness):
                                        zipf.write(temp_file_path, arcname=arcname)
                                    else:
                                        # 밝기 조절 실패 시 원본 사용
                                        zipf.write(file_path, arcname=arcname)
                                else:
                                    # 이미지가 아닌 파일은 원본 그대로 추가
                                    arcname = os.path.relpath(file_path, image_base_folder)
                                    zipf.write(file_path, arcname=arcname)

        # 임시 파일 정리   
        os.remove(html_filename)
        
        # 임시 이미지 폴더 정리
        if os.path.exists(temp_image_folder):
            shutil.rmtree(temp_image_folder)

        # Download button
        with open(zip_filename, "rb") as f:
            st.download_button(
                label="[순서3] 내려받기",
                data=f,
                file_name=zip_filename,
                mime="application/zip"
            )
        
        # ZIP 파일도 정리 (다운로드 후)
        if os.path.exists(zip_filename):
            os.remove(zip_filename)

else:
    st.info("Please enter a valid date in YYYYMMDD format.")