#!/usr/bin/env python
import os, sys
import inspect

import gazu
from PyQt6 import QtCore, QtWidgets, uic, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QApplication
import time

from get_resolve import getResolve


class TimelineExporter(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TimelineExporter, self).__init__(parent)

        # Get the absolute path to the current script
        script_path = os.path.abspath(inspect.getfile(inspect.currentframe()))
        script_dir = os.path.dirname(script_path)
        
        ui_file = os.path.join(os.path.dirname(script_dir), 'ui', 'timeline_export.ui')#os.path.join(script_dir, 'timeline_export.ui')
        self.ui = uic.loadUi(ui_file, self)
        self.resolve = getResolve()[0]
        self.clip_items = self.get_clips()
        self.project = None
        self.project_root = None
        self.setWindowTitle('Export To Kitsu')
        self.done_icon = QtGui.QPixmap(os.path.join(os.path.dirname(script_dir), 'ui', 'icons', 'checkmark.png'))
        self.ui.progressBar.setFormat("Ready")
        
        self.check_gazu_connection()
        self.project_box.addItems(self.get_projects())

        
        # fix stylesheet
        icons_path = os.path.join(os.path.dirname(script_dir), 'ui', 'icons').replace('\\', '/')
        styleSheet = self.styleSheet().replace('image: url(icons:',f'image: url({icons_path}/')
        self.setStyleSheet(styleSheet)

        self.set_project()
        if self.clip_items != []:
            self.build_widgets()
        else:
            self.export_button.setEnabled(False)
        self.project_box.currentIndexChanged.connect(self.set_project)
        self.export_button.released.connect(self.export_clicked)
        self.clip_rez_box.currentIndexChanged.connect(self.clip_rez_box_changed)

    def get_clips(self):
        try:
            video_clips = []
            self.project_manager = self.resolve.GetProjectManager()
            self.resolve_project = self.project_manager.GetCurrentProject()
            self.timeline = self.resolve_project.GetCurrentTimeline()

            clips_dict = []

            track_count = self.timeline.GetTrackCount("video")
            for track_index in range(1, track_count + 1):
                clips = self.timeline.GetItemListInTrack("video", track_index)
                if clips:
                    for clip in clips:
                        properties = clip.GetMediaPoolItem().GetClipProperty()
                        clip_start_point = clip.GetLeftOffset()
                        if clip_start_point < 1001:
                            clip_start_point = 1001
                        clips_dict.append({
                            "name": clip.GetName(),
                            "clip": clip,
                            "track_number": track_index, 
                            "start_frame": clip_start_point,
                            "end_frame": int(clip_start_point)+ int(clip.GetDuration()), #clip.GetEnd(),
                            "fps": properties['FPS'],
                            "resolution": properties['Resolution'],
                            "thumbnail": '',  # self.get_thumbnail()
                            "shot": properties.get('Shot', ''),
                            "scene": properties.get('Scene', ''),
                            "take": properties.get('Take', ''),
                        })
            clips_dict = sorted(
                clips_dict,
                key=lambda clip: (
                    clip["scene"],
                    clip["shot"],
                    clip["track_number"]
                )
            )
        except:
            clips_dict = []

        return clips_dict

    def show_message_box_custom(self, title, message):
        # Create a QMessageBox
        msg = QtWidgets.QMessageBox(self)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        msg.raise_()

        # Wait for the user to close the message box
        msg.exec()

    def show_message_box(self):
        # Create a QMessageBox
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msg.setText("Cannot find KITSU_PROJECT_ROOT, please select an export directory.")
        msg.setWindowTitle("Select Export Directory")
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        
        # Wait for the user to close the message box
        msg.exec()

        # Prompt the user to select a folder
        folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Folder")
        
        # Return the selected folder's path
        return folder

    def export_clicked(self):

        # Get the Resolve project manager and project
        project_manager = self.resolve.GetProjectManager()
        project = project_manager.GetCurrentProject()
        timeline = project.GetCurrentTimeline()

        render_settings = {}

        # Get the render queue
        project.DeleteAllRenderJobs()

        if self.project_root and os.path.exists(self.project_root):
            folder = os.path.join(self.project_root, 'shot')
        else:
            folder = self.show_message_box()

        if not folder:
            return

        # Get the current project
        kitsu_project = gazu.project.get_project_by_name(self.project_box.currentText())

        for row, clip in enumerate(self.clip_items):
            clip['update'] = True
            sequence = gazu.shot.get_sequence_by_name(kitsu_project, self.tableWidget.item(row, 3).text())
            if sequence:
                kistsu_shot_name = f"{self.tableWidget.item(row, 3).text()}_{self.tableWidget.item(row, 4).text()}"
                shot = gazu.shot.get_shot_by_name(sequence, kistsu_shot_name)
                if shot and self.tableWidget.cellWidget(row, 1).findChild(QtWidgets.QCheckBox).isChecked():
                    clip['update'] = self.duplicate_msg(kistsu_shot_name)

        for row, clip in enumerate(self.clip_items):
            clip_info = {
                'is_plate': self.tableWidget.cellWidget(row, 1).findChild(QtWidgets.QCheckBox).isChecked(),
                'og_name': self.ui.tableWidget.item(row, 2).text(),
                'sequence': self.tableWidget.item(row, 3).text(),
                'shot_number' : self.ui.tableWidget.item(row, 4).text(),
                'take': self.ui.tableWidget.item(row, 5).text(),
                'kitsu_shot_name': str(f"{self.ui.tableWidget.item(row, 3).text()}_{self.ui.tableWidget.item(row, 4).text()}"),
                'full_shot_name': self.ui.tableWidget.item(row, 6).text(),
                'resolution': self.ui.tableWidget.item(row, 7).text(),
                'fps': self.ui.tableWidget.item(row, 8).text(),
                'start_frame': self.ui.tableWidget.item(row, 9).text(),
                'end_frame': self.ui.tableWidget.item(row, 10).text(),
                'description': self.ui.tableWidget.cellWidget(row, 11).toPlainText()
            }

            # Calculate clip-specific start and end frames
            if clip['update']:
                
                clip_start = clip['clip'].GetStart()
                clip_end = clip['clip'].GetEnd()

                shot_folder = os.path.join(folder, clip_info['sequence'], clip_info['kitsu_shot_name'], 'media', 'sourceplate', clip_info['take'])
                if os.path.exists(shot_folder):
                    version = len([i for i in os.listdir(shot_folder) if os.path.isdir(os.path.join(shot_folder, i))])+1
                else:
                    version = 1

                # Set the render settings for proxy
                # --------------------------------

                proxy_render_path = os.path.join(shot_folder,f'v{version:04d}','proxy')
                preview_file_path = os.path.join(proxy_render_path, f'{clip_info["full_shot_name"]}.mp4')

                project.SetCurrentRenderMode(1)
                render_settings["TargetDir"] = proxy_render_path
                render_settings["CustomName"] = clip_info['full_shot_name']
                render_settings["ExportVideo"] = True
                render_settings["ExportAudio"] = True 

                # Set the custom resolution and FPS
                resolution = clip["resolution"].split('x')
                original_width = int(resolution[0])
                original_height = int(resolution[1])

                # Target height is 1080p
                target_height = 1080
                scale_factor = target_height / original_height
                scaled_width = int(original_width * scale_factor)

                # Ensure the width is even (some codecs require it)
                if scaled_width % 2 != 0:
                    scaled_width += 1

                render_settings["Resolution"] = "Custom"
                render_settings["FormatWidth"] = scaled_width
                render_settings["FormatHeight"] = target_height
                render_settings["FrameRate"] = clip_info['fps']  # Set the frame rate
                render_settings["MarkIn"] = clip_start
                render_settings["MarkOut"] = clip_end

                proxy_render = render_settings
                # Set the starting frame number for the render
                render_settings["StartFrame"] = clip_info['start_frame']
                project.SetRenderSettings(proxy_render)
                project.SetCurrentRenderFormatAndCodec('mp4', 'H264')

                # Add render job for the clip
                job_id_preview = project.AddRenderJob()

                # Set the render settings, including resolution, FPS, and EXR format with DWAA compression
                # ---------------------------------------------------------------------------------------

                render_path = os.path.join(shot_folder,f'v{version:04d}','main')
                file_path = os.path.join(render_path, f'{clip_info["full_shot_name"]}.exr')

                project.SetCurrentRenderMode(1)
                render_settings["TargetDir"] = render_path
                render_settings["CustomName"] = clip_info['full_shot_name']
                render_settings["ExportVideo"] = True
                render_settings["ExportAudio"] = False  # EXR doesn't support audio

                # Set the custom resolution and FPS
                resolution = clip_info["resolution"].split('x')
                render_settings["Resolution"] = 'Custom'
                render_settings["FormatWidth"] = int(resolution[0])
                render_settings["FormatHeight"] = int(resolution[1])
                render_settings["FrameRate"] = clip_info['fps']  # Set the frame rate
                render_settings["MarkIn"] = clip_start
                render_settings["MarkOut"] = clip_end
                
                # Set the starting frame number for the render
                render_settings["StartFrame"] = clip_info['start_frame']
                project.SetRenderSettings(render_settings)
                project.SetCurrentRenderFormatAndCodec('exr', 'RGBFloatDWAA')

                # disable all clips but the one we are exporting
                track_count = self.timeline.GetTrackCount('video')
                for track_index in range(1, track_count + 1):
                    all_clips = timeline.GetItemListInTrack('video', track_index)
                    for current_clip in all_clips:
                        current_clip.SetClipEnabled(False)
                clip['clip'].SetClipEnabled(True)

                # Add render job for the clip
                job_id = project.AddRenderJob()

                # Start rendering
                project.StartRendering([job_id, job_id_preview], isInteractiveMode=True)
                
                item = self.tableWidget.cellWidget(row, 0).findChild(QtWidgets.QLabel)
                item.setText('Rendering...')
                self.tableWidget.resizeColumnsToContents()
                QApplication.processEvents()

                layout = self.tableWidget.cellWidget(row, 0).layout()
                item.hide()
                sub_progressBar = QtWidgets.QProgressBar()
                sub_progressBar.setFixedWidth(self.tableWidget.columnWidth(0))
                layout.addWidget(sub_progressBar)
                self.tableWidget.resizeColumnsToContents()
                QApplication.processEvents()

                while(project.IsRenderingInProgress()):
                    self.tableWidget.resizeColumnsToContents()
                    QApplication.processEvents()
                    time.sleep(1)
                    for current_job_id in [job_id, job_id_preview]:
                        if project.GetRenderJobStatus(job_id)['JobStatus'] == 'Rendering':
                            self.ui.progressBar.setFormat(f"Exporting: {clip_info['full_shot_name']} at {resolution[0]}x{resolution[1]}, {clip_info['fps']} FPS, EXR DWAA format...")
                        else:
                            self.ui.progressBar.setFormat(f"Exporting: {clip_info['full_shot_name']} PROXY...")

                        if project.GetRenderJobStatus(current_job_id)['JobStatus'] == 'Rendering':
                            completion_percentage = project.GetRenderJobStatus(current_job_id)['CompletionPercentage']

                    sub_progressBar.setValue(completion_percentage)
                    

                if clip_info['is_plate']:
                    item.setText('Sending to Kitsu...')
                    self.tableWidget.resizeColumnsToContents()
                    self.ui.progressBar.setFormat(f'Sending {clip_info["kitsu_shot_name"]} to Kitsu')
                    QApplication.processEvents()
                    self.export_to_kitsu(clip_info, preview_file_path, file_path)


                sub_progressBar.hide()
                item.show()
                layout.setContentsMargins(0, 0, 0, 0)
                item.setPixmap(self.done_icon)
                item.setFixedSize(24, 24)
                item.setScaledContents(True)
                item.setText("")  # No text
                item.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.tableWidget.resizeColumnsToContents()
            
                self.ui.progressBar.setValue(int((row+1)/len(self.clip_items) * 100))
                
                
                QApplication.processEvents()
        self.ui.progressBar.setValue(100)
        self.ui.progressBar.setFormat('DONE !!!')
        self.show_message_box_custom('Project Export Complete', 'Successfully exported shots to Kitsu')
        self.close()
        return True
   
    def duplicate_msg(self, shot_name):
        # Create a QMessageBox
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(f"{shot_name} item already exists, do you want to update it?")
        msg_box.setWindowTitle("Update Confirmation")
        msg_box.setWindowModality(Qt.WindowModality.ApplicationModal)  # Correct enum

        # Add buttons and set roles
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        # Set window flags to keep the message box on top of all windows
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Execute the message box and get the result
        result = msg_box.exec()

        # Check which button was pressed
        if result == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def export_to_kitsu(self, task_item, preview_file, file_path, update=True):
        
        project = gazu.project.get_project_by_name(self.project_box.currentText())
        sequence = gazu.shot.get_sequence_by_name(project, task_item['sequence'])
        if not sequence:
            sequence = gazu.shot.new_sequence(project, task_item['sequence'])

        self.ui.progressBar.setFormat(f"Sending {task_item['kitsu_shot_name']} to Kitsu, please wait...")
        QApplication.processEvents()

        shot = gazu.shot.get_shot_by_name(sequence,task_item['kitsu_shot_name'])

        preview_task = gazu.task.get_task_type_by_name('Plate Ingest')
        if not preview_task:
            preview_task = gazu.task.new_task_type('Plate Ingest', for_entity='Shot')

        if shot:
            shot['data']['frame_in']= task_item['start_frame']
            shot['data']['frame_out']= task_item['end_frame']
            shot['nb_frames'] = float(task_item['end_frame'])-float(task_item['start_frame'])
            shot['data']['fps'] = task_item['fps']
            shot['data']['resolution'] = task_item['resolution']
            shot['description'] = task_item['description']
            gazu.shot.update_shot(shot)
        else:
            shot = gazu.shot.new_shot(
                project, 
                sequence, 
                task_item['kitsu_shot_name'], 
                frame_in=task_item['start_frame'], 
                frame_out=task_item['end_frame'],
                nb_frames = float(task_item['end_frame'])-float(task_item['start_frame']),
                description=task_item['description'],
                data = {
                    'fps':task_item['fps'],
                    'resolution':task_item['resolution'],
                    'description':task_item['description']
                    }
            )
        
        #  Set preview as asset thumbnail
        task = gazu.task.new_task(shot, preview_task)
        status = gazu.task.get_task_status_by_name('done')
        comment = gazu.task.add_comment(task, status, '<b> THUMBNAIL FROM : </b>\n' + file_path)

        preview_file = gazu.task.add_preview(
            task,
            comment,
            preview_file,
            )
        gazu.task.set_main_preview(preview_file)

    def check_gazu_connection(self):
        try:
            self.token = {'access_token': os.environ['KITSU_ACCESS_TOKEN']}
            gazu.client.set_host(url+'/api')
            gazu.client.set_tokens(self.token)
        except:
            url, user, passwrd = ('https://kitsu.vivarium.ca','emile.massie@gmail.com', 'emile220')
            gazu.client.set_host(url+'/api')
            gazu.log_in(user, passwrd)
            os.environ['KITSU_ACCESS_TOKEN'] = gazu.refresh_token()['access_token']
            self.token = {'access_token': os.environ['KITSU_ACCESS_TOKEN']}
            gazu.client.set_tokens(self.token)

        return self.token

    def get_projects(self):
        try:
            return [os.environ['KITSU_PROJECT']]
        except:
            project_list = gazu.project.all_open_projects()
            return [i['name'] for i in project_list]
    
    def set_project(self):
        self.project = gazu.project.get_project_by_name(self.project_box.currentText())
        try:
            self.project_root = self.project['data']['project_root']
        except:
            self.project_root = None
        self.projectRoot.setText(self.project_root)

        self.build_widgets()

    def clip_rez_box_changed(self):
        self.build_widgets()

    def build_widgets(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        kitsu_project = gazu.project.get_project_by_name(self.project_box.currentText())
        if kitsu_project['code']:
            project_name = kitsu_project['code']
        else:
            project_name = kitsu_project['name']
        
        sequences = gazu.shot.all_sequences_for_project(gazu.project.get_project_by_name(self.project_box.currentText())['id'])
        
        for rowPosition, clip in enumerate(self.clip_items):
                #thumbnail_file = clip['thumbnail'].scaled(self.tableWidget.columnWidth(1),self.tableWidget.columnWidth(1), QtCore.Qt.KeepAspectRatio)
                #media_source = clip.source().mediaSource()
                self.tableWidget.insertRow(rowPosition)


                if self.ui.clip_rez_box.currentText() == 'Timeline Resolution':
                    width = self.timeline.GetSetting("timelineResolutionWidth")
                    height = self.timeline.GetSetting("timelineResolutionHeight")
                    clip['resolution'] = f'{width}x{height}'
                elif self.ui.clip_rez_box.currentText() == 'Clip Resolution':
                    properties = clip['clip'].GetMediaPoolItem().GetClipProperty()
                    clip['resolution'] = properties['Resolution']


                # Create QLabel with pixmap
                item = QtWidgets.QLabel('Pending')

                # Wrap it in a QWidget with a layout to center it in the cell
                container = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout(container)
                layout.addWidget(item)
                layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                layout.setContentsMargins(10, 2, 10, 2)
                container.setLayout(layout)

                # Create the checkbox
                checkbox = QtWidgets.QCheckBox()
                if clip['track_number'] == 1:
                    checkbox.setChecked(True)

                # Create a QWidget to hold the checkbox
                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout(widget)
                layout.addWidget(checkbox)
                layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
                widget.setLayout(layout)


                self.tableWidget.setCellWidget(rowPosition, 0, container)   
                self.tableWidget.setCellWidget(rowPosition, 1, widget)
                self.tableWidget.setItem(rowPosition , 2, QtWidgets.QTableWidgetItem(str(clip['name'])))
                self.tableWidget.setItem(rowPosition , 3, QtWidgets.QTableWidgetItem(str(clip['scene'])))
                self.tableWidget.setItem(rowPosition , 4, QtWidgets.QTableWidgetItem(clip['shot']))
                self.tableWidget.setItem(rowPosition , 5, QtWidgets.QTableWidgetItem(clip["take"]))
                self.tableWidget.setItem(rowPosition , 6, QtWidgets.QTableWidgetItem(f'{project_name.upper()}_{clip["scene"]}_{clip["shot"]}_{clip["take"]}'))
                self.tableWidget.setItem(rowPosition , 7, QtWidgets.QTableWidgetItem(str(clip['resolution'])))
                self.tableWidget.setItem(rowPosition , 8, QtWidgets.QTableWidgetItem(str(clip['fps'])))
                self.tableWidget.setItem(rowPosition , 9, QtWidgets.QTableWidgetItem(str(clip['start_frame'])))
                self.tableWidget.setItem(rowPosition , 10, QtWidgets.QTableWidgetItem(str(clip['end_frame'])))
                
                multistring = QtWidgets.QTextEdit()
                self.tableWidget.setCellWidget(rowPosition,11,multistring)

                
                
        self.tableWidget.resizeColumnsToContents()
        #self.tableWidget.resizeRowsToContents()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Exporter = TimelineExporter()
    Exporter.show()
    sys.exit(app.exec())

