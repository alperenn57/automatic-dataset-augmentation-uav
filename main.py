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
        self.qtTasarim.pushButton.clicked.connect(self.Alperen)

    def Alperen(self):
        url = self.qtTasarim.lineEdit_2.text()
        model_yolu = self.qtTasarim.lineEdit.text()
        
        self.process_video(url, model_yolu)

    def process_video(self, url, model_yolu):
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
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_yolu)
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(frame_rate * 3)  # 3 saniye ileri sarma

        ss_yolu = "screenshots"
        label_yolu = "labels"
        os.makedirs(ss_yolu, exist_ok=True)
        os.makedirs(label_yolu, exist_ok=True)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            detections = results.pandas().xyxy[0]

            if not detections.empty:
                frame_count = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                frame_filename = os.path.join(ss_yolu, f'frame_{frame_count}.jpg')
                label_filename = os.path.join(label_yolu, f'frame_{frame_count}.txt')
                cv2.imwrite(frame_filename, frame)

                unique_labels = set()
                with open(label_filename, 'w') as label_file:
                    for _, row in detections.iterrows():
                        class_id = int(row['class'])
                        x_center = (row['xmin'] + row['xmax']) / 2 / frame.shape[1]
                        y_center = (row['ymin'] + row['ymax']) / 2 / frame.shape[0]
                        width = (row['xmax'] - row['xmin']) / frame.shape[1]
                        height = (row['ymax'] - row['ymin']) / frame.shape[0]

                        label_text = f"{class_id} {x_center} {y_center} {width} {height}\n"
                        if label_text not in unique_labels:
                            unique_labels.add(label_text)
                            label_file.write(label_text)

                print(f"Kaydedildi: {frame_filename} ve {label_filename}")

            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) + frame_interval)

        cap.release()
        cv2.destroyAllWindows()
        os.remove('temp_video.mp4')
        print("İşlem tamamlandı.")

        self.check_and_save_annotations(ss_yolu, label_yolu)

    def check_and_save_annotations(self, image_folder, annotation_folder):
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
                        boxes.append((class_id, x1, y1, x2, y2))
                return boxes

            boxes = read_yolo_annotation(annotation_path, img_width, img_height)

            for class_id, x1, y1, x2, y2 in boxes:
                color = (0, 255, 0)
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, f"Drone {class_id}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            cv2.imshow("Etiket Düzenleyici", img)

            while True:
                key = cv2.waitKey(0) & 0xFF
                if key == ord('s'):
                    print(f"Korundu: {image_file}")
                elif key == ord('r'):
                    os.remove(image_path)
                    if os.path.exists(annotation_path):
                        os.remove(annotation_path)
                    print(f"Silindi: {image_file}")
                elif key == ord('c'):
                    print("İşlemler durduruluyor.")
                    cv2.destroyAllWindows()
                    return
                break

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
