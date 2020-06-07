"""
    Файл основной логики бота 
"""
import json

import telebot
from telebot import apihelper
from telebot import types

import ClientController
import CommonController
from db import Session
from models.DataBaseClasses import *

cfg = json.load(open("config.json"))
token = cfg['bot']['token']
bot = telebot.TeleBot(token)

if 'proxy' in cfg.keys():
    apihelper.proxy = cfg['proxy']

apihelper.ENABLE_MIDDLEWARE = True


@bot.middleware_handler(update_types=['message'])
def session_middleware(bot_instance, message):
    """
        Установка сессии БД
    """
    print("session UPDATE")
    message.session = Session()


@bot.middleware_handler(update_types=['message'])
def auth_middleware(bot_instance, message):
    """
        Авторизация пользователя
    """
    chat_id = message.chat.id
    message.user = User.find_by_conversation(message.session, chat_id)
    print(f"Conversation UPDATE: {chat_id}, {message.user.name}")


@bot.middleware_handler(update_types=['message'])
def set_empty_text_middleware(bot_instance, message):
    """
        Фиксим отсутствие поля text
    """
    if not message.text:
        message.text = ''


CommonController.init(bot)
ClientController.init(bot)


# вход в систему менеджера/админа
@bot.message_handler(commands=["superuser_init"])
def create_superuser(message):
    """
        Добавление роли пользователю по токену
    """
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start.")
    elif len(args) != 2:
        bot.send_message(
            message.chat.id, "Неправильное использование команды superuser.\nШаблон:/superuser_init TOKEN")
    elif not Token.find(message.session, args[1]):
        bot.send_message(message.chat.id, "Данный токен не существует. Попробуйте еще раз.")
    else:
        token_new = args[1]
        my_token = Token.find(message.session, token_new)
        if my_token:
            user.appoint(message.session, my_token.role_id)
            my_token.activate(message.session)
            bot.send_message(
                message.chat.id, f"Токен успешно активирован, ваша роль {RoleNames(my_token.role_id).name}.")
        else:
            bot.send_message(
                message.chat.id, "Не удалось авторизоваться в системе. Попробуйте еще раз.")

    #     if RoleNames(user.role_id).name == "CLIENT":
    #         if all_tickets:
    #             for ticket in all_tickets:
    #                 ans += 'Ticket id: ' + str(ticket.id) + '\n'
    #                 ans += 'Title: ' + ticket.title + '\n'
    #                 ans += "Start date: " + str(ticket.start_date) + '\n'
    #                 ans += 'Status: '
    #                 if ticket.close_date:
    #                     ans += "Тикет закрыт.\nClose data: " + str(ticket.close_date) + '\n\n'
    #                 else:
    #                     ans += 'Тикет активен. \n\n' 
    #                 bot.send_message(message.chat.id, "Список тикетов:\n\n" + ans)
    #         else:
    #             bot.send_message(message.chat.id, "У вас нет тикетов. Для создания тикета воспользуйтесь кнопкой 'Создать тикет.'")

    #     else:
    #         if all_tickets:
    #             for ticket in all_tickets:
    #                 ans += 'Ticket id: ' + str(ticket.id) + '\n'
    #                 ans += 'Title: ' + ticket.title + '\n'
    #                 if RoleNames(user.role_id).name == "ADMIN":
    #                     ans += 'Manager_id: ' + str(ticket.manager_id) + '\n'
    #                 ans += "Client_id: " + str(ticket.client_id) + '\n'
    #                 # messages = Ticket.get_all_messages(message.session, ticket.id, ticket.client_id)
    #                 ans += "Wait time: " + str(ticket.get_wait_time(message.session)) + "\n"
    #                 ans += "Start date: " + str(ticket.start_date) + '\n\n'
    #                 bot.send_message(message.chat.id, "Список тикетов:\n\n" + ans)
    #         else:
    #             bot.send_message(message.chat.id, "За Вами еще не закреплен ни один тикет.")

    # else:
    #     bot.send_message(message.chat.id, "Для того, чтобы просмотреть список тикетов, необходимо зарегистрироваться в "
    #                      "системе. Воспользуйтесь командой /start или /superuser_init.")


# Просмотр активных тикетов.
@bot.message_handler(commands=["ticket_list"])
def active_ticket_list(message):
    user = message.user
    user = User.find_by_conversation(message.session, message.chat.id)
    print(user.id)
    #print(f"FROM BOT BEFORE GET: {len(user.get_all_tickets(message.session))}")

    if user:
        ans = ''
        all_tickets = user.get_all_tickets(message.session)

        for ticket in all_tickets:
            ans += 'Ticket id: ' + str(ticket.id) + '\n'
            ans += 'Title: ' + ticket.title + '\n'
            ans += "Start date: " + str(ticket.start_date) + '\n'

            if RoleNames(user.role_id).name == "ADMIN":
                ans += 'Manager_id: ' + str(ticket.manager_id) + '\n'
                ans += "Client_id: " + str(ticket.client_id) + '\n'
                ans += "Wait time: " + str(ticket.get_wait_time(message.session)) + "\n"

            if RoleNames(user.role_id).name == "MANAGER":
                ans += "Client_id: " + str(ticket.client_id) + '\n'
                ans += "Wait time: " + str(ticket.get_wait_time(message.session)) + "\n"

            if RoleNames(user.role_id).name == 'CLIENT':
                ans += 'Status: '
                if ticket.close_date:
                    ans += "Тикет закрыт.\nClose data: " + str(ticket.close_date) + '\n'
                else:
                    ans += 'Тикет активен. \n'

            ans += '\n'

        if all_tickets:
            print(f"TICKET_LIST: MESSAGE.CHAT.ID = {message.chat.id}")

            bot.send_message(message.chat.id, "Список тикетов:\n\n" + ans)

        elif RoleNames(user.role_id).name == 'CLIENT':
            bot.send_message(message.chat.id,
                             "У вас нет тикетов. Для создания тикета воспользуйтесь кнопкой 'Создать тикет.'")
        else:
            bot.send_message(message.chat.id, "За Вами еще не закреплен ни один тикет.")
    else:
        bot.send_message(message.chat.id, "Для того, чтобы просмотреть список тикетов, необходимо зарегистрироваться в "
                                          "системе. Воспользуйтесь командой /start или /superuser_init.")


@bot.message_handler(commands=["ticket_id"])
def chose_ticket(message):
    user = message.user
    if user == None:
        bot.send_message(message.chat.id, "Для того, чтобы просмотреть список тикетов, необходимо зарегистрироваться в " \
                                          "системе. Воспользуйтесь командой /start или /superuser_init.")
    elif user.role_id == RoleNames.CLIENT.value:
        bot.send_message(message.chat.id,
                         "Введите номер тикета, на который Вы хотите переключиться. Чтобы посмотреть список " \
                         "активных тикетов, Вы можете воспользоваться командой /ticket_list, а затем снова /ticket_id.")
        bot.register_next_step_handler(message, switch_for_client)
    else:
        bot.send_message(message.chat.id, "Введите номер тикета, который Вы хотите просмотреть. Для просмотра активных " \
                                          "тикетов Вы можете воспользоваться кнопкой 'Список моих тикетов'.")
        bot.register_next_step_handler(message, switch_for_superuser)


def switch_for_client(message):
    if message.text == "/ticket_list":
        active_ticket_list(message)
    else:
        if Ticket.get_by_id(message.session, message.text) == None:
            bot.send_message(message.chat.id, "Введен некоторектный ticket_id. Пожалуйста, попробуйте еще раз.")
        else:
            bot.send_message(message.chat.id, "Тикет успешно выбран. В ближайшем времени с Вами свяжется менеджер.")


def switch_for_superuser(message):
    chat_id = message.chat.id
    if message.text == "/ticket_list":
        active_ticket_list(message)
    else:
        ticket = Ticket.get_by_id(message.session, message.text)
        if Ticket.get_by_id(message.session, message.text) == None:
            bot.send_message(message.chat.id, "Введен некорректный ticket_id. Пожалуйста, попробуйте еще раз.")
        else:
            ans = "Информация для ticket_id " + str(ticket.id) + ":\n\n"
            ans += 'Title: ' + ticket.title + '\n' + 'Manager_id: '
            if ticket.manager_id == None:
                ans += "Менеджер еще не найден. Поиск менеджера..." + '\n'
            else:
                ans += str(ticket.manager_id) + '\n'
            ans += "Client_id: " + str(ticket.client_id) + '\n'
            ans += "Start date: " + str(ticket.start_date) + '\n\n'
            ans += "История переписки:\n\n"
            messages = ticket.get_all_messages(message.session)
            for msg in messages:
                ans += str(msg.date) + "\n"
                role = User.find_by_id(message.session, msg.sender_id).role_id
                ans += RoleNames(role).name + ": " + msg.body + "\n\n"
            bot.send_message(chat_id, ans)


'''
#Закрытие тикета.
'''


@bot.message_handler(commands=["ticket_close"])
def close_ticket(message):
    """
        Закрытие тикета клиентом
    """
    if not message.user:
        bot.send_message(message.chat.id, "Для того, чтобы закрыть тикет, необходимо зарегистрироваться в " \
                                          "системе. Воспользуйтесь командой /start или /superuser_init.")
    elif message.user.role_id == RoleNames.MANAGER.value:
        bot.send_message(message.chat.id, "Данная команда не предназначена для менеджеров. Воспользуйтесь командой " \
                                          "/help, чтобы просмотреть список возможных команд.")
    else:
        bot.send_message(message.chat.id, "Введите номер тикета, который Вы хотите закрыть.")
        bot.register_next_step_handler(message, ticket_close)


def ticket_close(message):
    """
        Обработка закрытия тикета
    """
    ticket = Ticket.get_by_id(message.session, message.text)
    if not ticket:
        bot.send_message(message.chat.id, "Введен некорреткный номер тикета. Команда прервана.\nПовторите попытку.")
    elif User.find_by_id(message.session, ticket.client_id).role_id == RoleNames.ADMIN.value:
        bot.send_message(message.chat.id,
                         f"Тикет {message.text} был закрыт по решению администратора. Для уточнения информации " \
                         "обратитесь к менеджеру.")
    elif ticket.close_date != None:
        bot.send_message(message.chat.id, "Тикет уже закрыт.")
    else:
        bot.send_message(message.chat.id, "Тикет успешно закрыт.")
        ticket.close(message.session)


@bot.message_handler(commands=["manager_create"])
def create_manager(message):
    """
        Создание токена нового менеджера
    """
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start.")
    elif (len(args)) != 1:
        bot.send_message(
            message.chat.id, "Много аргументов: команда должна быть /manager_create.")
    else:
        if user.role_id != RoleNames.ADMIN.value:
            bot.send_message(
                message.chat.id, f"Извините. У вас недостаточно прав, вы - {RoleNames(user.role_id).name}.")
        else:
            new_token = Token.generate(message.session, RoleNames.MANAGER.value)
            bot.send_message(
                message.chat.id, f"{new_token.value}\nТокен создан - срок действия 24 часа.")


@bot.message_handler(commands=["admin_create"])
def create_admin(message):
    """
        Создание токена нового админа
    """
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif (len(args)) != 1:
        bot.send_message(
            message.chat.id, "Много аргументов: команда должна выглядеть так /admin_create")
    else:
        if user.role_id != RoleNames.ADMIN.value:
            bot.send_message(
                message.chat.id, f"Извиите. У вас недостаточно прав, вы - {RoleNames(user.role_id).name}")
        else:
            new_token = Token.generate(message.session, RoleNames.ADMIN.value)
            bot.send_message(
                message.chat.id, f"{new_token.value}\nТокен создан - срок действия 24 часа")


@bot.message_handler(commands=["manager_list"])
def get_manager_list(message):
    """
        Получение списка менеджеров
    """
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif user.role_id != RoleNames.ADMIN.value:
        bot.send_message(
            message.chat.id, "Извините, эта команда доступна только для администраторов приложения.")
    else:
        managers = User.get_all_users_with_role(
            message.session, RoleNames.MANAGER.value)
        if not managers:
            bot.send_message(message.chat.id, "Менеджеры не найдены, для добавления воспользуйтесь командой"
                                              " /manager create")
        else:
            for number, manager in enumerate(managers, start=1):
                bot.send_message(
                    message.chat.id, f"№{number} Имя - {manager.name}, id - {manager.conversation}")


@bot.message_handler(commands=["role"])
def check_role(message):
    """
        Команда выводит текущую роль пользователя
    """
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    else:
        bot.send_message(
            message.chat.id, f"Ваша текущая роль - {RoleNames(user.role_id).name}")


# удаление менеджера
@bot.message_handler(commands=["manager_remove"])
def manager_remove(message):
    """
        Удаление менеджера (разжалование)
    """
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif len(args) != 2:
        bot.send_message(
            message.chat.id, "Неверное использование команды. Шаблон: /manager_remove <manager id>")
    elif user.role_id != RoleNames.ADMIN.value:
        bot.send_message(
            message.chat.id, "Извините, эта команда доступна только для администраторов приложения.")
    else:
        """
            Что тут происходит?
            Красота
        """
        global manager_id
        manager_id = args[1]
        manager = User.find_by_conversation(message.session, manager_id)
        if not manager:
            bot.send_message(
                message.chat.id, "Менеджеров с таким id не найдено в базе данных.")
        else:
            keyboard = types.InlineKeyboardMarkup()
            key_yes = types.InlineKeyboardButton(
                text="Да", callback_data='yes')
            keyboard.add(key_yes)
            key_no = types.InlineKeyboardButton(text="Нет", callback_data='no')
            keyboard.add(key_no)
            bot.send_message(
                message.chat.id, "Вы действительно хотите сделать это?", reply_markup=keyboard)

            @bot.callback_query_handler(func=lambda call: True)
            def caller_worker(call):
                global manager_id
                manager = User.find_by_conversation(message.session, manager_id)
                if call.data == "yes":
                    manager.demote_manager(message.session)
                    bot.send_message(
                        message.chat.id, f"Менеджер с id {manager_id} удалён")
                elif call.data == "no":
                    bot.send_message(
                        message.chat.id, "Отменяем операцию удаления.")


# отказ менеджера от тикета


def describe(message):
    """
        Описание причины отказа от тикента менеджера
    """
    if not message.text:
        bot.send_message(chat, "Описание отказа от тикета обязательно.\n \
            Опишите причину закрытия тикета\n")
        bot.register_next_step_handler(message, describe)
    else:
        global tick_id
        ticket = Ticket.get_by_id(message.session, tick_id)
        ticket.put_refuse_data(message.session, message.text)
        ticket.reappoint(message.session)
        bot.send_message(message.chat.id, f"Вы отказались от тикета {tick_id}\n"
                                          "Для проверки воспользуйтесь командой /ticket_list")


@bot.message_handler(commands=["ticket_refuse"])
def ticket_refuse(message):
    """
        Коммманда отказа менеджера от тикета
    """
    args = message.text.split()
    user = message.user
    chat = message.chat.id
    if len(args) != 2:
        bot.send_message(
            chat, "Неверное использование команды. Шаблон: /ticket_refuse <ticket id>")
    elif user.role_id != RoleNames.MANAGER.value:
        bot.send_message(chat, f"Извините, ваша роль не позволяет воспользоваться командой, \
            нужно быть manager/nВаша роль {RoleNames(User.find_by_conversation(message.session, chat).role_id).name}")
    elif not Ticket.get_by_id(message.session, args[1]):
        bot.send_message(chat, "Извините, номер данного тикета не найден в базе")
    else:
        global tick_id
        tick_id = args[1]
        bot.send_message(chat, "Опишите причину закрытия тикета\n")
        bot.register_next_step_handler(message, describe)


@bot.message_handler(commands=["ticket_add"])
def create_ticket(message):
    """
        Команда создания тикета клиентом
    """
    user = message.user
    print(f"FROM BOT BEFORE CREATE: {len(user.get_all_tickets(message.session))}")

    if not user:
        bot.send_message(message.chat.id, "Для того, чтобы создать тикет, необходимо зарегистрироваться в " \
                                          "системе. Воспользуйтесь командой /start.")
    else:
        if user.role_id != RoleNames.CLIENT.value:
            bot.send_message(message.chat.id, "Создавать тикеты может только Клиент.")
        else:
            bot.send_message(message.chat.id, user.name + ", для начала кратко сформулируйте Вашу проблему:")
            bot.register_next_step_handler(message, get_title)


def get_title(message):
    """
        Получение заголовка тикета
    """
    user = message.user
    new_ticket = Ticket.create(message.session, message.text, message.chat.id)

    print(f"FROM BOT AFTER CREATE: {len(user.get_all_tickets(message.session))}")

    bot.send_message(message.chat.id, "Отлично. Теперь опишите Ваш вопрос более детально: ")
    if not new_ticket:
        bot.send_message(message.chat.id,
                         user.name + ", извините, в системе нет ни одного менеджера. Пожалуйста, обратитесь спустя пару минут.")
    else:
        bot.register_next_step_handler(message, get_ticket_body, new_ticket.id)


def get_ticket_body(message, ticket_id: int):
    """
        Получение описания тикета
    """
    user = message.user
    Message.add(message.session, message.text, ticket_id, message.chat.id)
    bot.send_message(message.chat.id, "Ваш вопрос успешно отправлен. В ближайшем времени с Вами свяжется менеджер.")
<<<<<<< HEAD


=======
>>>>>>> a6b079f23be646a59b7dcd551b25f21ae744381c
# ответ менеджера на тикет
@bot.message_handler(commands=["message"])
def manager_answer(message):
    """
        ответ менеджера на тикет
    """
    user_role = message.user.role_id

    if user_role == RoleNames.CLIENT.value:
<<<<<<< HEAD

        keyboard = types.InlineKeyboardMarkup()
        key_input = types.InlineKeyboardButton(text="Добавить сообщение в тикет", callback_data="Добавить")
        keyboard.add(key_input)
        key_show = types.InlineKeyboardButton(text="Просмотреть историю тикета", callback_data='История')
        keyboard.add(key_show)
        key_list = types.InlineKeyboardButton(text="Список моих тикетов", callback_data='Список')
        keyboard.add(key_list)
        keyboard.row(
            types.InlineKeyboardButton(text="Создать тикет", callback_data='Создать'),
            types.InlineKeyboardButton(text="Удалить тикет", callback_data='Удалить')
        )
        bot.send_message(message.chat.id, "Что вы хотите сделать?", reply_markup=keyboard)

        @bot.callback_query_handler(func=lambda callback: True)
        def caller_worker(callback):
            message.user = User.find_by_conversation(message.session, callback.from_user.id)
            message.chat.id = callback.from_user.id
            if callback.data == "Добавить":
                bot.send_message(message.chat.id, "Введите ticket_id:")
                bot.register_next_step_handler(message, write_message)
            elif callback.data == "Список":
                # active_ticket_list(message)
                bot.send_message(message.chat.id, "Введите письку:")
                bot.register_next_step_handler(message, active_ticket_list)
            elif callback.data == "Создать":
                create_ticket(message)
            elif callback.data == "Удалить":
                close_ticket(message)
            elif callback.data == "История":
                bot.send_message(message.chat.id, "Введите ticket_id:")
                bot.register_next_step_handler(message, history)

=======
>>>>>>> a6b079f23be646a59b7dcd551b25f21ae744381c
        def write_message(message):
            ticket_id = message.text
            user = message.user
            try:
                ticket_id = int(ticket_id)
            except:
                bot.send_message(message.chat.id, "Некорректный номер тикета.")
                manager_answer(message)
            else:
                ticket = Ticket.get_by_id(message.session, ticket_id)

                if ticket and ticket.client_id == user.id:
                    bot.send_message(message.chat.id, "Хорошо, введите Ваше сообщение.")
                    bot.register_next_step_handler(message, append_message, ticket_id)
                else:
                    bot.send_message(message.chat.id, "Тикет не найден. Попробуйте еще раз.")

        def append_message(message, ticket_id):
            Message.add(message.session, message.text, ticket_id, message.chat.id)
            bot.send_message(message.chat.id, "Ваш вопрос успешно отправлен менеджеру, ожидайте.")
        '''
        keyboard = types.InlineKeyboardMarkup()
        key_input = types.InlineKeyboardButton(text="Добавить сообщение в тикет", callback_data="Добавить")
        keyboard.add(key_input)
        key_show = types.InlineKeyboardButton(text="Просмотреть историю тикета", callback_data='История')
        keyboard.add(key_show)
        key_list = types.InlineKeyboardButton(text="Список моих тикетов", callback_data='Список')
        keyboard.add(key_list)
        keyboard.row(
            types.InlineKeyboardButton(text="Создать тикет", callback_data='Создать'),
            types.InlineKeyboardButton(text="Удалить тикет", callback_data='Удалить')
        )
        '''
        def worker(message):
            print(message.text)
            if str(message.text) == "Добавить сообщение в тикет":
                bot.send_message(message.chat.id, "Введите ticket_id:", reply_markup = types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, write_message)
            elif str(message.text) == "Создать тикет":
                bot.send_message(message.chat.id, "Секундочку....", reply_markup = types.ReplyKeyboardRemove())
                create_ticket(message)
            elif str(message.text) == "Список моих тикетов":
                bot.send_message(message.chat.id, "Хорошо, вывожу.", reply_markup = types.ReplyKeyboardRemove())
                active_ticket_list(message)
            elif str(message.text) == "Посмотреть историю тикета":
                bot.send_message(message.chat.id, "Введите ticket_id:", reply_markup = types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, history)
            elif str(message.text) == "Удалить тикет":
                bot.send_message(message.chat.id, "Секундочку...", reply_markup = types.ReplyKeyboardRemove())
                close_ticket(message)
        bot.send_message(message.chat.id, "Что вы хотите сделать?", reply_markup = keyboard_client())
        bot.register_next_step_handler(message, worker)

    elif user_role == RoleNames.MANAGER.value:
        keyboard = types.InlineKeyboardMarkup()
        key_history = types.InlineKeyboardButton(text="Просмотреть историю сообщений тикета", callback_data="История")
        keyboard.add(key_history)
        key_reply = types.InlineKeyboardButton(text="Выбрать тикет для ответа", callback_data='Ответ')
        keyboard.add(key_reply)
        key_show = types.InlineKeyboardButton(text="Просмотреть активные тикеты", callback_data='Список')
        keyboard.add(key_show)
        key_refuse = types.InlineKeyboardButton(text="Отказаться от тикета", callback_data='Отказ')
        keyboard.add(key_refuse)
        bot.send_message(message.chat.id, "Что Вы хотите сделать?", reply_markup=keyboard)

        @bot.callback_query_handler(func=lambda callback: True)
        def caller_worker(callback):
            message.user = User.find_by_conversation(message.session, callback.from_user.id)
            message.chat.id = callback.from_user.id
            if callback.data == "Список":
                # active_ticket_list(message)
                bot.send_message(message.chat.id, "Введите письку:")
                bot.register_next_step_handler(message, active_ticket_list)
            if callback.data == "История":
                print(f"HISTORY: MESSAGE.CHAT.ID = {message.chat.id}")
                bot.send_message(message.chat.id, "Введите ticket_id:")
                bot.register_next_step_handler(message, history)
            if callback.data == "Ответ":
                bot.send_message(message.chat.id, "Введите ticket_id:")
                bot.register_next_step_handler(message, get_reply_id)
            if callback.data == "Отказ":
                bot.send_message(message.chat.id, "Введите ticket_id:")
                bot.register_next_step_handler(message, get_refuse_id)


def history(message):
    """
        История тикета
    """
    print(f'CHAT_ID = {message.chat.id}')

    ticket_id = message.text
    chat_id = message.chat.id
    try:
        ticket_id = int(ticket_id)
    except:
        bot.send_message(message.chat.id, "Некорректный номер тикета.")
        manager_answer(message)
    else:
        ticket = Ticket.get_by_id(message.session, ticket_id)
        user_id = User.find_by_conversation(message.session, chat_id).id
        messages = Ticket.get_all_messages(message.session, ticket_id)
        messages.reverse()

        if not (ticket and user_id in (ticket.client_id, ticket.manager_id)):
            bot.send_message(message.chat.id, f"Тикет с номером {ticket_id} не найдено.\n")
        else:
            ans = ''
            if len(messages) > 10:
                messages = messages[:11]
            for m in messages:
                ans += RoleNames(User.find_by_id(message.session, m.sender_id).role_id).name + '\n'
                ans += "Дата: " + str(m.date) + "\n"
                ans += "Сообщение: " + m.body + "\n\n"

            if messages:
                bot.send_message(chat_id, "История последних сообщений:\n\n" + ans)
            else:
                bot.send_message(chat_id, "История сообщений пустая.")


def get_reply_id(message):
    ticket_id = message.text
    chat_id = message.chat.id
    try:
        ticket_id = int(ticket_id)
    except:
        bot.send_message(message.chat.id, "Тикет введен некорректно.")
        manager_answer(message)
    else:
        user = message.user
        ticket = Ticket.get_by_id(message.session, ticket_id)
        user_id = User.find_by_conversation(message.session, chat_id).id

        if ticket and user_id in (ticket.client_id, ticket.manager_id):
            bot.send_message(message.chat.id, "Введите Ваш ответ:")
<<<<<<< HEAD

            @bot.middleware_handler(update_types=['message'])
            def save_ticket_id(bot_instance, message):
                message.ticket_id = ticket_id

            bot.register_next_step_handler(message, get_reply)
=======
            bot.register_next_step_handler(message, get_reply, ticket_id)
>>>>>>> a6b079f23be646a59b7dcd551b25f21ae744381c
        else:
            bot.send_message(message.chat.id, f"Тикет с номером {ticket_id} не найден.")


def get_refuse_id(message):
    ticket_id = message.text
    try:
        ticket_id = int(ticket_id)
    except:
        bot.send_message(message.chat.id, "Тикет введен некорректно.")
        manager_answer(message)

    else:
        if not Ticket.get_all_messages(message.session, ticket_id):
            bot.send_message(message.chat.id, f"Тикет с номером {ticket_id} не найден.")
        else:
            user = User.find_by_conversation(message.session, message.chat.id)
            if user.role_id != RoleNames.MANAGER.value:
                bot.send_message(message.chat.id, f"Извините, ваша роль не позволяет воспользоваться командой, \
                    нужно быть manager/nВаша роль {RoleNames(User.find_by_conversation(message.session, chat).role_id).name}")
            else:
                global tic
                tic = ticket_id
                bot.send_message(message.chat.id, "Опишите причину закрытия тикета:\n")
                bot.register_next_step_handler(message, describe_refuse)


def describe_refuse(message):
    if not message.text:
        bot.send_message(message.chat.id, "Описание отказа от тикета обязательно.\n \
            Опишите причину закрытия тикета\n")
        bot.register_next_step_handler(message, describe_refuse)
    else:
        global tic
        ticket = Ticket.get_by_id(message.session, tic)
        ticket.put_refuse_data(message.session, message.text)
        ticket.reappoint(message.session)
<<<<<<< HEAD
        bot.send_message(message.chat.id, f"Вы отказались от тикета {tick_id}\n"
                                          "Для проверки воспользуйтесь командой /ticket_list.")


def get_reply(message):
    curr_ticket = Ticket.get_by_id(message.session, message.ticket_id)
=======
        bot.send_message(message.chat.id, f"Вы отказались от тикета {tic}\n"
        "Для проверки воспользуйтесь командой /ticket_list.")
        
def get_reply(message, ticket_id):
    curr_ticket = Ticket.get_by_id(message.session, ticket_id)
>>>>>>> a6b079f23be646a59b7dcd551b25f21ae744381c
    client_convers = User.find_by_id(message.session, curr_ticket.client_id).conversation

    # client_id = message.session.query(Message).filter(Message.ticket_id == ticket_id).first()
    # client = User.find_by_id(message.session, client_id.sender_id).conversation
    reply = message.text
    Message.add(message.session, reply, ticket_id, message.chat.id)
    bot.send_message(client_convers, f"Вам ответил менеджер. Ticket #{curr_ticket.id}")
    bot.send_message(message.chat.id, "Ответ отправлен.")


# Команды адмиинистратора:


# отмена операции(удаления менеджера)
@bot.message_handler(commands=["cancel"])
def cancel(message):
    pass


@bot.message_handler(content_types=["text"])
def echo(message):
    manager_answer(message)


@bot.middleware_handler(update_types=['message'])
def session_middleware(bot_instance, message):
    """
       Завершение сессии БД
    """
    message.session.close()
<<<<<<< HEAD
    print("session CLOSE")

=======
def keyboard_manager():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    key_history = types.KeyboardButton('Просмотреть историю сообщений тикета')
    markup.add(key_history)
    key_reply = types.InlineKeyboardButton("Выбрать тикет для ответа")
    markup.add(key_reply)
    key_show = types.InlineKeyboardButton("Просмотреть активные тикеты")
    markup.add(key_show)
    key_refuse = types.InlineKeyboardButton("Отказаться от тикета")
    markup.add(key_refuse)
    return markup

def keyboard_client():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    key_input = types.KeyboardButton("Добавить сообщение в тикет")
    markup.add(key_input)
    key_show = types.KeyboardButton("Просмотреть историю тикета")
    markup.add(key_show)
    key_list = types.KeyboardButton("Список моих тикетов")
    markup.add(key_list)
    markup.row(
        types.KeyboardButton("Создать тикет"),
        types.KeyboardButton("Удалить тикет")
        )
    return markup

bot.polling(none_stop = True)
>>>>>>> a6b079f23be646a59b7dcd551b25f21ae744381c

