from PIL                          import Image
from PyQt5                        import QtCore, QtGui, QtWidgets
from bscripts.api_communicate     import call_api
from bscripts.customwidgets       import LeafAPI, MovableScrollWidget, RootAPI
from bscripts.customwidgets       import create_scb_branch
from bscripts.tricks              import tech as t
from script_pack.preset_colors    import *
from script_pack.settings_widgets import GLOBALHighLight, GODLabel
import os
import screeninfo
#from pyscbwrapper import SCB

class SCBMain(QtWidgets.QMainWindow):
    def __init__(self):
        super(SCBMain, self).__init__()
        self.show()
        self.bookmarks = []
        self.setWindowTitle(os.environ['PROGRAM_NAME'] + ' ' + os.environ['VERSION'])
        self.position_mainwindow(primary=True)
        self.setup_gui()
        t.style(self, name='main')
        t.style(self.centralwidget, background='rgba(10,10,10,110)')
        t.start_thread(dummy=True, slave_args=0.5, master_fn=self.post_init)

    def position_mainwindow(self, primary=False):
        if primary:
            primary_monitor = [x for x in screeninfo.get_monitors() if x.is_primary]
            if primary_monitor:
                primary = primary_monitor[0]

                x = int(primary.x)
                y = int(primary.y)
                w = int(primary.width * 0.8)
                h = int(primary.height * 0.8)

                self.move(x + int(primary.width * 0.1), y + (int(primary.height * 0.1)))
                self.resize(w, h)
            else:
                self.resize(1000, 700)
                self.move(100,100)

    def setup_gui(self):

        self.centralwidget = QtWidgets.QWidget(self)

        self._gridlayout = QtWidgets.QGridLayout(self.centralwidget)
        self._gridlayout.setContentsMargins(0, 22, 0, 0)
        self._gridlayout.setSpacing(0)

        self.back = QtWidgets.QFrame(self.centralwidget)
        self.back.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.back.setFrameShadow(QtWidgets.QFrame.Plain)
        self.back.setLineWidth(0)

        self.grid_layout = QtWidgets.QGridLayout(self.back)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(0)

        self.scroll_area = QtWidgets.QScrollArea(self.back)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.scroll_area.sizePolicy().hasHeightForWidth())

        self.scroll_area.setSizePolicy(sizePolicy)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_area.setFrameShadow(QtWidgets.QFrame.Plain)
        self.scroll_area.setLineWidth(0)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.scroll_area.setWidgetResizable(True)

        self.scrollcanvas_main = QtWidgets.QWidget()

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.scrollcanvas_main.sizePolicy().hasHeightForWidth())

        self.scrollcanvas_main.setSizePolicy(sizePolicy)

        self.__gridlayout = QtWidgets.QGridLayout(self.scrollcanvas_main)
        self.__gridlayout.setContentsMargins(0, 0, 0, 0)
        self.__gridlayout.setSpacing(0)

        self.scroll_area.setWidget(self.scrollcanvas_main)

        self.grid_layout.addWidget(self.scroll_area, 0, 0, 1, 1)

        self._gridlayout.addWidget(self.back, 0, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)


    def post_init(self):
        self.draw_root()
        self.draw_bookmarks()

    class BookMarkWidget(GLOBALHighLight, GODLabel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setLineWidth(1)
            self.setFrameShape(QtWidgets.QFrame.Box)

        def default_colors(self):
            self.deactivated_on = dict(color=BLACK, background=SMISK_LIGHT)
            self.deactivated_off = dict(color=BLACK, background=SMISK_HARD)

            self.deactivated_on = dict(color=TEXT_WHITE, background=BOOKMARK_DE_1)
            self.deactivated_off = dict(color=TEXT_OFF, background=DARK_BACK)

        def change_colors(self):
            if not self.activated:
                for i in ['activated_on', 'activated_off', 'deactivated_on', 'deactivated_off']:
                    for ii in [self]:
                        ii.swap_preset(i, restore=True)

            else:
                self.swap_preset('deactivated_off', new_value=dict(background=ACTIVE_GREEN))
                self.swap_preset('deactivated_on', new_value=dict(background=HIGH_GREEN))
                self.swap_preset('deactivated_off', new_value=dict(color=TEXT_WHITE))
                self.swap_preset('deactivated_on', new_value=dict(color=TEXT_WHITE))

        def setup_killsignal(self):
            self.bookmark_signal = t.signals()
            self.bookmark_signal.killswitch.connect(self.killswitch)
            self.child.signal = self.bookmark_signal

        def killswitch(self):
            self.activation_toggle(force=False)
            self.change_colors()
            t.signal_highlight()
            if self.child:
                self.child.close()
                self.child = False

        def open_seed(self):
            self.activation_toggle()
            self.change_colors()

            if self.activated:
                self.child = MovableScrollWidget(
                    place=self.main.scrollcanvas_main, url=self.url, query=self.query, main=self.main)

                self.setup_killsignal()
                self.child.make_title(self.text() or 'BOOKMARK')
                self.child.data = self.data

                if type(self.data) == dict:
                    self.child.make_title(text=self.data['title'])
                    self.main.grow_new_leaf(data=self.data, url=self.url, movablewidget=self.child)
                else:
                    data = [(x['text'], x,) for x in self.data]
                    data.sort(key=lambda x: x[0])
                    data = [x[1] for x in data]
                    self.main.grow_new_bransch(data=data, url=self.url, movablewidget=self.child)
            else:
                self.bookmark_signal.killswitch.emit()

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            if ev.button() == 1:
                self.open_seed()
            else:
                class KILLER(QtWidgets.QLabel):
                    def __init__(self, place, text, delete):
                        super().__init__(place)
                        self.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
                        self.setText(text)
                        self.delete = delete
                        self.parent = place

                    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                        if self.delete:
                            bookmarks = t.config('bookmarks')
                            if self.bookmark_count in bookmarks:
                                bookmarks.pop(self.bookmark_count)
                                t.save_config('bookmarks', bookmarks)
                                self.partner.close()
                        else:
                            self.parent.close()

                parent = QtWidgets.QLabel(self)
                t.pos(parent, inside=self)
                parent.show()

                delete = KILLER(parent, 'DELETE', True)
                delete.bookmark_count = self.bookmark_count
                delete.partner = self
                t.pos(delete, width=self.width() * 0.5, height=self)
                t.style(delete, background='red', color=BLACK)
                t.correct_broken_font_size(delete)

                cancel = KILLER(parent, 'CANCEL', False)
                t.pos(cancel, size=delete, after=delete)
                t.style(cancel, background='green', color=BLACK)
                t.correct_broken_font_size(cancel)

    def draw_this_bookmark(self, bookmark):
        widget = self.BookMarkWidget(place=self, main=self, mouse=True)
        widget.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        widget.default_colors()
        widget.setText(bookmark['text'])
        widget.url = bookmark['url']
        widget.query = bookmark['query']
        widget.data = bookmark['data']
        widget.bookmark_count = bookmark['count']

        width = t.shrink_label_to_text(widget, no_change=True, x_margin=12)

        if width < 80:
            width = 80

        height = t.shrink_label_to_text(widget, no_change=True, height=True) or 20

        t.pos(widget, width=width, height=height * 1.1)
        self._gridlayout.setContentsMargins(0, widget.height(), 0, 0)
        if self.bookmarks:
            t.pos(widget, after=self.bookmarks[-1], x_margin=1)

        self.bookmarks.append(widget)

    def draw_bookmarks(self):
        self.bookmarks = []
        bookmarks = t.config('bookmarks')

        if type(bookmarks) != dict:
            bookmarks = {}

        for i in bookmarks:
            self.draw_this_bookmark(bookmark=bookmarks[i])
        t.signal_highlight()

    def grow_new_seed(self, data, url, movablewidget):
        for count, text in enumerate(data['valueTexts']):

            seed_data = dict(
                text=text,
                code_text=data['text'],
                code=data['code'],
                value=data['values'][count]
            )
            canvas = create_scb_branch(
                place=movablewidget, main=self, widget=LeafAPI.Leaf, data=seed_data, width=movablewidget.width()
            )
            canvas.url = url
            movablewidget.widgets.append(canvas)

        movablewidget.expand_me()
        movablewidget.load_crown()
        t.signal_highlight()

    def grow_new_leaf(self, data, url, movablewidget):
        for i in data['variables']:
            canvas = create_scb_branch(
                data=i, place=movablewidget, widget=LeafAPI, main=self, width=movablewidget.width()
            )
            canvas.url = url
            movablewidget.widgets.append(canvas)

        movablewidget.expand_me()
        movablewidget.load_crown()
        t.signal_highlight()

    def grow_new_bransch(self, data, url, movablewidget):
        for i in data:
            canvas = create_scb_branch(
                data=i, place=movablewidget, widget=RootAPI, main=self, width=movablewidget.width()
            )
            canvas.url = url + i['id'] + '/'
            movablewidget.widgets.append(canvas)

        movablewidget.expand_me()
        movablewidget.load_crown()
        t.signal_highlight()

    def draw_root(self):
        def set_starting_crown(self):
            tree = 'https://cli'
            tree += 'par,.world/wp-con,en,/uploads/2020/09/Big-,ree-clipar,-,ransparen,.png'.replace(',','t')

            tmpfile = t.tmp_file(file_of_interest=tree, hash=True, reuse=True, extension='webp')

            def slave_work():
                t.download_file(tree, tmpfile)
                if os.path.exists(tmpfile):

                    img = Image.open(tmpfile)

                    width = self.root.width()
                    if width and img.size[0] < width:
                        height = round(img.size[1] * (width / img.size[0]))
                    else:
                        width = img.size[0]
                        height = img.size[1]

                    image_size = width, height
                    img.thumbnail(image_size, Image.ANTIALIAS)
                    img.save(tmpfile, "webp", quality=70, method=6)
                    img.close()

                    img = Image.open(tmpfile)
                    img = img.convert("RGBA")
                    img = img.crop((0, 0, width, int(height * 0.85)))
                    datas = img.getdata()

                    new_data = []
                    for item in datas:
                        if sum(item[0:3]) > 700 or item[3] < 30:
                            new_data.append((255, 255, 255, 0))
                        else:
                            new_data.append(item)

                    img.putdata(new_data)
                    img.save(tmpfile, "webp", quality=70, method=6)
                    img.close()

            def master_work():
                self.root.filesdropped([tmpfile], None, 1)
                self.setWindowTitle(self.windowTitle() + ' ' + 'tree planted!')

            if not self.root.crown:
                t.start_thread(slave_work, master_fn=master_work)

        class ROOT(MovableScrollWidget):
            class TITLE(MovableScrollWidget.TITLE):
                def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
                    return # we dont bookmark root

        url = 'http://api.scb.se/OV0104/v1/doris/en/ssd/'
        data = call_api(url=url)
        if data:
            self.root = ROOT(place=self.scrollcanvas_main, main=self, url=url)
            self.root.make_title(text='ROOT')
            self.root.move(20,280)
            self.root.data = data

            data = [(x['text'], x,) for x in data]
            data.sort(key=lambda x:x[0])
            data = [x[1] for x in data]
            self.grow_new_bransch(data=data, url=url, movablewidget=self.root)
            set_starting_crown(self)




# import random
# from PyQt5                        import QtCore, QtGui, QtWidgets
# from PyQt5.Qt                     import QPixmap
# from PyQt5.QtCore                 import QPoint
# from bscripts.tricks              import tech as t
# from script_pack.preset_colors    import *
# from script_pack.settings_widgets import Canvas, DragDroper, GLOBALHighLight
# from script_pack.settings_widgets import GODLabel, create_indikator
# from bscripts.database_stuff import DB, sqlite
# import json
# import os
# import pickle
# import requests
# import screeninfo
# import sys
# import time
# #from pyscbwrapper import SCB
#
#
# class SCBMain(QtWidgets.QMainWindow):
#     def __init__(self):
#         super(SCBMain, self).__init__()
#
#         self.show()
#         self.bookmarks = []
#         self.setWindowTitle(os.environ['PROGRAM_NAME'] + ' ' + os.environ['VERSION'])
#         self.position_mainwindow(primary=True)
#         self.setup_gui()
#         self.post_init()
#
#     def position_mainwindow(self, primary=False):
#         if primary:
#             primary_monitor = [x for x in screeninfo.get_monitors() if x.is_primary]
#             if primary_monitor:
#                 primary_monitor = primary_monitor[0]
#                 self.resize(int(primary_monitor.width * 0.8), int(primary_monitor.height * 0.8))
#                 self.move(int(primary_monitor.width * 0.1), int(primary_monitor.height * 0.1))
#
#     def setup_gui(self):
#
#         self.centralwidget = QtWidgets.QWidget(self)
#
#         self._gridlayout = QtWidgets.QGridLayout(self.centralwidget)
#         self._gridlayout.setContentsMargins(0, 22, 0, 0)
#         self._gridlayout.setSpacing(0)
#
#         self.back = QtWidgets.QFrame(self.centralwidget)
#         self.back.setFrameShape(QtWidgets.QFrame.NoFrame)
#         self.back.setFrameShadow(QtWidgets.QFrame.Plain)
#         self.back.setLineWidth(0)
#
#         self.grid_layout = QtWidgets.QGridLayout(self.back)
#         self.grid_layout.setContentsMargins(0, 0, 0, 0)
#         self.grid_layout.setSpacing(0)
#
#         self.scroll_area = QtWidgets.QScrollArea(self.back)
#
#         sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
#         sizePolicy.setHorizontalStretch(1)
#         sizePolicy.setVerticalStretch(1)
#         sizePolicy.setHeightForWidth(self.scroll_area.sizePolicy().hasHeightForWidth())
#
#         self.scroll_area.setSizePolicy(sizePolicy)
#         self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
#         self.scroll_area.setFrameShadow(QtWidgets.QFrame.Plain)
#         self.scroll_area.setLineWidth(0)
#         self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
#         self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
#         self.scroll_area.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
#         self.scroll_area.setWidgetResizable(True)
#
#         self.scrollcanvas_main = QtWidgets.QWidget()
#
#         sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
#         sizePolicy.setHorizontalStretch(1)
#         sizePolicy.setVerticalStretch(1)
#         sizePolicy.setHeightForWidth(self.scrollcanvas_main.sizePolicy().hasHeightForWidth())
#
#         self.scrollcanvas_main.setSizePolicy(sizePolicy)
#
#         self.__gridlayout = QtWidgets.QGridLayout(self.scrollcanvas_main)
#         self.__gridlayout.setContentsMargins(0, 0, 0, 0)
#         self.__gridlayout.setSpacing(0)
#
#         self.scroll_area.setWidget(self.scrollcanvas_main)
#
#         self.grid_layout.addWidget(self.scroll_area, 0, 0, 1, 1)
#
#         self._gridlayout.addWidget(self.back, 0, 0, 1, 1)
#         self.setCentralWidget(self.centralwidget)
#
#     def get_wt_ht(self):
#         """
#         returns width taken and height taken AND:
#         NEW Width + NEW Height if you need new row
#         :param key: self.widgets['key']
#         :return: tuple
#         """
#         wt = 1 # width taken
#         ht = 1 # height taken
#         nw = 1 # next approved width
#         nh = 1 # next approved height
#
#         for count in range(len(self.widgets) - 1, -1, -1):
#             widget = self.widgets[count]
#             if widget.geometry().top() >= ht: # height taken
#                 ht = widget.geometry().top()
#
#                 if widget.geometry().right() > wt: # width taken
#                     wt = widget.geometry().right() + 2
#
#                 if widget.geometry().bottom() > nh: # next height
#                     nh = widget.geometry().bottom() + 2
#
#         return wt, ht, nw, nh
#
#     class MovableScrollWidget(QtWidgets.QLabel):
#         def __init__(self, place, main, parent, url, data):
#             super().__init__(place)
#             self.make_toolplate()
#             self.make_backplate()
#             self.make_scrollarea()
#
#             if type(url) != dict:
#                 url = dict(url=url)
#
#             self.data = data
#             self.urldict = url
#             self.parent = parent
#             self.main = main
#             self._type = '_' + t.md5_hash_string()
#             self.show()
#             t.style(self, background=TRANSPARENT)
#             t.style(self.scrollarea, background=TRANSPARENT)
#             t.style(self.backplate, background=TRANSPARENT)
#
#         def load_crown(self):
#             if 'data' in self.urldict:
#                 data = json.dumps(self.urldict['data'])
#                 url = self.urldict['url'] + '&data=' + data
#             else:
#                 url = self.urldict['url']
#
#             pixmap = t.config(url, image=True)
#             if pixmap:
#                 path = t.tmp_file(url, hash=True, reuse=True)
#                 if not os.path.exists(path) or not os.path.getsize(path):
#                     with open(path, 'wb') as f:
#                         f.write(pixmap)
#
#                 factor = t.config(url)
#                 if factor:
#                     self.set_this_add_crown(path, width_percentage=factor)
#                 else:
#                     self.set_this_add_crown(path)
#
#                 self.title.position_crown()
#
#         def raise_us(self):
#             if 'title' in dir(self):
#                 self.title.raise_us()
#
#         def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
#             self.set_positions()
#
#         def set_positions(self, x=0, y=0):
#             if 'columns' in dir(self):
#                 height = self.columns[0].geometry().bottom() +1
#             elif 'title' in dir(self):
#                 height = self.title.geometry().bottom() +1
#             else:
#                 return
#
#             t.pos(self.toolplate, height=height, width=self)
#             t.pos(self.backplate, below=self.toolplate, width=self, y_margin=y)
#             t.pos(self.scrollarea, below=self.toolplate, width=self, y_margin=y)
#
#         def make_toolplate(self):
#             self.toolplate = QtWidgets.QLabel(self)
#             t.style(self.toolplate, background=TRANSPARENT)
#             self.toolplate.show()
#
#         def make_backplate(self):
#             self.backplate = QtWidgets.QWidget(self)
#             t.style(self.backplate, background=TRANSPARENT)
#             t.pos(self.backplate, height=0)
#             self.backplate.show()
#
#         def make_scrollarea(self):
#             self.scrollarea = QtWidgets.QScrollArea(self)
#             self.scrollarea.setWidget(self.backplate)
#             self.scrollarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
#             self.scrollarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
#             self.scrollarea.setLineWidth(0)
#             self.scrollarea.setFrameShape(QtWidgets.QScrollArea.Box)
#             self.scrollarea.show()
#
#         def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
#             if 'crown' in dir(self):
#                 self.crown.close()
#
#         class CROWN(QtWidgets.QLabel):
#             def __init__(self, place, path, width, partner):
#                 super().__init__(place)
#                 self.partner = partner
#                 pixmap = QPixmap(path).scaledToWidth(width, QtCore.Qt.SmoothTransformation)
#                 playspace = partner.width() - width
#                 self.random = random.randint(0, playspace)
#                 t.pos(self, size=pixmap)
#                 t.style(self, background=TRANSPARENT)
#                 self.setPixmap(pixmap)
#                 self.show()
#
#             def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
#                 self.partner.title.drag_widget(ev)
#
#             def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
#                 self.partner.title.old_position = ev.globalPos()
#                 if ev.button() == 1:
#                     self.partner.title.raise_us()
#
#             def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
#                 self.partner.title.mouseReleaseEvent(ev)
#
#         def set_this_add_crown(self, path, width_percentage=0.5):
#             if not os.path.exists(path):
#                 return
#
#             width = int(self.width() * width_percentage)
#             self.crown = self.CROWN(self.main.scrollcanvas_main, path, width, partner=self)
#
#         def filesdropped(self, filelist, ev):
#             loc = t.separate_file_from_folder(filelist[0])
#             if loc.ext.lower() not in {'webp', 'jpeg', 'jpg', 'png', 'bmp'}:
#                 return
#
#             if 'data' in self.urldict:
#                 data = json.dumps(self.urldict['data'])
#                 url = self.urldict['url'] + '&data=' + data
#             else:
#                 url = self.urldict['url']
#
#             t.tmp_file(url, hash=True, delete=True)
#             blob = t.make_image_into_blob(image_path=loc.full_path, width=self.title.width())
#             t.save_config(url, blob, image=True)
#
#             heightfactor = ev.pos().x() / self.width()
#
#             if 'crown' in dir(self):
#                 self.crown.close()
#                 del self.crown
#
#             self.set_this_add_crown(loc.full_path, heightfactor)
#             self.title.position_crown()
#
#             t.save_config(url, heightfactor)
#
#         class TITLE(GODLabel, DragDroper):
#             def __init__(self, place, text, parent, tooltip=False, *args, **kwargs):
#                 super().__init__(place=place, *args, **kwargs)
#                 self.parent = parent
#                 self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
#                 self.setText(text)
#                 self.setLineWidth(1)
#                 self.setFrameShape(QtWidgets.QFrame.Box)
#                 t.style(self, background=TOOLTIP_DRK_BG, color=TITLE_WHITE)
#                 self.show()
#                 if tooltip:
#                     self.setToolTip(text)
#
#             def drag_widget(self, ev):
#                 if 'old_position' not in dir(self):
#                     self.old_position = ev.globalPos()
#
#                 delta = QPoint(ev.globalPos() - self.old_position)
#                 self.parent.move(self.parent.x() + delta.x(), self.parent.y() + delta.y())
#                 self.old_position = ev.globalPos()
#
#                 if 'crown' in dir(self.parent):
#                     self.position_crown()
#
#             def position_crown(self):
#                 t.pos(self.parent.crown, above=self.parent, move=[self.parent.crown.random, 0])
#
#             def raise_us(self):
#                 self.parent.raise_()
#                 if 'crown' in dir(self.parent):
#                     self.parent.crown.raise_()
#
#             def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
#                 self.drag_widget(ev)
#
#             def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
#                 if ev.button() == 2 and self.text() != 'ROOT' and 'signal' in dir(self):
#                     self.signal.killswitch.emit()
#
#             def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
#                 self.old_position = ev.globalPos()
#                 if ev.button() == 1:
#                     self.raise_us()
#
#             def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
#                 if 'save_thingey' in dir(self):
#                     return
#
#                 class SAVEThingey(Canvas):
#                     class Button(Canvas.Button):
#                         def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
#                             text = self.parent.lineedit.text().strip()
#                             bookmarks = t.config('bookmarks')
#                             if not bookmarks:
#                                 bookmarks = {}
#
#                             for i in range(10):
#                                 if i in bookmarks:
#                                     continue
#
#                                 bookmarks[i] = dict(text=text, urldict=self.parent.urldict, data=self.parent.data)
#                                 t.save_config('bookmarks', bookmarks)
#                                 self.parent.signal.killswitch.emit()
#                                 return
#
#                 def killswitch():
#                     self.save_thingey.close()
#                     del self.save_thingey
#
#                 self.save_thingey = create_indikator(
#                     place=self,
#                     button=True,
#                     lineedit=True,
#                     tiplabel='BOOKMARK',
#                     button_listen=True,
#                     lineedit_background=BLACK,
#                     lineedit_foreground=TEXT_WHITE,
#                     canvas_background=BLACK,
#                     deactivated_off=dict(background='brown'),
#                     deactivated_on=dict(background='yellow'),
#                     mouse=True,
#                     edge=1,
#                     Special=SAVEThingey,
#                 )
#
#                 t.pos(self.save_thingey, inside=self)
#                 self.save_thingey.urldict = self.parent.urldict
#                 #self.save_thingey.data = self.parent.parent.data
#                 self.save_thingey.data = self.parent.data
#                 self.save_thingey.signal = t.signals()
#                 self.save_thingey.signal.killswitch.connect(killswitch)
#
#         def make_title(self, text, width=500):
#             self.title = self.TITLE(self.toolplate, text=text, parent=self, drops=True)
#             self.title.filesdropped = self.filesdropped
#
#             t.pos(self.title, height=30, width=width)
#             t.correct_broken_font_size(self.title, y_margin=4, minsize=14)
#             if t.correct_broken_font_size(self.title, maxsize=14, shorten=True):
#                 org_width = self.title.width()
#                 for c in range(3, 7):
#                     t.pos(self.title, width=self.title, add=org_width)
#                     if not t.correct_broken_font_size(self.title, maxsize=14, shorten=True) or c == 6:
#                         t.pos(self.title, width=org_width, height=self.title.height() * c)
#                         self.title.setWordWrap(True)
#                         self.title.setText(text)
#                         break
#
#             if self.width() < self.title.width():
#                 t.pos(self, width=self.title)
#             else:
#                 self.set_positions()
#
#         def make_column(self, coldict, x=0, y=0):
#             self.columns = []
#             for count in range(len(coldict)):
#                 for text, lenlen in coldict[count].items():
#                     column = self.TITLE(self.toolplate, text=text, parent=self, tooltip=True)
#                     w = (self.title.width() - len(coldict)) / len(coldict)
#                     t.pos(column, height=30, width=w)
#                     t.correct_broken_font_size(column, y_margin=4, maxsize=14, minsize=13)
#
#                     if count+1 != len(coldict) and lenlen <= len(text):
#                         shorter_width = column.fontMetrics().boundingRect(column.text()).width()
#                         if shorter_width < w:
#                             t.pos(column, width=shorter_width, add=20)
#
#                     elif count+1 == len(coldict):
#                         t.pos(column, after=self.columns[-1], x_margin=x)
#                         t.pos(column, left=column, right=self.title)  # extends last column
#
#                     t.correct_broken_font_size(column, maxsize=12, shorten=True)
#
#                 if not self.columns:
#                     t.pos(column, below=self.title, y_margin=y)
#                 else:
#                     t.pos(column, after=self.columns[-1], x_margin=x)
#
#                 t.style(column, background=COLUMN_BACK, color=TITLE_WHITE)
#                 self.columns.append(column)
#
#             self.set_positions()
#
#     class RootAPI(Canvas):
#         def default_colors(self):
#             self.button.deactivated_on = dict(color=BLACK, background=SMISK_LIGHT)
#             self.button.deactivated_off = dict(color=BLACK, background=SMISK_HARD)
#
#             self.label.deactivated_on = dict(color=TEXT_WHITE, background=DARK_BACK)
#             self.label.deactivated_off = dict(color=TEXT_OFF, background=BLACK)
#
#         def change_colors(self):
#             if not self.activated:
#                 for i in ['activated_on', 'activated_off', 'deactivated_on', 'deactivated_off']:
#                     for ii in [self.button, self.label]:
#                         ii.swap_preset(i, restore=True)
#
#             else:
#                 self.button.swap_preset('deactivated_off', new_value=dict(background=ACTIVE_GREEN))
#                 self.button.swap_preset('deactivated_on', new_value=dict(background=HIGH_GREEN))
#                 self.label.swap_preset('deactivated_off', new_value=dict(color=TEXT_WHITE))
#                 self.label.swap_preset('deactivated_on', new_value=dict(color=TEXT_WHITE))
#
#         def create_wood(self, data):
#             maxwidth = self.child.title.fontMetrics().boundingRect(self.child.title.text()).width()
#
#             data = [(x['text'], x,) for x in data]
#             data.sort(key=lambda x: x[0])
#
#             for i in data:
#                 my_url = self.url + self.data['id'] + '/'
#                 canvas = self.apiwidget(place=self.child, data=i[1], type=self.data['id'], url=my_url)
#                 self.child.widgets.append(canvas)
#
#                 if canvas.button.width() < canvas.button.height():
#                     maxwidth = 0
#                     break
#
#                 elif canvas.label.fontMetrics().boundingRect(canvas.label.text()).width() > maxwidth:
#                     maxwidth = canvas.label.fontMetrics().boundingRect(canvas.label.text()).width()
#
#             if maxwidth > self.child.title.fontMetrics().boundingRect(self.child.title.text()).width():
#                 t.pos(self.child.title, width=maxwidth, add=55)
#                 t.pos(self.child, width=self.child.title)
#                 for i in self.child.widgets:
#                     t.pos(i, width=maxwidth, add=55)
#
#         def create_leaf(self, data):
#             for i in data['variables']:
#                 canvas = self.apiwidget(place=self.child, data=i, type=self.data['id'], url=self.url, widget=self.TableAPI)
#                 self.child.widgets.append(canvas)
#
#         def killswitch(self):
#             if 'child' in dir(self):
#                 self.child.close()
#                 del self.child
#
#             self.activation_toggle(force=False)
#             self.change_colors()
#             signal = t.signals('_global')
#             signal.highlight.emit('_')
#
#         def expand_child(self):
#             if self.child.widgets:
#                 bottom = self.child.widgets[-1].geometry().bottom() + 3
#                 t.pos(self.child.backplate, height=bottom)
#
#                 max = self.main.height() * 0.8
#                 if bottom < max:
#                     t.pos(self.child, height=self.child.backplate, add=self.child.toolplate.height())
#                     t.pos(self.child.scrollarea, height=self.child.backplate)
#                 else:
#                     t.pos(self.child, height=max)
#                     t.pos(self.child.scrollarea, height=max, sub=self.child.toolplate.height())
#
#         def setup_killswitch(self):
#             self.child.title.signal = t.signals()
#             self.child.title.signal.killswitch.connect(self.killswitch)
#
#         def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
#             self.activation_toggle()
#             self.change_colors()
#
#             if self.activated:
#                 self.parent.raise_us()
#                 data = self.call_api(url=self.url, id=self.data['id'])
#
#                 if not data:
#                     return
#
#                 self.child = self.MovableScrollWidget(
#                     self.main.scrollcanvas_main, self.main, self, url=self.url + self.data['id'], data=data)
#
#                 self.child.widgets = []
#
#                 if self.data['type'] == 'l':
#
#                     self.child.make_title(text=self.data['text'])
#                     self.create_wood(data)
#
#                 elif self.data['type'] == 't':
#                     self.child.make_title(text=data['title'])
#                     self.create_leaf(data)
#
#                 self.setup_killswitch()
#                 self.expand_child()
#                 t.pos(self.child, after=self.parent, x_margin=5)
#                 self.child.load_crown()
#
#             else:
#                 try: self.child.title.signal.killswitch.emit()
#                 except AttributeError: pass
#
#             signal = t.signals('_global')
#             signal.highlight.emit('_')
#
#     class TableAPI(RootAPI):
#         class Leaf(Canvas):
#             def default_colors(self):
#                 self.button.deactivated_on = dict(color=BLACK, background=DEACTIVE_LEAF_1)
#                 self.button.deactivated_off = dict(color=BLACK, background=DEACTIVE_LEAF_2)
#
#                 self.label.deactivated_on = dict(color=TEXT_WHITE, background=DARK_BACK)
#                 self.label.deactivated_off = dict(color=TEXT_OFF, background=BLACK)
#
#             def change_colors(self):
#                 if not self.activated:
#                     for i in ['activated_on', 'activated_off', 'deactivated_on', 'deactivated_off']:
#                         for ii in [self.button, self.label]:
#                             ii.swap_preset(i, restore=True)
#
#                 else:
#                     self.button.swap_preset('deactivated_off', new_value=dict(background=ACTIVE_LEAF_1))
#                     self.button.swap_preset('deactivated_on', new_value=dict(background=ACTIVE_LEAF_2))
#
#                     self.label.swap_preset('deactivated_off', new_value=dict(color=TEXT_WHITE))
#                     self.label.swap_preset('deactivated_on', new_value=dict(color=TEXT_WHITE))
#
#             def setup_killswitch(self):
#                 self.seed.title.signal = t.signals()
#                 self.seed.title.signal.killswitch.connect(self.killswitch)
#
#             def killswitch(self):
#                 if 'seed' in dir(self):
#                     self.seed.close()
#                     del self.seed
#
#                 self.activation_toggle(force=False)
#                 self.change_colors()
#
#                 signal = t.signals('_global')
#                 signal.highlight.emit('_')
#
#             class NextPageSquare(GODLabel, GLOBALHighLight):
#                 def default_colors(self):
#                     self.deactivated_on = dict(color=BLACK, background=HIGH_RED)
#                     self.deactivated_off = dict(color=BLACK, background=DEACTIVE_RED)
#
#                     self.activated_on = dict(color=BLACK, background=HIGH_GREEN)
#                     self.activated_off = dict(color=BLACK, background=ACTIVE_GREEN)
#
#                 def draw_my_work(self, x=0, y=0):
#                     if not self.activated:
#                         t.close_and_pop(self.seed.seeds)
#                         return
#
#                     t.pos(self.seed, height=self.seed.toolplate)
#                     t.pos(self.seed.scrollarea, height=0)
#                     t.pos(self.seed.backplate, height=0)
#
#                     signal = t.signals(name=self.seed._type)
#                     signal.killswitch.emit()
#                     signal = t.signals(name=self.seed._type, reset=True)
#
#                     for count, work in enumerate(self.work):
#                         for cc, value in enumerate(work):
#                             val = GODLabel(place=self.seed.backplate)
#                             val.setAlignment(QtCore.Qt.AlignRight)
#                             val.setFrameShape(QtWidgets.QFrame.Box)
#                             val.setLineWidth(1)
#                             val.setIndent(3)
#                             val.setText(value)
#
#                             t.style(val, background=GRAY, color=BLACK, font=12)
#
#                             if count == 0:
#                                 col = self.seed.columns[cc]
#                                 t.pos(val, size=col, left=col, height=20, y_margin=y)
#                             else:
#                                 prev = self.seed.seeds[-len(work)]
#                                 t.pos(val, coat=prev, below=prev, y_margin=y)
#
#                             t.correct_broken_font_size(val, shorten=True, maxsize=12, minsize=11)
#                             self.seed.seeds.append(val)
#
#                         t.pos(self.seed.backplate, height=self.seed.backplate, add=21)
#                         max = self.main.height() * 0.9
#                         if self.seed.height() < max:
#                             t.pos(self.seed, height=self.seed.toolplate, add=self.seed.backplate.height())
#                             t.pos(self.seed.scrollarea, height=self.seed.backplate)
#
#                     signal.killswitch.connect(self.killswitch)
#
#                 def killswitch(self):
#                     if self.activated:
#                         self.activation_toggle(force=False)
#                         t.close_and_pop(self.seed.seeds)
#
#                         signal = t.signals('_global')
#                         signal.highlight.emit('_')
#
#                 def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
#                     self.activation_toggle()
#                     self.draw_my_work()
#
#             def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
#                 self.activation_toggle()
#                 self.change_colors()
#
#                 if not self.activated:
#                     self.killswitch()
#                     return
#
#                 query = dict(
#                     query=[
#                         dict(code=self.code,
#                              selection=dict(filter='item', values=[self.value])),
#                     ],
#                     response=dict(format='json')
#                 )
#                 query = json.dumps(query)
#                 rv = self.main.post_api(url=self.url, data=query)
#                 if rv:
#                     self.seed = self.MovableScrollWidget(
#                         self.main.scrollcanvas_main, self.main, self, url=dict(url=self.url, data=query), data=rv)
#
#                     self.seed.make_title(text=rv['metadata'][0]['label'], width=500)
#                     self.setup_killswitch()
#
#                     t.pos(self.seed, width=500, height=self.seed.title, after=self.parent, x_margin=5)
#
#                     columns = [x['text'] for x in rv['columns']]
#
#                     coldict = {}
#                     for count, col in enumerate(columns):
#                         coldict[count] = {col: 0}
#                         for dictionary in rv['data']:
#                             work = dictionary['key'] + dictionary['values']
#                             if len(work[count]) > coldict[count][col]:
#                                 coldict[count][col] = len(work[count])
#                                 if coldict[count][col] > len(col):
#                                     break
#
#                     def move_down_others(self, size):
#                         t.pos(self.seed.toolplate, height=self.seed.toolplate, add=size + 1)
#
#                         for i in [self.seed.title, self.seed.backplate]:
#                             t.pos(i, move=[0, size + 1])
#
#                         for i in self.seed.columns:
#                             t.pos(i, move=[0, size + 1])
#
#                     self.seed.make_column(coldict)
#
#                     self.seed.seeds = []
#                     self.seed.pages = []
#
#                     page = 0
#                     page_size = 250
#                     for count, dictionary in enumerate(rv['data']):
#                         work = dictionary['key'] + dictionary['values']
#
#                         if count == page:
#                             page += page_size
#                             square = self.NextPageSquare(place=self.seed.toolplate, mouse=True)
#                             square.setLineWidth(1)
#                             square.setFrameShape(QtWidgets.QFrame.Box)
#                             square.default_colors()
#                             square.main = self.main
#                             square.seed = self.seed
#
#                             square.work = []
#                             t.style(square, background=ACTIVE_GREEN, color=BLACK)
#
#                             if not self.seed.pages:
#                                 size = 9
#                                 t.pos(square, size=[size, size])
#                                 move_down_others(self, size=size)
#
#                             else:
#                                 t.pos(square, coat=self.seed.pages[-1], after=self.seed.pages[-1], x_margin=1)
#                                 if square.geometry().right() > self.seed.title.geometry().right():
#                                     t.pos(square, below=self.seed.pages[-1], y_margin=1, left=self.seed.title)
#                                     move_down_others(self, size=9)
#
#                             self.seed.pages.append(square)
#
#                         self.seed.pages[-1].work.append(work)
#
#                     if self.seed.pages:
#                         self.seed.pages[0].activation_toggle(force=True)
#                         self.seed.pages[0].draw_my_work()
#                         signal = t.signals('_global')
#                         signal.highlight.emit('_')
#
#         def create_dandelion(self, place, text, main, value, code):
#             canvas = create_indikator(
#                 place.backplate,
#                 Special=self.Leaf,
#                 button=True,
#                 label=True,
#                 mouse=True,
#                 button_width=30,
#                 canvas_border=1,
#                 canvas_background=GRAY,
#                 button_listen=True,
#                 label_background=BLACK,
#                 label_foreground=TEXT_WHITE,
#             )
#             canvas._type = self._type + self._type
#             canvas.label.setText(text)
#             canvas.label.setIndent(3)
#             canvas.parent = place
#             canvas.main = main
#             canvas.value = value
#             canvas.code = code
#             canvas.url = self.parent.parent.url + self.parent.parent.data['id']
#             canvas.MovableScrollWidget = self.MovableScrollWidget
#             canvas.default_colors()
#
#             height = self.parent.widgets[0].height()
#
#             if not self.parent.leafs:
#                 t.pos(canvas, width=500, height=height, below=self, move=[height,0])
#                 t.pos(self.parent, width=self.parent, add=height)
#             else:
#                 t.pos(canvas, width=500, height=height, below=self.parent.leafs[-1])
#
#
#             for count in range(0, 4):
#                 if t.correct_broken_font_size(canvas.label, shorten=True, maxsize=12, minsize=11):
#                     t.pos(canvas, width=canvas, add=canvas.width())
#                     canvas.label.setText(text)
#                 else:
#                     break
#
#             t.pos(canvas, height=canvas.height() + (canvas.height() * count), width=500)
#             canvas.label.setWordWrap(True)
#             canvas.label.setText(text)
#
#             max = self.main.height() * 0.8
#             t.pos(place.backplate, height=place.backplate, add=canvas.height())
#             if place.height() < max:
#                 t.pos(place, height=place, add=canvas.height())
#                 t.pos(place.scrollarea, height=place.scrollarea, add=canvas.height())
#
#             for i in self.parent.widgets:
#                 if i.geometry().top() >= canvas.geometry().top():
#                     t.pos(i, move=[0, canvas.height()])
#
#             return canvas
#
#         def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
#             if 'leafs' not in dir(self.parent):
#                 self.parent.leafs = []
#
#             if self.parent.leafs:
#                 t.close_and_pop(self.parent.leafs)
#
#                 if 'backup' in dir(self):
#                     for widget in self.backup:
#                         t.pos(widget, width=self.backup[widget]['width'], height=self.backup[widget]['height'])
#
#                 for count, i in enumerate(self.parent.widgets):
#                     if i.activated and i != self:
#                         i.activation_toggle(force=False)
#                         i.change_colors()
#
#                     if count > 0:
#                         t.pos(i, below=self.parent.widgets[count-1])
#
#             self.activation_toggle()
#             self.change_colors()
#
#             if self.activated:
#
#                 self.backup = {
#                     self.parent:
#                         dict(width=self.parent.width(), height=self.parent.height()),
#                     self.parent.scrollarea:
#                         dict(width=self.parent.scrollarea.width(), height=self.parent.scrollarea.height()),
#                     self.parent.backplate:
#                         dict(width=self.parent.backplate.width(), height=self.parent.backplate.height()),
#                 }
#
#                 maxwidth = -1
#
#                 for count, i in enumerate(self.data['valueTexts']):
#                     canvas = self.create_dandelion(
#                         place=self.parent,
#                         text=i,
#                         main=self.main,
#                         value=self.data['values'][count],
#                         code=self.data['code']
#                     )
#                     self.parent.leafs.append(canvas)
#
#                     if maxwidth == False:
#                         continue
#
#                     elif canvas.button.width() < canvas.button.height():
#                         maxwidth = False
#
#                     elif canvas.label.fontMetrics().boundingRect(canvas.label.text()).width() > maxwidth:
#                         maxwidth = canvas.label.fontMetrics().boundingRect(canvas.label.text()).width()
#
#                 if maxwidth:
#                     for i in self.parent.leafs:
#                         t.pos(i, width=maxwidth, add=55)
#
#
#             signal = t.signals('_global')
#             signal.highlight.emit('_')
#
#     def apiwidget(self, place, data, type, widget=RootAPI, url='http://api.scb.se/OV0104/v1/doris/en/ssd/', height=28):
#         canvas = create_indikator(
#             place.backplate,
#             Special=widget,
#             button=True,
#             label=True,
#             mouse=True,
#             button_width=height,
#             canvas_background=GRAY,
#             canvas_border=1,
#             button_listen=True,
#             label_background=BLACK,
#             label_foreground=TEXT_WHITE,
#         )
#
#         canvas._type = type
#         canvas.data = data
#         canvas.parent = place
#         canvas.MovableScrollWidget = self.MovableScrollWidget
#         canvas.TableAPI = self.TableAPI
#         canvas.call_api = self.call_api
#         canvas.main = self
#         canvas.apiwidget = self.apiwidget
#         canvas.label.setText(data['text'])
#         canvas.label.setIndent(3)
#         canvas.url = url
#         canvas.default_colors()
#
#         if not place.widgets:
#             t.pos(canvas, width=500, height=height)
#         else:
#             t.pos(canvas, width=500, height=height, below=place.widgets[-1])
#
#         for count in range(0,4):
#             if t.correct_broken_font_size(canvas.label, shorten=True, maxsize=12, minsize=11):
#                 t.pos(canvas, width=canvas, add=canvas.width())
#                 canvas.label.setText(data['text'])
#             else:
#                 break
#
#         t.pos(canvas, height=canvas.height() + (canvas.height() * count), width=500)
#         canvas.label.setWordWrap(True)
#         canvas.label.setText(data['text'])
#
#         return canvas
#
#     def call_api(self, url='http://api.scb.se/OV0104/v1/doris/en/ssd/', id=None):
#         if id:
#             url += id
#
#         tmp = t.tmp_file(file_of_interest=url, hash=True, days=7, reuse=True, extension='json')
#         if os.path.exists(tmp):
#             with open(tmp, 'r') as f:
#                 rv = json.load(f)
#                 return rv
#
#         response = requests.get(url, headers=t.header())
#         if response.status_code == 200:
#             data = response.json()
#
#             with open(tmp, 'w') as f:
#                 content = json.dumps(data)
#                 f.write(content)
#
#             return data
#
#     def post_api(self, url, data):
#         tmp = t.tmp_file(file_of_interest=url + data, hash=True, days=7, reuse=True, extension='json')
#         if os.path.exists(tmp):
#             with open(tmp, 'r') as f:
#                 rv = json.load(f)
#                 return rv
#
#         response = requests.request(method='post', url=url, data=data)
#         if response.status_code == 200:
#             rv = response.json()
#
#             with open(tmp, 'w') as f:
#                 content = json.dumps(rv)
#                 f.write(content)
#
#             return rv
#
#     def draw_root(self):
#         url = 'http://api.scb.se/OV0104/v1/doris/en/ssd/'
#         data = self.call_api(url=url)
#         if data:
#             self.root = self.MovableScrollWidget(self.scrollcanvas_main, self, self, data=data, url=url)
#             self.root.move(20,220)
#             self.root.make_title(text='ROOT')
#             self.root.widgets = []
#
#             data = [(x['text'], x,) for x in data]
#             data.sort(key=lambda x:x[0])
#
#             maxwidth = 0
#             for i in data:
#                 canvas = self.apiwidget(data=i[1], place=self.root, type='root')
#                 self.root.widgets.append(canvas)
#                 if canvas.label.fontMetrics().boundingRect(canvas.label.text()).width() > maxwidth:
#                     maxwidth = canvas.label.fontMetrics().boundingRect(canvas.label.text()).width()
#
#             t.pos(self.root.title, width=maxwidth, add=55)
#             t.pos(self.root, width=self.root.title)
#             for i in self.root.widgets:
#                 t.pos(i, width=maxwidth, add=55)
#
#             if self.root.widgets:
#                 bottom = self.root.widgets[-1].geometry().bottom() + 3
#                 t.pos(self.root.backplate, height=bottom)
#
#                 max = self.height() * 0.8
#                 if bottom < max:
#                     t.pos(self.root, height=self.root, add=self.root.backplate.height())
#                     t.pos(self.root.scrollarea, height=self.root.backplate)
#                 else:
#                     def post():
#                         t.pos(self.root.scrollarea, height=max - self.root.toolplate.height())
#                     t.pos(self.root, height=max)
#                     t.start_thread(dummy=True, master_fn=post)
#
#                 self.root.load_crown()
#
#     class BookMarkWidget(TableAPI):
#         def default_colors(self):
#             self.deactivated_on = dict(color=BLACK, background=TEXT_WHITE)
#             self.deactivated_off = dict(color=BLACK, background=GRAY)
#
#         def change_colors(self):
#             pass
#
#         def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
#             pass
#
#         def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
#             pass
#
#         def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
#             if 'data' in self.urldict:
#                 data = self.main.post_api(url=self.urldict['url'], data=self.urldict['data'])
#                 print("FIX ME!!!")
#                 print(data)
#             else:
#                 data = self.main.call_api(url=self.urldict['url'])
#                 self.child = self.main.MovableScrollWidget(
#                     self.main.scrollcanvas_main, self.main, self.main, url=self.urldict['url'], data=data
#                 )
#
#                 self.child.widgets = []
#
#                 if self.data['type'] == 'l':
#                     self.child.make_title(text=self.data['text'])
#                     self.create_wood(data)
#
#                 elif self.data['type'] == 't':
#                     self.child.make_title(text=data['title'])
#                     self.create_leaf(data)
#
#                 t.pos(self.child, after=self.main.root, x_margin=5)
#                 self.setup_killswitch()
#                 self.expand_child()
#                 self.child.load_crown()
#
#                 signal = t.signals('_global')
#                 signal.highlight.emit('_')
#
#     def post_init(self):
#         t.style(self, name='main')
#
#         def wait_for_gui(self):
#             self.draw_root()
#             bookmarks = t.config('bookmarks')
#             if bookmarks:
#                 for i in bookmarks:
#                     text = bookmarks[i]['text']
#                     urldict = bookmarks[i]['urldict']
#                     data =  bookmarks[i]['data']
#
#                     bookmark = self.BookMarkWidget(
#                         place=self,
#                         main=self,
#                         edge=1,
#                         width=80,
#                         height=30,
#                     )
#
#                     bookmark.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
#                     bookmark.setFrameShape(QtWidgets.QFrame.Box)
#                     bookmark.setLineWidth(1)
#                     bookmark.setText(text)
#                     bookmark.default_colors()
#                     bookmark.urldict = urldict
#                     bookmark.url = urldict['url'][0:-len(data['id'])] # todo not happy
#                     bookmark.main = self
#                     bookmark.data = data
#                     bookmark.apiwidget = self.apiwidget
#
#                     t.pos(bookmark, width=500)
#                     bookmark.show()
#                     width = bookmark.fontMetrics().boundingRect(bookmark.text()).width() + 12
#
#                     if not self.bookmarks:
#                         h = self.back.geometry().top()
#                         t.pos(bookmark, height=h, width=width)
#                     else:
#                         t.pos(bookmark, height=self.bookmarks[-1], after=self.bookmarks[-1], width=width, x_margin=1)
#
#                     self.bookmarks.append(bookmark)
#
#
#             signal = t.signals('_global')
#             signal.highlight.emit('_')
#
#         t.start_thread(
#             dummy=True,
#             slave_args=0.2,
#             master_fn=wait_for_gui,
#             master_kwargs=dict(self=self)
#         )
#
