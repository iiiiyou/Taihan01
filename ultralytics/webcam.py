import cv2
from ultralytics import YOLO
import supervision as sv
import numpy as np

def main():
    frame_width, frame_height = [1280, 720]

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    # cap2 = cv2.VideoCapture(1)
    # cap2.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    # cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    # cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    model = YOLO("yolov8m.pt")
    # model = YOLO("hardhat.pt")
    

    box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_thickness=2,
        text_scale=1
    )

    while True:
        ret, frame = cap.read()
        # ret, frame2 = cap2.read()

        result = model(frame, agnostic_nms=True)[0]
        detections = sv.Detections.from_yolov8(result)

        # result2 = model(frame2, agnostic_nms=True)[0]
        # detections2 = sv.Detections.from_yolov8(result2)

        labels = [f"{model.model.names[class_id]} {confidence:0.2f}" for _, _, confidence, class_id, _ in detections]
        # labels2 = [f"{model.model.names[class_id]} {confidence:0.2f}" for _, _, confidence, class_id, _ in detections2]

        frame = box_annotator.annotate(
            scene=frame, 
            detections=detections, 
            labels=labels
        )

        # frame2 = box_annotator.annotate(
        #     scene=frame2, 
        #     detections=detections2, 
        #     labels=labels2
        # )

        # for _, _, confidence, class_id, _ in detections:
        #    if confidence > 0.8:
        #     labels = [f"{model.model.names[class_id]} {confidence:0.2f}"]

        #     frame = box_annotator.annotate(
        #         scene=frame, 
        #         detections=detections, 
        #         labels=labels
        #     )
            
        cv2.imshow("detected", frame)
        # cv2.imshow("detected2", frame2)

        if (cv2.waitKey(30) == ord('q')):  
            break


if __name__ == "__main__":
    main()