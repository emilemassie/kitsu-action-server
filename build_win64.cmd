@ECHO ON
python3 -m PyInstaller --clean -y -n kitsu_action_server --noconsole --onefile --icon=./icons/icon.png --add-data ./icons:icons --add-data ./ui:ui kitsu_action_server.py
pause