import sqlite3
import json
import controller


#BASE = sqlite3.connect('D:/G5/Drawings/Base data/Т5.1.db')
#CURSOR = BASE.cursor()

def base_connect():
    base = sqlite3.connect('D:/G5/Drawings/Base data/Т5.1.db')
    cursor = base.cursor()
    query = 'SELECT * FROM components'
    cursor.execute(query)
    data = cursor.fetchall()
    out = []
    for line in data:
        out.append({'number' : line[0], 'name' : line[1],
                    'level' : line[2], 'attribute' : line[4]})
        #print(line)
    cursor.close()
    base.close()
    return out

# Функция составления модели по данным с БД
# принимает массив данных и ищет входящие по заданному уровню
def generate_model(base, cursor, mass):
    out_mass = []
    # Поиск элементов с заданным уровнем
    for element in mass:
        level_item = element['level']
        attribute_item = element['attribute']
        if attribute_item == 'assembly':
            com = element['number']
    # Запрос в базу на связанные с ним элементы
            search_query = 'SELECT component, quantity FROM connections WHERE included = ?;'
            cursor.execute(search_query, (com,))
            temp_mass = cursor.fetchall()
            out_mass.append({'number' : element['number'], 'level' : level_item, 'included' : temp_mass})
        else:
            out_mass.append(element)
    cursor.close()
    base.close()

    return out_mass

if __name__ == '__main__':

    base = sqlite3.connect('D:/PY/Drawings/Base data/Т5.1.db')
    cursor = base.cursor()
    old_data = [{'number': 'У-10.00.000-Ф'}, {'name': 'странная деталь'}, {'link': 'Папка 3/4'}]
    new_data = [{'number': 'У-10.00.000-Ф'}, {'name': 'не менее странная деталь'}, {'link': 'Папка 3/4'}]
    controller.write_to_base(base, cursor, old_data, new_data)


