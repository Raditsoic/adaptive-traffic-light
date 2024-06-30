from ultralytics import YOLO
import cv2

model = YOLO('yolov8l.pt')

conf_threshold = 0.1

target_classes = ['motorcycle', 'car', 'truck', 'bus']

def detect_vehicles_and_calculate_duration(image):
    results = model(image, conf=conf_threshold)

    object_count = 0
    for r in results:
        boxes = r.boxes

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if conf >= conf_threshold and model.names[cls] in target_classes:
                object_count += 1

                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                label = f'{model.names[cls]} {conf:.2f}'
                cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Calculate green light duration
    base_duration = 10  
    time_per_vehicle = 1  
    green_light_duration = base_duration + (object_count * time_per_vehicle)

    cv2.putText(image, f'Total vehicles: {object_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(image, f'Green light: {green_light_duration}s', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    return image, green_light_duration