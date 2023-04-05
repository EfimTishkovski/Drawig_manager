import os
import sqlite3
import json
import copy

# Функция получения данных из базы
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
    included_mass = []            # Массив для номеров сборок
    out_connections = []
    out_connections_enlarged = [] # Массив для расширенных данных
    for line in data_connections:
        included_mass.append(line[1])
    included_set = set(included_mass)
    temp = []
    temp_enlarged = []
    for line in included_set:
        for component in data_connections:
            if line == component[1]:
                # Добавление имени
                for element in out_components:
                    if element['number'] == component[0]:
                        name = element['name']
                        link = element['link']
                        attribute = element['attribute']
                        break
                else:
                    name = ''
                    link = ''
                    attribute = ''
                temp.append(component[0])
                temp_enlarged.append((component[0], name, component[2], link, attribute))
        out_connections.append({'number': line, 'included': temp.copy()})
        out_connections_enlarged.append({'number': line, 'included': temp_enlarged.copy()})
        temp.clear()
        temp_enlarged.clear()
    return out_components, out_connections, out_connections_enlarged

# Функция создания модели БД
def model(cursor_in_model, mode='generate'):
    """
    Функция создания модели БД
    :param cursor_in_model: Курсор, объект БД
    :param mode: чтение/запись/просмотр
    :return: возвращает модель БД в виде словаря со множественными вложениями
    """
    # Создание
    if mode == 'generate':
        massive_data = get_data_from_base(cursor_in_model)  # Получение данных из базы
        data_components = massive_data[0]
        data_connections = massive_data[1]
        data_connections_enl = massive_data[2]  # ?
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
            # Открывать файл и закрывать его принудительно

        return mass_app
    # Построение/просмотр
    if mode == 'view':
        with open('model.json', 'r', encoding='utf-8') as model_file:
            data = json.load(model_file)
        return data

    # Обновление
    if mode == 'update':
        pass

# Функция загрузки настроек
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

# Функция обновления настроек
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

# Функция записи в основную базу
def write_to_base(base, cursor, new_data='', old_data='', mode=''):
    """
    Функция записи в основную базу
    Структура массивов new_data и old_data:
    ({number: 'Д-00.00.000-Ы'}, {name: 'странная деталь'}, {link: 'странное место'})
    перевести на {'number': 'Д-00.00.000-Ы', 'name': 'странная деталь', 'link': 'странное место', 'attribute': 'part'}
    для добавления нового (add)
    {'number': 'Д-00.00.001-Ы', 'name': 'странная деталь', 'link': 'странное место', 'attribute': 'part',
     'ass': 'ДE-10.00.000', 'quantity': 2}
    :param new_data:
    :param old_data:
    :param mode: режим, что делаем(add добавить, edit редактировать, delete удалить)
    :param base: Объект базы
    :param cursor: Объект курсора
    :param data: данные для записи
    :return: успешно / неуспешно
    формат ответа функции: True, текстовое сообщение  False, текстовое сообщение
    """
    try:
        if mode == 'edit':
            # Редактирование существующего компонента
            # Определение заменяемых атрибутов (номер/имя/ссылка)
            change_attribute = []
            for item in zip(old_data, new_data):
                a = list(item[0].values())[0]
                b = list(item[1].values())[0]
                if a != b:
                    change_attribute.append(list(item[0].keys())[0])

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
        elif mode == 'add':
            # Добавление нового
            # old_data не используется

            # Добавление компонента "сборка"

            # Проверка на наличие в базе
            search_query = 'SELECT number FROM components WHERE number = ?'
            cursor.execute(search_query, (new_data['number'], ))
            answer = cursor.fetchone()
            # Добавить раздельное для детали и сборки
            if answer:
                return False, f"{new_data['number']} Номер уже есть в базе"
            # Для детали
            elif answer is None and new_data['attribute'] == 'part':
                # Добавление в таблицу компонентов
                query = 'INSERT INTO components (number, name, link, attribute) VALUES (?, ?, ?, ?)'
                cursor.execute(query, (new_data['number'], new_data['name'], new_data['link'], new_data['attribute']))
                base.commit()

                # Добавление в таблицу связей
                query_connections = 'INSERT INTO connections (component, included, quantity) VALUES (?, ?, ?)'
                cursor.execute(query_connections, (new_data['number'], new_data['ass'], new_data['quantity']))
                base.commit()

                return True, f"{new_data['number']} успешно добавлена"

            # Для сборки
            elif answer is None and new_data['attribute'] == 'assembly':
                # Добавление в таблицу компонентов
                query = 'INSERT INTO components (number, name, link, attribute) VALUES (?, ?, ?, ?)'
                cursor.execute(query, (new_data['number'], new_data['name'], new_data['link'], new_data['attribute']))
                base.commit()

                # Добавление в таблицу связей
                query_connections = 'INSERT INTO connections (component, included, quantity) VALUES (?, ?, ?)'
                cursor.execute(query_connections, (new_data['number'], new_data['ass'], new_data['quantity']))
                base.commit()

                # Добавить одну пустую строку чтобы сборка была сборкой
                query_connections = 'INSERT INTO connections (component, included, quantity) VALUES (?, ?, ?)'
                cursor.execute(query_connections, ('', '', ''))
                base.commit()

                return True, f"{new_data['number']} успешно добавлена"
        elif mode == 'delete':
            # Для детали
            if old_data['attribute'] == 'part':

                # Удаление из текущей сборки
                query_delete_connections = 'DELETE FROM connections WHERE component = ? AND included = ?;'
                cursor.execute(query_delete_connections, (old_data['number'], old_data['ass']))
                base.commit()
                return True, f"Деталь {old_data['number']} удалена из сборки {old_data['ass']}"
            # Для сборки
            if old_data['attribute'] == 'assembly':
                # Удаление из текущей сборки
                query_delete_connections = 'DELETE FROM connections WHERE component = ? AND included = ?;'
                cursor.execute(query_delete_connections, (old_data['number'], old_data['ass']))
                base.commit()
                return True, f"Сборка {old_data['number']} удалена из сборки {old_data['ass']}"


    except sqlite3.Error as error:
        print(error)
        return False, error

# Возможно не используется
def link_of_drawing(cursor, number_drawing):
    """
    Функция полученя ссылки чертежа из базы
    :param cursor: Объект курсора
    :param number_drawing: номер чертежа
    :return: ссылка из базы
    """
    query = 'SELECT link FROM components WHERE number = ?'
    cursor.execute(query, (number_drawing,))
    data = cursor.fetchall()
    return data[0]

# Возможно не используется
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
    new = [['Т5.1-10.11.002-А', 'Лонжерон', '1', 'None', 'part'], ['Т5.1-10.11.008-А', 'Стенка', '1', 'None', 'part'],
           ['23', 'домик', '7', '', '']]
    old = [['Т5.1-10.11.002-А', 'Лонжерон', '1', 'None', 'part'], ['Т5.1-10.11.008-А', 'Стенка', '1', 'None', 'part']]
