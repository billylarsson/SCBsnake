from PyQt5                     import QtGui, QtWidgets
from bscripts.tricks           import tech as t
from script_pack.preset_colors import *
import os

class GOD:
    def __init__(self,
                 place=None,
                 main=None,
                 type=None,
                 signal=False,
                 reset=True,
                 parent=None,
                 *args, **kwargs
                 ):

        self.activated = False
        self.main = main or False
        self.parent = parent or place or False
        self.determine_type(place, type)
        self.setup_signal(signal, reset)

    def setup_signal(self, signal, reset):
        if signal:
            if signal == True:
                self.signal = t.signals(self.type, reset=reset)
            else:
                self.signal = t.signals(signal, reset=reset)
        else:
            self.signal = False

    def determine_type(self, place, type):
        if type:
            self.type = type
        elif place and 'type' in dir(place) and place.type not in ['main']: # blacklist
            self.type = place.type
        else:
            self.type = '_' + t.md5_hash_string()

    def save(self, type=None, data=None):
        if data:
            if type:
                t.save_config(type, data)
            else:
                t.save_config(self.type, data)

    def activation_toggle(self, force=None, save=True):
        if force == False:
            self.activated = False
        elif force == True:
            self.activated = True
        else:
            if self.activated:
                self.activated = False
            else:
                self.activated = True

        if save:
            t.save_config(self.type, self.activated)

class DragDroper(GOD):
    def __init__(self, drops=False, mouse=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(drops)
        self.setMouseTracking(mouse)

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent) -> None:
        if a0.mimeData().hasUrls() and a0.mimeData().urls() and len(a0.mimeData().urls()) == 1:
            file = a0.mimeData().urls()[0]
            file = file.path()
            if os.path.isfile(file):
                a0.accept()
        return

    def dropEvent(self, a0: QtGui.QDropEvent) -> None:
        if a0.mimeData().hasUrls() and a0.mimeData().urls()[0].isLocalFile():

            if len(a0.mimeData().urls()) == 1:
                a0.accept()

                files = [x.path() for x in a0.mimeData().urls()]
                self.filesdropped(files, a0)

class GODLabel(QtWidgets.QLabel, GOD):
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs['place'], *args, **kwargs)
        self.show()

    def filesdropped(self, files):
        pass

class GODLE(QtWidgets.QLineEdit, GOD):
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs['place'], *args, **kwargs)
        self.textChanged.connect(self.text_changed)
        self.show()

    def text_changed(self):
        text = self.text().strip()
        if not text:
            return

class GODLEPath(GODLE):
    def __init__(self, autoinit=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if autoinit:
            self.set_saved_path()

    def filesdropped(self, files):
        if not files:
            return

        self.setText(files[0])

    def text_changed(self):
        text = self.text().strip()

        if text and os.path.exists(text):
            self.save(data=text)
            if not self.activated:
                t.style(self, color='white')
                self.activation_toggle(force=True, save=False) # already saved
                if self.signal:
                    self.signal.activated.emit()
        else:
            if self.activated:
                t.style(self, color='gray')
                self.activation_toggle(force=False, save=False)
                if self.signal:
                    self.signal.deactivated.emit()

    def set_saved_path(self):
        rv = t.config(self.type)
        if rv:
            self.setText(rv)
            self.activation_toggle(force=True, save=False)
            self.signal.activated.emit()

class GLOBALHighLight(DragDroper, GOD):
    def __init__(self,
                 signal=True,
                 reset=False,
                 activated_on=None,
                 activated_off=None,
                 deactivated_on=None,
                 deactivated_off=None,
                 *args, **kwargs
                 ):

        if signal == True:
            signal = '_global'

        super().__init__(signal=signal, reset=reset, *args, **kwargs)
        self.signal.highlight.connect(self.highlight_toggle)

        self.activated_on = activated_on or dict(background=HIGH_GREEN)
        self.activated_off = activated_off or dict(background=ACTIVE_GREEN)
        self.deactivated_on = deactivated_on or dict(background=HIGH_RED)
        self.deactivated_off = deactivated_off or dict(background=DEACTIVE_RED)

    def swap_preset(self, variable, new_value=None, restore=False):
        if not getattr(self, variable):
            return

        if 'swap_presets_backup' not in dir(self):
            self.swap_presets_backup = {}

        if variable not in self.swap_presets_backup: # makes a backup
            self.swap_presets_backup[variable] = getattr(self, variable)

        if new_value and new_value != getattr(self, variable):
            setattr(self, variable, new_value)

        if restore and getattr(self, variable) != self.swap_presets_backup[variable]:
            setattr(self, variable, self.swap_presets_backup[variable])

    def highlight_toggle(self, string=None, force=None):
        if force:
            string = self.type
        elif force == False:
            string = '_' + t.md5_hash_string()

        if string == self.type:
            if self.activated:
                t.style(self, **self.activated_on)
            else:
                t.style(self, **self.deactivated_on)
        else:
            if self.activated:
                t.style(self, **self.activated_off)
            else:
                t.style(self, **self.deactivated_off)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.signal.highlight.emit(self.type)



class Canvas(GODLabel):
    def __init__(self,
                 edge,
                 width,
                 height,
                 button_width=0,
                 canvas_border=0,
                 canvas_background='transparent',
                 *args, **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.edge = edge
        self.canvas_border = canvas_border
        self.button_width = button_width
        t.pos(self, size=[height, width])
        t.style(self, background=canvas_background)

    def build_lineedit(self, immutable=False, **kwargs):
        self.lineedit = self.LineEdit(place=self, main=self.main, parent=self, **kwargs)
        if immutable:
            self.lineedit.setReadOnly(True)

    def build_label(self, **kwargs):
        self.label = self.Label(place=self, main=self.main, parent=self, **kwargs)

    def build_button(self, **kwargs):
        self.button = self.Button(place=self, main=self.main, parent=self, **kwargs)

    def build_tiplabel(self, text, fontsize=None, width=None):
        if not 'lineedit' in dir(self):
            return

        self.tiplabel = t.pos(new=self.lineedit, inside=self.lineedit)
        self.tiplabel.width_size = width
        self.tiplabel.setText(text)

        if fontsize:
            t.style(self.tiplabel, font=fontsize)
            self.tiplabel.font_size = fontsize
        else:
            self.tiplabel.font_size = t.correct_broken_font_size(self.tiplabel)

        t.style(self.tiplabel, color=TIPTEXT, background='transparent')

    def button_and_lineedit_reactions(self):
        if not 'button' in dir(self) or not 'lineedit' in dir(self):
            return

        if not self.lineedit.signal:
            return

        self.lineedit.signal.activated.connect(
            lambda: t.style(self.button, background=ACTIVE_GREEN))

        self.lineedit.signal.activated.connect(
            lambda: t.style(self.button.activation_toggle(force=True, save=False)))

        self.lineedit.signal.deactivated.connect(
            lambda: t.style(self.button, background=DEACTIVE_RED))

        self.lineedit.signal.deactivated.connect(
            lambda: t.style(self.button.activation_toggle(force=False, save=False)))

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if self.width() < 100:
            return

        self.set_positions()

    def set_positions(self):
        """
        self.button_width locks button at that width, else it will be symetric square from self.height()
        :return:
        """
        if 'canvas_border' in dir(self):
            cb = self.canvas_border
        else:
            cb = 0

        if 'button' in dir(self):
            hw = self.height() - (cb * 2)

            if self.button_width:
                bw = self.button_width
            else:
                bw = hw
            t.pos(self.button, height=hw, width=bw, left=cb, top=cb)

        if 'lineedit' in dir(self):
            if 'button' in dir(self):
                t.pos(self.lineedit, after=self.button, x_margin=self.edge, height=self.height() - (cb * 2), top=cb)
                t.pos(self.lineedit, left=self.lineedit, right=self.width() - cb - 1)
            else:
                t.pos(self.lineedit, inside=self, margin=cb)

            if 'tiplabel' in dir(self):
                if self.tiplabel.width_size:
                    t.pos(self.tiplabel, width=self.tiplabel.width_size)

                t.pos(self.tiplabel, height=self.lineedit.height() - (cb * 2), right=self.lineedit.width() - cb, x_margin=self.edge)

        if 'label' in dir(self):
            if 'button' in dir(self):
                t.pos(self.label, inside=self, left=dict(right=self.button), x_margin=self.edge, right=self.width() - cb)
                t.pos(self.label, height=self.label, sub=cb * 2, move=[0,cb])
            else:
                t.pos(self.label, inside=self, margin=cb)

    class LineEdit(DragDroper, GODLEPath):
        def __init__(self,
                    activated_on=None,
                    activated_off=None,
                    deactivated_on=None,
                    deactivated_off=None,
                    lineedit_background = 'white',
                    lineedit_foreground = 'black',
                    *args, **kwargs
                    ):
            super().__init__(
                             activated_on=activated_on or dict(color=TEXT_ON),
                             activated_off=activated_off or dict(color=TEXT_WHITE),
                             deactivated_on=deactivated_on or dict(color=TEXT_ON),
                             deactivated_off=deactivated_off or dict(color=TEXT_OFF),
                             *args, **kwargs)

            t.style(self, background=lineedit_background, color=lineedit_foreground, font=14)

    class Label(GODLabel, GLOBALHighLight):
        def __init__(self,
                        activated_on=None,
                        activated_off=None,
                        deactivated_on=None,
                        deactivated_off=None,
                        label_background='white',
                        label_foreground='black',
                        *args, **kwargs
                    ):
            super().__init__(
                             activated_on=activated_on or dict(color=TEXT_ON),
                             activated_off=activated_off or dict(color=TEXT_WHITE),
                             deactivated_on=deactivated_on or dict(color=TEXT_ON),
                             deactivated_off=deactivated_off or dict(color=TEXT_OFF),
                             *args, **kwargs)

            t.style(self, background=label_background, color=label_foreground, font=14)

    class Button(GODLabel, GLOBALHighLight):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            t.style(self, background=DEACTIVE_RED, color='black')
            self.setFrameShape(QtWidgets.QFrame.Box)
            self.setLineWidth(self.parent.edge)

def create_indikator(
                        place,
                        edge=1,
                        button=False,
                        lineedit=False,
                        label=False,
                        tiplabel=None,
                        height=30,
                        width=300,
                        tipfont=None,
                        tipwidth=None,
                        tooltip=None,
                        button_listen=False,
                        type=None,
                        post_init_signal=True,
                        Special=None,
                        *args, **kwargs
                    ):

    if Special:
        canvas = Special(place=place, edge=edge, width=width, height=height, type=type, *args, **kwargs)
    else:
        canvas = Canvas(place=place, edge=edge, width=width, height=height, type=type, *args, **kwargs)

    if lineedit:
        canvas.build_lineedit(**kwargs)
    if label:
        canvas.build_label(**kwargs)
    if button:
        canvas.build_button(**kwargs)
    if tiplabel:
        canvas.build_tiplabel(text=tiplabel, fontsize=tipfont, width=tipwidth)
    if button_listen:
        canvas.button_and_lineedit_reactions()
    if tooltip:
        canvas.setToolTip(tooltip)
        t.style(canvas, tooltip=True, background='black', color='white', font=14)

    if post_init_signal and lineedit and canvas.lineedit.activated:
        canvas.lineedit.signal.activated.emit()

    return canvas