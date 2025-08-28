# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask, request

import subprocess, importlib
from appdirs import user_config_dir
import os, getpass, sys
import gazu, json

import PyQt6
from PyQt6 import QtCore, QtWidgets, uic, QtGui
from PyQt6.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot,QMetaObject
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


VERSION = '1.1.0'

def get_application_root_path():
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)

    return application_path


# Flask constructor takes the name of 
# current module (__name__) as argument.

class kitsu_version_list(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.root_folder = os.path.dirname(__file__)
        uic.loadUi(os.path.join(self.root_folder,'ui','version_list.ui'), self) 
        self.setWindowTitle('Select Version')
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.root_folder,'icons','icon.png')))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint)
        

class kitsu_action_server(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    log_update = QtCore.pyqtSignal(str)  # Signal to update the log
    show_message_project = QtCore.pyqtSignal(str)
    update_tray_icon_info = QtCore.pyqtSignal(str)
    setup_version_tree = QtCore.pyqtSignal(str,object, object)
    show_msg_proj = QtCore.pyqtSignal(str)

    def __init__(self, ui_window, server, host='0.0.0.0', port='90'):
        super().__init__()
        self.server = server
        self.host = host
        self.port = port
        self.ui_window = ui_window
        self.version = None

         # adding defaults set porject root
        self.server.add_url_rule('/set-project-root', view_func=self.set_project_root, methods=['POST'])

    def set_project_root(self):
        data = request.form  # Use form data instead of JSON

        if not data:
            return jsonify({'error': 'No form data received'}), 400
        else:
            project = gazu.project.get_project(data['projectid'])
            print(project)
            self.show_msg_proj.emit(project['name'])
        
        return self.get_plugin_page('Settting Project Root')

    def get_plugin_page(self, message):
        return """<html>
        <head>
            <script>
                window.onload = function() {
                    setTimeout(function() {
                        window.close();
                    }, 100);  // Closes after 2 seconds
                };
            </script>
        </head>
        <body>
            """+message+"""
        </body>
        </html>"""

    def get_version(self, plugin, args=[]):
        task = gazu.task.get_task(os.environ['KITSU_CONTEXT_ID'])
        if task['task_type']['for_entity'].lower() == 'shot':
            version_folder = os.path.abspath(os.path.join(os.environ['KITSU_PROJECT_ROOT'],'shot',os.environ['KITSU_SEQUENCE'] , os.environ['KITSU_SHOT'], 'project_files',task['task_type']['name'].lower().replace(' ','_')))
        else:
            task_name = task['task_type']['name'].lower().replace(' ','_') # shading
            task_type =  task['task_type']['for_entity'].lower().replace(' ','_') # asset
            task_asset = task['entity']['name'].lower().replace(' ','_') # mychar
            asset_cathegory = task['entity_type']['name'].lower().replace(' ','_') # character

            version_folder = os.path.abspath(os.path.join(os.environ['KITSU_PROJECT_ROOT'],task_type, asset_cathegory,task_asset, task_name, 'project_files'))
            
        os.makedirs(version_folder, exist_ok=True)
        print('------------------------------------> ',version_folder)
        self.setup_version_tree.emit(version_folder,plugin, args)
        self.version = None

    def set_environ(self, fromweb=None):

        if self.ui_window.url and self.ui_window.user and self.ui_window.access_token:

            data = {

                'KITSU_HOST':self.ui_window.url,
                'KITSU_USER': self.ui_window.user,
                'KITSU_ACCESS_TOKEN':self.ui_window.access_token

            }

            full_text = (
                f'KITSU_HOST : {self.ui_window.url}\n'
                f'KITSU_USER : {self.ui_window.user}'
            )

            for i in data:
                os.environ[i] = data[i]

                self.update_tray_icon_info.emit(full_text)

            if fromweb:
                task = gazu.task.get_task(fromweb['selection'])
                project_name = gazu.project.get_project(fromweb['projectid'])['name']
                os.environ['KITSU_CONTEXT_ID'] = fromweb['selection']
                os.environ['KITSU_PROJECT'] = project_name

                if task['task_type']['for_entity'].lower() == 'shot':

                    os.environ['KITSU_SEQUENCE'] = task['sequence']['name']
                    os.environ['KITSU_SHOT'] = task['entity']['name']

                    full_text = full_text + (
                        f'\n\nKITSU_CONTEXT_ID : {fromweb["selection"]}\n'
                        f'KITSU_PROJECT : {project_name}\n'
                        f"KITSU_SEQUENCE : {task['sequence']['name']}\n"
                        f"KITSU_SHOT : {task['entity']['name']}"
                    )
                else:

                    full_text = full_text + (
                        f'\n\nKITSU_CONTEXT_ID : {fromweb["selection"]}\n'
                        f'KITSU_PROJECT : {project_name}\n'
                        f"KITSU_ASSET_TYPE : {task['task_type']['name']}"
                        f"KITSU_ASSET : {task['entity']['name']}\n"
                    )

                project_root = self.ui_window.get_project_root(project_name)

                if not project_root:
                    # Run in the main GUI thread
                    project_root = self.show_message_project.emit(project_name)
                if project_root:
                    os.environ['KITSU_PROJECT_ROOT'] = project_root
                    self.log_update.emit(f"KITSU_PROJECT_ROOT : {project_root}")

            self.log_update.emit('\n--------------------------') 
            self.log_update.emit(full_text)   
            self.log_update.emit('--------------------------\n')

            
            
            
        return os.environ.copy()
        
    def run(self):
        self.server.run(host=self.host, port=self.port)

class kitsu_action_ui(QtWidgets.QMainWindow):
    update_signal = QtCore.pyqtSignal(str)
    show_notification = QtCore.pyqtSignal(str,str,object,int)
    show_plugin_dialog_signal = pyqtSignal(object)  # QWidget class
    def __init__(self):
        super().__init__()
        self.server = Flask(__name__)
        self.host = '0.0.0.0'
        self.port = '90'

        self.show_plugin_dialog_signal.connect(self.show_widget_window)
        
        self.root_folder = os.path.dirname(__file__)
        uic.loadUi(os.path.join(self.root_folder,'ui','kitsu-action-server.ui'), self) 
        self.version_label.setText('v'+str(VERSION))
        self.icon = QtGui.QIcon(os.path.join(self.root_folder,'icons','icon.png'))
        self.setWindowIcon(self.icon)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowMinimizeButtonHint)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.settings_file = self.get_config_file()
        self.exit_button.setIcon(QtGui.QIcon(os.path.join(self.root_folder,'icons','x.svg')))
        self.exit_button.clicked.connect(self.close_and_hide)

        # Variables to track mouse position for dragging
        self._isResizing = False
        self._isDragging = False
        self._dragPosition = QPoint()
        self._resizeMargin = 10  # Margin around edges for resizing
        self._dragArea = None

        self.active_plugin_function = None



        self.plugin_folder = os.path.join(get_application_root_path(), 'plugins')
        self.plugins = self.get_plugins(self.plugin_folder)
        self.get_plugins_funct()
         


        self.access_token = None
        self.settings_dict = {}
        self.url = None
        self.user = None
        self.access_token = None 

        self.connection_status = False
        self.load_settings()

        self.vv = kitsu_version_list()
        self.vv.listWidget.itemDoubleClicked.connect(self.on_version_clicked)

        self.server_worker = kitsu_action_server(self,self.server, self.host, self.port)
        self.server_worker.log_update.connect(self.update_log)
        self.server_worker.show_message_project.connect(self.show_message_project)
        self.server_worker.setup_version_tree.connect(self.update_tree)
        self.server_worker.update_tray_icon_info.connect(self.update_tray)
        self.server_worker.show_msg_proj.connect(self.show_message_project)
        
        if self.check_connection():
            self.t_user_2.setText(self.user)
            self.t_pwd_2.setText('********')
            self.t_url_2.setText(self.url)
            self.connection_status = True

            self.stackedWidget.setCurrentIndex(1)
            self.server_worker.start()
            
        else:
            self.stackedWidget.setCurrentIndex(0)
            self.show()

        self.connect_button.released.connect(self.connect_clicked)
        self.load_all_plugins_settings(verbose=False)
        self.setup_plugin_ui() 
        self.server.add_url_rule('/open_task_directory', view_func=self.show_task_directory, methods=['POST'])

    def show_widget_window(self, widget_cls, *args, **kwargs):
        widget = widget_cls(*args, **kwargs)
        widget.setWindowIcon(self.icon)
        widget.setStyleSheet(self.styleSheet())
        widget.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        widget.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Optional auto-cleanup
        widget.raise_()
        widget.activateWindow()
        widget.show()

        # Save reference to avoid garbage collection
        self._last_opened_widget = widget
    
    def show_task_directory(self):
        data = request.form  # Use form data instead of JSON
        print(data)

        for task_id in data['selection'].split(','):
            task = gazu.task.get_task(task_id)
            entity = gazu.entity.get_entity(task['entity']['id'])
            entity_type = entity['type'].lower()
            entity_name = entity['name']

            
            print(entity)
            project_name = gazu.project.get_project(data['projectid'])['name']

            if self.get_project_root(project_name):
                project_root = self.get_project_root(project_name)
            else:
                project_root = self.show_message_project(project_name)

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
                os.makedirs(task_dir, exist_ok=True)  # Create the directory if it doesn't exist

                if sys.platform == "win32":
                    os.startfile(task_dir)  # Windows
                elif sys.platform == "darwin":
                    subprocess.run(["open", task_dir])  # macOS
                else:
                    subprocess.run(["xdg-open", task_dir])  # Linux
                
                return f'Task Directory opened : {task_dir}' 


    def close_and_hide(self):
        self.show_notification.emit("Kitsu Action Server","Application was minimized to Tray", self.icon, 200)
        self.close()

    def update_tray(self, text):
        self.update_signal.emit(text)

    def update_tree(self, version_folder, plugin, args):

        self.vv.listWidget.clear()
        print(version_folder, plugin, args)
        version_num = 1
        for version in reversed(os.listdir(version_folder)):
            for file in os.listdir(os.path.join(version_folder,version)):
                if file.endswith(plugin.extension):
                    list_item = QtWidgets.QListWidgetItem(file)
                    list_item.setData(QtCore.Qt.ItemDataRole.UserRole, os.path.join(version_folder,version,file))
                    list_item.setData(QtCore.Qt.ItemDataRole.UserRole+1, plugin)
                    list_item.setData(QtCore.Qt.ItemDataRole.UserRole+2, args)
                    self.vv.listWidget.addItem(list_item)        
            version_num += 1
        if version_num == 0:
            version_num = 1

        item = QtWidgets.QListWidgetItem('New Version')
        item.setData(QtCore.Qt.ItemDataRole.UserRole+1, plugin)
        item.setData(QtCore.Qt.ItemDataRole.UserRole+2, lambda: plugin.create_new_version(version_num, version_folder, args))
        self.vv.listWidget.addItem(item)

        self.vv.show()
        
    def on_version_clicked(self, item):
        """Handle item double-click event."""
        file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
        args = item.data(QtCore.Qt.ItemDataRole.UserRole+2)
        plugin = item.data(QtCore.Qt.ItemDataRole.UserRole+1)
        print(f"Double-clicked: {file_path}") 
        if item.text() == 'New Version':
            args()
        else:
            plugin.open_file(file_path,args)
        self.vv.close()
        return file_path
        
    def load_all_plugins_settings(self, verbose=True):
        msg = 'Loaded : '
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                self.settings_dict = json.load(f)
            for plugin in self.plugins:
                try:
                    plugin.exec = self.settings_dict['plugins'][plugin.name]['exec']
                    msg = msg + plugin.name+','
                except:
                    plugin.exec = None
        
            
            if verbose:
                self.update_log(msg[:-1]+' Executable Paths')

    def show_message_project(self, project_name):

        project_root = None
        reply_box = QtWidgets.QMessageBox(self)  # Create the message box instance
        reply_box.setWindowTitle(f"No Project Root for '{project_name}'")
        reply_box.setText("There is no project root associated with this project in your settings.\nDo you want to set one now?")
        reply_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        reply_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)

        # Force the message box to stay on top
        reply_box.setWindowFlags(reply_box.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)

        reply = reply_box.exec()


        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            project_root = QtWidgets.QFileDialog.getExistingDirectory(self, f"Select {project_name} Project Directory")
            if project_root:
                self.set_project_root(project_name,project_root)

        return project_root

    def get_project_root(self, project_name):
        try:
            with open(self.settings_file, 'r') as f:
                settings_dict = json.load(f)
                project_root = settings_dict['project_roots'][project_name]
            return project_root
        except:
            return False

    def set_project_root(self, project_name, project_root):
        try:
            with open(self.settings_file, 'r') as f:
                settings_dict = json.load(f)

                try:
                    project_roots = settings_dict['project_roots']
                except:
                    settings_dict['project_roots'] = {}
                    project_roots = settings_dict['project_roots']

                project_roots[project_name] = project_root
            f.close()
            j = json.dumps(settings_dict, indent=4)
            with open(self.settings_file, 'w') as f:
                print(j, file=f)

            self.parent.update_log('Saved Settings')
            return project_root
        except:
            return False
        
    def set_plugin_executable(self, plugin, label):
        exec_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, f"Select {plugin.name} Executable")
        if exec_path:
            label.setText(exec_path)
            self.save_plugin_config(plugin,exec_path)
            return exec_path

    def get_plugin_exec(self, plugin, label):
        try:
            return self.settings_dict['plugins'][plugin.name]['exec']
        except:
            exec_path = self.set_plugin_executable(plugin,label)
            return exec_path
         
    def save_plugin_config(self, plugin, exec_path=None):
        with open(self.settings_file, 'r') as f:
                new_dict = json.load(f)

        new_dict.setdefault('plugins', {}).setdefault(plugin.name, {})['exec'] = exec_path

        j = json.dumps(new_dict, indent=4)
        with open(self.settings_file, 'w') as f:
            print(j, file=f)

    def setup_plugin_ui(self):
        self.tableWidget.setRowCount(0)
        for row_count, plugin in enumerate(self.plugins):
            item = QtWidgets.QTableWidgetItem(plugin.name)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            pr_wt = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout()
            layout.setContentsMargins(3, 0, 0, 0)
            label = QtWidgets.QLineEdit('')
            plugin_exec = self.get_plugin_exec(plugin, label)
            label.setText(plugin_exec)
            label.setToolTip(plugin_exec)
            label.setReadOnly(True)
            layout.addWidget(label)
            button = QtWidgets.QPushButton()
            button.setText('CHANGE')
            button.released.connect(lambda p=plugin, l=label: self.set_plugin_executable(p, l))
            layout.addWidget(button)
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Minimum)
            pr_wt.setLayout(layout)
            
            self.tableWidget.insertRow(row_count)
            self.tableWidget.setItem(self.tableWidget.rowCount()-1, 0,item)
            self.tableWidget.setCellWidget(self.tableWidget.rowCount()-1, 1, pr_wt)
    
    def get_plugins_funct(self):
        self.update_log('Getting plugins functions\n')
        print(self.plugins)
        for plugin in self.plugins:
            try:
                for function in plugin.get_url_rules():
                    print(plugin.name, function['url'], function['function'], function['methods'])
                    self.update_log(plugin.name +' '+ self.host+str(function['url'])+ ' '+ str(function['methods']))
                    self.server.add_url_rule(function['url'], view_func=function['function'], methods=function['methods'])
            except Exception as aaa:
                print(str(aaa))
                self.update_log(str(aaa), 'orange')
        return

    def get_plugins(self, folder = None):
        plugin_list = []
        print(folder)
        if folder:
            self.plugin_folder = folder
        if self.plugin_folder and os.path.isdir(self.plugin_folder):
            for folder in os.listdir(self.plugin_folder):
                if os.path.isdir(os.path.join(self.plugin_folder, folder)):
                    for file in os.listdir(os.path.join(self.plugin_folder, folder)):
                        if file == folder+'.py':
                            name = file[:-3]
                            module = self.dynamic_import('kitsu_connect_plugin_'+name, os.path.join(self.plugin_folder, folder,file))
                            print('Loaded Plugin: ' + name)
                            plugin = module.Plugin(self)
                            plugin_list.append(plugin)

        
        return plugin_list

    def dynamic_import(self, module_name, py_path):
        module_spec = importlib.util.spec_from_file_location(module_name, py_path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module 

    def get_config_file(SELF):
        # Get the current username
        username = getpass.getuser()

        # Define your application name and author/company name
        app_name = "kitsu-action-server"
        app_author = "kitsu-action-server"  # Optional, not needed for Linux

        # Get the user-specific configuration directory
        config_dir = user_config_dir(app_name, app_author)

        # Create the configuration directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)

        # Define the path for your configuration file
        config_file = os.path.join(config_dir, f"{username}_settings.conf")
        return config_file   
            
    def check_connection(self):
        if self.access_token:
            try:
                token = {'access_token': self.access_token}
                gazu.client.set_host(self.url+'/api')
                gazu.client.set_tokens(token)
                user = gazu.client.get_current_user()
                self.connection_status = True
                self.status_text.setText("<span style='color:green'>CONNECTED</span>")
                return True
            except:
                self.connection_status = False
                return False
        else:
            self.connection_status = False
            self.status_text.setText("<span style='color:RED'>NOT CONNECTED</span>")
            return False

    def get_kitsu_token(self):
        try:
            self.user = self.t_user.text()
            self.url = self.t_url.text()
            gazu.client.set_host(self.url+'/api')
            gazu.log_in(self.user, self.t_pwd.text())
            self.access_token = gazu.refresh_token()['access_token']
            return self.access_token
        except Exception as eee:
            print(str(eee))
            self.connection_status = False
            self.status_c.setText('<span style="color:red;">ERROR CONNECTING</span>'+str(eee))
            self.parent.update_log('<span style="color:red;">ERROR CONNECTING</span>'+str(eee))

            return False
 
    def connect_clicked(self):
        if self.get_kitsu_token():
            self.save_settings()
            self.load_settings()
            if self.check_connection():
                self.stackedWidget.setCurrentIndex(1)
                self.t_user_2.setText(self.user)
                self.t_pwd_2.setText('********')
                self.t_url_2.setText(self.url)
                self.connection_status = True
                self.server_worker.start()
                return True
            else:
                return False
        else:
            return False

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                self.settings_dict = json.load(f)
                self.url = self.settings_dict['host']
                self.user = self.settings_dict['username']
                self.access_token = self.settings_dict['key']

                self.t_url.setText(self.url)
                self.t_user.setText(self.user)

                if self.check_connection():
                    #self.connection_status = True
                    return True
                else:
                    #self.connection_status = False
                    return False

                
        except Exception as eee:
            #self.setConnectStatus(False)
            print('Cannot load settings')
            print(eee)
            return False

    def save_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                new_dict = json.load(f)
                new_dict['host'] = self.url
                new_dict['username'] = self.user
                new_dict['key'] = self.access_token
        except:
            new_dict = {
                "host": self.url,
                "username":self.user,
                "key": self.access_token
            }

        j = json.dumps(new_dict, indent=4)
        with open(self.settings_file, 'w') as f:
            print(j, file=f)

        self.update_log('Saved Settings')

    def update_log(self, message, color=None):

        if color:
            self.log_view.append(f'<p style="color:{color};">'+message+'</p> ')
        else:
            self.log_view.append(message)  # Append message to log view

        self.log_view.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Detect if we're clicking in a resize area
            self._dragArea = self._detectDragArea(event.pos())
            if self._dragArea:
                self._isResizing = True
                self._dragPosition = event.globalPosition().toPoint()
                event.accept()
            else:
                # Otherwise, assume we're dragging the window
                self._isDragging = True
                self.old_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

                event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._isResizing and self._dragArea:
            # Calculate how much the mouse has moved
            delta = event.globalPosition().toPoint() - self._dragPosition
            self._resizeWindow(delta)
            self._dragPosition = event.globalPosition().toPoint()
            event.accept()
        elif self._isDragging:
            # Move the window if it's being dragged
            self.move(event.globalPosition().toPoint() - self.old_position)

            event.accept()
        else:
            # Change cursor shape when hovering over edges or corners
            self._setCursorShape(event.pos())
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Stop dragging and resizing
            self._isResizing = False
            self._isDragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _detectDragArea(self, pos):
        """ Detect which area of the window is being clicked for resizing. """
        rect = self.rect()
        top, left, right, bottom = rect.top(), rect.left(), rect.right(), rect.bottom()
        margin = self._resizeMargin

        if left <= pos.x() <= left + margin and top <= pos.y() <= top + margin:
            return 'top-left'
        elif right - margin <= pos.x() <= right and top <= pos.y() <= top + margin:
            return 'top-right'
        elif left <= pos.x() <= left + margin and bottom - margin <= pos.y() <= bottom:
            return 'bottom-left'
        elif right - margin <= pos.x() <= right and bottom - margin <= pos.y() <= bottom:
            return 'bottom-right'
        elif left <= pos.x() <= left + margin:
            return 'left'
        elif right - margin <= pos.x() <= right:
            return 'right'
        elif top <= pos.y() <= top + margin:
            return 'top'
        elif bottom - margin <= pos.y() <= bottom:
            return 'bottom'
        return None

    def _resizeWindow(self, delta):
        """ Resize the window based on the mouse movement delta. """
        if self._dragArea == 'right':
            self.setGeometry(self.x(), self.y(), self.width() + delta.x(), self.height())
        elif self._dragArea == 'bottom':
            self.setGeometry(self.x(), self.y(), self.width(), self.height() + delta.y())
        elif self._dragArea == 'bottom-right':
            self.setGeometry(self.x(), self.y(), self.width() + delta.x(), self.height() + delta.y())
        elif self._dragArea == 'left':
            self.setGeometry(self.x() + delta.x(), self.y(), self.width() - delta.x(), self.height())
        elif self._dragArea == 'top':
            self.setGeometry(self.x(), self.y() + delta.y(), self.width(), self.height() - delta.y())
        elif self._dragArea == 'top-left':
            self.setGeometry(self.x() + delta.x(), self.y() + delta.y(), self.width() - delta.x(), self.height() - delta.y())
        elif self._dragArea == 'top-right':
            self.setGeometry(self.x(), self.y() + delta.y(), self.width() + delta.x(), self.height() - delta.y())
        elif self._dragArea == 'bottom-left':
            self.setGeometry(self.x() + delta.x(), self.y(), self.width() - delta.x(), self.height() + delta.y())

    def _setCursorShape(self, pos):
        """ Change the cursor shape based on the drag area detected. """
        area = self._detectDragArea(pos)
        if area in ['top-left', 'bottom-right']:
            self.setCursor(Qt.SizeFDiagCursor)
        elif area in ['top-right', 'bottom-left']:
            self.setCursor(Qt.SizeBDiagCursor)
        elif area in ['left', 'right']:
            self.setCursor(Qt.SizeHorCursor)
        elif area in ['top', 'bottom']:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)            

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QMenu(parent)


        widget_action = QtWidgets.QWidgetAction(self)
        label = QtWidgets.QLabel()
        label.setMargin(48)
        pixmap = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'icon.png'))  # Replace with your JPEG file path
        scaled_pixmap = pixmap.scaled(128,128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        #self.label.setWordWrap(True)
        widget_action.setDefaultWidget(label)
        menu.addAction(widget_action)


        widget_action = QtWidgets.QWidgetAction(self)
        widget_action.setEnabled(False)
        self.label = QtWidgets.QLabel("")
        self.label.setStyleSheet("border: 1px solid gray;margin:20px")
        #self.label.setWordWrap(True)
        widget_action.setDefaultWidget(self.label)
        menu.addAction(widget_action)

        #menu.addSeparator()



        show_action = menu.addAction("Show")
        show_action.triggered.connect(lambda: parent.show())
        exitAction = menu.addAction("Exit")
        exitAction.triggered.connect(lambda: sys.exit())

        
        self.setContextMenu(menu)
        self.activated.connect(self.on_activate)

    def on_activate(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.parent().show()

    def show_message(self, title, message, icon=None, timeout=1000):
        self.showMessage(title, message, QtGui.QIcon(icon), timeout)
    
    def update_info(self, sss):
        self.label.setMargin(16)
        self.label.setText(sss)

# main driver function
if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    kas = kitsu_action_ui()
    icon = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
    trayIcon = SystemTrayIcon(QtGui.QIcon(icon), kas)
    kas.show_notification.connect(trayIcon.show_message)
    kas.update_signal.connect(trayIcon.update_info)
    kas.server_worker.set_environ()
    trayIcon.setToolTip('Kitsu Action Server')
    trayIcon.show()

    if kas.server_worker.isRunning():
        trayIcon.show_message("Kitsu Action Server","Server is running in the background", icon, 1000)

    sys.exit(app.exec())

