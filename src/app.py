import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from ultralytics import YOLO

class WasteClassificationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Waste Sorting")
        self.setGeometry(100, 100, 1280, 720)

        # Model yolu (yerel çalıştırma)
        self.model = YOLO('models/best.pt')

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera_frame)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #1e1e1e;")
        self.layout.addWidget(self.image_label, stretch=3)

        self.right_panel = QVBoxLayout()
        self.layout.addLayout(self.right_panel, stretch=1)

        self.result_box = QTextEdit(self)
        self.result_box.setReadOnly(True)
        self.result_box.setStyleSheet("background-color: #121212; color: #00ff66; font-size: 15px;")
        self.right_panel.addWidget(self.result_box)

        self.btn_select_image = QPushButton("Görüntü Seç", self)
        self.btn_select_image.clicked.connect(self.select_image)
        self.right_panel.addWidget(self.btn_select_image)

        self.btn_start_cam = QPushButton("Kamerayı Başlat", self)
        self.btn_start_cam.clicked.connect(self.start_camera)
        self.right_panel.addWidget(self.btn_start_cam)

        self.btn_stop_cam = QPushButton("Kamerayı Durdur", self)
        self.btn_stop_cam.clicked.connect(self.stop_camera)
        self.right_panel.addWidget(self.btn_stop_cam)

        self.btn_classify = QPushButton("Çek ve Sınıflandır", self)
        self.btn_classify.clicked.connect(self.capture_and_classify)
        self.right_panel.addWidget(self.btn_classify)

        self.current_frame = None

    def select_image(self):
        self.stop_camera()
        file_name, _ = QFileDialog.getOpenFileName(self, "Görüntü Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            frame = cv2.imread(file_name)
            self.current_frame = frame
            self.process_and_display(frame)

    def start_camera(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            self.timer.start(30)

    def stop_camera(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def update_camera_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            self.display_image(frame)

    def capture_and_classify(self):
        if self.current_frame is not None:
            self.process_and_display(self.current_frame)

    def process_and_display(self, frame):
        results = self.model.predict(frame)
        result = results[0]

        self.result_box.clear()
        if result.probs is not None:
            class_ids = result.probs.top5
            confidences = result.probs.top5conf

            for i, class_id in enumerate(class_ids):
                class_name = result.names[class_id]
                confidence = confidences[i].item()
                self.result_box.append(f"{class_name}: %{confidence*100:.1f}")

        self.display_image(frame)

    def display_image(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(self.image_label.size(), Qt.KeepAspectRatio)
        self.image_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WasteClassificationApp()
    window.show()
    sys.exit(app.exec_())
