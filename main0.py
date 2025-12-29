from arayuz import Ui_MainWindow
from PyQt5.QtWidgets import *
import sys
import cv2
import torch
import yt_dlp
import os
import shutil
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.qtTasarim = Ui_MainWindow()
        self.qtTasarim.setupUi(self)
        self.qtTasarim.pushButton.clicked.connect(self.start_processing)

    def start_processing(self):
        url = self.qtTasarim.lineEdit_2.text()
        model_path = self.qtTasarim.lineEdit.text()
        self.process_video(url, model_path)

    def process_video(self, url, model_path):
        ydl_opts = {
            'format': 'bestvideo[height<=720]',
            'quiet': True,
            'outtmpl': 'temp_video.mp4'
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"Video indirilemedi: {e}")
            return

        cap = cv2.VideoCapture('temp_video.mp4')
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(frame_rate * 3)  # 3 saniye aralıklarla

        ss_folder = "screenshots"
        label_folder = "labels"
        os.makedirs(ss_folder, exist_ok=True)
        os.makedirs(label_folder, exist_ok=True)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            detections = results.pandas().xyxy[0]

            if not detections.empty:
                frame_count = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                frame_file = os.path.join(ss_folder, f'frame_{frame_count}.jpg')
                label_file = os.path.join(label_folder, f'frame_{frame_count}.txt')
                cv2.imwrite(frame_file, frame)

                unique_labels = set()
                with open(label_file, 'w') as f:
                    for _, row in detections.iterrows():
                        class_id = int(row['class'])
                        x_center = (row['xmin'] + row['xmax']) / 2 / frame.shape[1]
                        y_center = (row['ymin'] + row['ymax']) / 2 / frame.shape[0]
                        width = (row['xmax'] - row['xmin']) / frame.shape[1]
                        height = (row['ymax'] - row['ymin']) / frame.shape[0]

                        label_text = f"{class_id} {x_center} {y_center} {width} {height}\n"
                        if label_text not in unique_labels:
                            unique_labels.add(label_text)
                            f.write(label_text)

                print(f"Kaydedildi: {frame_file} ve {label_file}")

            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) + frame_interval)

        cap.release()
        cv2.destroyAllWindows()
        os.remove('temp_video.mp4')
        print("Video işleme tamamlandı.")

        self.edit_annotations(ss_folder, label_folder)

    def edit_annotations(self, image_folder, annotation_folder):
        image_files = sorted([f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])

        for image_file in image_files:
            image_path = os.path.join(image_folder, image_file)
            annotation_path = os.path.join(annotation_folder, os.path.splitext(image_file)[0] + ".txt")

            img = cv2.imread(image_path)
            if img is None:
                print(f"Hata: {image_path} yüklenemedi!")
                continue

            img_height, img_width, _ = img.shape

            def read_yolo_annotation(anno_file, img_width, img_height):
                boxes = []
                if not os.path.exists(anno_file):
                    return boxes
                with open(anno_file, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        data = line.strip().split()
                        class_id = int(data[0])
                        x_center, y_center, width, height = map(float, data[1:])
                        x1 = int((x_center - width / 2) * img_width)
                        y1 = int((y_center - height / 2) * img_height)
                        x2 = int((x_center + width / 2) * img_width)
                        y2 = int((y_center + height / 2) * img_height)
                        boxes.append([class_id, x1, y1, x2, y2])
                return boxes

            model_boxes = read_yolo_annotation(annotation_path, img_width, img_height)
            clone = img.copy()
            current_boxes = model_boxes.copy()

            drawing = False
            ix, iy = -1, -1

            def draw_rectangle(event, x, y, flags, param):
                nonlocal ix, iy, drawing, current_boxes, clone
                if event == cv2.EVENT_LBUTTONDOWN:
                    drawing = True
                    ix, iy = x, y
                elif event == cv2.EVENT_MOUSEMOVE and drawing:
                    temp_img = clone.copy()
                    cv2.rectangle(temp_img, (ix, iy), (x, y), (0, 0, 255), 2)
                    cv2.imshow("Etiket Düzenleyici", temp_img)
                elif event == cv2.EVENT_LBUTTONUP:
                    drawing = False
                    x1, y1 = min(ix, x), min(iy, y)
                    x2, y2 = max(ix, x), max(iy, y)
                    class_id = 0  # Manuel etiket ID
                    current_boxes.append([class_id, x1, y1, x2, y2])
                    cv2.rectangle(clone, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.imshow("Etiket Düzenleyici", clone)

            cv2.namedWindow("Etiket Düzenleyici")
            cv2.setMouseCallback("Etiket Düzenleyici", draw_rectangle)

            while True:
                img_display = clone.copy()
                for class_id, x1, y1, x2, y2 in current_boxes:
                    color = (0, 255, 0) if [class_id, x1, y1, x2, y2] in model_boxes else (0, 0, 255)
                    cv2.rectangle(img_display, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(img_display, f"Drone {class_id}", (x1, y1 - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.imshow("Etiket Düzenleyici", img_display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('s'):
                    with open(annotation_path, 'w') as f:
                        for class_id, x1, y1, x2, y2 in current_boxes:
                            x_center = ((x1 + x2) / 2) / img_width
                            y_center = ((y1 + y2) / 2) / img_height
                            width = (x2 - x1) / img_width
                            height = (y2 - y1) / img_height
                            f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
                    print(f"Kaydedildi: {image_file}")
                    break
                elif key == ord('r'):
                    os.remove(image_path)
                    if os.path.exists(annotation_path):
                        os.remove(annotation_path)
                    print(f"Silindi: {image_file}")
                    break
                elif key == ord('z'):  # Model etiketlerini sil
                    current_boxes = [b for b in current_boxes if b not in model_boxes]
                    print("Model etiketleri silindi.")
                elif key == ord('c'):
                    print("İşlemler durduruluyor.")
                    cv2.destroyAllWindows()
                    return

            cv2.destroyAllWindows()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
