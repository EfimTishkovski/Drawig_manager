import os
import sys
import sqlite3
import json
import subprocess

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

from controller import *

gl_base = ''  # Глобальная переменная для имени активной базы
gl_cursor = ''  # Глобальный курсор

#buf_current_sp_data = [] # Буферная перемменая для считывания данных из таблибы СП

# Функция окошка инфосообщения
def message_window(messege, title='Внимание!'):
    message_box = QMessageBox()
    message_box.setText(messege)
    message_box.setWindowTitle(title)
    message_box.setIcon(QMessageBox.Warning)
    message_box.setWindowIcon(QIcon('curwed_line.png'))
    message_box.exec_()

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
                self.edit_drawing(number=number)
            elif component_type == 'assembly':
                self.edit_assembly(number=number)
                print(component_type)
            elif component_type == 'gost':
                print(component_type)
                self.edit_drawing()  # А оно надо?
            elif component_type == 'outsource':
                print(component_type)
                self.edit_drawing()  # А оно надо?
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

        # Заполнение данными таблицы
        self.current_sp_number = ''
        if items_component:
            self.buf_current_sp_data = []
            buf = []
            self.sp_table.setRowCount(len(items_component))  # Установка количества строк
            # Передача данных в таблицу
            for row in range(len(items_component)):
                temp = []
                for column in range(len(items_component[row])):
                    self.sp_table.setItem(row, column, QtWidgets.QTableWidgetItem(str(items_component[row][column])))
                    temp.append(str(items_component[row][column]))
                buf.append(temp)
            self.sp_table.resizeColumnsToContents()  # Подгонка размеров колонок по содержимому
            self.buf_current_sp_data.extend(buf)     # Передача данных в буферный массив (для отслеживания изменений)
            self.current_sp_number = number          # Получение номера редактируемой сборки
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

    # Функция редактирования чертежа (и состава сборки)
    def edit_drawing(self, number):
        try:
            incl = ''
            for line in self.data_connections:
                for cell in line['included']:
                    if cell[0] == number:
                        incl = line['number']   # Номер содержащей сборки
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
            self.ass_edit_window.setEnabled(True)
            self.drawing_edit_flag = True
        else:
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

    # Функция указания ссылки на чертёж (временно не используется)
    def new_link(self):
        direktory = self.work_dir_line.toPlainText()
        new_link = QFileDialog.getOpenFileName(self, 'Открыть файл', direktory, '*.pdf')[0]
        new_link = new_link.split('/')[-1]
        return new_link

    # Функция добавленя элемента
    # Добавляет пустую строку для ввода
    def add_element(self):
        row_count = self.sp_table.rowCount()        # Установка количества строк
        self.sp_table.insertRow(row_count)
        column_count = self.sp_table.columnCount()  # Установка количества столбцов

        type_box = QtWidgets.QComboBox()
        type_box.addItems(['part', 'assembly', 'gost', 'outsource'])

        for num in range(column_count):
            self.sp_table.setItem(row_count, num, QtWidgets.QTableWidgetItem(str('')))   # Мнимое заполнение, для удобства

        self.sp_table.setCellWidget(row_count, column_count - 1, type_box)       # Добавление комбобокса в последнюю ячейку
        self.sp_table.resizeColumnsToContents()

        # Функция задания ссылки для нового элемента
    def link_new_element(self, item):
        try:
            if item.column() == 3:
                row = item.row()
                direktory = self.work_dir_line.toPlainText()
                new_link = QFileDialog.getOpenFileName(self, 'Открыть файл', direktory, '*.pdf')[0]
                new_link = new_link.split('/')[-1]
                self.sp_table.setItem(row, item.column(), QtWidgets.QTableWidgetItem(new_link))
        except:
            self.statusBar().showMessage('Ошибка назначения ссылки')

    # Функция сохранения изменений
    def save_new_element(self):
        new_data = self.get_data_from_table()
        old_data = self.buf_current_sp_data
        # Переработать формат данных в нормальный словарь
        dif = []       # Массив для разницы данных
        count = 0
        for line in new_data:
            count += 1
            if line in old_data:
                continue
            else:
                dif.append({'number': line[0], 'name': line[1], 'quantity': line[2],
                           'link': line[3], 'attribute': line[4], 'ass': self.current_sp_number,
                            'attribute': self.sp_table.cellWidget(count - 1, 4).currentText()})
        print('данные', dif)
        # Сохранение циклом если новых строк сразу несколько
        if dif:
            for line in dif:
                answer = write_to_base(base=gl_base, cursor=gl_cursor, new_data=line, mode='add')
                if answer[0]:
                    self.statusBar().showMessage(answer[1])  # Переделать на инфо окно
                else:
                    self.statusBar().showMessage(answer[1])
        else:
            self.statusBar().showMessage('Нет новых данных')

    # Функция получения данных из таблицы
    def get_data_from_table(self):
        out = []
        row = self.sp_table.rowCount()
        column = self.sp_table.columnCount()
        for line in range(row):
            temp = []
            for cell in range(column):
                cell_data = self.sp_table.item(line, cell)
                temp.append(cell_data.text())
            out.append(temp)

        return out


    """
    Дневник разработчика =)
    
    Редактирование чертежей (номер, имя, ссылка) сделать в таблице сборки 
    Подумать над первичным входжением ?
    
    Дальнейшая работа над добавлением/удалением детали. Сохранение изменений в базе (в работе 28.12.22)
     
    dif цикл в view.py
    Добавить обновление дерева при добавлении новых компонентов
    
    """

    def __init__(self):
        super(Main_window, self).__init__()
        loadUi('Form.ui', self)
        settings = settings_load()  # Загрузка сохранённых настроек

        # Настройки при запуске
        # self.drawing_edit_window.setEnabled(False)  # Окно редактирования чертежа не активно
        self.ass_edit_window.setEnabled(False)  # Окно редактирования сборки не активно

        # Переменные
        self.user_pdf_program = False  # Флаг выбора пользовательской проги для pdf
        self.work_dir = settings[0]['work_dir']  # Рабочая папка #'D:/G5/PY/Drawig_manager/draw_lib/'
        self.base = settings[1]['base']  # База
        self.drawing_edit_flag = False  # Флаг редактирования чертежа
        self.buf_current_sp_data = []   # Буферная перемменая для считывания данных из таблибы СП
        self.current_sp_number = ''     # Номер редактируемой сборки

        connection_base(self.base)  # Соединение с базой

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
        self.selectionButton.clicked.connect(self.select_base)  # Указание базы
        self.selection_work_dir_Button.clicked.connect(self.select_work_dir)  # Указание рабочей папки
        self.treeWidget.itemClicked.connect(self.click_line)  # Обработчик нажатия на строку
        # self.treeWidget.itemDoubleClicked.connect(self.dublle_click_item)
        self.checkBox_edit.stateChanged.connect(self.draw_edit_state)  # Обработчик состояния чекбокса редактирования
        self.work_dir_checkBox.stateChanged.connect(self.work_dir_state)  # Обработчик состояния чекбокса рабочей папки
        self.base_checkBox.stateChanged.connect(self.work_base_state)  # Обработчик состояния чекбокса базы
        # self.new_link_Button.clicked.connect(self.new_link)               # Указание новой ссылки на чертёж
        # self.save_change_Button.clicked.connect(self.save_draw_change)    # Сохранение изменений компонента(чертежа)
        self.add_button.clicked.connect(self.add_element)                   # Добавить элемент в сборку
        self.sp_table.itemClicked.connect(self.link_new_element)            # Указание ссылки для элемента
        self.save_change_Button_sp.clicked.connect(self.save_new_element)   # Нажатие на кнопку сохранить изменения


# Запуск
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main_window()
    window.show()
    sys.exit(app.exec_())
