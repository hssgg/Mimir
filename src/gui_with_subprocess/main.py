#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = 'Liantian'
# __email__ = "liantian.me+code@gmail.com"
#
# MIT License
#
# Copyright (c) 2018 liantian
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import sys
import psutil
import socket
import platform
import signal
import subprocess
from contextlib import closing
import wx
import wx.adv
from cefpython3 import cefpython as cef
import logging

logging.basicConfig(filename='error.log', level=logging.DEBUG)


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def kill_process_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    gone, still_alive = psutil.wait_procs(children, timeout=5)
    if including_parent:
        parent.kill()
        parent.wait(5)


# Configuration
WIDTH = 800
HEIGHT = 600
WINDOWS_TITLE = "example"


class CustomTaskBarIcon(wx.adv.TaskBarIcon):
    MENU_CLOSE = wx.NewId()
    MENU_RELOAD_URL = wx.NewId()

    def __init__(self, parent):
        wx.adv.TaskBarIcon.__init__(self)
        self.parent = parent
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "icon.ico"),
                             wx.BITMAP_TYPE_ICO))
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_task_bar_left_click)
        self.Bind(wx.EVT_MENU, self.close_app, id=self.MENU_CLOSE)
        self.Bind(wx.EVT_MENU, self.reload_url, id=self.MENU_RELOAD_URL)

    def close_app(self, event):
        self.parent.Close()

    def reload_url(self, event):
        self.parent.reload_url()

    def on_task_bar_left_click(self, event):
        if self.parent.IsShown():
            self.parent.Hide()
        else:
            self.parent.Show()
            self.parent.Centre()

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.MENU_CLOSE, "關閉")
        menu.Append(self.MENU_RELOAD_URL, "回到首页")

        return menu


class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY, title=WINDOWS_TITLE, size=(WIDTH, HEIGHT),
                          style=wx.CAPTION)
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "icon.ico"),
                             wx.BITMAP_TYPE_ICO))
        self.browser = None
        self.tbIcon = CustomTaskBarIcon(self)
        self.parent = parent

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_ICONIZE, self.on_minimize)
        self.Bind(wx.EVT_SHOW, self.on_show)

        self.browser_panel = wx.Panel(self, style=wx.WANTS_CHARS)
        self.browser_panel.Bind(wx.EVT_SIZE, self.on_size)
        self.flask_port = find_free_port()
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.SW_HIDE | subprocess.STARTF_USESHOWWINDOW
        self.flask_process = subprocess.Popen(["web.exe", "--port", str(self.flask_port)],
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)

        self.browser = None

    def on_show(self, event):
        if self.browser:
            return
        window_info = cef.WindowInfo()
        (width, height) = self.browser_panel.GetClientSize().Get()
        assert self.browser_panel.GetHandle(), "Window handle not available yet"
        window_info.SetAsChild(self.browser_panel.GetHandle(), [0, 0, width, height])
        self.browser = cef.CreateBrowserSync(window_info, url="http://127.0.0.1:{}".format(self.flask_port))

    def on_size(self, event):
        if not self.browser:
            return
        cef.WindowUtils().OnSize(self.browser_panel.GetHandle(), 0, 0, 0)

        self.browser.NotifyMoveOrResizeStarted()

    def reload_url(self):
        if not self.browser:
            return
        self.browser.LoadUrl("http://127.0.0.1:{}".format(self.flask_port))

    def on_close(self, event):
        self.tbIcon.RemoveIcon()
        self.tbIcon.Destroy()
        if not self.browser:
            return
        self.browser.ParentWindowWillClose()
        event.Skip()
        self.browser = None
        kill_process_tree(self.flask_process.pid)

    def on_minimize(self, event):
        if self.IsIconized():
            self.Hide()


class CefApp(wx.App):

    def __init__(self, redirect):
        self.timer = None
        self.timer_id = 1
        self.is_initialized = False
        super(CefApp, self).__init__(redirect=redirect)

    def OnInit(self):
        self.initialize()
        return True

    def initialize(self):
        if self.is_initialized:
            return
        self.is_initialized = True
        self.create_timer()

        frame = MainFrame(self)
        self.SetTopWindow(frame)
        # frame.Show()
        # frame.Hide()

    def create_timer(self):
        self.timer = wx.Timer(self, self.timer_id)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(10)  # 10ms timer

    def on_timer(self, event):
        cef.MessageLoopWork()

    def OnExit(self):
        self.timer.Stop()
        return 0


def main():
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    settings = {
        "context_menu": {
            "enabled": False
        },
        "ignore_certificate_errors": True,
        "remote_debugging_port": -1
    }
    cef.DpiAware.EnableHighDpiSupport()
    cef.Initialize(settings=settings)
    app = CefApp(False)
    app.MainLoop()
    del app  # Must destroy before calling Shutdown
    cef.Shutdown()


if __name__ == '__main__':
    main()
