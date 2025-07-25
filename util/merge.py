import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
import sys
import logging
sys.path.append('C:/source')
import util.format_date_time as date

# 로거 설정 - 파일과 콘솔에 다른 형식으로 로그 기록 (날짜별 파일 생성)
from datetime import datetime
current_date = datetime.now().strftime("%Y%m%d")
log_file_path = f"C:/source/log/merge_error_{current_date}.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# 로거 생성
logger = logging.getLogger('merge_logger')
logger.setLevel(logging.ERROR)

# 파일 핸들러 (자세한 정보)
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 콘솔 핸들러 (간단한 시간만)
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(console_formatter)

# 핸들러 추가
logger.addHandler(file_handler)
logger.addHandler(console_handler)

files = os.listdir()

jpg_files = []
fileapth = "C:/source/util/"
# files = os.listdir(fileapth)
# for file in files:
#     if file.endswith(".jpg") or file.endswith(".JPG"):
#         jpg_files.append(fileapth+file)


def merge(imgs, channel):
    try:
        # 입력 검증
        if not imgs or len(imgs) == 0:
            logger.error("입력 이미지가 없습니다")
            if channel == 2:
                return np.zeros((213, 640), dtype=np.uint8)
            elif channel == 3:
                return np.zeros((213, 640, 3), dtype=np.uint8)
            else:
                return np.zeros((213, 640), dtype=np.uint8)
        
        if channel is None:
            logger.error("채널 정보가 없습니다")
            return np.zeros((213, 640, 3), dtype=np.uint8)
        
        images = []
        stacked_image = None  # 초기값 설정
        
        if channel == 2:    # 2차원 ndarray 로 진행할 경우
            for file in imgs:
                # img = cv2.imread(file, cv2.IMREAD_GRAYSCALE) # 이미지 파일을 2차원 흑백이미지로 가져오기
                img = cv2.cvtColor(file, cv2.COLOR_BGR2GRAY) # 3차원 이미지를 2차원 ndarry중 흑백이미지로 변환하는 방법
                height, width = img.shape

                # Calculate crop dimensions
                # crop_height = 213
                crop_start = 214
                crop_end = 427
                
                cropped_img = img[crop_start:crop_end, :] # Crop the image
                images.append(cropped_img)

            padding = [0] *640
            images.append(padding) # 2차원

            # Stack the images vertically
            stacked_image = np.vstack(images)

        elif channel == 3:    # 3차원 ndarray 로 진행할 경우
            for file in imgs:
                height, width, ch = file.shape

                # Calculate crop dimensions
                # crop_height = 213
                crop_start = 214
                crop_end = 427
                
                cropped_img = file[crop_start:crop_end, :]   # Crop the image
                images.append(cropped_img)

            black_line = np.zeros((1, 640, 3), np.uint8)
            images.append(black_line)   # 3차원

            # Stack the images vertically
            stacked_image = np.concatenate(images, axis=0)
        
        else:
            logger.error(f"지원하지 않는 채널입니다: {channel}")
            return np.zeros((213, 640, 3), dtype=np.uint8)

        # 최종 검증
        if stacked_image is None:
            logger.error("이미지 처리 중 오류가 발생했습니다")
            if channel == 2:
                return np.zeros((213, 640), dtype=np.uint8)
            else:
                return np.zeros((213, 640, 3), dtype=np.uint8)

        # plt.imshow(stacked_image, cmap='gray')
        # stacked_image.shape

        # Save the stacked image
        # cv2.imwrite(fileapth+"stacked_image_"+str(channel)+"_"+date.get_time_millisec()+".jpg", stacked_image)

        # img = cv2.imread(fileapth+'stacked_image.jpg',0)
        # plt.imshow(img, cmap='gray')
        # height, width = img.shape
        return stacked_image        # img = cv2.imread(fileapth+'stacked_image.jpg',0)
        # plt.imshow(img, cmap='gray')
        # height, width = img.shape
        return stacked_image
    
    except Exception as e:
        # 오류 로그 기록
        logger.error(f"merge 함수에서 오류 발생: {str(e)}, 입력 이미지 수: {len(imgs) if imgs else 0}, 채널: {channel}")
        
        # 기본 빈 이미지 반환 (GUI 프로그램이 계속 동작할 수 있도록)
        if channel == 2:
            return np.zeros((213, 640), dtype=np.uint8)  # 2차원 빈 이미지
        elif channel == 3:
            return np.zeros((213, 640, 3), dtype=np.uint8)  # 3차원 빈 이미지
        else:
            return np.zeros((213, 640), dtype=np.uint8)  # 기본값
