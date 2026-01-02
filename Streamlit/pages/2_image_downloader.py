import streamlit as st
import sqlite3
import pandas as pd
import os
from zipfile import ZipFile
from utils.style import load_css
import shutil

# Streamlit UI
st.title("불량 검출 보고서 압축 파일 생성")
selected_date = st.text_input("검출 일자 (YYYYMMDD):")
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
                                # C:/image 기준 상대 경로 계산
                                arcname = os.path.relpath(file_path, image_base_folder)
                                zipf.write(file_path, arcname=arcname)

        # 임시 파일 정리   
        os.remove(html_filename)

        # Download button
        with open(zip_filename, "rb") as f:
            st.download_button(
                label="내려받기",
                data=f,
                file_name=zip_filename,
                mime="application/zip"
            )
        
        # ZIP 파일도 정리 (다운로드 후)
        if os.path.exists(zip_filename):
            os.remove(zip_filename)

else:
    st.info("Please enter a valid date in YYYYMMDD format.")