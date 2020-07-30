# -*- coding: utf-8 -*-
'''
***************************************************************************
    inputs.py
    ---------------------
    Date                 : April 2019
    Copyright            : (C) 2019 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

various inputs to edit project parameters
'''

__author__ = 'Christoph Franke'
__date__ = '17/04/2019'

import os
from typing import List
from qgis.PyQt.Qt import (QSpinBox, QSlider, QObject, QDoubleSpinBox,
                          QLineEdit, QComboBox, Qt, QLabel, QHBoxLayout,
                          QCheckBox, QPushButton, QSizePolicy, QLayout)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import pyqtSignal

from projektcheck.settings import settings


class InputType(QObject):
    '''
    abstract class for an input-element, wraps QInputs to be used in parameter
    dialogs and parameter previews

    Attributes
    ----------
    changed : pyqtSignal
        emitted when value of input is changed, current value
    focus : pyqtSignal
        emitted when input comes into focus
    locked : pyqtSignal
        emitted when lock-status of input is toggled, lock-status
    '''
    changed = pyqtSignal(object)
    focus = pyqtSignal()
    locked = pyqtSignal(bool)

    def draw(self, layout: QLayout, unit: str = ''):
        '''
        add input to the layout

        Parameters
        ----------
        layout : QLayout
            layout to add the input to
        unit : str, optional
            the unit shown after the value, defaults to no unit
        '''
        layout.addWidget(self.input)
        if unit:
            layout.addWidget(QLabel(unit))

    @property
    def value(self) -> object:
        '''
        Returns
        -------
        object
            current value of this input
        '''
        return self.get_value()

    @value.setter
    def value(self, value: object):
        self.set_value(value)

    def set_value(self, value: object):
        '''
        override this to the set the value of the input
        '''
        raise NotImplementedError

    def get_value(self) -> object:
        '''
        override this to the get the current value of the input
        '''
        raise NotImplementedError

    @property
    def is_locked(self) -> bool:
        '''
        override function to implement a locked state

        Returns
        -------
        bool
            lock-state of input
        '''
        return False

    def registerFocusEvent(self, input):
        '''
        override, emits focus signal
        '''
        # dirty but works, easier than subclassing all types of inputs just to
        # emit the signal
        focus_base = input.focusInEvent
        def focusInEvent(evt):
            focus_base(evt)
            self.focus.emit()
        input.focusInEvent = focusInEvent


class Checkbox(InputType):
    '''
    checkbox input
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input = QCheckBox()
        self.input.stateChanged.connect(
            lambda state: self.changed.emit(self.input.isChecked()))
        self.registerFocusEvent(self.input)

    def set_value(self, checked: bool):
        '''
        set the check-state of the checkbox

        Parameters
        ----------
        checked : bool
            check-state
        '''
        self.input.setChecked(checked or False)

    def get_value(self) -> bool:
        '''
        get current check-state of the checkbox

        Returns
        -------
        bool
            current check-state
        '''
        return self.input.isChecked()


class Slider(InputType):
    '''
    slider input, displays a slider and a number input next to it, both
    connected to each other
    '''

    def __init__(self, minimum: int = 0, maximum: int = 100000000,
                 step: int = 1, width: int = 300,
                 lockable: bool = False, locked: bool = False, **kwargs):
        '''
        Parameters
        ----------
        width : int, optional
            width of slider in pixels, defaults to 300 pixels
        minimum : int, optional
            minimum value that the user can set
        maximum : int, optional
            maximum value that the user can set
        step : int, optional
            the tick intervall of the slider and single step of the number
            input, defaults to 1
        lockable : bool, optional
            the slider and number input can be locked by a checkbox that will
            be displayed next to them if True, defaults to not lockable
        locked : bool, optional
            initial lock-state of inputs, only applied if lockable is True,
            defaults to inputs being not locked
        '''
        super().__init__(**kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.lockable = lockable
        self.step = step
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setTickInterval(step)
        self.slider.setFixedWidth(width)
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(minimum)
        self.spinbox.setMaximum(maximum)
        self.spinbox.setSingleStep(step)
        self.registerFocusEvent(self.spinbox)
        self.registerFocusEvent(self.slider)

        if lockable:
            self.lock_button = QPushButton()
            self.lock_button.setCheckable(True)
            self.lock_button.setChecked(locked)
            self.lock_button.setSizePolicy(
                QSizePolicy.Fixed, QSizePolicy.Fixed)

            def toggle_icon(emit=True):
                is_locked = self.lock_button.isChecked()
                fn = '20190619_iconset_mob_lock_locked_02.png' if is_locked \
                    else '20190619_iconset_mob_lock_unlocked_03.png'
                self.slider.setEnabled(not is_locked)
                self.spinbox.setEnabled(not is_locked)
                icon_path = os.path.join(settings.IMAGE_PATH, 'iconset_mob', fn)
                icon = QIcon(icon_path)
                self.lock_button.setIcon(icon)
                self.locked.emit(is_locked)
            toggle_icon(emit=False)
            self.lock_button.clicked.connect(lambda: toggle_icon(emit=True))

        self.slider.valueChanged.connect(
            lambda: self.set_value(self.slider.value()))
        self.spinbox.valueChanged.connect(
            lambda: self.set_value(self.spinbox.value()))
        self.slider.valueChanged.connect(
            lambda: self.changed.emit(self.get_value()))
        self.spinbox.valueChanged.connect(
            lambda: self.changed.emit(self.get_value())
        )

    def set_value(self, value: int):
        '''
        set a number to both the slider and the number input

        Parameters
        ----------
        checked : int
            check-state
        '''
        for element in [self.slider, self.spinbox]:
            # avoid infinite recursion
            element.blockSignals(True)
            element.setValue(value or 0)
            element.blockSignals(False)

    @property
    def is_locked(self) -> bool:
        '''
        Returns
        -------
        bool
            current lock-state of slider and number input
        '''
        if not self.lockable:
            return False
        return self.lock_button.isChecked()

    def draw(self, layout: QLayout, unit: str = ''):
        '''
        add slider, the connected number and the lock (if lockable) input
        to the layout

        Parameters
        ----------
        layout : QLayout
            layout to add the inputs to
        unit : str, optional
            the unit shown after the value, defaults to no unit
        '''
        l = QHBoxLayout()
        l.addWidget(self.slider)
        l.addWidget(self.spinbox)
        if unit:
            l.addWidget(QLabel(unit))
        if self.lockable:
            l.addWidget(self.lock_button)
        layout.addLayout(l)

    def get_value(self) -> int:
        '''
        get the currently set number

        Returns
        -------
        int
            currently set number
        '''
        return self.slider.value()


class ComboBox(InputType):
    '''
    combobox input
    '''
    def __init__(self, values: List[str] = [], data: list = [],
                 width: int = None, **kwargs):
        '''
        Parameters
        ----------
        values : list, optional
            list of text items to fill the combobox with, defaults to an empty
            combobox
        data : list, optional
            list of data objects corresponding to the passed values, has to be
            of same length as those values, will be applied to the items in the
            same order, defaults to no data
        width : int, optional
            width of combobox in pixels, defaults flexible width
        '''
        super().__init__(**kwargs)
        self.input = QComboBox()
        self.registerFocusEvent(self.input)
        if width is not None:
            self.input.setFixedWidth(width)
        self.input.currentIndexChanged.connect(
            lambda: self.changed.emit(self.get_value()))
        for i, value in enumerate(values):
            args = [value]
            if len(data) > 0:
                args.append(data[i])
            self.add_value(*args)
        self.registerFocusEvent(self.input)

    def add_value(self, value: str, data: object = None):
        '''
        add an item to the combobox

        Parameters
        ----------
        value : str
            text of the item
        data : object, optional
            data object of the item, defaults to no data
        '''
        self.input.addItem(value, userData=data)

    def set_value(self, value: str):
        '''
        set the selected item

        Parameters
        ----------
        value : str
            text of item to select
        '''
        self.input.setCurrentText(str(value))

    def get_value(self) -> str:
        '''
        get currently selected item text

        Returns
        -------
        value : str
            text of selected item
        '''
        return self.input.currentText()

    def get_data(self):
        '''
        get data of currently selected item

        Returns
        -------
        value : object
            data of selected item
        '''
        return self.input.currentData()


class LineEdit(InputType):
    '''
    text input
    '''
    def __init__(self, width: int = None, **kwargs):
        '''
        Parameters
        ----------
        width : int, optional
            width of text input in pixels, defaults flexible width
        '''
        super().__init__(**kwargs)
        self.input = QLineEdit()
        if width is not None:
            self.input.setFixedWidth(width)
        self.input.textChanged.connect(self.changed.emit)
        self.registerFocusEvent(self.input)

    def set_value(self, value: str):
        '''
        set the text of the line input

        Parameters
        ----------
        value : str
            text
        '''
        self.input.setText(str(value or ''))

    def get_value(self) -> str:
        '''
        get the current text of the line input

        Returns
        -------
        value : str
            text
        '''
        return self.input.text()


class SpinBox(InputType):
    '''
    spinbox integer number input
    '''
    InputClass = QSpinBox
    def __init__(self, minimum=0, maximum=100000000, step=1,
                 lockable=False, locked=False, reversed_lock=False, **kwargs):
        '''
        Parameters
        ----------
        minimum : int, optional
            minimum value that the user can set
        maximum : int, optional
            maximum value that the user can set
        step : int, optional
            the single step of the number input when changing values,
            defaults to 1
        lockable : bool, optional
            the number input can be locked by a checkbox that will
            be displayed next to it if True, defaults to not lockable
        locked : bool, optional
            initial lock-state of input, only applied if lockable is True,
            defaults to input being not locked
        reversed_lock : bool, optional
            reverses the locking logic, if True checking the lock will enable
            the inputs instead of disabling them, defaults to normal lock
            behaviour (disabling inputs when setting lock-state to True)
        '''
        super().__init__(**kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.input = self.InputClass()
        self.input.setMinimum(minimum)
        self.input.setMaximum(maximum)
        self.input.setSingleStep(step)
        self.input.valueChanged.connect(self.changed.emit)
        self.registerFocusEvent(self.input)
        self.lockable = lockable

        # ToDo: almost the same as in Slider, outsource into common function
        if lockable:
            self.lock_button = QPushButton()
            self.lock_button.setCheckable(True)
            self.lock_button.setChecked(locked)
            self.lock_button.setSizePolicy(
                QSizePolicy.Fixed, QSizePolicy.Fixed)

            def toggle_icon(emit=True):
                is_locked = self.lock_button.isChecked()
                fn = '20190619_iconset_mob_lock_locked_02.png' if is_locked \
                    else '20190619_iconset_mob_lock_unlocked_03.png'
                self.input.setEnabled(is_locked if reversed_lock else
                                      not is_locked)
                icon_path = os.path.join(settings.IMAGE_PATH, 'iconset_mob', fn)
                icon = QIcon(icon_path)
                self.lock_button.setIcon(icon)
                self.locked.emit(is_locked)
            toggle_icon(emit=False)
            self.lock_button.clicked.connect(lambda: toggle_icon(emit=True))

    def set_value(self, value: int):
        '''
        set the value of the input

        Parameters
        ----------
        value : int
            value to set
        '''
        self.input.setValue(value or 0)

    def get_value(self) -> int:
        '''
        get the current value of the input

        Returns
        -------
        value : int
            current value of input
        '''
        return self.input.value()

    @property
    def is_locked(self) -> bool:
        '''
        Returns
        -------
        bool
            current lock-state of number input
        '''
        if not self.lockable:
            return False
        return self.lock_button.isChecked()

    def draw(self, layout: QLayout, unit: str = ''):
        '''
        add number input and the lock (if lockable) to the layout

        Parameters
        ----------
        layout : QLayout
            layout to add the inputs to
        unit : str, optional
            the unit shown after the value, defaults to no unit
        '''
        l = QHBoxLayout()
        l.addWidget(self.input)
        if unit:
            l.addWidget(QLabel(unit))
        if self.lockable:
            l.addWidget(self.lock_button)
        layout.addLayout(l)


class DoubleSpinBox(SpinBox):
    '''
    spinbox float number input

    same as SpinBox, but with floats instead of integers
    '''
    InputClass = QDoubleSpinBox
