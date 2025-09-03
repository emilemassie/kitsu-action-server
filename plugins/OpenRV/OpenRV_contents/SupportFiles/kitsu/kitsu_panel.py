import os
import re
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QDockWidget, QApplication, QMainWindow
from PySide2.QtGui import QPixmap
from PySide2.QtCore import Qt, Signal, QThread, QObject, QFile

from rv import rvtypes, commands
import gazu
from flow_layout import FlowLayout


def try_gazu_connection():
    try:
        gazu.client.set_host(os.getenv('KITSU_HOST') + "/api")
        gazu.log_in("emile.massie@gmail.com", "emile220")
        print("Connected to Kitsu")
        return True
    except Exception as e:
        print(e)
        return False


class ClickableVersionWidget(QWidget):
    doubleClicked = Signal(str)

    def __init__(self, file_path, image_path=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.version_name = os.path.basename(file_path)

        self.setFixedSize(160, 90)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Thumbnail
        self.image_label = QLabel()
        self.image_label.setFixedSize(160, 90)
        self.image_label.setScaledContents(True)
        if image_path:
            self.image_label.setPixmap(QPixmap(image_path))

        # Info text
        label_name = f'{os.path.basename(image_path).split(".")[0] if image_path else ""}\n{self.version_name}\n{self.file_path}'
        self.text_label = QLabel(label_name)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("background-color: rgba(0,0,0,128); color: white; padding: 5px;")
        self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout.addWidget(self.image_label)
        layout.addWidget(self.text_label, alignment=Qt.AlignTop)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.file_path)


class VersionFoldersWorker(QObject):
    finished = Signal(dict)
    progress = Signal(str, int)
    create_widget = Signal(str, str)  # path, preview file

    def __init__(self, root_path, context_id, isconnected):
        super().__init__()
        self.is_stopped = False
        self.root_path = root_path
        self.context_id = context_id
        self.isconnected = isconnected
        self.total_folders = 0

    def run(self):
        result = self.collect_version_folders()
        self.finished.emit(result or {})

    def collect_version_folders(self):
        if not (self.isconnected and self.context_id):
            return None

        self.progress.emit("Collecting version folders...", 0)
        version_folders = {}
        exts = ('.exr', '.jpg', '.jpeg', '.png', '.mov', '.mp4', '.tif', '.tiff', '.dpx')

        # Count folders only once (avoid double os.walk)
        all_dirs = [os.path.join(dp, dn) for dp, dns, _ in os.walk(self.root_path) for dn in dns]
        self.total_folders = len(all_dirs)
        self.progress.emit(
                f"Processing {0}/{self.total_folders}",
                int(0 / self.total_folders * 100),
            )

        for counter, full_path in enumerate(all_dirs, 1):
            
            if getattr(self, "is_stopped", False):
                print("⏹ Worker interrupted")
                return

            try:
                # Find first media file (no need to sort the whole dir)
                media_files = [f for f in os.listdir(full_path) if f.lower().endswith(exts)]
            except PermissionError:
                continue  # skip restricted folders

            if not media_files:
                continue

            relative_path = os.path.relpath(full_path, self.root_path)
            tags = relative_path.replace("\\", "/").split("/")

            if "media" not in tags:
                continue

            tags.remove("media")
            self.progress.emit(
                f"Processing {counter}/{self.total_folders}",
                int(counter / self.total_folders * 100),
            )

            version_folders[full_path] = {
                "ctime": os.path.getctime(full_path),
                "tags": tags,
            }
            # Only preview first file
            self.create_widget.emit(full_path, os.path.join(full_path, media_files[0]))

        # Sort once at the end
        return dict(sorted(version_folders.items(), key=lambda item: item[1]["ctime"], reverse=True))



class KitsuPanel(rvtypes.MinorMode):
    def __init__(self, supportPath):
        super().__init__()
        self.init("Emile Exemple", None, None)
        self.isconnected = try_gazu_connection()

        loader = QUiLoader()
        uifile = QFile(os.path.join(supportPath, "kitsu_panel.ui"))
        uifile.open(QFile.ReadOnly)
        self.panel = loader.load(uifile)
        uifile.close()

        # Scroll area
        self.panel.scroll_area = QScrollArea(self.panel)
        self.panel.scroll_area.setWidgetResizable(True)
        self.panel.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.panel.scroll_content = QWidget()
        self.panel.version_grid = FlowLayout(self.panel.scroll_content)
        self.panel.scroll_content.setLayout(self.panel.version_grid)
        self.panel.scroll_area.setWidget(self.panel.scroll_content)
        self.panel.progressBar.setValue(0)

        self.panel.FlowLayout.addWidget(self.panel.scroll_area)

        self.context_id = os.getenv("KITSU_CONTEXT_ID")
        if self.context_id:
            self.panel.context_id_label.setText(self.context_id)
        self.project_root = os.getenv("KITSU_PROJECT_ROOT")

        # Dock widget
        self.dock_widget = QDockWidget("Kitsu")
        self.dock_widget.setWidget(self.panel)
        self.dock_widget.setMinimumWidth(self.panel.width())
        self.dock_widget.setObjectName("KitsuPanel")

        self.inject_into_main_window()
        self.panel.refresh_button.clicked.connect(self.refresh_versions_threaded)



    def inject_into_main_window(self):
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMainWindow):
                widget.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
                self.dock_widget.hide()  # starts hidden
                return
        print("❌ Could not find RV main window")

    # 👉 Instead of using self.is_showing, check directly:
    def toggle_panel(self):
        if self.dock_widget.isVisible():
            self.dock_widget.hide()
        else:
            self.dock_widget.show()

    def inject_into_main_window(self):
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMainWindow):
                widget.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
                self.dock_widget.hide()
                return
        print("❌ Could not find RV main window")

    def create_widget_for_version(self, path, preview_file):
        widget = ClickableVersionWidget(path, preview_file)
        widget.doubleClicked.connect(self.version_doubleClicked)
        self.panel.version_grid.addWidget(widget)
        self.panel.version_grid.update()
        return widget

    def clear_current_session(self):
        for node in commands.nodes():
            if commands.nodeType(node) == "RVSourceGroup":
                commands.deleteNode(node)

    def load_all_media_from_directory(self, directory_path):
        exts = {'.exr', '.jpg', '.jpeg', '.png', '.mov', '.mp4', '.tif', '.tiff', '.dpx'}
        media_files = [
            os.path.join(directory_path, f)
            for f in sorted(os.listdir(directory_path))
            if os.path.splitext(f)[1].lower() in exts
        ]
        if media_files:
            commands.addSource(media_files[0])
        else:
            print("No supported media files in", directory_path)

    def version_doubleClicked(self, path):
        self.clear_current_session()
        self.load_all_media_from_directory(path)

    def get_path_from_context_id(self, context_id):

        project_root = os.getenv("KITSU_PROJECT_ROOT")
        
        task = gazu.task.get_task(context_id)
        entity = gazu.entity.get_entity(task['entity']['id'])
        entity_type = entity['type'].lower()
        entity_name = entity['name']
        print(task, task['project'])

        task_dir = None 
        
        if project_root:
            if entity_type == 'shot':
                parent_name = gazu.entity.get_entity(entity['parent_id'])['name']
            else:
                parent_name = gazu.entity.get_entity_type(entity['entity_type_id'])['name']
            
            task_dir = os.path.join(project_root,entity_type,parent_name,entity_name)
        else:
            return 'No Project Root'
        
        if task_dir:
            return task_dir

    def refresh_versions_threaded(self):
        # If a worker thread is already running, stop it first
        try:
            if hasattr(self, "worker_thread") and self.worker_thread.isRunning():
                print("⏹ Stopping previous worker...")
                self.worker.is_stopped = True
                self.worker_thread.requestInterruption()
                self.worker_thread.quit()
                self.worker_thread.wait()  # Block until fully stopped
                self.panel.refresh_button.setText("Refresh")
                return
        except Exception as e:
            print("Error stopping previous worker:", e)

        self.panel.refresh_button.setText("Cancel")

        print("🔄 Starting new refresh...")
        #root_path = os.getenv("KITSU_PROJECT_ROOT")
        root_path = self.get_path_from_context_id(self.context_id)

        if not root_path:
            print("❌ KITSU_PROJECT_ROOT not set")
            return
        
        self.worker_thread = QThread()
        self.worker = VersionFoldersWorker(root_path, self.context_id, self.isconnected)
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.create_widget.connect(self.create_widget_for_version)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_versions_ready)

        # Cleanup
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()
        return


    def on_progress(self, message, count):
        self.panel.waiting_status_label.setText(message)
        self.panel.progressBar.setValue(count)


    def on_versions_ready(self, sorted_versions):
        self.on_progress("", 0)
        self.panel.progressBar.setValue(0)

