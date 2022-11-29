import os
import sys
import sqlite3
import json
import subprocess

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.uic import loadUi
from PyQt5 import QtCore

from controller import *

gl_base = ''    # Глобальная переменная для имени активной базы
gl_cursor = ''  # Глобальный курсор


# Функция подключения к базе
def connection_base():
    base = sqlite3.connect('D:/PY/Drawings/Base data/Т5.1.db')
    cursor = base.cursor()
    global gl_base, gl_cursor
    gl_base = base
    gl_cursor = cursor
    print("Соединение с базой")


class Main_window(QMainWindow):

    # Функция отображения дерева
    def show_tree_new(self):
        # Получение данных по модели базы
        data = model(gl_cursor, mode='view')[0]
        #print(data)

        # Корневой/первичный элемент
        name_first_element = data['number']
        items = []
        item = QtWidgets.QTreeWidgetItem([name_first_element])

        # Добавление дочерних элементов
        if data['included']:
            # Уровень 1
            for element_1 in data['included']:
                child_item_1 = QtWidgets.QTreeWidgetItem([element_1['number']])
                # Уровень 2
                if element_1['included']:
                    for element_2 in element_1['included']:
                        if isinstance(element_2, dict):
                            child_item_2 = QtWidgets.QTreeWidgetItem([element_2['number']])
                            # Уровень 3
                            for element_3 in element_2['included']:
                                if isinstance(element_3, dict):
                                    child_item_3 = QtWidgets.QTreeWidgetItem([element_3['number']])
                                    # Уровень 4
                                    for element_4 in element_3['included']:
                                        if isinstance(element_4, dict):
                                            child_item_4 = QtWidgets.QTreeWidgetItem([element_4['number']])
                                            # Место под Уровень 5
                                            child_item_3.addChild(child_item_4)
                                        else:
                                            child_item_4 = QtWidgets.QTreeWidgetItem([element_4])
                                            child_item_3.addChild(child_item_4)
                                    child_item_2.addChild(child_item_3)
                                else:
                                    child_item_3 = QtWidgets.QTreeWidgetItem([element_3])
                                    child_item_2.addChild(child_item_3)
                            child_item_1.addChild(child_item_2)
                        else:
                            child_item_2 = QtWidgets.QTreeWidgetItem([element_2])
                            child_item_1.addChild(child_item_2)
                item.addChild(child_item_1)

        items.append(item)
        self.treeWidget.insertTopLevelItems(0, items)

    # Функция указания пути к базе
    def select_base(self):
        try:
            basename = QFileDialog.getOpenFileName(self, 'Открыть файл', '', '*.db')[0]
            relativ_path_to_base = basename.partition(self.work_dir)
            if basename:
                print(basename)
                print(relativ_path_to_base)
        except:
            self.statusBar().showMessage('Ошибка открытия базы')

    # Функция открытия чертежа
    def show_drawing(self, link):
        try:
            if self.user_pdf_program:
                pass
                # Открытие прогой юзера
            else:
                #path = self.
                os.startfile(path)
                #os.startfile('D:/PY/Drawings/draw_lib/Т5.1-10.11.001 - Боковина рамы.pdf')


        except:
            self.statusBar().showMessage('Ошибка открытия чертежа')

        os.startfile('D:/PY/Drawings/draw_lib/Т5.1-10.11.001 - Боковина рамы')
            # path_to_acrobat = self.patch_to_pdf  # Путь к проге заданной пользователем
            # process = subprocess.Popen([path_to_acrobat, '/A', 'page = ALL', link], shell=False, stdout=subprocess.PIPE)
            # process.wait()

    def click_item(self):
        item = self.treeWidget.currentItem()
        print(item.text(0))

    def dublle_click_item(self):
        item = self.treeWidget.currentItem()
        print(item.text(0) + 'двойной клик')
        os.startfile('D:/PY/Drawings/draw_lib/Т5.1-10.11.001 - Боковина рамы.pdf')


    def __init__(self):
        super(Main_window, self).__init__()
        loadUi('Form.ui', self)
        connection_base()

        # Переменные
        self.user_pdf_program = False  # Флаг выбора пользовательской проги для pdf
        self.work_dir = ''             # Рабочая папка

        self.launch.clicked.connect(self.show_tree_new)
        self.selectionButton.clicked.connect(self.select_base)
        #self.treeWidget.currentItemChanged.connect(self.click_item)
        #self.treeWidget.itemClicked.connect(self.click_item)
        self.treeWidget.itemDoubleClicked.connect(self.dublle_click_item)



# Запуск
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main_window()
    window.show()
    sys.exit(app.exec_())

