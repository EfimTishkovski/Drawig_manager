import os
import sys
import sqlite3
import json
import subprocess

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

from controller import *

gl_base = ''    # Глобальная переменная для имени активной базы
gl_cursor = ''  # Глобальный курсор


# Функция подключения к базе
def connection_base(link):
    try:
        base = sqlite3.connect(link)
        cursor = base.cursor()
        global gl_base, gl_cursor
        gl_base = base
        gl_cursor = cursor
        print("Соединение с базой")
    except:
        print('Соединения с базой нет')


class Main_window(QMainWindow):

    # Функция отображения дерева
    def show_tree_new(self):
        # Получение данных по модели базы
        data = model(gl_cursor, mode='view')[0]

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
            if basename:
                global gl_base
                gl_base = basename
                self.base_line.setText(basename)
                print(basename)
        except:
            self.statusBar().showMessage('Ошибка открытия базы')

    # Функция открытия чертежа
    def show_drawing(self):
        try:
            item = self.treeWidget.currentItem()
            number = item.text(0)
            path = link_of_drawing(gl_cursor, number_drawing=number)
            if path[0] is not None:
                if self.user_pdf_program:
                    pass
                    # Открытие прогой юзера
                    # path_to_acrobat = self.patch_to_pdf  # Путь к проге заданной пользователем
                    # process = subprocess.Popen([path_to_acrobat, '/A', 'page = ALL', link], shell=False, stdout=subprocess.PIPE)
                    # process.wait()
                else:
                    # Открытие прогой по умолчанию
                    full_path = self.work_dir + path[0]
                    os.startfile(full_path)
            else:
                self.statusBar().showMessage('Не задана ссылка на чертёж')
        except:
            self.statusBar().showMessage('Ошибка открытия чертежа')

    # Функция редактирования чертежа
    def edit_drawing(self):
        try:
            item = self.treeWidget.currentItem()
            number = item.text(0)
            query = 'SELECT name, link FROM components WHERE number = ?'
            gl_cursor.execute(query, (number,))
            data = gl_cursor.fetchall()[0]
            self.number_line.setText(number)
            self.name_line.setText(data[0])
            self.link_line.setText(data[1])
        except:
            self.statusBar().showMessage('Ошибка редактирования чертежа')


    # Функция обработки нажатия на строку дерева(открытие или редактирование)
    def click_line(self):
        if self.drawing_edit_flag:
            self.edit_drawing()
        else:
            self.show_drawing()


    # Функция отслеживания состояния чекбокса редактирования
    def draw_edit_state(self, state):
        if state == Qt.Checked:
            self.drawing_edit_window.setEnabled(True)
            self.drawing_edit_flag = True
        else:
            self.drawing_edit_window.setEnabled(False)
            self.drawing_edit_flag = False


    # Функция отслеживания состояния чекбокса папки с чертежами
    def work_dir_state(self, state):
        if state == Qt.Checked:
            user_work_dir = self.work_dir_line.toPlainText()
            answer_metod = update_settings(name_setting='work_dir', new_state=user_work_dir)
            if answer_metod:
                self.statusBar().showMessage('Рабочая папка сохранена')
            else:
                self.statusBar().showMessage('Ошибка сохранения рабочей папки')


    # Функция отслеживания состояния чекбокса базы
    def work_base_state(self, state):
        if state == Qt.Checked:
            current_base = self.base_line.toPlainText()
            answer_metod = update_settings(name_setting='base', new_state=current_base)
            if answer_metod:
                self.statusBar().showMessage('База по умолчанию')
            else:
                self.statusBar().showMessage('Ошибка назаначения базы по умолчанию')


    # Функция указания пути к рабочей папке
    def select_work_dir(self):
        try:
            work_dir = QFileDialog.getExistingDirectory(self, 'Выберите рабочую папку', '') + '/'
            if work_dir:
                self.work_dir_line.setText(work_dir)
        except:
            self.statusBar().showMessage('Ошибка указания рабочей папки')


    # Функция указания ссылки на чертёж
    def new_link(self):
        direktory = self.work_dir_line.toPlainText()
        new_link = QFileDialog.getOpenFileName(self, 'Открыть файл', direktory, '*.pdf')[0]
        new_link = new_link.split('/')[-1]
        self.link_line.setText(new_link)


    # Функция сохранения новой ссылки
    def new_link_save(self):
        link = self.link_line.toPlainText()
        number = self.number_line.text()
        answer_base = write_to_base(gl_base, gl_cursor, (link, number))
        if answer_base:
            self.statusBar().showMessage('Изменения сохранены')
        else:
            self.statusBar().showMessage('Ошибка сохранения изменений')


    def __init__(self):
        super(Main_window, self).__init__()
        loadUi('Form.ui', self)
        settings = settings_load()                  # Загрузка сохранённых настроек

        # Настройки при запуске
        self.drawing_edit_window.setEnabled(False)  # Окно редактирования не активно

        # Переменные
        self.user_pdf_program = False                # Флаг выбора пользовательской проги для pdf
        self.work_dir = settings[0]['work_dir']      # Рабочая папка #'D:/G5/PY/Drawig_manager/draw_lib/'
        self.base = settings[1]['base']              # База
        self.drawing_edit_flag = False               # Флаг редактирования чертежа

        connection_base(self.base)

        self.work_dir_line.setText(self.work_dir)
        self.base_line.setText(self.base)

        self.launch.clicked.connect(self.show_tree_new)
        self.selectionButton.clicked.connect(self.select_base)                # Указание базы
        self.selection_work_dir_Button.clicked.connect(self.select_work_dir)  # Указание рабочей папки
        self.treeWidget.itemClicked.connect(self.click_line)              # Обработчик нажатия на строку
        #self.treeWidget.itemDoubleClicked.connect(self.dublle_click_item)
        self.checkBox_edit.stateChanged.connect(self.draw_edit_state)     # Обработчик состояния чекбокса редактирования
        self.work_dir_checkBox.stateChanged.connect(self.work_dir_state)  # Обработчик состояния чекбокса рабочей папки
        self.base_checkBox.stateChanged.connect(self.work_base_state)     # Обработчик состояния чекбокса базы
        self.new_link_Button.clicked.connect(self.new_link)               # Указание новой ссылки на чертёж
        self.save_change_Button.clicked.connect(self.new_link_save)       # Сохранение новой ссылки


# Запуск
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main_window()
    window.show()
    sys.exit(app.exec_())

