from telebot import TeleBot, types
from config import vk_token, host, user, password, database
from classes_main import *


def main():
    bot_token = "TOKEN"

    bot = TeleBot(bot_token)

    @bot.message_handler(commands=['help', 'start'])
    def send_welcome(message):
        help_markup = help_markup_constructor()
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=help_markup)

    @bot.callback_query_handler(func=lambda call: call.data[0:6] == "Помощь")
    def help_handler(call):
        text = call.data[7:]
        if text == "Внести группу":
            search_group_markup = search_markup_constructor()
            bot.send_message(call.message.chat.id, "Как будем искать:", reply_markup=search_group_markup)
        elif text == "Показать группы":
            bot_show_groups(call, "Участников")
        elif text == "Удалить группу":
            bot_show_groups(call, "Удалить")

    @bot.callback_query_handler(func=lambda call: call.data[0:10] == "Участников")
    def number_of_users_handler(call):
        group_id = call.data[11:]
        number_of_users = NumberOfUsersInGroup(group_id, host, user, password, database).number_of_users
        group_name = NumberOfUsersInGroup(group_id, host, user, password, database).group_name
        help_markup = help_markup_constructor()
        bot.send_message(call.message.chat.id, f"Число учатников {group_name}: {number_of_users}\n"
                                               f"Выберите следующее действие:", reply_markup=help_markup)

    @bot.callback_query_handler(func=lambda call: call.data[0:7] == "Удалить")
    def number_of_users_handler(call):
        group_id = call.data[8:]
        group_name = DeleteGroupFromBase(group_id, host, user, password, database).group_name
        help_markup = help_markup_constructor()
        bot.send_message(call.message.chat.id, f"Группа {group_name} удалена.", reply_markup=help_markup)

    @bot.callback_query_handler(func=lambda call: call.data[0:10] == "Сохранение")
    def variant_group_add_handler(call):
        variant = call.data[11:]
        if variant == "по id":
            msg = bot.send_message(call.message.chat.id, "Отправьте id группы:")
            bot.register_next_step_handler(msg, group_id_handler)
        elif variant == "по имени":
            msg = bot.send_message(call.message.chat.id, "Отправьте название группы:")
            bot.register_next_step_handler(msg, group_name_handler)

    def group_id_handler(message):
        group_id = message.text
        print("Введённый id группы:", group_id)
        bot_add_group(message, group_id)

    def group_name_handler(message):
        group_name = message.text
        print("Введённое имя группы:", group_name)
        group_id = SearchGroupIdInVk(vk_token, group_name).group_id
        if group_id == None:
            search_markup = search_markup_constructor()
            bot.send_message(message.chat.id, "Группа с данным названием не найдена.\n"
                                              "Пожалуйста, проверьте правильность его написания.", reply_markup=search_markup)
        else:
            bot_add_group(message, group_id)

    def bot_add_group(message, group_id):
        id_currect = SaveGroupUsers(group_id, vk_token, host, user, password, database).id_currect
        if id_currect:
            bot.send_message(message.chat.id, "Группа успешно сохранена.")
        else:
            search_markup = search_markup_constructor()
            bot.send_message(message.chat.id, "Пожалуйста, проверьте верность введённого id.", reply_markup=search_markup)

    @bot.message_handler(content_types=['text'])
    def send_help(message):
        bot.send_message(message.chat.id, 'Для начала работы введи /start')

    def help_markup_constructor():
        help_markup = types.InlineKeyboardMarkup(row_width=1)
        save_group = types.InlineKeyboardButton("Внести новую группу", callback_data="Помощь Внести группу")
        show_groups = types.InlineKeyboardButton("Показать группы в базе", callback_data="Помощь Показать группы")
        delete_group = types.InlineKeyboardButton("Удалить группу", callback_data="Помощь Удалить группу")
        git_hub_project = types.InlineKeyboardButton("Открыть репозиторий проекта",
                                                     url="https://github.com/Ifanfomin/vk_analysis_of_users_subscription_to_groups")
        help_markup.add(save_group, show_groups, delete_group, git_hub_project)
        return help_markup

    def search_markup_constructor():
        search_group_markup = types.InlineKeyboardMarkup(row_width=1)
        search_by_name = types.InlineKeyboardButton("Ввести название", callback_data="Сохранение по имени")
        search_by_id = types.InlineKeyboardButton("Ввести id", callback_data="Сохранение по id")
        search_group_markup.add(search_by_name, search_by_id)
        return search_group_markup

    def bot_show_groups(call, action_type):
        groups = ShowDataBaseTables(host, user, password, database).groups
        show_groups_markup = types.InlineKeyboardMarkup(row_width=1)
        button = types.InlineKeyboardButton('Кнопка', callback_data="Кнопка")
        for group in groups:
            button = types.InlineKeyboardButton(f'"{group[0]}"   "{group[1]}"', callback_data=f"{action_type} {group[1]}")
            show_groups_markup.add(button)
        if action_type == "Участников":
            action_type = "показать число участников"
        elif action_type == "Удалить":
            action_type = "удалить группу"
        bot.send_message(call.message.chat.id, f"Нажмите ,чтобы {action_type}.\n"
                                               f"Группы в базе ('имя', 'id'):",
                         reply_markup=show_groups_markup)

    bot.infinity_polling()

if __name__ == "__main__":
    main()
