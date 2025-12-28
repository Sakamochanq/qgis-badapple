import cv2
import numpy as np


# QGIS環境チェック
try:
    from qgis.PyQt.QtCore import QTimer
    from qgis.core import (
        QgsProject,
        QgsVectorLayer,
        QgsFeature,
        QgsGeometry,
        QgsPointXY,
    )
    from qgis.utils import iface
    IN_QGIS = True
except ImportError:
    IN_QGIS = False

class VideoPlayer:
    # コンストラクタ
    def __init__(self, video_path, origin=(139.0, 35.0), scale=0.0001, threshold=128, fps=60):
        self.video_path = video_path
        self.origin = origin
        self.scale = scale
        self.threshold = threshold
        
        self.cap = None
        self.timer = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.video_fps = 60
        self.target_fps = fps
        
        self.line_layer = None
        self.point_layer = None
        
        self._init_video()
    
    # 動画の初期化
    def _init_video(self):
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if self.target_fps is None:
            self.target_fps = self.video_fps
        
        print(f"Video loaded: {self.width}x{self.height}, {self.total_frames} frames, {self.video_fps:.1f} FPS")