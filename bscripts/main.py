from PIL                          import Image
from PyQt5                        import QtCore, QtGui, QtWidgets
from bscripts.api_communicate     import call_api
from bscripts.customwidgets       import LeafAPI, MovableScrollWidget, RootAPI
from bscripts.customwidgets       import create_scb_branch
from bscripts.tricks              import tech as t
from script_pack.preset_colors    import *
from script_pack.settings_widgets import GLOBALHighLight, GODLabel
import os,json
import screeninfo
#from pyscbwrapper import SCB

class Targeting:
    def __init__(self):
        self.reset()

    def reset(self):
        self.targets = ['se', 'eu']
        for i in self.targets:
            setattr(self, i, False)

    def change_target(self, eu=False, se=False):
        self.reset()

        if eu:
            self.eu = True
        elif se:
            self.se = True

TARGET = Targeting()
TARGET.change_target(se=True)

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
            tmp = [(i['values'][count], i['valueTexts'][count],) for count in range(len(i['values']))]
            tmp.sort(key=lambda x: x[1])
            i['values'] = [x[0] for x in tmp]
            i['valueTexts'] = [x[1] for x in tmp]
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
        if TARGET.se:
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

        elif TARGET.eu:
            import sys
            from rest_api_config import rest
            base = rest['API_BASE_URL']['1']
            base = (base[next(iter(base))])
            print(base)
            sys.exit()
            rv = call_api(url='http://ec.europa.eu/eurostat/wdds/rest/data/v2.1/json/en/nama_10_gdp')
            print(rv)
