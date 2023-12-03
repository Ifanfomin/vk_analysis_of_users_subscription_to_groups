from mysql.connector import connect, Error
import vk_api
import time


class SaveGroupUsers(object):
    """Данный класс сохраняет участников выбранной группы ВК в таблицу MySQL"""

    def __init__(self, group_id, token, host, user, password, database):  # Принимаем айди группы и данные mysql сервера
        self.__token = token
        self.session = vk_api.VkApi(token=self.__token)
        self.group_id = group_id
        self.db_conn_info = {"host": host, "user": user, "password": password, "database": database}
        self.id_currect = True
        self.group_name = False
        self.check_id_currect()

    def check_id_currect(self):  # Проверяем на существование введёный айди грппы
        try:
            self.session.method("groups.getById", {"group_id": self.group_id})
            self.connecting_to_data_base()
            print("Все участники группы сохранены")
        except Error as e:
            self.id_currect = False
            if e:
                print(e)
            else:
                print("Введён неверный id группы")

    def connecting_to_data_base(self):  # Подключаемся к mysql
        with connect(
                host=self.db_conn_info["host"],
                user=self.db_conn_info["user"],
                password=self.db_conn_info["password"],
                database=self.db_conn_info["database"]
        ) as connection:
            self.check_vk_ids_table(connection)

    def check_vk_ids_table(self, connection):  # Проверяем, есть ли уже таблица для имён групп
        query = """
                SHOW TABLES
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            self.tables = cursor.fetchall()

        vk_ids_table = False
        for table in self.tables:
            if table[0] == "vk_ids":
                vk_ids_table = True

        if vk_ids_table == True:
            self.check_group_table(connection)
        else:
            self.make_vk_ids_table(connection)

    def make_vk_ids_table(self, connection):  # Таблицы для имён нет, создаём новую
        query = """
                CREATE TABLE vk_ids(
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id VARCHAR(100),
                group_name VARCHAR(100)
                )
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
        self.check_group_table(connection)

    def check_group_table(self, connection):  # Проверяем, есть ли у нас уже эта группа и полная ли она
        table_in_base = False
        for table in self.tables:
            if table[0] == self.group_id:
                table_in_base = True
        if table_in_base:
            self.append_table(connection)
        else:
            self.create_table_for_group(connection)

    def create_table_for_group(self, connection):  # Данной группы в базе нет, значить создаём для неё новую таблицу
        create_table_query = """
                CREATE TABLE """ + self.group_id + """(
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(100),
                user_name VARCHAR(100),
                birthday  VARCHAR(100),
                university VARCHAR(100)
                )
                """
        self.group_name = self.session.method("groups.getById", {"group_id": self.group_id})[0]["name"]
        append_group_to_ids_query = f"""INSERT vk_ids(group_id, group_name) 
                                        VALUES ('{self.group_id}', '{self.group_name}')"""
        with connection.cursor() as cursor:
            cursor.execute(append_group_to_ids_query)

        with connection.cursor() as cursor:
            cursor.execute(create_table_query)

        self.get_group_members(0, connection)

    def append_table(self, connection):  # Группа уже есть, но неполная, значить начнём заполнение с последней точки
        query = """
                SELECT COUNT(*) FROM """ + self.group_id + """
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            count = cursor.fetchone()[0]
        self.get_group_members(count, connection)

    def get_group_members(self, start_from, connection):  # Получаем по 1000 участников из группы
        members_count = self.session.method("groups.getMembers", {"group_id": self.group_id})["count"]
        print(members_count)
        print("Приступаем к сохранению участников группы")
        for offset in range(start_from, members_count, 1000):
            self.members = self.session.method("groups.getMembers",
                                               {"group_id": self.group_id,
                                                "count": 1000,
                                                "offset": offset,
                                                "fields": "bdate, universities"}
                                               )["items"]
            self.save_members_to_db(connection)
            print("Участников сохранено: " + str(offset + len(self.members)))

    def save_members_to_db(self, connection):  # Сохраняем полученных участников в таблицу mysql
        users_list = []
        for user in self.members:
            user_list = []
            user_list.append(user["id"])
            user_first_last_name = user["first_name"] + " " + user["last_name"]
            if self.symbol_searching(user_first_last_name) and len(user_first_last_name) < 100:  # Смотрим, чтобы не попались лишние символы
                user_list.append(user_first_last_name)
            else:
                user_list.append("name not defined")
            if "bdate" in user:
                if len(user["bdate"]) > 7:
                    user_list.append(user["bdate"])
                else:
                    user_list.append("empty")
            else:
                user_list.append("empty")
            if "universities" in user:
                if len(user["universities"]) > 0:
                    if self.symbol_searching(user["universities"][0]["name"]) and len(user["universities"][0]["name"]) < 100:  # # Смотрим, чтобы не попались лишние символы
                        user_list.append(user["universities"][0]["name"])
                    else:
                        user_list.append("empty")
                else:
                    user_list.append("empty")
            else:
                user_list.append("empty")
            users_list.append(user_list)

        query = """
                INSERT INTO """ + self.group_id + """
                (user_id, user_name, birthday, university)
                VALUES (%s, %s, %s, %s)
                """
        with connection.cursor() as cursor:
            cursor.executemany(query, users_list)
            connection.commit()
        time.sleep(0.4)  # Ждём, чтобы ВК нас не забанил (но при больших группах всё же банит)

    def symbol_searching(self, string): # Проверка на отсутствие лишних букв
        return all([i in r"abcdefghigklmnopqrstuvwxyzABCDEFGHIGKLMNOPQRSTUVWXYZабвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗ" \
                  "ИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ01234567890!@#$%^&*()-=_+~`|/[]{},.<>;:' " for i in string])


class ShowDataBaseTables(object):
    """Данный класс при вызове очищает базу данных"""

    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.show_data_base_tables()

    def show_data_base_tables(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                query_show_tables = "SHOW TABLES"
                query_vk_ids = "SELECT group_name, group_id FROM vk_ids"
                with connection.cursor() as cursor:
                    cursor.execute(query_show_tables)
                    if cursor.fetchall() != []:
                        cursor.execute(query_vk_ids)
                        self.groups = cursor.fetchall()
                        print("Группы в базе ('имя', 'id'):")
                        for group in self.groups:
                            print(f"'{group[0]}'", '', f"'{group[1]}'")
                        query_show_columns = f"SHOW COLUMNS FROM {self.groups[0][1]}"
                        cursor.execute(query_show_columns)
                        columns = cursor.fetchall()
                        print()
                        print("Столбцы таблиц:")
                        print(end="| ")
                        for column in columns:
                            if columns.index(column) == len(columns) - 1:
                                print(column[0] + " |")
                            else:
                                print(column[0], end=' | ')
                    else:
                        self.groups = []
                        print("База пуста")

        except Error as e:
            print(e)


class ShowDataBaseTable(object):
    """Данный класс показывает все строки выбранной таблицы"""

    def __init__(self, group_id, host, user, password, database):
        self.table_name = group_id
        self.table = None
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.show_data_base_table()

    def show_data_base_table(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                query = f"SELECT * FROM {self.table_name}"
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    self.table = cursor.fetchall()
                    for string in self.table:
                        print(string)

        except Error as e:
            print(e)


class NumbersOfUsersInGroups(object):
    """Данный класс при вызове показывает количество подписчиков выбранной группы"""

    def __init__(self, groups_ids, host, user, password, database):
        self.groups_ids = groups_ids
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.groups_id_number_of_users_dict = {}
        self.numbers_of_users_in_groups()

    def numbers_of_users_in_groups(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                for group_id in self.groups_ids:
                    count_query = f"SELECT count(id) FROM {group_id}"
                    group_name_query = f"SELECT group_name FROM vk_ids WHERE group_id = '{group_id}'"
                    with connection.cursor() as cursor:
                        cursor.execute(count_query)
                        number_of_users = cursor.fetchone()[0]
                        cursor.execute(group_name_query)
                        group_name = cursor.fetchone()[0]
                    self.groups_id_number_of_users_dict[group_id] = {"name": group_name, "count": number_of_users}
                # return self.groups_id_number_of_users_dict
                # print(f"Количество подписчиков {self.group_name}: {self.number_of_users}")
        except Error as e:
            print(e)


class DeleteGroupFromBase(object):
    """Данный класс при вызове очищает базу данных"""

    def __init__(self, group_id, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.group_id = group_id
        self.group_name = None
        self.delete_group_from_base()

    def delete_group_from_base(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                group_name_query = f"SELECT group_name FROM vk_ids WHERE group_id = '{self.group_id}'"
                with connection.cursor() as cursor:
                    cursor.execute(group_name_query)
                    self.group_name = cursor.fetchall()[0][0]
                delete_table_query = f"DROP TABLE {self.group_id}"
                delete_from_vk_ids = f"DELETE FROM vk_ids WHERE group_id = '{self.group_id}'"
                with connection.cursor() as cursor:
                    cursor.execute(delete_table_query)
                    cursor.execute(delete_from_vk_ids)
                    connection.commit()
                connection.commit()
                print(f"Группа {self.group_name} удалена.")
        except Error as e:
            print(e)


class ClearDataBase(object):
    """Данный класс при вызове очищает базу данных"""

    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.clear_data_base()

    def clear_data_base(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                query = "SHOW TABLES"
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    tables = cursor.fetchall()
                for table in tables:
                    query = f"DROP TABLE {table[0]}"
                    with connection.cursor() as cursor:
                        cursor.execute(query)
                print("Таблицы успешно удалены")
        except Error as e:
            print(e)


class SearchGroupIdInVk(object):
    """Данный класс будет производить поиск группы по её имени"""

    def __init__(self, searching_group_name, token):
        self.__token = token
        self.session = vk_api.VkApi(token=self.__token)
        self.searching_group_name = searching_group_name
        self.group_id = None
        self.another_groups = []
        self.search_id()

    def search_id(self):
        groups = self.session.method("groups.search",
                                     {"q":self.searching_group_name, "count": 1000})["items"]
        for group in groups:
            if self.searching_group_name == group["name"]:
                self.group_id = group["screen_name"]
        for i in range(10):
            self.another_groups.append(groups[i]["name"])
        if self.group_id != None:
            print(f"ID {self.searching_group_name}: {self.group_id}")
            print("Другие варианты:")
            [print(group) for group in self.another_groups]
        else:
            print("Данная группа не найдена. Возможно вы имели ввиду:")
            [print(group) for group in self.another_groups]


class MyQueryExecute(object):
    """Данный класс отправляет введённый пользователем запрос"""

    def __init__(self, query, host, user, password, database):
        self.query = query
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.query_execute()

    def query_execute(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(self.query)
                    all_data = cursor.fetchall()
                    for data in all_data:
                        print(data)
                    # print(all_data)
        except Error as e:
            print(e)

class SearchForIntersections(object):
    """Данный класс производит поиск пересечений по нескольким таблицам"""

    def __init__(self, groups_list, host, user, password, database):
        self.groups_list = groups_list
        self.columns = []
        self.users = []
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connect_to_db()

    def connect_to_db(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                self.select_columns(connection)
        except Error as e:
            print(e)

    def select_columns(self, connection):
        select_columns_query = f"SHOW COLUMNS FROM {self.groups_list[0]}"
        with connection.cursor() as cursor:
            cursor.execute(select_columns_query)
            self.columns = cursor.fetchall()
        self.search_for_intersections(connection)

    def search_for_intersections(self, connection):
        search_query = ""
        for group_index in range(len(self.groups_list)):
            search_query += "SELECT "

            for column_index in range(len(self.columns)):
                if column_index != len(self.columns) - 1 and self.columns[column_index][0] != "id":
                    search_query += self.columns[column_index][0] + ", "

                elif self.columns[column_index][0] != "id":
                    search_query += self.columns[column_index][0] + " "

            search_query += f"FROM {self.groups_list[group_index]} "

            if group_index != len(self.groups_list) - 1:
                search_query += "INTERSECT "

        with connection.cursor() as cursor:
            cursor.execute(search_query)
            self.users = cursor.fetchall()
            print(f"Пересечений: {len(self.users)}")
            # for user in self.users:
            #     print(user)


class SearchForUnions(object):
    """Данный класс производит поиск пересечений по нескольким таблицам"""

    def __init__(self, groups_list, host, user, password, database):
        self.groups_list = groups_list
        self.columns = []
        self.users = []
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connect_to_db()

    def connect_to_db(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                self.select_columns(connection)
        except Error as e:
            print(e)

    def select_columns(self, connection):
        select_columns_query = f"SHOW COLUMNS FROM {self.groups_list[0]}"
        with connection.cursor() as cursor:
            cursor.execute(select_columns_query)
            self.columns = cursor.fetchall()
        self.search_for_unions(connection)

    def search_for_unions(self, connection):
        search_query = ""
        for group_index in range(len(self.groups_list)):
            search_query += "SELECT "

            for column_index in range(len(self.columns)):
                if column_index != len(self.columns) - 1 and self.columns[column_index][0] != "id":
                    search_query += self.columns[column_index][0] + ", "

                elif self.columns[column_index][0] != "id":
                    search_query += self.columns[column_index][0] + " "

            search_query += f"FROM {self.groups_list[group_index]} "

            if group_index != len(self.groups_list) - 1:
                search_query += "UNION "

        with connection.cursor() as cursor:
            cursor.execute(search_query)
            self.users = cursor.fetchall()
            print(f"Всего: {len(self.users)}")

            # for user in self.users:
            #     print(user)


class SearchByWords(object):
    def __init__(self, search_list, groups_list, host, user, password, database):
        self.search_list = search_list  # [['True' если нужен NOT LIKE, 'айди пользователя'], ['True', 'имя'], ['True', 'день рождения'], ['True', 'универ']]
        self.settings = ['user_id', 'user_name', 'birthday', 'university']
        self.groups_list = groups_list
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.info_dict = {}  # {"имя группы 1": [пошла инфа], "имя группы 2": [пошла инфа]}
        self.connect_to_db()

    def connect_to_db(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                self.start_search(connection)
        except Error as e:
            print(e)

    def start_search(self, connection):
        for index, search_string in enumerate(self.search_list):
            if search_string[0] == False and search_string[1] == "":
                self.search_list[index][1] = "%"
            elif search_string[0] == True and search_string[1] == "":
                if index == 2:
                    self.search_list[index][1] = "empty"
                elif index == 3:
                    self.search_list[index][1] = "empty"

        for group_id in self.groups_list:
            query = "SELECT * FROM "
            query += group_id + " "
            query += "WHERE "

            for index, setting in enumerate(self.settings):
                if self.search_list[index][0] == True:
                    query += f"{setting} NOT LIKE '{self.search_list[index][1]}' AND "
                else:
                    query += f"{setting} LIKE '{self.search_list[index][1]}' AND "

            query = query[:-4]
            print(query)

            with connection.cursor() as cursor:
                cursor.execute(query)
                users = cursor.fetchall()
                # for user in users:
                #     print(user)

                cursor.execute(f"SELECT group_name FROM vk_ids WHERE group_id = '{group_id}'")
                group_name = cursor.fetchone()[0]

            self.info_dict[group_name] = users
