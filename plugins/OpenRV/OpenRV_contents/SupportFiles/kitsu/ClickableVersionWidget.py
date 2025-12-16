import os
import numpy as np
import OpenEXR, Imath
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide2.QtCore import Qt, Signal, QThread, QObject, QSize
from PySide2.QtGui import QPixmap, QImage, QPainter, QPainterPath

class ExrLoaderWorker(QObject):
    finished = Signal(QPixmap)
    failed = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            exr_file = OpenEXR.InputFile(self.path)
            header = exr_file.header()
            dw = header['dataWindow']
            width = dw.max.x - dw.min.x + 1
            height = dw.max.y - dw.min.y + 1

            channels = ['R', 'G', 'B']
            pt = Imath.PixelType(Imath.PixelType.FLOAT)

            r = np.frombuffer(exr_file.channel('R', pt), dtype=np.float32).reshape((height, width))
            g = np.frombuffer(exr_file.channel('G', pt), dtype=np.float32).reshape((height, width))
            b = np.frombuffer(exr_file.channel('B', pt), dtype=np.float32).reshape((height, width))

            img = np.dstack((r, g, b))
            img = np.clip(img, 0.0, 1.0) * 255.0
            img = img.astype(np.uint8)

            h, w, ch = img.shape
            qimage = QImage(img.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            self.finished.emit(pixmap)
        except Exception as e:
            self.failed.emit(str(e))



class ClickableVersionWidget(QWidget):
    doubleClicked = Signal(str)

    def __init__(self, file_path, image_path=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.version_name = os.path.basename(file_path)

        self.setFixedSize(160, 90)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Thumbnail placeholder
        self.image_label = QLabel("Loading...")
        self.image_label.setFixedSize(160, 90)
        self.image_label.setScaledContents(True)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #000; color: white; border-radius: 10px;")

        if image_path:
            if image_path.lower().endswith(".exr"):
                self.load_exr_async(image_path)
            else:
                pixmap = QPixmap(image_path)
                self.image_label.setPixmap(self.get_rounded_pixmap(pixmap, 200))

        # Info text
        label_name = f'{os.path.basename(image_path).split(".")[0] if image_path else ""}\n{self.version_name}\n{self.file_path}'
        self.text_label = QLabel(label_name)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("background-color: rgba(0,0,0,128); color: white; padding: 5px; border-radius: 200px;")
        self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout.addWidget(self.image_label)
        layout.addWidget(self.text_label, alignment=Qt.AlignTop)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.file_path)

    def load_exr_async(self, path):
        """Run EXR loading in another thread"""
        self.thread = QThread()
        self.worker = ExrLoaderWorker(path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_exr_loaded)
        self.worker.failed.connect(self.on_exr_failed)

        # Cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.failed.connect(self.thread.quit)
        self.worker.failed.connect(self.worker.deleteLater)

        self.thread.start()

    def on_exr_loaded(self, pixmap):
        self.image_label.setPixmap(self.get_rounded_pixmap(pixmap, 200))

    def on_exr_failed(self, error):
        self.image_label.setText(f"Failed: {error}")

    def get_rounded_pixmap(self, pixmap, target_size, radius=None):
        """
        Return a pixmap scaled to `target_size` with rounded corners.
        target_size can be:
        - QSize
        - (width, height) tuple
        - int (width, height will match pixmap aspect ratio)
        """
        if pixmap.isNull():
            return pixmap

        # Convert int or tuple to QSize
        if isinstance(target_size, int):
            w = target_size
            h = int(w * pixmap.height() / pixmap.width())
            target_size = QSize(w, h)
        elif isinstance(target_size, tuple):
            target_size = QSize(*target_size)

        if radius is None:
            radius = min(target_size.width(), target_size.height()) // 10

        scaled_pixmap = pixmap.scaled(
            target_size,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        rounded = QPixmap(target_size)
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, target_size.width(), target_size.height(), radius, radius)
        painter.setClipPath(path)

        x_offset = (target_size.width() - scaled_pixmap.width()) // 2
        y_offset = (target_size.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        painter.end()

        return rounded
