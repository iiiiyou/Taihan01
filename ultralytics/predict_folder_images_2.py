from ultralytics import YOLO
import os
from PIL import Image, ImageDraw, ImageFont # ImageFont 를 import 합니다.

# --- 모델 로드 ---
model = YOLO('C:/source/models/taihanfiber_18-1_20250725_yolo11s-seg_best.pt')

# --- 이미지 파일 경로 리스트 ---
image_folder = 'C:/image/20250721/Original'  # 이미지 폴더 경로 지정
image_files = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png', '.jpeg'))]

# --- 폰트 설정 ---
try:
    # <<<<<<< 이 부분을 수정하세요 >>>>>>>>>
    # 사용할 폰트 파일 경로 (예: Windows의 경우)
    # 시스템에 설치된 다른 ttf 폰트 파일 경로로 변경 가능 (예: 'malgun.ttf' for 맑은 고딕)
    font_path = "C:/Windows/Fonts/arial.ttf"
    # 원하는 폰트 크기 설정
    font_size = 20  # <<<<<<< 원하는 크기로 조절하세요 (기존보다 크게)
    font = ImageFont.truetype(font_path, font_size)
except IOError:
    print(f"지정한 폰트 파일을 찾을 수 없습니다 ({font_path}). 기본 폰트를 사용합니다.")
    # 기본 폰트 로드 (크기 조절이 제한적일 수 있음)
    font_size = 15 # 기본 폰트는 크기 지정이 다를 수 있으므로 예시 크기 설정
    font = ImageFont.load_default()

# --- 결과 처리 ---
output_folder = 'C:/temp/20250721_original/output1'
os.makedirs(output_folder, exist_ok=True) # 결과 저장 폴더 생성 (없으면)


for image_path in image_files:
    # 이미지를 열고 RGB로 변환
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # 해당 이미지에 대해 YOLO 모델로 예측 수행
    result = model(image_path)
    save_flag = False  # conf 0.5 이상 박스가 있으면 True로 변경

    # 예측 결과의 각 바운딩 박스에 대해 반복
    for box in result[0].boxes:
        xyxy = box.xyxy[0].tolist()  # 바운딩 박스 좌표 추출
        x1, y1, x2, y2 = map(int, xyxy)
        draw.rectangle((x1, y1, x2, y2), outline="red", width=2)  # 빨간색 테두리 박스 그림

        # 클래스 및 신뢰도 정보 추출
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        name = model.names[cls]
        text = f"{name}: {conf:.2f}"  # 박스 위에 표시할 텍스트 생성

        # 텍스트 위치 계산 (박스 위, 이미지 밖이면 박스 아래)
        text_y_position = y1 - font_size - 5
        if text_y_position < 0:
            text_y_position = y1 + 5
        draw.text((x1, text_y_position), text, fill="red", font=font)  # 텍스트 그림

        # 터미널에 예측 결과 출력
        print(f"Image: {image_path}, Class: {name}, Confidence: {conf}")

        # conf가 0.5 이상인 박스가 하나라도 있으면 저장 플래그 설정
        if conf >= 0.5:
            save_flag = True

    # conf 0.5 이상 박스가 있으면 결과 이미지 저장
    if save_flag:
        output_path = os.path.join(output_folder, f'{os.path.basename(image_path)}_output.jpg')
        image.save(output_path)
        print(f"Processed: {image_path}")

print("\n모든 이미지 처리 완료.")
# print(f"결과 이미지는 {output_folder} 에 저장되었습니다.") # 저장 활성화 시 주석 해제