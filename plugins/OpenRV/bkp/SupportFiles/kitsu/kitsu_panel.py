import os

from PySide2 import QtWidgets, QtCore
from PySide2.QtUiTools import QUiLoader

from rv import rvtypes
import gazu

def try_gazu_connection():
    try:

        gazu.client.set_host("https://kitsu.vivarium.ca/api")
        gazu.log_in("emile.massie@gmail.com", "emile220")
        print("Connected to Kitsu")
        return True
    except Exception as e:
        print(e)
        return False

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

        self.tree = self.panel.findChild(QtWidgets.QTreeView, "treeView")

        try:
            self.context_id = os.environ['KITSU_CONTEXT_ID']
            self.build_tree()
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

    def build_tree(self):
        if self.isconnected and self.context_id:
            project = gazu.project.get_project(self.context_id)
            print(project)
            self.model = QtWidgets.QFileSystemModel()
            root_path = os.path.join('z:', 'projects')
            self.model.setRootPath(root_path)
            self.model.setFilter(QtCore.QDir.Filter.AllEntries | QtCore.QDir.Filter.NoDotAndDotDot)
            self.tree.setModel(self.model)
            self.tree.setRootIndex(self.model.index(root_path))