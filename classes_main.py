from mysql.connector import connect, Error
import vk_api
import time


class SaveGroupUsers(object):
    """Здесь я реалезую работу с vk api через свой класс"""

    def __init__(self, group_id, token, host, user, password, database):
        self.__token = token
        self.session = vk_api.VkApi(token=self.__token)
        self.group_id = group_id
        self.db_conn_info = {"host": host, "user": user, "password": password, "database": database}
        self.id_currect = True
        self.check_id_currect()

    def check_id_currect(self):
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

    def connecting_to_data_base(self):
        with connect(
                host=self.db_conn_info["host"],
                user=self.db_conn_info["user"],
                password=self.db_conn_info["password"],
                database=self.db_conn_info["database"]
        ) as connection:
            self.check_vk_ids_table(connection)

    def check_vk_ids_table(self, connection):
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

    def make_vk_ids_table(self, connection):
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

    def check_group_table(self, connection):
        table_in_base = False
        for table in self.tables:
            if table[0] == self.group_id:
                table_in_base = True
        if table_in_base:
            self.append_table(connection)
        else:
            self.create_table_for_group(connection)

    def create_table_for_group(self, connection):
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

    def append_table(self, connection):
        query = """
                SELECT COUNT(*) FROM """ + self.group_id + """
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            count = cursor.fetchone()[0]
        self.get_group_members(count, connection)

    def get_group_members(self, start_from, connection):
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
            print("Участников сохранено: " + str(offset))

    def save_members_to_db(self, connection):
        users_list = []
        for user in self.members:
            user_list = []
            user_list.append(user["id"])
            user_first_last_name = user["first_name"] + user["last_name"]
            if self.symbol_searching(user_first_last_name) and len(user_first_last_name) < 100:
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
                    if self.symbol_searching(user["universities"][0]["name"]) and len(user["universities"][0]["name"]) < 100:
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
        time.sleep(0.3)

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
                query = "SELECT group_name, group_id FROM vk_ids"
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    self.groups = cursor.fetchall()
                    print("Группы в базе ('имя', 'id'):")
                    for group in self.groups:
                        print(f"'{group[0]}'", '', f"'{group[1]}'")
        except Error as e:
            print(e)


class NumberOfUsersInGroup(object):
    """Данный класс при вызове показывает количество подписчиков выбранной группы"""

    def __init__(self, group_id, host, user, password, database):
        self.group_id = group_id
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.number_of_users_in_group()

    def number_of_users_in_group(self):
        try:
            with connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                count_query = f"SELECT count(id) FROM {self.group_id}"
                group_name_query = f"SELECT group_name FROM vk_ids WHERE group_id = '{self.group_id}'"
                with connection.cursor() as cursor:
                    cursor.execute(count_query)
                    self.number_of_users = cursor.fetchone()[0]
                    cursor.execute(group_name_query)
                    self.group_name = cursor.fetchone()[0]
                    print(f"Количество подписчиков {self.group_name}: {self.number_of_users}")
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
                    self.group_name = cursor.fetchall()[0]
                delete_table_query = f"DROP TABLE {self.group_id}"
                delete_from_vk_ids = f"DELETE FROM vk_ids WHERE group_id = '{self.group_id}'"
                with connection.cursor() as cursor:
                    cursor.execute(delete_table_query)
                    cursor.execute(delete_from_vk_ids)
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
                print("Таблицы успешно удалены.")
        except Error as e:
            print(e)

class SearchGroupIdInVk(object):
    """Данный класс будет производить поиск группы по её имени"""

    def __init__(self, token, searching_group_name):
        self.__token = token
        self.session = vk_api.VkApi(token=self.token)
        self.searching_group_name = searching_group_name
        self.group_id = None
        self.search_id()

    def search_id(self):
        offset = 0
        while self.group_id == None or offset < 10000:
            groups = self.session.method("groups.search", {"q":self.searching_group_name, "offset": offset, "count": 1000})["items"]
            for group in groups:
                if self.searching_group_name == group["name"]:
                    self.group_id = group["screen_name"]
            offset += 1000
            print(offset)
            time.sleep(0.3)
        if self.group_id != None:
            print("Группа найдена")
        else:
            print("Проверьте верность введёного названия")


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
                    print(all_data)
        except Error as e:
            print(e)
