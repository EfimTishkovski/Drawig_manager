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

gl_base = ''     # Глобальная переменная для имени активной базы
gl_cursor = ''   # Глобальный курсор
buf_number = ''  # Переменная-буфер для номера
buf_name = ''    # Переменная-буфер для имени
buf_link = ''    # Переменная-буфер для ссылки


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

    # Функция открытия компонента
    def edit_component(self):
        try:
            item = self.treeWidget.currentItem()
            number = item.text(0)
            # Определение типа компонента
            for line in self.data_components:
                if line['number'] == number:
                    component_type = line['attribute']
                    component_link = line['link']
                    component_name = line['name']
                    break
            else:
                component_type = ''
                component_link = ''
                component_name = ''

            if component_type == 'part':
                print(component_type)
                # Допистать вызов содержащей спецификации (куда входит)
                self.edit_drawing(number=number, name=component_name, link=component_link)
            elif component_type == 'assembly':
                self.edit_assembly(number=number)
                print(component_type)
            elif component_type == 'gost':
                print(component_type)
                self.edit_drawing()     # А оно надо?
            elif component_type == 'outsource':
                print(component_type)
                self.edit_drawing()     # А оно надо?
            elif component_type == '':
                self.statusBar().showMessage(f'Компонент  {number} тип не определён')
            else:
                self.statusBar().showMessage(f'Компонент  {number} {component_type} не известный тип')
        except:
            self.statusBar().showMessage('Ошибка открытия компонента')

    # Функция редактирования сборки
    def edit_assembly(self, number):
        items_component = []
        for line in self.data_connections:
            if line['number'] == number:
                items_component.extend(line['included'])
                break
        else:
            items_component = []

        print(items_component)
        # Заполнение данными таблицы
        if items_component:
            self.sp_table.setRowCount(len(items_component))  # Установка количества строк
            # Передача данных в таблицу
            for row in range(len(items_component)):
                for column in range(len(items_component[row])):
                    self.sp_table.setItem(row, column, QtWidgets.QTableWidgetItem(str(items_component[row][column])))
            self.sp_table.resizeColumnsToContents()         # Подгонка размеров колонок по содержимому
        else:
            self.sp_table.clear()


    # Функция открытия чертежа
    def show_drawing(self):
        try:
            item = self.treeWidget.currentItem()
            number = item.text(0)

            # Поиск ссылки
            for line in self.data_components:
                if line['number'] == number:
                    component_link = line['link']
                    break
            else:
                component_link = ''

            # Проверка на пустую ссылку
            if component_link is False or component_link is None:
                self.statusBar().showMessage('Ссылка не задана или не найдена')
            else:
                # Открытие чертежа
                if self.user_pdf_program:
                    pass
                # Открытие прогой юзера
                # path_to_acrobat = self.patch_to_pdf  # Путь к проге заданной пользователем
                # process = subprocess.Popen([path_to_acrobat, '/A', 'page = ALL', link], shell=False, stdout=subprocess.PIPE)
                # process.wait()
                else:
                    # Открытие прогой по умолчанию
                    full_path = self.work_dir + component_link
                    os.startfile(full_path)
        except:
            self.statusBar().showMessage('Ошибка открытия чертежа')


    # Функция редактирования чертежа
    def edit_drawing(self, number, name, link):
        try:
            # Отображение данных по чертежу
            self.number_line.setText(number)
            self.name_line.setText(name)
            self.link_line.setText(link)
            # Сохранение данных в буферные переменные
            global buf_number, buf_name, buf_link  # ?
            buf_number = number                    # ?
            buf_name = name                        # ?
            buf_link = link                        # ?

            # Новая часть
            incl = ''
            for line in self.data_connections:
                for cell in  line['included']:
                    if cell[0] == number:
                        incl = line['number']
                        break
            self.edit_assembly(number=incl)
        except:
            self.statusBar().showMessage('Ошибка редактирования чертежа')


    # Функция обработки нажатия на строку дерева(открытие или редактирование)
    def click_line(self):
        if self.drawing_edit_flag:
            self.edit_component()
        else:
            self.show_drawing()


    # Функция отслеживания состояния чекбокса редактирования
    def draw_edit_state(self, state):
        if state == Qt.Checked:
            self.drawing_edit_window.setEnabled(True)
            self.ass_edit_window.setEnabled(True)
            self.drawing_edit_flag = True
        else:
            self.drawing_edit_window.setEnabled(False)
            self.ass_edit_window.setEnabled(False)
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


    # Функция сохранения изменений
    def save_draw_change(self):
        # Считывание прежних данных
        global buf_number, buf_name, buf_link
        old_number = buf_number
        old_name = buf_name
        old_link = buf_link
        link = self.link_line.toPlainText()
        number = self.number_line.text()
        name = self.name_line.toPlainText()
        # Дописать проверку на неизменность вводимых данных
        # Дописать проверку на непустой ввод (наверное кроме ссылки)
        new_data = []
        if old_number != number:
            new_data.append(number)
        if old_name != name:
            new_data.append(name)
        if old_link != link:
            new_data.append(link)

        # Продолжить работу по отслеживанию изменений над write_to_base
        if new_data:
            answer_base = write_to_base(gl_base, gl_cursor, (link, number))
            if answer_base:
                self.statusBar().showMessage('Изменения сохранены')
            else:
                self.statusBar().showMessage('Ошибка сохранения изменений')


    """
    Дневник разработчика =)
    Убрать окно редактирования чертежа
    Редактирование чертежей (номер, имя, ссылка) сделать в таблице сборки
    
    Подумать над первичным входжением ?
    Сделать вызов спецификации, содержащей чертёж, при нажатии на чертёж в дереве (готово)
    Подчистить и упорядочить код
    Дальнейшая работа на внесением изменений в компонент детали
    
    Отслеживать изменения тадлицы сборки, находить разницу и вносить изменения в БД
    """

    def __init__(self):
        super(Main_window, self).__init__()
        loadUi('Form.ui', self)
        settings = settings_load()                  # Загрузка сохранённых настроек

        # Настройки при запуске
        self.drawing_edit_window.setEnabled(False)  # Окно редактирования чертежа не активно
        self.ass_edit_window.setEnabled(False)      # Окно редактирования сборки не активно

        # Переменные
        self.user_pdf_program = False                # Флаг выбора пользовательской проги для pdf
        self.work_dir = settings[0]['work_dir']      # Рабочая папка #'D:/G5/PY/Drawig_manager/draw_lib/'
        self.base = settings[1]['base']              # База
        self.drawing_edit_flag = False               # Флаг редактирования чертежа

        connection_base(self.base)                   # Соединение с базой

        # Получение данных из базы по компонентам и связям
        try:
            self.data_components, self.data_connections = get_data_from_base(gl_cursor)
            print('Данные из базы получены')
        except:
            self.data_components = []
            self.data_connections = []
            print('Ошибка полученя данных из базы')

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
        self.save_change_Button.clicked.connect(self.save_draw_change)    # Сохранение изменений компонента(чертежа)


# Запуск
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main_window()
    window.show()
    sys.exit(app.exec_())

