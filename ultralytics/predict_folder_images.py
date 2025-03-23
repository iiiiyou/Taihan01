from ultralytics import YOLO
import os
from PIL import Image, ImageDraw

# 모델 로드

model = YOLO('C:/source/models/taihanfiber_12-1_20250309_yolo11m-seg_best.pt')

# 이미지 파일 경로 리스트
image_folder = 'C:/temp/20250317_original/original'  # 이미지 폴더 경로 지정
image_files = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png', '.jpeg'))]

# 예측 실행
results = model(image_files)

# 결과 처리
for i, result in enumerate(results):
    image_path = image_files[i]
    image = Image.open(image_path).convert("RGB")  # RGB 이미지로 변환
    draw = ImageDraw.Draw(image)

    # 바운딩 박스 그리기
    for box in result.boxes:
        xyxy = box.xyxy[0].tolist()  # 바운딩 박스 좌표
        x1, y1, x2, y2 = map(int, xyxy)
        draw.rectangle((x1, y1, x2, y2), outline="red", width=2)  # 빨간색 테두리

        # 클래스 및 확률 정보
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        name = model.names[cls]

        # 텍스트 추가
        text = f"{name}: {conf:.2f}"
        draw.text((x1, y1 - 10), text, fill="red")  # 빨간색 텍스트
        
        # 이미지에 바운딩 박스, 클래스, 확률 정보 추가
        # (OpenCV 등의 라이브러리를 사용하여 이미지에 직접 그릴 수 있습니다.)
        print(f"Image: {image_path}, Class: {name}, Confidence: {conf}")

    # 결과 이미지 저장 (선택 사항)
    output_path = f'C:/temp/20250317_original/output/{os.path.basename(image_path)}_output.jpg'
    # image.save(output_path)