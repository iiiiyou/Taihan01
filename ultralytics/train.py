from ultralytics import YOLO
import os
import shutil

from roboflow import Roboflow

dataset_name = "taihanfiber_3-2"
if not os.path.exists("datasets/"+dataset_name):

    rf = Roboflow(api_key="bxW7hooY5jiknZS3GIxI")
    project = rf.workspace("i4umaket").project("taihanfiber_3")
    version = project.version(2)
    dataset = version.download("yolov8")

    shutil.move(dataset_name, "datasets/"+dataset_name)

# 모델을 로드하세요..
model = YOLO('yolov8s-seg.yaml')  # YAML에서 새 모델 구축
model = YOLO('yolov8s-seg.pt')  # 사전 훈련된 모델 로드 (훈련을 위해 권장됨)
# model = YOLO('yolov8m.yaml').load('yolov8n.pt')  # YAML에서 구축 및 가중치 전달


# 모델을 훈련합니다.

if __name__ == '__main__':
    print("training start")
    # data.yaml안에 있는 경로 기본 설정 "C:\Users\<user>\AppData\Roaming\Ultralytics\settings.yaml"
    # datasets_dir: C:\workspace\maketek "in settings.yaml"
    results = model.train(data="datasets/"+dataset_name+"/data.yaml", epochs=300, imgsz=640, workers=0)

    # data.yaml 안의 image파일 경로
    # test: test/images
    # train: train/images
    # val: valid/images 