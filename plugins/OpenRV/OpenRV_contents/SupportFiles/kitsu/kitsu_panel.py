import os

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide2.QtGui import QPixmap
from PySide2.QtCore import Qt, Signal
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import QThread, Signal, QObject

import re
from pathlib import Path

from rv import rvtypes
import rv.commands
import gazu

from flow_layout import FlowLayout


def try_gazu_connection():
    try:

        gazu.client.set_host(os.getenv('KITSU_HOST')+"/api")
        gazu.log_in("emile.massie@gmail.com", "emile220")
        print("Connected to Kitsu")
        return True
    except Exception as e:
        print(e)
        return False

class ClickableVersionWidget(QWidget):
    doubleClicked = Signal(str)  # You can emit version path or name

    def __init__(self, file_path, image_path=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.version_name = os.path.basename(file_path)
        self.image_path = image_path

        self.setFixedSize(160, 90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create stacked layout
        self.image_label = QLabel()
        self.image_label.setFixedSize(160, 90)
        self.image_label.setScaledContents(True)

        if self.image_path:
            self.image_label.setPixmap(QPixmap(self.image_path))


        label_name = f'{os.path.basename(image_path).split(".")[0]}\n{self.version_name}\n{self.file_path}'

        self.text_label = QLabel(label_name)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("background-color: rgba(0, 0, 0, 128); color: white; padding: 5px; border-radius: 5px;")
        self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout.addWidget(self.image_label)
        layout.addWidget(self.text_label, alignment=Qt.AlignTop)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.file_path)



class VersionFoldersWorker(QObject):
    finished = Signal(dict)
    progress = Signal(str,int)
    def __init__(self, root_path, context_id, isconnected):
        super().__init__()
        self.root_path = root_path
        self.context_id = context_id
        self.isconnected = isconnected
        self.total_folders = self.count_folders()

    def run(self):
        result = self.collect_version_folders_sorted_by_ctime()
        self.finished.emit(result if result else {})

    def count_folders(self):
        count = 0
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            count += len(dirnames)
        return count

    def collect_version_folders_sorted_by_ctime(self):
        self.progress.emit("Collecting version folders...", 0)
        if self.isconnected and self.context_id:
            version_folders = {}
            # Regex pattern to match folders like v0001, v0002, etc.
            pattern = re.compile(r"^v\d{4}$")
            supported_extensions = ['.exr', '.jpg', '.jpeg', '.png', '.mov', '.mp4', '.tif', '.tiff', '.dpx']
            counter = 0
            for dirpath, dirnames, filenames in os.walk(self.root_path):
                # self.progress.emit(f"Scanned {counter}/{self.total_folders} subdirectories", counter)
                for dirname in dirnames:
                    counter += 1
                    full_path = os.path.join(dirpath, dirname)
                    media_files = [
                        os.path.join(full_path, f)
                        for f in sorted(os.listdir(full_path))
                        if os.path.splitext(f)[1].lower() in supported_extensions
                    ]
                    if not media_files:
                        continue
                    ctime = os.path.getctime(full_path)
                    relative_path = os.path.relpath(full_path, self.root_path)
                    tags = relative_path.replace("\\", "/").split("/")
                    if 'media' not in tags:
                        continue
                    else:
                        self.progress.emit(f"Processing {counter}/{self.total_folders} subdirectories", int(counter / self.total_folders * 100))
                        tags.remove('media')
                    version_folders[full_path] = {
                        'ctime': ctime,
                        'tags': tags
                    }
            sorted_versions = dict(
                sorted(version_folders.items(), key=lambda item: item[1]['ctime'], reverse=True)
            )
            return sorted_versions
        else:
            return None

class KitsuPanel(rvtypes.MinorMode):
    def __init__(self, supportPath):
        super().__init__()
        self.init("Emile Exemple", None, None)
        self.isconnected = try_gazu_connection()

        self.loader = QUiLoader()
        
        uifile = QtCore.QFile(os.path.join(supportPath, "kitsu_panel.ui"))
        uifile.open(QtCore.QFile.ReadOnly)
        self.panel = self.loader.load(uifile)
        uifile.close()

        # Create the scroll area
        self.panel.scroll_area = QtWidgets.QScrollArea(self.panel)
        self.panel.scroll_area.setWidgetResizable(True)
        self.panel.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.panel.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Create the scroll content widget
        self.panel.scroll_content = QtWidgets.QWidget()
        self.panel.version_grid = FlowLayout(self.panel.scroll_content)
        # This ensures that scroll_content expands in width but flows vertically
        self.panel.scroll_content.setLayout(self.panel.version_grid)
        self.panel.scroll_area.setWidget(self.panel.scroll_content)

        # Add the scroll area to your main layout (replace this with your panel layout)
        main_layout = self.panel.FlowLayout
        main_layout.addWidget(self.panel.scroll_area)

        try:
            self.context_id = os.environ['KITSU_CONTEXT_ID']
            self.panel.context_id_label.setText(self.context_id)
            self.refresh_versions_threaded()
            
        except Exception as e:
            self.context_id = None
            print(e)

        

        # Wrap in a QDockWidget for docking
        self.dock_widget = QtWidgets.QDockWidget("Kitsu")
        self.dock_widget.setWidget(self.panel)
        self.dock_widget.setMinimumWidth(self.panel.width())
        self.dock_widget.setObjectName("KitsuPanel")
        self.is_showing = False

        # Embed it in OpenRV's main window
        self.inject_into_main_window()
        
        self.panel.refresh_button.clicked.connect(self.refresh_versions_threaded)

    def inject_into_main_window(self):
        # Find the main RV window
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(widget, QtWidgets.QMainWindow):
                main_window = widget
                break
        else:
            print("❌ Could not find RV main window")
            return
        main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.hide()
        self.is_showing = False

    def get_version_folders_sorted_by_ctime(self):
        if self.isconnected and self.context_id:
            root_path = os.getenv('KITSU_PROJECT_ROOT')
            version_folders = {}

            # Regex pattern to match folders like v0001, v0002, etc.
            pattern = re.compile(r"^v\d{4}$")



            supported_extensions = ['.exr', '.jpg', '.jpeg', '.png', '.mov', '.mp4', '.tif', '.tiff', '.dpx']
    
        

            # Scan all subdirectories
            for dirpath, dirnames, filenames in os.walk(root_path):
                for dirname in dirnames:

                    full_path = os.path.join(dirpath, dirname)
                    media_files = [
                        os.path.join(full_path, f)
                        for f in sorted(os.listdir(full_path))
                        if os.path.splitext(f)[1].lower() in supported_extensions
                    ]

                    if not media_files:
                        print("No supported media files found in the directory. --- >" + full_path)
                        continue
                    else :

                        print("Found media files in directory:", full_path)
                        ctime = os.path.getctime(full_path)

                        # Get relative path from root and split it into tags
                        relative_path = os.path.relpath(full_path, root_path)
                        tags = relative_path.replace("\\", "/").split("/")

                        # Filter: keep only if 'media' in the path tags
                        if 'media' not in tags:
                            continue
                        else: 
                            tags.remove('media')

                        version_folders[full_path] = {
                            'ctime': ctime,
                            'tags': tags
                        }

            # Sort by creation time
            sorted_versions = dict(
                sorted(version_folders.items(), key=lambda item: item[1]['ctime'], reverse=True)
            )

            return sorted_versions
        else:
            return None
        
    def populate_version_panel(self, sorted_versions):
        for path, info in sorted_versions.items():
            info['files'] = os.listdir(path)
            #print(path, info['ctime'], info['tags'], info['files'])

        all_tags = set()
        for entry in sorted_versions.values():
            all_tags.update(entry['tags'])


        # Clear all existing widgets
        while self.panel.version_grid.count():
            item = self.panel.version_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add QLabel widgets with image previews
        for path, data in sorted_versions.items():
            files = data['files']
            if not files:
                continue
            first_file_path = os.path.join(path, files[0])

            widget = ClickableVersionWidget(path, first_file_path)
            widget.doubleClicked.connect(lambda path: self.version_doubleClicked(path))
            self.panel.version_grid.addWidget(widget)
            #self.panel.version_grid.update()

    def clear_current_session(self):
    # Get all nodes in the session
        all_nodes = rv.commands.nodes()
        
        # Filter for source group nodes (they hold the media)
        source_groups = [node for node in all_nodes if rv.commands.nodeType(node) == 'RVSourceGroup']
        
        # Delete each source group
        for sg in source_groups:
            rv.commands.deleteNode(sg)

    def load_all_media_from_directory(self, directory_path):
        supported_extensions = ['.exr', '.jpg', '.jpeg', '.png', '.mov', '.mp4', '.tif', '.tiff', '.dpx']
    
        media_files = [
            os.path.join(directory_path, f)
            for f in sorted(os.listdir(directory_path))
            if os.path.splitext(f)[1].lower() in supported_extensions
        ]

        if not media_files:
            print("No supported media files found in the directory. --- >" + directory_path)
            return
        
        rv.commands.addSource(media_files[0])

    def version_doubleClicked(self, path=None):
        if not path:
            return
        
        self.clear_current_session()
        self.load_all_media_from_directory(path)

    def refresh_versions_threaded(self):
        print("Refreshing versions...")
        self.panel.stackedWidget.setCurrentIndex(1)  # Switch to the loading screen
        root_path = os.getenv('KITSU_PROJECT_ROOT')
        context_id = getattr(self, 'context_id', None)
        isconnected = getattr(self, 'isconnected', False)
        self.worker_thread = QThread()
        self.worker = VersionFoldersWorker(root_path, context_id, isconnected)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_versions_ready)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def on_progress(self, message, count):
        print(f"Progress: {message} ({count})")
        self.panel.waiting_status_label.setText(f"{message}")
        self.panel.stackedWidget.setCurrentIndex(1)

    def on_versions_ready(self, sorted_versions):
        self.on_progress("Versions loaded", 100)
        self.populate_version_panel(sorted_versions)
        self.panel.stackedWidget.setCurrentIndex(0)
