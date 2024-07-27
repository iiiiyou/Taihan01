import cv2
from ultralytics import YOLO

cap = cv2.VideoCapture(0)
model = YOLO("yolov8m.pt") 
# model = YOLO("best.pt") 

# Load the exported NCNN model
model = YOLO("./yolov8n_ncnn_model")


while True:
    ret, frame = cap.read()
    result = model(frame)[0]

    for box in result.boxes:
        class_id = result.names[box.cls[0].item()]
        if class_id == 'person':
            cords = box.xyxy[0].tolist()
            cords = [round(x) for x in cords]
            conf = round(box.conf[0].item(), 2)

            start = x1,y1 = cords[0:2]   
            end = x2,y2 = cords[2:4]  
            color = (255, 0, 0)
            image = cv2.rectangle(frame, start, end, color, 2)

            center = [int((x1 + x2)/2), int((y1 + y2)/2)]
            message = f"{class_id[0:7]}, xy:{center}, conf:{conf}"

            if conf > 0.8:
                image = cv2.putText(frame, message , (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1, cv2.LINE_AA)

            cv2.imshow('detected', image)

        # Press `q` to quit
        if cv2.waitKey(1) == ord("q"):
            cap.release()
            cv2.destroyAllWindows()


'''CLI
# Export a YOLOv8n PyTorch model to NCNN format
yolo export model=yolov8n.pt format=ncnn  # creates '/yolov8n_ncnn_model'

# Run inference with the exported model
yolo predict model='./yolov8n_ncnn_model' source='https://ultralytics.com/images/bus.jpg'
'''