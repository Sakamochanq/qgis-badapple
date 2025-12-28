import cv2
import numpy as np


# 再生する動画のFPS設定
SET_VIDEO_FPS = 60

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
    def __init__(self, video_path, origin=(139.0, 35.0), scale=0.0001, threshold=128, fps=SET_VIDEO_FPS):
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
        



 # フレームをラインとポイントに変換
    def frame_to_lines_and_points(self, frame):
        # グレースケール変換
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # 二値化
        binary = (gray < self.threshold).astype(np.uint8)
        height, width = binary.shape
        
        lines = []
        points = []
        
        # 各行をスキャン
        for row in range(height):
            line_start = None
            for col in range(width):
                if binary[row, col] == 1:
                    if line_start is None:
                        line_start = col
                else:
                    if line_start is not None:
                        y = self.origin[1] + (height - row) * self.scale
                        x1 = self.origin[0] + line_start * self.scale
                        x2 = self.origin[0] + col * self.scale
                        
                        if col - line_start == 1:
                            points.append((x1, y))
                        else:
                            lines.append([(x1, y), (x2, y)])
                        line_start = None
            
            if line_start is not None:
                y = self.origin[1] + (height - row) * self.scale
                x1 = self.origin[0] + line_start * self.scale
                x2 = self.origin[0] + width * self.scale
                
                if width - line_start == 1:
                    points.append((x1, y))
                else:
                    lines.append([(x1, y), (x2, y)])
        
        return lines, points
    
    
    # レイヤーの更新
    def update_layers(self, lines, points):
        # ラインレイヤーの更新
        if self.line_layer is None or not self.line_layer.isValid():
            self.line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "Video_Lines", "memory")
            QgsProject.instance().addMapLayer(self.line_layer)
        
        self.line_layer.startEditing()
        self.line_layer.deleteFeatures([f.id() for f in self.line_layer.getFeatures()])
        
        for line_pts in lines:
            if len(line_pts) >= 2:
                feature = QgsFeature()
                qgs_points = [QgsPointXY(p[0], p[1]) for p in line_pts]
                feature.setGeometry(QgsGeometry.fromPolylineXY(qgs_points))
                self.line_layer.addFeature(feature)
        
        self.line_layer.commitChanges()
        
        # ポイントレイヤーの更新
        if self.point_layer is None or not self.point_layer.isValid():
            self.point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "Video_Points", "memory")
            QgsProject.instance().addMapLayer(self.point_layer)
        
        self.point_layer.startEditing()
        self.point_layer.deleteFeatures([f.id() for f in self.point_layer.getFeatures()])
        
        for pt in points:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(pt[0], pt[1])))
            self.point_layer.addFeature(feature)
        
        self.point_layer.commitChanges()
        
        # キャンバス全体を更新
        self.line_layer.triggerRepaint()
        self.point_layer.triggerRepaint()
        iface.mapCanvas().refresh()
        
# ---------------- ここからコントローラー 部分 ----------------

    # FPS設定
    # def set_fps(self, fps):
    #     self.target_fps = fps
    #     if self.is_playing and self.timer:
    #         interval = int(1000 / self.target_fps)
    #         self.timer.setInterval(interval)
    #     print(f"FPS set to {fps}")
    
        
    # 指定したフレームにシーク
    def seek(self, frame_number):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self.current_frame = frame_number
        
        # 1フレーム表示
        ret, frame = self.cap.read()
        if ret:
            lines, points = self._frame_to_lines_and_points(frame)
            self._update_layers(lines, points)
        print(f"Seeked to frame {frame_number}")
    
    # 再生
    def play(self):
        if not IN_QGIS:
            print("QGIS environment required")
            return
        
        if self.is_playing:
            return
        
        self.is_playing = True
        
        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(self._on_timer)
        
        interval = int(1000 / self.target_fps)
        self.timer.start(interval)
        print(f"Playing at {self.target_fps:.1f} FPS (interval: {interval}ms)")

    # 一時停止
    def pause(self):
        self.is_playing = False
        if self.timer:
            self.timer.stop()
        print("Paused")
    
    # 終了
    def stop(self):
        self.is_playing = False
        if self.timer:
            self.timer.stop()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.current_frame = 0
        print("Stopped")
        
    #  キャンバス全体のクリーンアップ
    def cleanup(self):
        self.stop()
        if self.cap:
            self.cap.release()
        
        # レイヤー削除
        project = QgsProject.instance()
        if self.line_layer and self.line_layer.id() in project.mapLayers():
            project.removeMapLayer(self.line_layer.id())
        if self.point_layer and self.point_layer.id() in project.mapLayers():
            project.removeMapLayer(self.point_layer.id())
        print("Cleaned up")
