
import os, sys, json, shutil, tempfile, nuke

from PySide2.QtCore import QFile, Qt, QCoreApplication
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QSizePolicy, QSpacerItem, QMessageBox
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtWidgets, QtGui, QtCore

folder_path = os.path.dirname(os.path.dirname(__file__))
import gazu




class StretchableWidget(QWidget):
    def __init__(self, combo_box):
        QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout()
        vertical_spacer = QSpacerItem(1, 5, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.setLayout(layout)
        # Add the combo box to the layout with a stretch factor
        layout.addItem(vertical_spacer)
        self.cb = combo_box
        layout.addWidget(self.cb)
        layout.addItem(vertical_spacer)

    def getText(self):
        return self.cb.currentText()


class studio_timeline_exporter(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=None)

        self.resize(900,500)

        self.setWindowTitle("Kitsu Connect - Export Clips")
        self.ui = QUiLoader().load(os.path.join(folder_path, "ui", 'nuke_studio_export_timeline.ui'), self)
        #self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)

        self.files_to_copy = None

        gazu.set_host(os.getenv('KITSU_HOST')+'/api')
        token = {'access_token': os.getenv('KITSU_ACCESS_TOKEN')}
        gazu.client.set_tokens(token)

        self.context_id = os.getenv('KITSU_CONTEXT_ID')
        self.project = os.getenv('KITSU_PROJECT')
        self.project_root = os.getenv('KITSU_PROJECT_ROOT')

        self.ui.export_button.clicked.connect(self.export_timeline)

        if self.project_root == None or self.project_root == '' or self.project_root == 'None':
            self.setProjectRoot()

        self.ui.tableWidget.clearContents()
        self.populateWidgets()


    def setProjectRoot(self):
        # Show the message box
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Cannot find KITSU_PROJECT_ROOT, please set a new project root folder")
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Wait for the user to close the message box
        msg.exec()

        # Prompt the user to select a folder
        folder = QFileDialog.getExistingDirectory(None, "Select Folder")
        
        # Return the selected folder's path
        self.project_root = folder
        project = gazu.project.get_project_by_name(self.project)

        self.project_data = project['data']
        if not project['data'] or project['data'] == 'None':
            project['data'] = {'project_root':None}

        if not 'project_root' in project:
            project['project_root'] = None

        project['data']['project_root'] = folder
        gazu.project.update_project(project)
        os.environ['KITSU_PROJECT_ROOT'] = folder
        return folder


    def populateWidgets(self):
        import hiero, nuke
        self.ui.tableWidget.clearContents()
        self.files_to_copy = None

        self.ui.project.setText(self.project)
        self.ui.projectRoot.setText(self.project_root)

        sequences = gazu.shot.all_sequences_for_project(gazu.project.get_project_by_name(self.project)['id'])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(1,QtWidgets.QHeaderView.Fixed)
        selection = hiero.ui.getTimelineEditor(hiero.ui.activeSequence()).selection()
        self.selection = selection

        if (selection):
            for rowPosition, clip in enumerate(selection):
                thumbnail_file = clip.source().thumbnail()
                media_source = clip.source().mediaSource()
                self.ui.tableWidget.insertRow(rowPosition)

                combo_box = QtWidgets.QComboBox()
                combo_box.setEditable(True)
                combo_box.addItems([i['name'] for i in sequences])
                self.ui.tableWidget.setCellWidget(rowPosition, 0, combo_box)

                label = QtWidgets.QLabel('')
                pixmap = QtGui.QPixmap(clip.source().thumbnail()).scaled(self.ui.tableWidget.columnWidth(1),self.ui.tableWidget.columnWidth(1), QtCore.Qt.KeepAspectRatio)
                label.setPixmap(pixmap)
                self.ui.tableWidget.setCellWidget(rowPosition,1,label)
                self.ui.tableWidget.setRowHeight(rowPosition, pixmap.height())

                self.ui.tableWidget.setItem(rowPosition , 2, QtWidgets.QTableWidgetItem(clip.name()))
                self.ui.tableWidget.setItem(rowPosition , 3, QtWidgets.QTableWidgetItem(f'{media_source.width()}x{media_source.height()}'))
                self.ui.tableWidget.setItem(rowPosition , 4, QtWidgets.QTableWidgetItem(str(clip.source().framerate())))

                if int(clip.source().mediaSource().startTime()+clip.sourceIn()) < 1:
                    in_frame = 1
                    out_frame = int(clip.source().mediaSource().startTime()+clip.sourceOut())+1
                else:
                    in_frame = int(clip.source().mediaSource().startTime()+clip.sourceIn())
                    out_frame = int(clip.source().mediaSource().startTime()+clip.sourceOut())
                    
                self.ui.tableWidget.setItem(rowPosition , 5, QtWidgets.QTableWidgetItem(str(in_frame)))
                self.ui.tableWidget.setItem(rowPosition , 6, QtWidgets.QTableWidgetItem(str(out_frame)))
                
                multistring = QtWidgets.QTextEdit()
                multistring.setAlignment(Qt.AlignLeft | Qt.AlignAbsolute | Qt.AlignVCenter)
                self.ui.tableWidget.setCellWidget(rowPosition,7,multistring)
                
            
            self.ui.tableWidget.resizeColumnsToContents()  


    def show_message_box(self, item_name=None):
        # Create a QMessageBox
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        if item_name:
            msg_box.setText(f"{item_name} already exists, do you want to update it?")
        else:
            msg_box.setText("This item already exists, do you want to update it?")
        msg_box.setWindowTitle("Update Confirmation")
        msg_box.setWindowModality(Qt.ApplicationModal)  # Ensure the message box is on top
        
        # Add buttons to the message box
        msg_box.addButton(QMessageBox.Yes)
        msg_box.addButton(QMessageBox.No)

        # Set window flags to keep the message box on top of all windows
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)

        # Execute the message box and get the result
        result = msg_box.exec_()
        
        # Check which button was pressed
        if result == QMessageBox.Yes:
            return True
        else:
            return False
            
    def export_timeline(self):
        project = gazu.project.get_project_by_name(self.ui.project.text())

        self.files_to_copy = []


        for row in range(self.ui.tableWidget.rowCount()):
            
            sequence = gazu.shot.get_sequence_by_name(project, self.ui.tableWidget.cellWidget(row, 0).currentText())
            if not sequence:
                sequence = gazu.shot.new_sequence(project, self.ui.tableWidget.cellWidget(row, 0).currentText())

            shot_name = self.ui.tableWidget.item(row, 2).text()
            resolution = self.ui.tableWidget.item(row, 3).text()
            fps = self.ui.tableWidget.item(row, 4).text()
            frame_in = int(self.ui.tableWidget.item(row, 5).text())
            frame_out = int(self.ui.tableWidget.item(row, 6).text())
            description =  self.ui.tableWidget.cellWidget(row, 7).toPlainText()
            hiero_track_item = self.selection[row]
            file_path = hiero_track_item.source().mediaSource().firstpath()
            

            self.ui.status_text.setText('STATUS : Exporting '+ shot_name)
            shot = gazu.shot.get_shot_by_name(sequence,shot_name)

            preview_task = gazu.task.get_task_type_by_name('Plate Ingest')
            if not preview_task:
                preview_task = gazu.task.new_task_type('Plate Ingest', for_entity='Shot')

            if shot:
                question = self.show_message_box(shot_name)
                if question:
                    shot['data']['frame_in']= frame_in
                    shot['data']['frame_out']= frame_out
                    shot['nb_frames'] = frame_out-frame_in
                    shot['data']['fps'] = fps
                    shot['data']['resolution'] = resolution
                    shot['description'] = description
                    gazu.shot.update_shot(shot)
            else:
                shot = gazu.shot.new_shot(
                    project, 
                    sequence, 
                    shot_name, 
                    frame_in=frame_in, 
                    frame_out=frame_out,
                    nb_frames = frame_out-frame_in,
                    description=description,
                    data = {
                        'fps':fps,
                        'resolution':resolution,
                        'description':description
                        }
                )
            
            #  Set preview as asset thumbnail
            task = gazu.task.new_task(shot, preview_task)
            status = gazu.task.get_task_status_by_name('done')
            comment = gazu.task.add_comment(task, status, '<b> THUMBNAIL FROM : </b>\n' + file_path)

            thumbnail_path = temp_file_path = tempfile.mkstemp()[1]+'.jpeg'
            hiero_track_item.source().thumbnail().save(thumbnail_path, 'JPEG')    

            preview_file = gazu.task.add_preview(
                task,
                comment,
                thumbnail_path
                )
            gazu.task.set_main_preview(preview_file)

            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path) 
        
            if (self.ui.export_to_root.isChecked()):
                clip = hiero_track_item
                self.ui.status_text.setText('STATUS : Exporting '+ clip.name())

                if self.project_root:
                    project_folder = self.project_root
                    shot_name = clip.name()

                    shot_folder = os.path.join(project_folder, 'shots', sequence['name'])

                    # Create shot folder
                    if not os.path.exists(shot_folder):
                        os.makedirs(os.path.join(shot_folder))
                    if not os.path.exists(os.path.join(shot_folder, shot_name)):
                        os.makedirs(os.path.join(shot_folder, shot_name))

                    og_file_path = clip.source().mediaSource().firstpath()
                    destination_path = os.path.join(shot_folder, shot_name, 'media','sourceplate')
                    self.files_to_copy.append([og_file_path, destination_path, row])
                        
        for file in self.files_to_copy:
            og_file_path = file[0]
            destination_path = file[1]
            row = file[2]

            try:
                folder_count = 0
                for dir in os.listdir(destination_path):
                    if os.path.isdir(os.path.join(destination_path,dir)):
                        folder_count += 1
            except:
                pass

            destination_path_version = os.path.join(destination_path, 'v'+'{:04d}'.format(folder_count+1))

            if not os.path.exists(destination_path_version):
                os.makedirs(destination_path_version)

            self.ui.status_text.setText('STATUS : Copying '+ os.path.basename(og_file_path))
            self.copy_file_with_progress(og_file_path, os.path.join(destination_path_version, os.path.basename(og_file_path)), row)

        self.ui.status_text.setText('STATUS : Done !!!')

        msg = QMessageBox()
        msg.setText("Exported Shots Successfully !!!")
        msg.setWindowTitle("Succes !!!")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        # Wait for the user to close the message box
        msg.exec()



    def scan_for_exr_sequences(self,directory):
        import glob
        from collections import defaultdict
        # Use glob to find all .exr files in the directory
        exr_files = glob.glob(os.path.join(directory, '*.exr'))

        # Dictionary to hold sequences
        sequences = defaultdict(list)

        # Regular expression to match sequence files
        import re
        sequence_pattern = re.compile(r'(.*?)(\d+)(\.exr)$')

        for file in exr_files:
            filename = os.path.basename(file)
            match = sequence_pattern.match(filename)
            if match:
                prefix, frame_number, extension = match.groups()
                sequences[prefix].append((int(frame_number), file))

        # Sort each sequence by frame number
        for prefix in sequences:
            sequences[prefix].sort()

        # Convert each list of tuples to a list of filenames
        for prefix in sequences:
            sequences[prefix] = [file for frame_number, file in sequences[prefix]]

        return sequences

    def copy_file_with_progress(self, source, destination, row, chunk_size=4096*4096):
        # Get the size of the source file
        #nuke.tprint(source, destination)
        total_size = os.stat(source).st_size
        bytes_written = 0

        if str(source).endswith('.exr'):
            directory = os.path.dirname(source)
            exr_sequences = self.scan_for_exr_sequences(directory)

            # Print the sequences
            for prefix, files in exr_sequences.items():
                print(f"Sequence {prefix}:")
                files_lenght = len(files)
                for file_num, file in enumerate(files):
                    percentage = file_num/files_lenght*100
                    print(percentage)
                    status = f"Copying {os.path.basename(file)}... {percentage:.2f}%"
                    self.ui.status_text.setText(f'STATUS : {status}')
                    self.setRowColor(row,[0,int(percentage),0])
                    QCoreApplication.processEvents()
                    nuke.tprint(status, end='\r')
                    shutil.copyfile(file, os.path.join(os.path.dirname(destination),os.path.basename(file)))          

        else:
            with open(source, 'rb') as fsrc, open(destination, 'wb') as fdst:
                while True:
                    # Read a chunk from the source file
                    chunk = fsrc.read(chunk_size)
                    if not chunk:
                        break

                    # Write the chunk to the destination file
                    fdst.write(chunk)
                    bytes_written += len(chunk)

                    # Calculate and print the progress
                    percentage = (bytes_written / total_size) * 100
                    status = f"Copying {os.path.basename(source)}... {percentage:.2f}%"
                    self.ui.status_text.setText(f'STATUS : {status}')
                    nuke.tprint(percentage)
                    self.setRowColor(row,[0,int(percentage),0])
                    QCoreApplication.processEvents()
                    nuke.tprint(status, end='\r')
        
    def setRowColor(self, row, color):
        r = int(color[0])
        g = int(color[1])
        b = int(color[2])
        for i in range(self.ui.tableWidget.columnCount()):
            try:
                self.ui.tableWidget.item(row, i).setBackgroundColor(QtGui.QColor(r,g,b))
            except:
                color = str(r) +','+str(g)+','+str(b)
                self.ui.tableWidget.cellWidget(row, i).setStyleSheet('background-color : rgb('+color +');')




def showWindow():
    global studio_timeline_export
    studio_timeline_export = studio_timeline_exporter()
    studio_timeline_export.show()