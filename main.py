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


import wx
from cefpython3 import cefpython as cef
import platform
import sys
import os
import wx.adv

import concurrent.futures
import threading
from flask_app import app as flask_app
from utils import find_free_port

WindowUtils = cef.WindowUtils()

# Configuration
WIDTH = 1024
HEIGHT = 768

WINDOWS_TITLE = "example"

flask_port = find_free_port()


class CustomTaskBarIcon(wx.adv.TaskBarIcon):
    MENU_CLOSE = wx.NewId()

    def __init__(self, parent):
        wx.adv.TaskBarIcon.__init__(self)
        self.parent = parent
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "resources", "icon.png"), wx.BITMAP_TYPE_PNG))
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_task_bar_left_click)
        self.Bind(wx.EVT_MENU, self.close_app, id=self.MENU_CLOSE)

    def close_app(self, event):
        self.parent.Close()

    def on_task_bar_left_click(self, event):
        self.parent.Show()
        self.parent.Restore()

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.MENU_CLOSE, "關閉")

        return menu


class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY, title=WINDOWS_TITLE, size=(WIDTH, HEIGHT), style=wx.SYSTEM_MENU | wx.CAPTION | wx.MINIMIZE_BOX)
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "resources", "icon.png"), wx.BITMAP_TYPE_PNG))
        self.browser = None
        self.tbIcon = CustomTaskBarIcon(self)
        self.parent = parent

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_ICONIZE, self.on_minimize)

        self.browser_panel = wx.Panel(self, style=wx.WANTS_CHARS)
        self.browser_panel.Bind(wx.EVT_SIZE, self.on_size)


        self.embed_browser()
        self.Show()
        self.Centre()

    def embed_browser(self):
        window_info = cef.WindowInfo()
        (width, height) = self.browser_panel.GetClientSize().Get()
        assert self.browser_panel.GetHandle(), "Window handle not available yet"
        window_info.SetAsChild(self.browser_panel.GetHandle(), [0, 0, width, height])
        self.browser = cef.CreateBrowserSync(window_info, url="http://127.0.0.1:{}".format(flask_port))
        # self.browser = cef.CreateBrowserSync(window_info, url="http://127.0.0.1:5000")

    def on_size(self, event):
        if not self.browser:
            return
        WindowUtils.OnSize(self.browser_panel.GetHandle(), 0, 0, 0)

        self.browser.NotifyMoveOrResizeStarted()

    def on_close(self, event):
        self.tbIcon.RemoveIcon()
        self.tbIcon.Destroy()
        if not self.browser:
            return
        self.browser.ParentWindowWillClose()
        event.Skip()
        self.browser = None

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
        frame.Show()

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
    flask_thread = threading.Thread(target=flask_app.run, kwargs={"port": flask_port})
    flask_thread.daemon = True
    flask_thread.start()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    settings = {}
    cef.DpiAware.EnableHighDpiSupport()
    cef.Initialize(settings=settings)
    app = CefApp(False)
    app.MainLoop()
    del app  # Must destroy before calling Shutdown
    cef.Shutdown()



if __name__ == '__main__':
    print("CEF Python {ver}".format(ver=cef.__version__))
    print("Python {ver} {arch}".format(ver=platform.python_version(), arch=platform.architecture()[0]))
    print("wxPython {ver}".format(ver=wx.version()))
    main()
