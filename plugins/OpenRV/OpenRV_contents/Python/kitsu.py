#
# Copyright (C) 2023  Autodesk, Inc. All Rights Reserved. 
# 
# SPDX-License-Identifier: Apache-2.0 
#
import os, sys
from rv.rvtypes import *
from rv.commands import *
from rv.extra_commands import *

import kitsu

class KitsuMenu(MinorMode):
    def __init__(self):
        MinorMode.__init__(self)
        self.SUPPORT_FILES_PATH = os.path.abspath(self.supportPath(kitsu, "kitsu"))
        sys.path.append(self.SUPPORT_FILES_PATH)
        sys.path.append(os.path.join(self.supportPath(kitsu, "kitsu"), 'site-packages'))

        import kitsu_panel
        self.panel = kitsu_panel.KitsuPanel(self.SUPPORT_FILES_PATH)

        self.init(
            "KitsuPanel-mode",
            [
                ("key-down-->", self.show_panel, "Opened Kitsu Panel"),
            ],
            None,
            [
                (
                    "KITSU",
                    [
                        ("Show Kitsu Panel", self.show_panel, "=", None),
                    ],
                )
            ],
        )
    
    def show_panel(self, event):
        if self.panel.dock_widget.isVisible():
            self.panel.dock_widget.hide()
            self.panel.is_showing = False
            displayFeedback("Hiding Kitsu Panel", 2.0)
        else:
            self.panel.dock_widget.show()
            displayFeedback("Opened Kitsu Panel", 2.0)
            self.panel.is_showing = True


def createMode():
    return KitsuMenu()

def startup():
    return KitsuMenu()