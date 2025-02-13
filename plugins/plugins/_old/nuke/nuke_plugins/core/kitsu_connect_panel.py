import nuke
import nukescripts
import os, sys

import gazu

from nukescripts import panels

from PySide2 import QtCore, QtGui, QtWidgets, QtUiTools

def show_qt_pane(widget_class, title, pane_id):
    """
    Show a Qt widget in a Nuke panel.
    Parameters
    ----------
    widget_class: str
        Widget class to show in the panel. Needs to be the full path to the class, already imported.
        Example: "my_module.kitsu_connect_panel"
    title: str
        Title of the panel.
    pane_id: str
        Unique identifier of the panel. Should match what is used when using registerWidgetAsPanel.
    """
    
    # Check if pane already exists.
    widgets = find_qt_widgets(pane_id)
    if widgets:
        # We found at least one instance, show the first one.
        widget = widgets[0]
        parent_widget = widgets[0].parentWidget()
        parent_widget.setCurrentWidget(widget)
        parent_widget.activateWindow()
        parent_widget.setFocus()
    else:
        # No instances were found, let's initialize a new one in a new Panel.
        panel = nukescripts.PythonPanel(title, pane_id)
        widget = nuke.PyCustom_Knob(title, "", "__import__('nukescripts').panels.WidgetKnob({})".format(widget_class))
        panel.addKnob(widget)
        panel.show()

def find_qt_widgets(widget_name):
    qwindow = get_nuke_main_window()
    widgets = qwindow.findChildren(QtWidgets.QWidget, widget_name)
    return widgets

def get_nuke_main_window():
    """Returns Nuke's main window"""
    app = QtWidgets.QApplication.instance()
    for obj in app.topLevelWidgets():
        if obj.inherits('QMainWindow') and obj.metaObject().className() == 'Foundry::UI::DockMainWindow':
            return obj
    return None

# KITSU CONNECT WIDGET

class kitsu_connect_panel(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        # load the ui file
        self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'kitsu_connect_panel.ui')), self)

        self.setLayout(self.ui.layout())
        
        gazu.set_host(os.getenv('KITSU_HOST')+'/api')
        token = {'access_token': os.getenv('KITSU_ACCESS_TOKEN')}
        gazu.client.set_tokens(token)
        
        self.project = gazu.project.get_project_by_name(os.getenv('KITSU_PROJECT'))
        try:
            self.task = gazu.task.get_task(os.getenv('KITSU_CONTEXT_ID'))
            self.shot = os.getenv('KITSU_SHOT')
            self.sequence = os.getenv('KITSU_SEQUENCE')
            self.project_root = os.getenv('KITSU_PROJECT_ROOT')

            self.ui.context_field.setText(os.getenv('KITSU_CONTEXT_ID'))
            self.ui.project_root_field.setText(self.project_root)

            self.build_save_load()
            self.build_media_tree()
        except:
            self.close()
       
    def updateValue(self):
        return
  
    def build_media_tree(self):
        shot_folder = os.path.join(self.project_root, 'shots', self.sequence, self.shot, 'media' )
        if not os.path.exists(shot_folder):
            os.makedirs(shot_folder, exist_ok=True)

        # Create the QFileSystemModel
        self.model_media = QtWidgets.QFileSystemModel()
        self.model_media.setRootPath(QtCore.QDir.rootPath())

        # Create the QTreeView
        self.ui.media_tree.setModel(self.model_media)

        # Set the icons for folders and files
        self.ui.media_tree.setRootIndex(self.model_media.index(shot_folder))
        self.ui.media_tree.setAnimated(True)
        self.ui.media_tree.setSortingEnabled(True)
        self.ui.media_tree.expand(0)

    def build_save_load(self):
        shot_folder = os.path.join(self.project_root, 'shots', self.sequence, self.shot, 'project_files' )
        if not os.path.exists(shot_folder):
            os.makedirs(shot_folder, exist_ok=True)

        # Create the QFileSystemModel
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(QtCore.QDir.rootPath())

        # Create the QTreeView
        self.ui.save_load_tree.setModel(self.model)

        # Set the icons for folders and files
        self.ui.save_load_tree.setRootIndex(self.model.index(QtCore.QDir.rootPath()))
        self.ui.save_load_tree.setAnimated(True)
        self.ui.save_load_tree.setSortingEnabled(True)

        self.ui.save_load_tree.setRootIndex(self.model.index(shot_folder))
        self.ui.save_load_tree.expandAll()

