import os
import sqlite3
import json
import copy


def get_data_from_base(cursor):
    """
    Функция получения данных из базы
    :param cursor: Курсор, объект БД
    :return: массив со всеми компонентами базы, массиб со всеми связями в базе
    что куда входит
    """
    # Данные из БД по компонентам
    query = 'SELECT * FROM components'
    cursor.execute(query)
    data = cursor.fetchall()
    out_components = []
    for line in data:
        out_components.append({'number': line[0], 'name': line[1],
                               'level': line[2], 'link': line[3], 'attribute': line[4]})

    # Данные из БД по связям(вхождению)
    query_for_connections = 'SELECT * FROM connections'
    cursor.execute(query_for_connections)
    data_connections = cursor.fetchall()
    included_mass = []  # Массив для номеров сборок
    out_connections = []
    for line in data_connections:
        included_mass.append(line[1])
    included_set = set(included_mass)
    temp = []
    for line in included_set:
        for component in data_connections:
            if line == component[1]:
                # Добавление имени
                for element in out_components:
                    if element['number'] == component[0]:
                        name = element['name']
                        break
                else:
                    name = ''
                temp.append((component[0], name, component[2]))
        out_connections.append({'number': line, 'included': temp.copy()})
        temp.clear()
    return out_components, out_connections


def model(cursor_in_model, mode='generate'):
    """
    Функция создания модели БД
    :param cursor_in_model: Курсор, объект БД
    :param mode: чтение/запись/просмотр
    :return: возвращает модель БД в виде словаря со множественными вложениями
    """
    # Создание
    if mode == 'generate':
        data_components, data_connections = get_data_from_base(cursor_in_model)  # Получение данных из базы
        mass_app = []  # Массив модели
        for line in data_components:
            if line['level'] == '0':
                comp_0 = line['number']  # Поиск нулевой сборки
                break
        else:
            comp_0 = ''
            print('Сборка с уровнем 0 не найдена')

        for line in data_connections:
            if line['number'] == comp_0:
                parts = copy.deepcopy(line['included'])
                mass_app.append({'number': comp_0, 'included': parts})  # Нулевая сборка и её входящие

        # Уровень 1
        temp = []
        inc_0 = mass_app[0]['included']  # Входящие в сборку 0
        buf = []
        for element in inc_0:
            temp.clear()
            for line in data_connections:
                if line['number'] == element:
                    temp.append({'number': element, 'included': line['included']})
                    break
            else:
                temp.append({'number': element, 'included': []})

            buf.append(temp[0])
        mass_app[0]['included'] = copy.deepcopy(buf)  # deepcopy решение проблемы с порчей data_components
        buf.clear()

        # Уровень 2
        size_level_1 = len(mass_app[0]['included'])
        for i_1 in range(size_level_1):
            size_level_2 = len(mass_app[0]['included'][i_1]['included'])
            for i_2 in range(size_level_2):
                item = mass_app[0]['included'][i_1]['included'][i_2]
                for line in data_connections:
                    if item == line['number']:
                        mass_app[0]['included'][i_1]['included'][i_2] = \
                            {'number': line['number'], 'included': line['included']}  # Проблема тут
                        break

        # Уровень 3
        size_level_0 = len(mass_app[0]['included'])
        for i_1 in range(size_level_0):
            size_level_1 = len(mass_app[0]['included'][i_1]['included'])
            for i_2 in range(size_level_1):
                if isinstance(mass_app[0]['included'][i_1]['included'][i_2], dict):
                    size_level_2 = len(mass_app[0]['included'][i_1]['included'][i_2]['included'])
                    for i_3 in range(size_level_2):
                        item = mass_app[0]['included'][i_1]['included'][i_2]['included'][i_3]
                        for element in data_connections:
                            if item == element['number']:
                                mass_app[0]['included'][i_1]['included'][i_2]['included'][i_3] \
                                    = {'number': element['number'], 'included': element['included']}

        # Запись в файл
        with open('model.json', 'w', encoding='utf-8') as model_file:
            json.dump(mass_app, model_file)

        return mass_app
    # Построение/просмотр
    if mode == 'view':
        with open('model.json', 'r', encoding='utf-8') as model_file:
            data = json.load(model_file)
        return data

    # Обновление
    if mode == 'update':
        pass

def settings_load():
    """
    Функция загрузки настроек
    :return: массив с данными по настройкам
    """
    try:
        connection = sqlite3.connect('system_settings.db')
        cursor = connection.cursor()
        query = 'SELECT * FROM user_settings'
        cursor.execute(query)
        data = cursor.fetchall()
        out = list()
        for line in data:
            temp = {}
            temp[line[0]] = line[1]
            out.append(temp)
        cursor.close()
        connection.close()
        return out
    except:
        out = []
        return out

def update_settings(name_setting, new_state):
    """
    Функция обновления настроек
    :param name_setting: Название настройки
    :param new_state: Новые данные по настройке
    :return: успешно / неуспешно
    """
    try:
        connection = sqlite3.connect('system_settings.db')
        cursor = connection.cursor()
        query = 'UPDATE user_settings SET value = ? WHERE name = ?'
        cursor.execute(query, (new_state, name_setting))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except:
        return False

def write_to_base(base, cursor, new_data, old_data):
    """
    Функция записи в основную базу
    Структура массивов new_data и old_data:
    ({number: 'Д-00.00.000-Ы'}, {name: 'странная деталь'}, {link: 'странное место'})
    :param base: Объект базы
    :param cursor: Объект курсора
    :param data: данные для записи
    :return: успешно / неуспешно
    """
    try:
        change_attribute = []
        for item in zip(old_data, new_data):
            a = list(item[0].values())[0]
            b = list(item[1].values())[0]
            if a != b:
                change_attribute.append(list(item[0].keys())[0])

        print(change_attribute)

        # Внесение изменений в базу
        for attribute in change_attribute:
            if attribute == 'number':
                pass
            elif attribute == 'name':
                query = 'UPDATE components SET name = ?, link = ? WHERE number = ?'
                cursor.execute(query, (new_data['name'], new_data['number']))
                base.commit()
            elif attribute == 'link':
                query = 'UPDATE components SET link = ?, link = ? WHERE number = ?'
                cursor.execute(query, (new_data['name'], new_data['number']))
                base.commit()

        return True
    except sqlite3.Error as error:
        print(error)
        return False

# Возможно не используется
def link_of_drawing(cursor, number_drawing):
    """
    Функция полученя ссылки чертежа из базы
    :param cursor: Объект курсора
    :param number_drawing: номер чертежа
    :return: ссылка из базы
    """
    query = 'SELECT link FROM components WHERE number = ?'
    cursor.execute(query, (number_drawing, ))
    data = cursor.fetchall()
    return data[0]


def show_drawing(link, work_dir, user_pdf_program):
    """
    Функция открытия чертежа
    :param link: Ссылка для открытия чертежа
    :param work_dir: Рабочая папка
    :param user_pdf_program: программа для pdf поумолчанию/пользовательская
    :return: сообщение об ошибке, если пусто, то отработала штатно
    """
    try:
        # Проверка на пустую ссылку
        if link is False or link is None:
            message = 'Ссылка не задана или не найдена'
            return message

        # Открытие чертежа
        if user_pdf_program:
            pass
                # Открытие прогой юзера
                # path_to_acrobat = self.patch_to_pdf  # Путь к проге заданной пользователем
                # process = subprocess.Popen([path_to_acrobat, '/A', 'page = ALL', link], shell=False, stdout=subprocess.PIPE)
                # process.wait()
        else:
            # Открытие прогой по умолчанию
            full_path = work_dir + link
            os.startfile(full_path)
    except:
        message = 'Ошибка открытия чертежа'
        return message


if __name__ == "__main__":
    print(settings_load())
