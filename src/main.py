#!/usr/bin/env python3

import os
import sys

from sys import exit, argv
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QTableWidget, QCheckBox
from PyQt6.QtGui import QTextCursor
from MainWindow import Ui_MainWindow


checkBoxes = [
    "enableBasic",
    "enableTarget",
    "enableCarry",
    "enableSword",
    "enableBiggoron",
    "enableHammer",
    "enableShieldCorners",
    "enableFrameTurn",
]

checkBoxToGroup = {
    "enableBasic": "basic",
    "enableTarget": "target_enabled",
    "enableCarry": "no_carry",
    "enableSword": "sword",
    "enableBiggoron": "biggoron",
    "enableHammer": "hammer",
    "enableShieldCorners": "shield corners",
    "enableFrameTurn": "c-up frame turn",
}


class MainWindow(QMainWindow):
    def __init__(self):
        """Main initialisation function"""
        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.proc = QProcess(self)

        self.initConnections()

    def print(self, content: str):
        self.ui.output.appendPlainText(content + ("\n" if not content.endswith("\n") else ""))

    def getTableValues(self, table: QTableWidget, enableAssert: bool = True):
        values: list[str] = []
        for i in range(table.rowCount()):
            curItem = table.item(i, 0)
            if curItem is not None and len(curItem.text()) > 0:
                values.append(curItem.text())
        if enableAssert:
            assert len(values) > 0
        return values

    def appendListArguments(self, argPrefix: str, argList: list):
        self.args.append(argPrefix)
        for arg in argList:
            self.args.append(f"{arg}")

    # from https://stackoverflow.com/a/70405825
    def getDataFolder(self):
        # path of your data in same folder of main .py or added using --add-data
        if getattr(sys, "frozen", False):
            data_folder_path = sys._MEIPASS
        else:
            data_folder_path = os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__))[:-4]
        return data_folder_path

    def searchAngles(self):
        self.optionsSetEnabled(False)

        self.allowedGroups: list[str] = []
        self.startAngles: list[str] = []
        self.findAngles: list[str] = []
        self.avoidAngles: list[str] = []
        self.args: list[str] = []

        for checkBox in checkBoxes:
            curCheckBox: QCheckBox = getattr(self.ui, checkBox)
            if curCheckBox.isChecked():
                self.allowedGroups.append(checkBoxToGroup[checkBox])

        try:
            assert len(self.allowedGroups) > 0
            self.startAngles = self.getTableValues(self.ui.startAnglesTable)
            self.findAngles = self.getTableValues(self.ui.findAnglesTable)
        except AssertionError:
            self.print("Assertion Error! Make sure to fill start and find angles tables.")
            self.optionsSetEnabled(True)
            return

        self.avoidAngles = self.getTableValues(self.ui.avoidAnglesTable, False)

        self.appendListArguments("-g", self.allowedGroups)
        self.appendListArguments("-s", self.startAngles)
        self.appendListArguments("-f", self.findAngles)

        if len(self.avoidAngles) > 0:
            self.appendListArguments("-a", self.avoidAngles)

        self.proc.setProgram(
            f"{self.getDataFolder()}/tools/{'AngleFinderCLI.exe' if os.name == 'nt' else 'AngleFinderCLI'}"
        )
        self.proc.setArguments(self.args)
        self.proc.start()

    def updateOutput(self):
        self.print(self.proc.readAllStandardOutput().data().decode("UTF-8"))
        self.print(self.proc.readAllStandardError().data().decode("UTF-8"))
        self.ui.output.moveCursor(QTextCursor.MoveOperation.End)

    def optionsSetEnabled(self, isEnabled: bool):
        for checkBox in checkBoxes:
            curCheckBox: QCheckBox = getattr(self.ui, checkBox)
            curCheckBox.setEnabled(isEnabled)
        self.ui.startAnglesTable.setEnabled(isEnabled)
        self.ui.findAnglesTable.setEnabled(isEnabled)
        self.ui.avoidAnglesTable.setEnabled(isEnabled)
        self.ui.searchBtn.setEnabled(isEnabled)

    def enableOptions(self):
        self.optionsSetEnabled(True)

    # connections callbacks

    def initConnections(self):
        """Initialises the callbacks"""
        self.ui.searchBtn.clicked.connect(self.searchAngles)
        self.proc.readyReadStandardOutput.connect(self.updateOutput)
        self.proc.readyReadStandardError.connect(self.updateOutput)
        self.proc.finished.connect(self.enableOptions)

    # https://github.com/ingwant/PyQt5-Video-Book/blob/fb6b54048ac5edde42aa14e3efa4485ac5343f14/%23013_QTableWidget_copy_paste/main.py#L17
    def updateKeyPressEvent(self, event, table: QTableWidget):
        try:
            # Check keyboard input(Ctrl + V) to accomplish of paste
            if event.key() == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                selection = table.selectedIndexes()

                if selection:
                    # Get the first selected cell position
                    row_anchor = selection[0].row()
                    column_anchor = selection[0].column()

                    # Create clipboard object to read data from clipboard
                    clipboard = QApplication.clipboard()
                    # Get data list from clipboard
                    rows = clipboard.text().split("\n")

                    # Add more rows if current row count doesn't match the new row count needed
                    if table.rowCount() < row_anchor + len(rows) - 1:
                        table.setRowCount(row_anchor + len(rows) - 1)

                    # Show data in table widget which gets from Excel file
                    for index_row, row in enumerate(rows):
                        values = row.split("\t")
                        for index_col, value in enumerate(values):
                            item = QTableWidgetItem(value)
                            table.setItem(row_anchor + index_row, column_anchor + index_col, item)

            # Check keyboard input(Ctrl + C) to accomplish copy
            # Check keyboard input(Ctrl + X) to accomplish cut
            if (event.key() == Qt.Key.Key_C or event.key() == Qt.Key.Key_X) and (
                event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                # get the selection section data
                copied_cell = sorted(table.selectedIndexes())
                # Define a variable to save selected data
                copy_text = ""
                max_column = copied_cell[-1].column()
                for cell in copied_cell:
                    # Get each cell text
                    cell_item = table.item(cell.row(), cell.column())
                    if cell_item:
                        copy_text += cell_item.text()
                        # Clear data in table widget when it cuts data
                        if event.key() == Qt.Key.Key_X:
                            cell_item.setText("")

                    else:
                        copy_text += ""

                    # Format the copied data for paste into Excel file
                    if cell.column() == max_column:
                        copy_text += "\n"
                    else:
                        copy_text += "\t"

                # Save data into clipboard
                QApplication.clipboard().setText(copy_text)

        except Exception as e:
            print(e)
            pass

    def keyPressEvent(self, event) -> None:
        super().keyPressEvent(event)
        self.updateKeyPressEvent(event, self.ui.startAnglesTable)
        self.updateKeyPressEvent(event, self.ui.findAnglesTable)


# start the app
if __name__ == "__main__":
    app = QApplication(argv)
    mainWindow = MainWindow()

    try:
        from qdarktheme import load_stylesheet

        app.setStyleSheet(load_stylesheet())
    except ModuleNotFoundError:
        pass

    mainWindow.show()
    exit(app.exec())
