import flet as ft
from config import database, vk_token
from classes_main import *


class SearchingScreen(object):
    """Класс для станицы поиска подписчиков на группы"""

    def __init__(self):
        self.sql_groups_table = ShowDataBaseTables(database).groups
        self.groups_count = len(self.sql_groups_table)
        self.check_box_column_list = []
        self.selected_groups = []
        self.search_screen = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Настройки поиска",
                    content=ft.Container(ft.Text("Выберите группы"),
                                         height=900, width=1700, alignment=ft.alignment.center),
                )
            ],
            expand=1
        )
        self.check_box_column = ft.Column(
            spacing=10, controls=self.check_box_column_list, scroll=ft.ScrollMode.ALWAYS, height=900
        )
        self.search_main_screen()

    def make_search_screen(self):
        def make_table(search_dict):
            group_number = 0
            self.search_screen.tabs = [self.search_screen.tabs[0]]
            for group_name, users_list in search_dict.items():
                group_number += 1
                group_column = ft.Column(
                    spacing=10, scroll=ft.ScrollMode.ALWAYS, height=900
                )
                group_column.controls.append(ft.Text(f"Группа {group_name}", size=20))
                group_column.controls.append(ft.Text(f"Участников {len(users_list)}", size=20))

                lines = []
                for user in users_list:
                    data_row = ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(
                                color=ft.colors.BLUE,
                                spans=[ft.TextSpan(
                                    text=user[1][0:],
                                    url=f"https://vk.com/id{user[1]}"
                                )], size=20)),
                            ft.DataCell(ft.Text(user[2], size=20)),
                            ft.DataCell(ft.Text(user[3], size=20)),
                            ft.DataCell(ft.Text(user[4], size=20)),
                        ]
                    )
                    lines.append(data_row)
                ft_table = ft.DataTable(
                    width=1700,
                    columns=[
                        ft.Text("", size=20),
                        ft.DataColumn(ft.Text("ID участника", size=20)),
                        ft.DataColumn(ft.Text("Имя Фамилия", size=20)),
                        ft.DataColumn(ft.Text("Дата Рождения", size=20)),
                        ft.DataColumn(ft.Text("Место обучения", size=20))
                    ],
                    rows=lines)
                group_column.controls.append(ft_table)
                self.search_screen.tabs.insert(group_number,
                                               ft.Tab(
                                                   text=group_column.controls[0].value,
                                                   icon=ft.icons.BAR_CHART,
                                                   content=ft.Container(group_column,
                                                                        height=900, width=1700,
                                                                        alignment=ft.alignment.center),
                                               ),
                                               )
            self.main_tabs.update()

        def button_clicked(e):
            if len(self.selected_groups):
                search_list = [[search_string_column.controls[1].controls[0].value, search_string_column.controls[1].controls[1].value],
                               [search_string_column.controls[2].controls[0].value, search_string_column.controls[2].controls[1].value],
                               [search_string_column.controls[3].controls[0].value, search_string_column.controls[3].controls[1].value],
                               [search_string_column.controls[4].controls[0].value, search_string_column.controls[4].controls[1].value]]
                print(search_list)
                search_by_words_dict = SearchByWords(search_list, self.selected_groups, database).info_dict
                new_dict = {}
                for key, value in search_by_words_dict.items():
                    if value != []:
                        new_dict[key] = value
                search_by_words_dict = new_dict
                make_table(search_by_words_dict)

        search_string_column = ft.Column(
            spacing=10, controls=[
                ft.Text(""),
                ft.Row([ft.Checkbox(), ft.TextField(label="ID", text_size=20)]),
                ft.Row([ft.Checkbox(), ft.TextField(label="Имя Фамилия", text_size=20)]),
                ft.Row([ft.Checkbox(), ft.TextField(label="Дата Рождения", text_size=20)]),
                ft.Row([ft.Checkbox(), ft.TextField(label="Место обучения", text_size=20)]),
                ft.ElevatedButton(text="Поиск", on_click=button_clicked),
                ft.Text("Для удобства используйте знак % и _", size=20),
                ft.Text(" % означает, что на его месте может быть любой набор символов", size=20),
                ft.Text("Например: '% Фомин' будет брать и 'Иван Фомин' и 'Никита Фомин'", size=20),
                ft.Text(" _ означает, что на его месте может быть один любой символ", size=20),
                ft.Text("Например: в '_._.2000' день и месяц могут быть только однозначными числами", size=20),
                ft.Text("Галочка нужна чтобы убрать из поиска выбранный запрос", size=20),
                ft.Text("Например: если перед полем 'Имя Фамилия' нажать галочку и ввести '%Иван %'", size=20),
                ft.Text("То из списка уберутся все люди с именем Иван", size=20)
            ], scroll=ft.ScrollMode.ALWAYS, height=900
        )

        self.search_screen.tabs[0].content = ft.Container(search_string_column, height=900, width=1700, alignment=ft.alignment.center)


    # делает страницы с информацией
    def make_info_screens(self):
        # айди, имя с фамилией, дата рождения, место обучения
        intersec_users = SearchForIntersections(self.selected_groups, database).users
        union_users = SearchForUnions(self.selected_groups, database).users
        groups_users_count = NumbersOfUsersInGroups(
            self.selected_groups, database).groups_id_number_of_users_dict

        # создание графика пересечений
        chart_intersections = self.make_birthday_chart(intersec_users)

        # основная информация
        info = self.basic_info_screen(intersec_users, union_users, groups_users_count)

        # длинный путь до основной инфы для пересечений
        self.main_tabs.content.tabs[1].content.content.tabs[0].content.content = info

        # длинный путь до места для графика
        self.main_tabs.content.tabs[1].content.content.tabs[1].content.content = chart_intersections
        self.main_tabs.update()

        # создание графика всех участников
        chart = self.make_birthday_chart(union_users)

        # длинный путь до места для графика
        self.main_tabs.content.tabs[1].content.content.tabs[2].content.content = chart

        self.main_tabs.update()

    # возвращает страницу с основной информацией
    def basic_info_screen(self, intersec_users, union_users, groups_users_count):
        screen_row = ft.Row()
        # столбец количеством подписчиков по отдельности
        column_list = [ft.Text("Число участников:", size=20)]
        for group_users_count in groups_users_count.values():
            # print(group_users_count)
            text = f"{group_users_count['name']}: {group_users_count['count']}"
            column_list.append(ft.Text(text, size=20))
        column = ft.Column(
            spacing=10, controls=column_list, scroll=ft.ScrollMode.ALWAYS, wrap=False
        )
        screen_row.controls.append(column)

        # поиск по айди, имени, дате рождения и месту обучения


        # основная информация
        intersec_birthday = 0
        for user in intersec_users:
            if user[2] != "empty":
                intersec_birthday += 1
        union_birthday = 0
        for user in union_users:
            if user[2] != "empty":
                union_birthday += 1

        column_list = [
            ft.Text(f"Всего подпискиков: {len(union_users)}", size=20),
            ft.Text(f"Всего подписчиков с датами рождения: {union_birthday}", size=20),
            ft.Text(f"Подписанных на все группы: {len(intersec_users)}", size=20),
            ft.Text(f"Подписанных на все группы и с датами рождения: {intersec_birthday}", size=20),
        ]

        column = ft.Column(
            spacing=10, controls=column_list, scroll=ft.ScrollMode.ALWAYS, wrap=False
        )
        screen_row.controls.append(column)
        return ft.Container(screen_row)

    # возвращает таблицу зависимости количества участников от их даты рождения
    def make_birthday_chart(self, users):  # делает график отношения года рождения к количеству родившихся
        bar_columns = []
        bar_labels = []
        years_dict = {}
        for user in users:
            if user[2] != "empty":
                if user[2][-4:] in years_dict.keys():
                    years_dict[user[2][-4:]] += 1
                else:
                    years_dict[user[2][-4:]] = 1

        sorted_years_dict = {}
        years_list = sorted(years_dict.keys())
        for year in years_list:
            for key, value in years_dict.items():
                if year == key:
                    sorted_years_dict[key] = value

        years_dict = sorted_years_dict
        print("Года: ", years_dict)

        # делаем удобный для вывода список лет с пропуском через "-"
        number_of_bars = 35
        if len(years_dict) > number_of_bars:
            offset = 0 # шаг пропуска лет
            index = 0 # номер пропущенного года
            # округление в большую сторону
            if len(years_dict) % number_of_bars != 0:
                offset = int(len(years_dict) / number_of_bars) + 1
            else:
                offset = len(years_dict) // number_of_bars
                
            skipped_years = ""
            count_of_users = 0
            smaller_years_dict = {}
            for year, number in years_dict.items():
                index += 1
                if index == 1:
                    skipped_years += year[2:] + "-"
                    count_of_users = number
                else:
                    count_of_users += number
                if index == offset:
                    skipped_years += year[2:]
                    if skipped_years not in smaller_years_dict:
                        smaller_years_dict[skipped_years] = count_of_users
                    else:
                        smaller_years_dict["20" + skipped_years] = count_of_users
                    index = 0
                    skipped_years = ""
                    count_of_users = 0

            years_dict = smaller_years_dict
            # print(years_dict)

        for index, year_and_number in enumerate(years_dict.items()):
            bar_columns.append(
                ft.BarChartGroup(
                    x=index,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=year_and_number[1],
                            width=40,
                            color=ft.colors.AMBER,
                            tooltip=year_and_number[0],
                            border_radius=0,
                        ),
                    ],
                ),
            )
            bar_labels.append(
                ft.ChartAxisLabel(
                    value=index, label=ft.Container(ft.Text(year_and_number[0]), padding=10)
                ),
            )

        if not years_dict.values():
            mx_y = 0
        else:
            mx_y = int(max(years_dict.values()) * 1.1)

        chart = ft.BarChart(
            bar_groups=bar_columns,
            border=ft.border.all(1, ft.colors.GREY_400),
            left_axis=ft.ChartAxis(
                labels_size=40, title=ft.Text("Количество людей"), title_size=40
            ),
            bottom_axis=ft.ChartAxis(
                labels=bar_labels,
                labels_size=40,
                title=ft.Text("Годы рождения"),
                title_size=40
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.GREY_300, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.5, ft.colors.GREY_300),
            max_y=mx_y,
            interactive=True,
            expand=True,
        )
        return chart

    # собирает список из выбранных групп
    def make_selected_groups_list(self):  # делает список выбранных групп
        self.selected_groups = []
        for line_i in range(len(self.check_box_column_list)):
            group_id = ""
            if 0 < line_i < self.groups_count + 1:  # перебирает выбранные строки и достаёт из названия айди группы
                if self.check_box_column_list[line_i].value == True:
                    group_id = self.check_box_column_list[line_i].label.split('"')[3]
            if group_id != "":
                self.selected_groups.append(group_id)
        if len(self.selected_groups) == 0:
            print("Пожалуйста, выберите группы")

    # обновляет список имеющихся групп при сохранении или удалении группы (надо проверить на работоспособность)
    def update_groups_list(self):
        self.sql_groups_table = ShowDataBaseTables(database).groups
        self.groups_count = len(self.sql_groups_table)
        self.make_groups_check_box_column()
        self.main_tabs.content.tabs[0].content.content = self.check_box_column
        self.main_tabs.update()

    # вызывает составление списка выбранных групп, вызывает сборщик страниц с информацией
    def start_to_make_info_screen(self, e):
        self.make_selected_groups_list()
        if len(self.selected_groups):
            self.make_info_screens()

    # составляет страницу для выбора групп
    def make_groups_check_box_column(self):
        self.check_box_column_list = []
        self.check_box_column_list.append(ft.Text("Выбор группы для поиска пересечений"))
        for line in self.sql_groups_table:
            self.check_box_column_list.append(ft.Checkbox(label=f'"{line[0]}" "{line[1]}"', value=False))

        submit_button = ft.ElevatedButton(text="Поиск", on_click=self.start_to_make_info_screen)
        self.check_box_column_list.append(submit_button)
        self.check_box_column = ft.Column(
            spacing=10, controls=self.check_box_column_list, scroll=ft.ScrollMode.ALWAYS, wrap=True
        )

    # вызывает первичное составление всех страниц
    def search_main_screen(self):
        self.make_groups_check_box_column()
        self.make_search_screen()
        information_tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Основная информация",
                    # tab_content=ft.Icon(ft.icons.BAR_CHART),
                    content=ft.Container(ft.Text("Выберите группы"),
                                         height=900, width=1700, alignment=ft.alignment.center),
                ),
                ft.Tab(
                    text="График пересечений по датам рождения",
                    icon=ft.icons.BAR_CHART,
                    content=ft.Container(ft.Text("Выберите группы"),
                                         height=900, width=1700, alignment=ft.alignment.center),
                ),
                ft.Tab(
                    text="График всех участников по датам рождения",
                    icon=ft.icons.BAR_CHART,
                    content=ft.Container(ft.Text("Выберите группы"),
                                         height=900, width=1700, alignment=ft.alignment.center),
                ),
            ],
            expand=1
        )

        self.main_tabs = ft.Container(ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(
                        text="Выбор групп",
                        content=ft.Container(self.check_box_column,
                                             height=900, width=1700, alignment=ft.alignment.center),
                    ),
                    ft.Tab(
                        text="Информация",
                        # icon=ft.icons.POLYMER,
                        content=ft.Container(information_tabs,
                                             height=900, width=1700),
                    ),
                    ft.Tab(
                        text="Поиск по выбранным группам",
                        # icon=ft.icons.POLYMER,
                        content=ft.Container(self.search_screen,
                                             height=900, width=1700, alignment=ft.alignment.center),
                    ),
                ], expand=1,
            ),
            height=1000,
            width=1700
        )
        # print(self.main_tabs.content.tabs[1].content.content.tabs[1].content.content)


def groups_ft_table():
    sql_column = ShowDataBaseTables(database).groups
    lines = []
    for line in sql_column:
        data_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(line[0], size=20)),
                ft.DataCell(ft.Text(
                    color=ft.colors.BLUE,
                    spans=[ft.TextSpan(
                        text=line[1][0:],
                        url=f"https://vk.com/{line[1]}"
                    )], size=20))
            ]
        )
        lines.append(data_row)

    ft_table = ft.DataTable(
        width=1700,
        columns=[
            ft.DataColumn(ft.Text("Имя группы", size=20)),
            ft.DataColumn(ft.Text("ID группы", size=20))
        ],
        rows=lines)
    column = ft.Column(controls=[ft_table], scroll=ft.ScrollMode.ALWAYS, height=900)
    return column


def search_intersections_screen():
    def make_ft_data_table(users, searching_groups_count):
        intersections_count = 0
        lines = []
        for user in users:
            intersections_count += 1
            data_row = ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(color=ft.colors.BLUE,
                                spans=[ft.TextSpan(
                                    text=user[0],
                                    url=f"https://vk.com/id{int(user[0])}"
                                )]),
                    ),
                    ft.DataCell(ft.Text(user[1])),
                    ft.DataCell(ft.Text(user[2])),
                    ft.DataCell(ft.Text(user[3]))
                ]
            )
            lines.append(data_row)
        ft_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Имя Фамилия")),
                ft.DataColumn(ft.Text("Дата рождения")),
                ft.DataColumn(ft.Text("Место обучения"))
            ],
            rows=lines
        )

        list_information = [ft.Text(f"Количество групп: {groups_count}", size=20),
                            ft.Text(f"Количество выбранных групп: {searching_groups_count}", size=20),
                            ft.Text(f"Koличество пересечений: {intersections_count}", size=20),
                            ft_table
                            ]
        information_column = ft.Column(spacing=10, controls=list_information,
                                       scroll=ft.ScrollMode.ALWAYS,
                                       height=900)
        page_row.controls[1] = information_column

    def start_search_intersections(e):
        print("Поиск начат")
        searching_groups = []
        for line_i in range(len(column_list)):
            group_id = ""
            if 0 < line_i < groups_count + 1:
                if column_list[line_i].value == True:
                    group_id = column_list[line_i].label.split('"')[3]
            if group_id != "":
                searching_groups.append(group_id)

        print(searching_groups)
        searching_groups_count = len(searching_groups)

        if searching_groups:
            users = SearchForIntersections(searching_groups, database).users
            print(users)
            make_ft_data_table(users, searching_groups_count)
            page_row.update()

    print("экран выбора групп для поиска пересечений")
    sql_column = ShowDataBaseTables(database).groups
    column_list = [ft.Text("Выбор группы для поиска пересечений")]
    groups_count = 0
    for line in sql_column:
        column_list.append(ft.Checkbox(label=f'"{line[0]}" "{line[1]}"', value=False))
        groups_count += 1

    users_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Имя Фамилия")),
            ft.DataColumn(ft.Text("Дата рождения")),
            ft.DataColumn(ft.Text("Место обучения"))
        ]
    )
    searching_group_count = 0
    intersections_count = 0
    list_information = [ft.Text(f"Количество групп: {groups_count}", size=20),
                        ft.Text(f"Количество выбранных групп: {searching_group_count}", size=20),
                        ft.Text(f"Koличество пересечений: {intersections_count}", size=20),
                        users_table
                        ]
    information_column = ft.Column(spacing=10, controls=list_information, scroll=ft.ScrollMode.ALWAYS,
                                   height=900)

    submit_button = ft.ElevatedButton(text="Поиск", on_click=start_search_intersections)
    column_list.append(submit_button)
    check_box_column = ft.Column(spacing=10, controls=column_list, scroll=ft.ScrollMode.ALWAYS, height=900)
    page_row = ft.Row([check_box_column, information_column])
    return page_row


def save_group_users(searching_screen):
    def start_save(e):
        print(group_id)
        try:
            page_column.controls[2] = ft.Text(f"Сохраняем...", size=20)
            page_column.update()
            group_name = SaveGroupUsers(group_id.value, vk_token, database).group_name
            if group_name:
                page_column.controls[2] = ft.Text(f"Группа {group_name} сохранена", size=20)
            else:
                page_column.controls[2] = ft.Text(f"Группа {group_id.value}, не найдена, либо уже существует", size=20)
            page_column.update()
            searching_screen.update_groups_list()
        except Error as e:
            page_column.controls[2] = ft.Text(f"Проверьте ID группы", size=20)
            page_column.update()

    group_id = ft.TextField(label="Введите ID группы", hint_text="ID группы")
    submit_to_save_button = ft.ElevatedButton(text="Сохранить", on_click=start_save)
    page_column = ft.Column(spacing=10,
                            controls=[group_id, submit_to_save_button, ft.Text("")],
                            scroll=ft.ScrollMode.ALWAYS,
                            height=900)
    return page_column


def ft_delete_group(searching_screen):
    global groups_count
    groups_count = 0

    def delete_from_screen(group_id):
        for check_box_id in range(2, len(column_list) - 1):
            check_box_group_id = column_list[check_box_id].label.split('"')[3]
            if check_box_group_id == group_id:
                print(group_id)
                column_list.pop(check_box_id)
                print(len(column_list))
                break

    def delete_groups(e):
        global groups_count
        groups_to_delete = []
        for line_i in range(len(column_list)):
            group_id = ""
            if 0 < line_i < groups_count + 1:
                if column_list[line_i].value == True:
                    group_id = column_list[line_i].label.split('"')[3]
            if group_id != "":
                groups_to_delete.append(group_id)
        print(groups_to_delete)
        if groups_to_delete:
            for group_id in groups_to_delete:
                DeleteGroupFromBase(group_id, database)
                delete_from_screen(group_id)
                groups_count -= 1
            check_box_column.update()
            print(groups_to_delete, "удален")
        searching_screen.update_groups_list()

    print("экран выбора групп для удаления")
    sql_column = ShowDataBaseTables(database).groups
    column_list = [ft.Text("Выбор группы для удаления")]
    for line in sql_column:
        column_list.append(ft.Checkbox(label=f'"{line[0]}" "{line[1]}"', value=False))
        groups_count += 1
    submit_button = ft.ElevatedButton(text="Удалить", on_click=delete_groups)
    column_list.append(submit_button)
    check_box_column = ft.Column(spacing=10,
                                 controls=column_list,
                                 scroll=ft.ScrollMode.ALWAYS,
                                 height=900)
    return check_box_column
