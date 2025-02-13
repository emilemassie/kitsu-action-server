import nuke, os, sys
import importlib.util


print('\n\n----------------------------')
print('     NUKE KITSU-CONNECT     ')
print('----------------------------\n\n')

sys.path.append(os.environ['KITSU_CONNECT_PACKAGES'])
os.environ['KITSU_CONNECT_NUKE_PATH'] = os.path.dirname(__file__)


# Create the main menu
kitsu_menu = nuke.menu("Nuke").addMenu("Kitsu-connect")

# KITSU CONNECT NUKE PANEL

from core import kitsu_connect_panel



pathToClass='kitsu_connect_panel.kitsu_connect_panel' #the full python path to your panel
HRName='Kitsu Connect' #the Human-readable name you want for your panel
regName='kitsu_connect.kitsu_connect_panel' #the internal registered name for this panel (used for saving and loading layouts)
nukescripts.panels.registerWidgetAsPanel(pathToClass, HRName, regName, True).addToPane(nuke.getPaneFor('Viewer.1'))
kitsu_menu.addCommand('Show Kitsu Connect Panel', lambda: kitsu_connect_panel.show_qt_pane("kitsu_connect_panel.kitsu_connect_panel", "Kitsu Connect", "kitsu_connect.kitsu_connect_panel"), 'ctrl+k')


def reload():
    pass

if nuke.env['studio']:
    # Add the timeline export functionnality and menu item
    from core import nuke_studio_export_clips
    kitsu_menu.addCommand("Send Selected Clips to Kitsu", nuke_studio_export_clips.showWindow, 'Ctrl+p')
    kitsu_menu.addCommand("reload", reload, 'ctrl+r')

else:
    # import boot_checkups
    from core import nuke_boot_checkups
    from core import nuke_default_nodes

    # IMPORT ALL THE TOOLSETS
    from core import kitsu_connect_toolsets

    # import and initialize the publisher
    from core import publisher
    global nuke_kitsu_connect_publisher
    nuke_kitsu_connect_publisher = publisher.KitsuConnecPublisher()
    kitsu_menu.addCommand('Publish Selected Read Node', lambda: nuke_kitsu_connect_publisher.show_publisher(), 'ctrl+p')


# Add menu items to the new menu
#if nuke.env['studio']:
#    kitsu_menu.addCommand("Send Timeline Clips to Kitsu", export_timeline, 'Ctrl+p')
#else:
#    kitsu_menu.addCommand("Publish", nuke_kitsu_publisher, 'Ctrl+p')
#    
#from core import settings
#kitsu_menu.addCommand("Settings", settings.KitsuConnectSettings().show, 'Ctrl+Shift+p')




