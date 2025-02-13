
print('IMPORTING : Kitsu-connect-publisher')

import os, sys
execGui=None
app_path = os.path.dirname(os.path.dirname(__file__))

import gazu
import json
import nuke
import tempfile

import threading

from PySide2.QtCore import QFile, Qt
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QFormLayout, QFileDialog
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QStandardItem, QStandardItemModel, QIcon

from core.progress_dialog import progress_dialog
import datetime


class KitsuConnecPublisher(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setWindowTitle("Kitsu Connect - Publisher")

        loader = QUiLoader()
        self.ui = loader.load(os.path.join(app_path, "ui", 'publisher.ui'), self)

        gazu.set_host(os.getenv('KITSU_HOST')+'/api')
        token = {'access_token': os.getenv('KITSU_ACCESS_TOKEN')}
        gazu.client.set_tokens(token)

        self.context_id = os.getenv('KITSU_CONTEXT_ID')
        self.task = gazu.task.get_task(self.context_id)

        self.ui.context.setText(self.context_id)
        self.ui.project.setText(os.getenv('KITSU_PROJECT'))
        self.ui.sequence.setText(os.getenv('KITSU_SEQUENCE'))
        self.ui.shot.setText(os.getenv('KITSU_SHOT'))
        self.ui.task.setText(os.getenv('KITSU_TASK'))
        
        #self.ui.publish_button.setEnabled(False)
        
        self.ui.publish_button.clicked.connect(self.run_publish)

        #self.settings = KitsuConnectSettings()
        self.progress_dialog = progress_dialog()    
        self.context = None

        self.file_path = None
        self.render_function = None

        if nuke.selectedNodes():
            node = nuke.selectedNodes()[0]
            w, h  = nuke.selectedNode().width(), nuke.selectedNode().height()
            if w > 2048:
                self.ui.reformat_checkbox.setChecked(True)

        self.set_status_items()
        #if self.settings.connection == True:
        #    projects = gazu.project.all_open_projects()

    def set_status_items(self):
        self.ui.t_task_stat.clear()
        for stat in reversed(gazu.task.all_task_statuses()):
            self.ui.t_task_stat.addItem(stat['name'])
            self.ui.t_task_stat.setCurrentIndex(0)


    def send_to_kitsu(self):
        status = gazu.task.get_task_status_by_name(self.ui.t_task_stat.currentText())
        task = gazu.task.get_task(self.context_id)

        task_data = task['data']
        print(task_data)

        if not isinstance(task_data, dict):
            task_data = {}
            

        try:
            task_data['published_files'].append([f"{datetime.datetime.now():%Y-%m-%d}",self.file_path])
        except:
            task_data['published_files'] = [[f"{datetime.datetime.now():%Y-%m-%d}",self.file_path]]

        print(task_data)
        task['data'] = task_data
        gazu.task.update_task(task)

        file_string = '\n\n<hr><b><u>COMPSCRIPT :\n</b></u><i>' + str(nuke.Root().name())+ '\n\n</i><b><u>FILE :</b></u><i>\n' + str(self.file_path) + '</i>\n'
        comment = gazu.task.add_comment(task, status, self.ui.publish_note.toPlainText()+file_string)

        self.preview_file = gazu.task.add_preview(
                task,
                comment,
                self.preview_file_path
            )

    def set_file_path(self, file_path):
        self.file_path = file_path
        self.ui.publish_file_path.setText(self.file_path)

    def run_publish(self):
        self.close()
        self.progress_dialog.setText('Initializing ...')
        self.progress_dialog.update(1)
        self.progress_dialog.show()

        self.progress_dialog.setText('Rendering preview file ...')
        self.progress_dialog.update(10)
        
        self.preview_file_path = self.kitsu_render_preview()

        self.progress_dialog.update(50)

        if self.preview_file_path:
            
            thread = threading.Thread(target=self.send_to_kitsu)
            thread.start()
            self.progress_dialog.setText('Uploading to Kitsu... please wait...')
            self.progress_dialog.update(80)
            thread.join()

            try:
                self.progress_dialog.setText('Setting preview file into database')
                self.progress_dialog.update(90)
                gazu.task.set_main_preview(self.preview_file) #  Set preview as asset thumbnail
            except:
                pass

            self.progress_dialog.setText('DONE !!!')
            self.progress_dialog.update(100)
        else:
            print('Invalid file path from the render function. \n\nself.kitsu_render_preview = None or False')

    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Video Files (*.mov *.mp4)")
        file_dialog.setViewMode(QFileDialog.Detail)

        file_path, _ = file_dialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mov *.mp4)")
        
        if file_path:
            self.ui.publish_file_path.setText(str(file_path))
            self.file_path = file_path

    def show_publisher(self):
        if nuke.selectedNodes():
            if 'Read' in nuke.selectedNodes()[0].Class():
                node = nuke.selectedNodes()[0]
                self.set_file_path(str(node['file'].getValue()))
                self.show()
            else:
                nuke.message('Please select a READ NODE to publish')
        else:
            nuke.message('Please slected a node to publish')
    
    def kitsu_render_preview(self):
        if nuke.selectedNodes():

            node = nuke.selectedNodes()[0]
            w, h  = nuke.selectedNode().width(), nuke.selectedNode().height()
            kitsu_format = None
            lut_file = None
            current_node = node
            try:
                task = gazu.task.get_task(os.environ['KITSU_CONTEXT_ID'])
                shot_id = task['entity_id']
                shot = gazu.shot.get_shot(shot_id)
                lut_file = shot['data']['lut']
            except:
                pass
            

            if lut_file:
                lut_node = nuke.createNode('Vectorfield', inpanel=False)
                lut_node['vfield_file'].setValue(lut_file.replace(os.sep, '/'))
                colorspace = node['colorspace'].value()
                if 'default' in colorspace:
                    colorspace = 'linear'
                lut_node['colorspaceIn'].setValue(colorspace)
                lut_node['colorspaceOut'].setValue('sRGB')
                lut_node.setInput(0, current_node)
                current_node = lut_node

            if self.ui.reformat_checkbox.isChecked():
                kitsu_format = nuke.createNode('Reformat', inpanel=False)
                kitsu_format['type'].setValue('to box')
                kitsu_format['box_width'].setValue(2048)
                kitsu_format.setInput(0, current_node)
                current_node = kitsu_format

            write_node = nuke.createNode('Write')
            write_node['knobChanged'].setValue('')
            write_node.setInput(0,current_node)
            

            # Set the file path and settings for the Write node (modify these according to your requirements)

            # first we doa temp file
            temp_dir = tempfile.mkdtemp()
            output_file_path = os.path.join(temp_dir, 'kitsu_preview.mov')
            output_file_path = output_file_path.replace(os.sep, '/')

            # we set all the settings
            write_node['file'].setValue(output_file_path)
            #write_node['mov64_codec'].setValue(11) # prores
            write_node['mov64_codec'].setValue('mp4v') # prores
            #write_node['mov_prores_codec_profile'].setValue(4)
            write_node['create_directories'].setValue(True)
            
            if nuke.root()['OCIO_config'].value() != 'nuke-default':
                if nuke.root()['colorManagement'].value() == 'OCIO':
                    write_node['colorspace'].setValue('matte_paint')

            first_frame = node['first'].value()
            last_frame = node['last'].value()
            write_node['file'].setValue(output_file_path)
            nuke.execute(write_node, int(first_frame), int(last_frame))
            nuke.delete(write_node)
            
            if kitsu_format:
                nuke.delete(kitsu_format)
            if lut_file:
                nuke.delete(lut_node)

        return output_file_path


print('[ SUCCES !!! ] : Kitsu-connect-publisher')

