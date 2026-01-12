import sys
import os
import importlib.util

# プロジェクトのパスをsys.pathに追加（exec()対応）
PROJECT_ROOT = r'<YourProjectPath>'
PROJECT_DIR = os.path.join(PROJECT_ROOT, 'src')

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# .venvのsite-packagesをパスに追加（QGISがパッケージを見つけられるように）
VENV_SITE_PACKAGES = os.path.join(PROJECT_ROOT, '.venv', 'Lib', 'site-packages')
if os.path.exists(VENV_SITE_PACKAGES) and VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

# VideoPlayerモジュールを直接ロード
video_player_path = os.path.join(PROJECT_DIR, 'utils', 'VideoPlayer.py')
spec = importlib.util.spec_from_file_location("VideoPlayer", video_player_path)
VideoPlayerModule = importlib.util.module_from_spec(spec)
sys.modules["VideoPlayer"] = VideoPlayerModule
spec.loader.exec_module(VideoPlayerModule)

VideoPlayer = VideoPlayerModule.VideoPlayer
set_video = VideoPlayerModule.set_video

# QGIS環境チェック
try:
    from qgis.PyQt.QtWidgets import QMessageBox
    IN_QGIS = True
except ImportError:
    from PyQt5.QtWidgets import QMessageBox, QApplication
    IN_QGIS = False

print("qgis-badapple Project Loaded.")

if __name__ == "__main__" and not IN_QGIS:
    app = QApplication(sys.argv)
    
    # アプリケーションの実行
    sys.exit(app.exec_())
