from PyQt5                        import QtCore, QtGui, QtWidgets
from PyQt5.Qt                     import QPixmap
from PyQt5.QtCore                 import QPoint
from bscripts.api_communicate     import call_api, post_api
from bscripts.tricks              import tech as t
from script_pack.preset_colors    import *
from script_pack.settings_widgets import Canvas, DragDroper, GLOBALHighLight
from script_pack.settings_widgets import GODLabel, create_indikator
import json
import os
import random

class MovableScrollWidget(GODLabel):
    def __init__(self, url, query=None, *args, **kwargs):

        self.title = False
        self.crown = False
        self.save_thingey = False
        self.old_position = False
        self.columns = []
        self.widgets = []

        super().__init__(*args, **kwargs)

        self.make_toolplate()
        self.make_backplate()
        self.make_scrollarea()

        self.url = url
        self.query = query

        self.show()

        t.style(self, background=TRANSPARENT)
        t.style(self.scrollarea, background=TRANSPARENT)
        t.style(self.backplate, background=TRANSPARENT)

    def make_toolplate(self):
        self.toolplate = QtWidgets.QLabel(self)
        t.style(self.toolplate, background=TRANSPARENT)
        self.toolplate.show()

    def make_backplate(self):
        self.backplate = QtWidgets.QWidget(self)
        t.style(self.backplate, background=TRANSPARENT)
        t.pos(self.backplate, height=0)
        self.backplate.show()

    def make_scrollarea(self):
        self.scrollarea = QtWidgets.QScrollArea(self)
        self.scrollarea.setWidget(self.backplate)
        self.scrollarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollarea.setLineWidth(0)
        self.scrollarea.setFrameShape(QtWidgets.QScrollArea.Box)
        self.scrollarea.show()

    def drag_widget(self, ev):
        if not self.old_position:
            self.old_position = ev.globalPos()

        delta = QPoint(ev.globalPos() - self.old_position)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_position = ev.globalPos()

        if self.crown:
            self.position_crown()

    def position_crown(self):
        t.pos(self.crown, above=self, move=[self.crown.random, 0])

    def raise_us(self):
        self.raise_()
        if self.crown:
            self.crown.raise_()

    class TITLE(GODLabel, DragDroper):
        def __init__(self, text, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.setText(text)
            self.setLineWidth(1)
            self.setFrameShape(QtWidgets.QFrame.Box)
            self.save_thingey = False
            t.style(self, background=TOOLTIP_DRK_BG, color=TITLE_WHITE)
            self.show()

        def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.parent.drag_widget(ev)

        def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
            if ev.button() == 2 and self.parent.signal:
                self.parent.signal.killswitch.emit()

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.parent.old_position = ev.globalPos()
            if ev.button() == 1:
                self.parent.raise_us()

        def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
            if self.save_thingey:
                self.save_thingey.show()
                return

            class SAVEThingey(Canvas):
                class Button(Canvas.Button):
                    def catch_my_data(self):
                        if self.parent.query:
                            data = post_api(self.parent.url, data=self.parent.query)
                        else:
                            data = call_api(self.parent.url)

                        return data

                    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                        text = self.parent.lineedit.text().strip() or 'bookmark'
                        bookmarks = t.config('bookmarks')

                        if type(bookmarks) != dict:
                            bookmarks = {}

                        for count in range(2):
                            for i in range(100):
                                if count == 0:
                                    if i not in bookmarks:
                                        continue

                                    elif self.parent.url != bookmarks[i]['url']:
                                        continue

                                    elif self.parent.query != bookmarks[i]['query']:
                                        continue

                                elif count == 1 and i in bookmarks:
                                    continue

                                data = self.catch_my_data()
                                bookmarks[i] = dict(text=text, url=self.parent.url, query=self.parent.query, data=data, count=i)
                                self.parent.main.draw_this_bookmark(bookmarks[i])
                                t.save_config('bookmarks', bookmarks)
                                self.parent.hide()
                                return

            self.save_thingey = create_indikator(
                place=self,
                button=True,
                lineedit=True,
                tiplabel='BOOKMARK',
                button_listen=True,
                lineedit_background=BLACK,
                lineedit_foreground=TEXT_WHITE,
                canvas_background=BLACK,
                deactivated_off=dict(background='brown'),
                deactivated_on=dict(background='yellow'),
                mouse=True,
                edge=1,
                Special=SAVEThingey,
            )

            t.pos(self.save_thingey, inside=self)
            self.save_thingey.url = self.parent.url
            self.save_thingey.query = self.parent.query
            self.save_thingey.main = self.parent.main

    def make_title(self, text, height=28, width=500, font=14):
        self.title = self.TITLE(place=self.toolplate, text=text, parent=self, main=self.main, drops=True)
        self.title.filesdropped = self.filesdropped
        self.title.setText(text)
        t.style(self.title, font=font)

        add_height_long_text(text, height=height, width=width, canvas=self.title, label=self.title)

        if self.title.wordWrap():
            t.pos(self, width=width)
        else:
            w = t.shrink_label_to_text(self.title, no_change=True, x_margin=12)
            if w < width * 0.65:
                w = width * 0.65

            t.pos(self.title, height=height)
            t.pos(self, width=w)

    def load_crown(self):
        pixmap = t.config(self.url, image=True)
        if pixmap:
            path = t.tmp_file(self.url, hash=True, reuse=True)
            if not os.path.exists(path) or not os.path.getsize(path):
                with open(path, 'wb') as f:
                    f.write(pixmap)

            factor = t.config(self.url)
            if factor:
                self.set_this_add_crown(path, width_percentage=factor)
            else:
                self.set_this_add_crown(path)

            self.position_crown()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.set_positions()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.crown:
            self.crown.close()

    class CROWN(QtWidgets.QLabel):
        def __init__(self, place, path, width, partner):
            super().__init__(place)
            self.partner = partner
            pixmap = QPixmap(path).scaledToWidth(width, QtCore.Qt.SmoothTransformation)
            playspace = partner.width() - width
            self.random = random.randint(0, playspace)
            t.pos(self, size=pixmap)
            t.style(self, background=TRANSPARENT)
            self.setPixmap(pixmap)
            self.show()

        def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.partner.drag_widget(ev)

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.partner.old_position = ev.globalPos()
            if ev.button() == 1:
                self.partner.raise_us()

        def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.partner.title.mouseReleaseEvent(ev)

    def set_this_add_crown(self, path, width_percentage=0.5):
        if not os.path.exists(path):
            return

        width = int(self.width() * width_percentage)
        self.crown = self.CROWN(self.main.scrollcanvas_main, path, width, partner=self)

    def filesdropped(self, filelist, ev, heightfactor=False):
        loc = t.separate_file_from_folder(filelist[0])
        if loc.ext.lower() not in {'webp', 'jpeg', 'jpg', 'png', 'bmp'}:
            return

        t.tmp_file(self.url, hash=True, delete=True)
        blob = t.make_image_into_blob(image_path=loc.full_path, width=self.title.width())
        t.save_config(self.url, blob, image=True)

        if not heightfactor:
            heightfactor = ev.pos().x() / self.width()

        if self.crown:
            self.crown.close()
            self.crown = False

        self.set_this_add_crown(loc.full_path, heightfactor)
        self.position_crown()

        t.save_config(self.url, heightfactor)

    def make_columns(self, columnlist, maxall=1000, maxsingle=250, font=12):
        self.columns = []

        label = QtWidgets.QLabel(self)
        t.style(label, font=font)
        for i in columnlist:
            label.setText(label.text() + ' ' + ('#' * i['lenght']))

        width = t.shrink_label_to_text(label, no_change=True)
        label.close()

        maxheight = 0

        for i in columnlist:
            column = self.TITLE(place=self.toolplate, text=i['text'], parent=self)
            column.setAlignment(QtCore.Qt.AlignHCenter)
            t.style(column, font=font, background=COLUMN_BACK)
            height = t.shrink_label_to_text(column, no_change=True, height=True)
            t.pos(column, below=self.title, height=height * 1.1)

            if i['exceeding']:
                column.setText('#' * i['lenght'])
                t.shrink_label_to_text(column, x_margin=12)
                column.setText(i['text'])
            else:
                t.shrink_label_to_text(column, x_margin=12)

            if width > maxall:
                column.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter)

                if column.width() > maxsingle:
                    add_height_long_text(i['text'], height=height, width=maxsingle, canvas=column, label=column)
                    t.pos(column, width=maxsingle)
                    if column.height() > maxheight:
                        maxheight = column.height()

                    column.setWordWrap(True)
                    column.setText(i['text'])

            if self.columns:
                t.pos(column, after=self.columns[-1])

            self.columns.append(column)


        if self.columns[-1].geometry().right() + 1 > self.title.width():
            t.pos(self, width=self.columns[-1].geometry().right() + 1)
        else:
            t.pos(self.columns[-1], left=self.columns[-1], right=self.title)

        for i in [self, self.toolplate]:
            if width > maxall and maxheight != 0:
                for ii in self.columns:
                    if ii.height() != maxheight:
                        t.pos(ii, height=maxheight)

            t.pos(i, height=i, add=self.columns[0].height())

    def set_positions(self, x=0, y=0):
        if self.columns:
            height = self.columns[0].geometry().bottom() +1
        elif self.title:
            t.pos(self.title, width=self)
            height = self.title.geometry().bottom() +1
        else:
            return

        t.pos(self.toolplate, height=height, width=self)
        t.pos(self.backplate, below=self.toolplate, width=self, y_margin=y)
        t.pos(self.scrollarea, below=self.toolplate, width=self, y_margin=y)

    def expand_me(self):
        maxheight = self.main.height() * 0.7
        childspace = self.widgets[-1].geometry().bottom() + 1
        t.pos(self.backplate, height=childspace)

        if self.backplate.geometry().bottom() > maxheight:
            t.pos(self, height=maxheight)
            t.pos(self.scrollarea, height=maxheight - self.toolplate.height())
        else:
            t.pos(self, height=self.toolplate, add=childspace)
            t.pos(self.scrollarea, coat=self.backplate)

class RootAPI(Canvas):
    def default_colors(self):
        self.button.deactivated_on = dict(color=BLACK, background=SMISK_LIGHT)
        self.button.deactivated_off = dict(color=BLACK, background=SMISK_HARD)

        self.label.deactivated_on = dict(color=TEXT_WHITE, background=DARK_BACK)
        self.label.deactivated_off = dict(color=TEXT_OFF, background=BLACK)

    def change_colors(self):
        if not self.activated:
            for i in ['activated_on', 'activated_off', 'deactivated_on', 'deactivated_off']:
                for ii in [self.button, self.label]:
                    ii.swap_preset(i, restore=True)

        else:
            self.button.swap_preset('deactivated_off', new_value=dict(background=ACTIVE_GREEN))
            self.button.swap_preset('deactivated_on', new_value=dict(background=HIGH_GREEN))
            self.label.swap_preset('deactivated_off', new_value=dict(color=TEXT_WHITE))
            self.label.swap_preset('deactivated_on', new_value=dict(color=TEXT_WHITE))

    def setup_killsignal(self):
        if not self.signal:
            self.signal = t.signals()
            self.signal.killswitch.connect(self.killswitch)
        self.child.signal = self.signal

    def crack_my_wood_open(self):
        data = call_api(url=self.url)

        if not data:
            return

        self.child = MovableScrollWidget(place=self.main.scrollcanvas_main, main=self.main, url=self.url)
        t.pos(self.child, after=self.parent, x_margin=5)
        self.setup_killsignal()

        if self.data['type'] == 'l':
            data = [(x['text'], x,) for x in data]
            data.sort(key=lambda x: x[0])
            data = [x[1] for x in data]

            self.child.make_title(text=self.data['text'])
            self.main.grow_new_bransch(data=data, url=self.url, movablewidget=self.child)
        else:
            self.child.make_title(text=data['title'])
            self.main.grow_new_leaf(data=data, url=self.url, movablewidget=self.child)

    def killswitch(self):
        self.activation_toggle(force=False)
        self.change_colors()
        t.signal_highlight()
        if self.child:
            self.child.close()
            self.child = False

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() != 2:
            self.parent.raise_us()

        self.activation_toggle()
        self.change_colors()

        if self.activated:
            self.child = False
            self.crack_my_wood_open()

        elif not self.activated:
            self.signal.killswitch.emit()

class LeafAPI(RootAPI):
    class Leaf(RootAPI):

        def default_colors(self):
            self.button.deactivated_on = dict(color=BLACK, background=DEACTIVE_LEAF_1)
            self.button.deactivated_off = dict(color=BLACK, background=DEACTIVE_LEAF_2)

            self.label.deactivated_on = dict(color=TEXT_WHITE, background=DARK_BACK)
            self.label.deactivated_off = dict(color=TEXT_OFF, background=BLACK)

        def change_colors(self):
            if not self.activated:
                for i in ['activated_on', 'activated_off', 'deactivated_on', 'deactivated_off']:
                    for ii in [self.button, self.label]:
                        ii.swap_preset(i, restore=True)

            else:
                self.button.swap_preset('deactivated_off', new_value=dict(background=ACTIVE_LEAF_1))
                self.button.swap_preset('deactivated_on', new_value=dict(background=ACTIVE_LEAF_2))

                self.label.swap_preset('deactivated_off', new_value=dict(color=TEXT_WHITE))
                self.label.swap_preset('deactivated_on', new_value=dict(color=TEXT_WHITE))

        def make_worklist_and_make_columns(self, rv):
            worklist = []
            columnlist = []
            columns = [x['text'] for x in rv['columns']]

            for count in range(len(columns)):
                text = columns[count]
                wd = dict(text=text, exceeding=False, lenght=len(text))
                columnlist.append(wd)

            for dictionary in rv['data']:
                work = dictionary['key'] + dictionary['values']
                worklist.append(work)

                for count in range(len(columns)):
                    if len(work[count]) > columnlist[count]['lenght']:
                        columnlist[count]['lenght'] = len(work[count])
                        columnlist[count]['exceeding'] = True

            self.child.make_columns(columnlist)
            return worklist

        def draw_batch_of_values(self, startfrom=0, batchsize=250):
            t.close_and_pop(self.child.widgets)
            t.pos(self.child.backplate, height=0)
            t.pos(self.child.scrollarea, height=0)
            t.pos(self.child, height=self.child.toolplate)

            for c in range(startfrom, startfrom + batchsize):
                if len(self.worklist) > c:
                    data = self.worklist[c]
                    for count, value in enumerate(data):
                        label = GODLabel(place=self.child.backplate)
                        label.setAlignment(QtCore.Qt.AlignRight)
                        label.setIndent(3)
                        label.setText(value)
                        t.pos(label, width=self.child.columns[count], left=self.child.columns[count])
                        t.style(label, background=GRAY, color=BLACK)

                        if len(self.child.widgets) >= len(data):
                            t.pos(label, below=self.child.widgets[-len(data)])

                        self.child.widgets.append(label)
                        label.show()

            self.child.expand_me()

        class BatchSquare(GODLabel, GLOBALHighLight):
            def __init__(self, startfrom, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.startfrom = startfrom
                self.setFrameShape(QtWidgets.QFrame.Box)
                self.setLineWidth(1)
                self.default_colors()

            def default_colors(self):
                self.deactivated_on = dict(color=BLACK, background=DEACTIVE_LEAF_1)
                self.deactivated_off = dict(color=BLACK, background=DEACTIVE_LEAF_2)

            def change_colors(self):
                if not self.activated:
                    for i in ['activated_on', 'activated_off', 'deactivated_on', 'deactivated_off']:
                        for ii in [self]:
                            ii.swap_preset(i, restore=True)

                else:
                    self.swap_preset('activated_on', new_value=dict(background=ACTIVE_LEAF_4, color=BLACK))
                    self.swap_preset('activated_off', new_value=dict(background=ACTIVE_LEAF_3, color=BLACK))

            def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                self.activation_toggle()
                self.change_colors()

                for i in self.parent.squares:
                    if i != self and i.activated:
                        i.activation_toggle()
                        i.change_colors()

                t.signal_highlight()
                self.parent.draw_batch_of_values(startfrom=self.startfrom)

        def draw_final_results(self, rv, batchsize=250):

            query = self.generate_query()
            self.child = MovableScrollWidget(
                place=self.main.scrollcanvas_main, main=self.main, url=self.url, query=query)

            self.setup_killsignal()
            self.child.make_title(text=self.data['text'])
            t.pos(self.child, height=self.child.title, after=self.parent.grandparent, x_margin=5)
            self.worklist = self.make_worklist_and_make_columns(rv)
            self.draw_batch_of_values(startfrom=0, batchsize=batchsize)

            if len(self.worklist) > batchsize:
                self.squares = []
                squareplate = QtWidgets.QLabel(self.child)
                squareplate.show()
                x = self.child.title.height() / 3
                t.pos(squareplate, size=[x,x], after=self.child.title, bottom=self.child.title, x_margin=1)
                t.style(squareplate, background=TRANSPARENT)
                square = self.BatchSquare(place=squareplate, startfrom=0, mouse=True, parent=self)
                t.pos(square, size=[x,x])
                self.squares.append(square)
                square.activation_toggle(force=True)
                square.change_colors() # first one is activate as it is created

                while self.squares[-1].startfrom + batchsize < len(self.worklist):

                    if len(self.squares) < 11 or squareplate.geometry().right() + x + 1< self.child.width():
                        t.pos(squareplate, width=squareplate, add=x + 1)

                    batch = self.squares[-1].startfrom + batchsize
                    square = self.BatchSquare(place=squareplate, startfrom=batch, mouse=True, parent=self)

                    if self.squares[-1].geometry().right() + x > squareplate.width():
                        t.pos(squareplate, height=squareplate, add=x + 1, move=[0, -x])
                        t.pos(square, size=[x,x], top=dict(bottom=self.squares[-1]))
                    else:
                        t.pos(square, size=[x,x], after=self.squares[-1], x_margin=1)

                    self.squares.append(square)

                if squareplate.height() > self.child.title.height():
                    t.pos(squareplate, after=self.child.columns[-1], size=[x,x])
                    t.pos(self.squares[0], left=0, top=0)

                    for count in range(1, len(self.squares)):
                        if self.squares[count-1].geometry().right() > 50:
                            t.pos(self.squares[count], below=self.squares[count-1], y_margin=1, left=0)
                        else:
                            t.pos(self.squares[count], after=self.squares[count-1], y_margin=1)

                        if squareplate.width() < self.squares[count].geometry().right():
                            t.pos(squareplate, width=self.squares[count].geometry().right() + 1)
                        if squareplate.height() < self.squares[count].geometry().bottom():
                            t.pos(squareplate, height=self.squares[count].geometry().bottom() + 1)

                    t.pos(self.child, width=self.child, add=squareplate.width())

                if self.child.width() < squareplate.geometry().right() + 1:
                    t.pos(self.child, width=squareplate.geometry().right() + 1)

                t.signal_highlight()








            # if len(self.worklist) > batchsize:
            #     square = self.BatchSquare(place=self.child.toolplate, startfrom=0, mouse=True, parent=self)
            #     square.activation_toggle(force=True)
            #     square.change_colors() # first one is activate as it is created
            #
            #     x = self.child.title.height() / 3
            #     t.pos(square, size=[x,x], after=self.child.title, x_margin=1, bottom=self.child.title, y_margin=1)
            #     self.squares.append(square)
            #
            #     while self.squares[-1].startfrom + batchsize < len(self.worklist):
            #         batch = self.squares[-1].startfrom + batchsize
            #         square = self.BatchSquare(place=self.child.toolplate, startfrom=batch, mouse=True, parent=self)
            #         t.pos(square, coat=self.squares[-1], after=self.squares[-1], x_margin=1)
            #         if square.geometry().right() > self.child.backplate.width():
            #
            #             if len(self.squares) < 11:
            #                 t.pos(self.child, width=self.child, add=square.width() + 1)
            #             else:
            #                 if self.squares[0].geometry().top() - square.height() < 0:
            #                     square.close()
            #                     print("FIX ME! scroll page or some other idea...")
            #                     break
            #                 else:
            #                     for i in self.squares:
            #                         t.pos(i, move=[0, - i.height()])
            #
            #                     t.pos(square, left=self.squares[0])
            #
            #         self.squares.append(square)
            # t.signal_highlight()

        def generate_query(self):
            query = dict(
                query=[
                    dict(code=self.data['code'],
                         selection=dict(filter='item', values=[self.data['value']])),
                ],
                response=dict(format='json')
            )
            query = json.dumps(query)
            return query

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.activation_toggle()
            self.change_colors()

            if not self.activated:
                self.killswitch()
                return

            query = self.generate_query()
            rv = post_api(self.url, data=query)
            if rv:
                self.draw_final_results(rv)

    def killswitch(self):
        self.activation_toggle(force=False)
        self.change_colors()
        self.pull_up_leaves()
        t.signal_highlight()
        if self.child:
            self.child.close()
            self.child = False

    def pull_up_leaves(self):
        belowers = [x for x in self.parent.widgets if x.geometry().top() >= self.child.geometry().top()]
        for i in belowers:
            t.pos(i, move=[0, -self.child.height()])
            if i.child:
                t.pos(i.child, move=[0, -self.child.height()])

        t.pos(self.parent.backplate, height=self.parent.backplate, sub=self.child.height())
        self.parent.expand_me()

    def push_down_leaves(self):
        belowers = [x for x in self.parent.widgets if x.geometry().top() >= self.child.geometry().top()]
        for i in belowers:
            t.pos(i, move=[0, self.child.height()])
            if i.child:
                t.pos(i.child, move=[0, self.child.height()])

        t.pos(self.parent.backplate, height=self.parent.backplate, add=self.child.height())

        if not belowers:
            # this hack works perfectly though, its ugly and bad practice!
            self.parent.widgets.append(self.child)
            self.parent.expand_me()
            self.parent.widgets.pop(-1)
        else:
            self.parent.expand_me()

    def crack_my_wood_open(self):
        self.child = MovableScrollWidget(place=self.parent.backplate, main=self.main, url=self.url)
        self.child.make_title(text='', height=0)
        self.child.title.hide()
        self.child.grandparent = self.parent
        self.setup_killsignal()
        t.pos(self.child, width=self, below=self, sub=10, move=[10,0])
        self.main.grow_new_seed(data=self.data, url=self.url, movablewidget=self.child)
        self.push_down_leaves()

def create_scb_branch(place, main, widget, data, height=28, width=500, font=12):
    canvas = create_indikator(
        place.backplate,
        Special=widget,
        button=True,
        label=True,
        mouse=True,
        button_width=height,
        canvas_background=GRAY,
        canvas_border=1,
        button_listen=True,
        label_background=BLACK,
        label_foreground=TEXT_WHITE,
    )
    canvas.main = main
    canvas.parent = place
    canvas.data = data
    canvas.child = False
    canvas.label.setIndent(3)
    canvas.default_colors()
    t.style(canvas.label, font=font)

    if not place.widgets:
        t.pos(canvas, width=width, height=height)
    else:
        t.pos(canvas, width=width, height=height, below=place.widgets[-1])

    add_height_long_text(data['text'], height, width, canvas=canvas, label=canvas.label)

    canvas.label.setText(data['text'])
    return canvas

def add_height_long_text(org_text, height, width, canvas, label):
    text = org_text.split()
    text.reverse()
    change = False

    while text:
        tmp = ""
        for count in range(len(text) - 1, -1, -1):
            tmp += ' ' + text[count]
            label.setText(tmp.strip())
            textwidth = t.shrink_label_to_text(label, no_change=True, x_margin=12)
            if height + textwidth > width:
                change = True
                t.pos(canvas, height=canvas, add=height)
                if tmp == ' ' + text[count]:
                    text.pop(count)
                break
            else:
                text.pop(count)

    label.setText(org_text)

    if change:
        label.setWordWrap(True)
