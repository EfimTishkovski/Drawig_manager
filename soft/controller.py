import sqlite3
import json
import copy


# Функция получения данных из базы
def get_data_from_base(cursor):
    # Данные из БД по компонентам
    query = 'SELECT * FROM components'
    cursor.execute(query)
    data = cursor.fetchall()
    out_components = []
    for line in data:
        out_components.append({'number': line[0], 'name': line[1],
                               'level': line[2], 'attribute': line[4]})

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
                temp.append(component[0], )
        out_connections.append({'number': line, 'included': temp.copy()})
        temp.clear()
    return out_components, out_connections


# Обновление/создание модели
def model(cursor_in_model, mode='generate'):
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

# Функция загрузки настроек
def settings_load():
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

# Функция обновления настроек
def update_settings(name_setting, new_state):
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



if __name__ == "__main__":
    print(settings_load())
