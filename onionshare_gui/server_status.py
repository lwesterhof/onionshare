# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import platform
from .alert import Alert
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings, common

class ServerStatus(QtWidgets.QVBoxLayout):
    """
    The server status chunk of the GUI.
    """
    server_started = QtCore.pyqtSignal()
    server_stopped = QtCore.pyqtSignal()
    url_copied = QtCore.pyqtSignal()
    hidservauth_copied = QtCore.pyqtSignal()

    STATUS_STOPPED = 0
    STATUS_WORKING = 1
    STATUS_STARTED = 2

    def __init__(self, qtapp, app, web, file_selection):
        super(ServerStatus, self).__init__()
        self.status = self.STATUS_STOPPED

        self.qtapp = qtapp
        self.app = app
        self.web = web
        self.file_selection = file_selection

        # Helper boolean as this is used in a few places
        self.timer_enabled = False
        # Shutdown timeout layout
        self.server_shutdown_timeout_checkbox = QtWidgets.QCheckBox()
        self.server_shutdown_timeout_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.server_shutdown_timeout_checkbox.toggled.connect(self.shutdown_timeout_toggled)
        self.server_shutdown_timeout_checkbox.setText(strings._("gui_settings_shutdown_timeout_choice", True))
        self.server_shutdown_timeout_label = QtWidgets.QLabel(strings._('gui_settings_shutdown_timeout', True))
        self.server_shutdown_timeout = QtWidgets.QDateTimeEdit()
        # Set proposed timeout to be 5 minutes into the future
        self.server_shutdown_timeout.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
        # Onion services can take a little while to start, so reduce the risk of it expiring too soon by setting the minimum to 2 min from now
        self.server_shutdown_timeout.setMinimumDateTime(QtCore.QDateTime.currentDateTime().addSecs(120))
        self.server_shutdown_timeout.setCurrentSectionIndex(4)
        self.server_shutdown_timeout_label.hide()
        self.server_shutdown_timeout.hide()
        shutdown_timeout_layout_group = QtWidgets.QHBoxLayout()
        shutdown_timeout_layout_group.addWidget(self.server_shutdown_timeout_checkbox)
        shutdown_timeout_layout_group.addWidget(self.server_shutdown_timeout_label)
        shutdown_timeout_layout_group.addWidget(self.server_shutdown_timeout)
        # server layout
        self.status_image_stopped = QtGui.QImage(common.get_resource_path('images/server_stopped.png'))
        self.status_image_working = QtGui.QImage(common.get_resource_path('images/server_working.png'))
        self.status_image_started = QtGui.QImage(common.get_resource_path('images/server_started.png'))
        self.status_image_label = QtWidgets.QLabel()
        self.status_image_label.setFixedWidth(30)
        self.server_button = QtWidgets.QPushButton()
        self.server_button.clicked.connect(self.server_button_clicked)
        server_layout = QtWidgets.QHBoxLayout()
        server_layout.addWidget(self.status_image_label)
        server_layout.addWidget(self.server_button)

        # url layout
        url_font = QtGui.QFont()
        self.url_label = QtWidgets.QLabel()
        self.url_label.setFont(url_font)
        self.url_label.setWordWrap(False)
        self.url_label.setAlignment(QtCore.Qt.AlignCenter)
        self.copy_url_button = QtWidgets.QPushButton(strings._('gui_copy_url', True))
        self.copy_url_button.clicked.connect(self.copy_url)
        self.copy_hidservauth_button = QtWidgets.QPushButton(strings._('gui_copy_hidservauth', True))
        self.copy_hidservauth_button.clicked.connect(self.copy_hidservauth)
        url_layout = QtWidgets.QHBoxLayout()
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.copy_url_button)
        url_layout.addWidget(self.copy_hidservauth_button)

        # add the widgets
        self.addLayout(shutdown_timeout_layout_group)
        self.addLayout(server_layout)
        self.addLayout(url_layout)

        self.update()

    def shutdown_timeout_toggled(self, checked):
        """
        Shutdown timer option was toggled. If checked, show the timer settings.
        """
        if checked:
            self.timer_enabled = True
            # Hide the checkbox, show the options
            self.server_shutdown_timeout_label.show()
            # Reset the default timer to 5 minutes into the future after toggling the option on
            self.server_shutdown_timeout.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
            self.server_shutdown_timeout.show()
        else:
            self.timer_enabled = False
            self.server_shutdown_timeout_label.hide()
            self.server_shutdown_timeout.hide()

    def shutdown_timeout_reset(self):
        """
        Reset the timeout in the UI after stopping a share
        """
        self.server_shutdown_timeout_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.server_shutdown_timeout.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(300))
        self.server_shutdown_timeout.setMinimumDateTime(QtCore.QDateTime.currentDateTime().addSecs(120))

    def update(self):
        """
        Update the GUI elements based on the current state.
        """
        # set the status image
        if self.status == self.STATUS_STOPPED:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_stopped))
        elif self.status == self.STATUS_WORKING:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_working))
        elif self.status == self.STATUS_STARTED:
            self.status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.status_image_started))

        # set the URL fields
        if self.status == self.STATUS_STARTED:
            self.url_label.setText('http://{0:s}/{1:s}'.format(self.app.onion_host, self.web.slug))
            self.url_label.show()
            self.copy_url_button.show()

            if self.app.stealth:
                self.copy_hidservauth_button.show()
            else:
                self.copy_hidservauth_button.hide()

            # resize parent widget
            p = self.parentWidget()
            p.resize(p.sizeHint())
        else:
            self.url_label.hide()
            self.copy_url_button.hide()
            self.copy_hidservauth_button.hide()

        # button
        if self.file_selection.get_num_files() == 0:
            self.server_button.setEnabled(False)
            self.server_button.setText(strings._('gui_start_server', True))
        else:
            if self.status == self.STATUS_STOPPED:
                self.server_button.setEnabled(True)
                self.server_button.setText(strings._('gui_start_server', True))
                self.server_shutdown_timeout.setEnabled(True)
                self.server_shutdown_timeout_checkbox.setEnabled(True)
            elif self.status == self.STATUS_STARTED:
                self.server_button.setEnabled(True)
                self.server_button.setText(strings._('gui_stop_server', True))
                self.server_shutdown_timeout.setEnabled(False)
                self.server_shutdown_timeout_checkbox.setEnabled(False)
            elif self.status == self.STATUS_WORKING:
                self.server_button.setEnabled(False)
                self.server_button.setText(strings._('gui_please_wait'))
                self.server_shutdown_timeout.setEnabled(False)
                self.server_shutdown_timeout_checkbox.setEnabled(False)
            else:
                self.server_button.setEnabled(False)
                self.server_button.setText(strings._('gui_please_wait'))
                self.server_shutdown_timeout.setEnabled(False)
                self.server_shutdown_timeout_checkbox.setEnabled(False)

    def server_button_clicked(self):
        """
        Toggle starting or stopping the server.
        """
        if self.status == self.STATUS_STOPPED:
            if self.timer_enabled:
                # Get the timeout chosen, stripped of its seconds. This prevents confusion if the share stops at (say) 37 seconds past the minute chosen
                self.timeout = self.server_shutdown_timeout.dateTime().toPyDateTime().replace(second=0, microsecond=0)
                # If the timeout has actually passed already before the user hit Start, refuse to start the server.
                if QtCore.QDateTime.currentDateTime().toPyDateTime() > self.timeout:
                    Alert(strings._('gui_server_timeout_expired', QtWidgets.QMessageBox.Warning))
                else:
                    self.start_server()
            else:
                self.start_server()
        elif self.status == self.STATUS_STARTED:
            self.stop_server()

    def start_server(self):
        """
        Start the server.
        """
        self.status = self.STATUS_WORKING
        self.update()
        self.server_started.emit()

    def start_server_finished(self):
        """
        The server has finished starting.
        """
        self.status = self.STATUS_STARTED
        self.copy_url()
        self.update()

    def stop_server(self):
        """
        Stop the server.
        """
        self.status = self.STATUS_WORKING
        self.shutdown_timeout_reset()
        self.update()
        self.server_stopped.emit()

    def stop_server_finished(self):
        """
        The server has finished stopping.
        """
        self.status = self.STATUS_STOPPED
        self.update()

    def copy_url(self):
        """
        Copy the onionshare URL to the clipboard.
        """
        url = 'http://{0:s}/{1:s}'.format(self.app.onion_host, self.web.slug)

        clipboard = self.qtapp.clipboard()
        clipboard.setText(url)

        self.url_copied.emit()

    def copy_hidservauth(self):
        """
        Copy the HidServAuth line to the clipboard.
        """
        clipboard = self.qtapp.clipboard()
        clipboard.setText(self.app.auth_string)

        self.hidservauth_copied.emit()
