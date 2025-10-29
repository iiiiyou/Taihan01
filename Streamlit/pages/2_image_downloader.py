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
        image_folder = f"C:/image/{selected_date}"
        zip_filename = f"{selected_date}_report.zip"

        html_content = "<html><head><title>검출보고서</title></head><body>"
        html_content += f"<h2>검출 일자: {selected_date}</h2><table border='1' cellspacing='0' cellpadding='5'>"
        html_content += "<tr>" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"

        # for _, row in df.iterrows():
        #     html_content += "<tr>"
        #     for col in df.columns:
        #         if col == "image":
        #             image_path = row[col]
        #             image_name = os.path.basename(image_path)
        #             html_content += (
        #                 f"<td>"
        #                 f"<a href='{image_name}' target='_blank'>"
        #                 f"<img src='{image_name}' alt='thumbnail' width='100' height='100'>"
        #                 f"</a></td>"
        #             )
        #         else:
        #             html_content += f"<td>{row[col]}</td>"
        #     html_content += "</tr>"
            
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

            # # Add all images from C:/image/YYYYMMDD
            # for root, _, files in os.walk(image_folder):
            #     for file in files:
            #         file_path = os.path.join(root, file)
            #         arcname = os.path.relpath(file_path, image_folder)
            #         zipf.write(file_path, arcname=os.path.join(selected_date, arcname))

            # box 폴더의 이미지들 추가
            box_folder = os.path.join(image_folder, 'box')
            if os.path.exists(box_folder):
                for file in os.listdir(box_folder):
                    file_path = os.path.join(box_folder, file)
                    if os.path.isfile(file_path):
                        # ZIP 내부에 box/파일명 형태로 저장
                        zipf.write(file_path, arcname=f'box/{file}')
            
            # Original 폴더의 이미지들 추가
            original_folder = os.path.join(image_folder, 'Original')
            if os.path.exists(original_folder):
                for file in os.listdir(original_folder):
                    file_path = os.path.join(original_folder, file)
                    if os.path.isfile(file_path):
                        # ZIP 내부에 Original/파일명 형태로 저장
                        zipf.write(file_path, arcname=f'Original/{file}')

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