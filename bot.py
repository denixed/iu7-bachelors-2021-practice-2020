from telebot import apihelper
import json
from db import Session
from models.DataBaseClasses import *
import telebot
from telebot import types

import CommonController
import ClientController

cfg = json.load(open("config.json"))
token = cfg['bot']['token']
bot = telebot.TeleBot(token)

apihelper.ENABLE_MIDDLEWARE = True

@bot.middleware_handler(update_types=['message'])
def session_middleware(bot_instance, message):
    """
        Установка сессии БД
    """
    message.session = Session()

@bot.middleware_handler(update_types=['message'])
def auth_middleware(bot_instance, message):
    """
        Авторизация пользователя
    """
    chat_id = message.chat.id
    message.user = User.find_by_conversation(message.session, chat_id)


CommonController.init(bot)
ClientController.init(bot)

# вход в систему менеджера/админа
@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/superuser init')
def create_superuser(message):
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start.")
    elif len(args) != 3:
        bot.send_message(
            message.chat.id, "Неправильное использование команды superuser.\nШаблон:/superuser init TOKEN")
    elif not Token.find(message.session, args[2]):
        bot.send_message(message.chat.id, "Данный токен не существует. Попробуйте еще раз.")
    else:
        token_new = args[2]
        my_token = Token.find(message.session, token_new)
        if my_token:
            user.appoint(message.session, my_token.role_id)
            my_token.activate(message.session)
            bot.send_message(
                message.chat.id, f"Токен успешно активирован, ваша роль {RoleNames(my_token.role_id).name}.")
        else:
            bot.send_message(
                message.chat.id, "Не удалось авторизоваться в системе. Попробуйте еще раз.")


#Просмотр активных тикетов.
@bot.message_handler(commands=["ticket_list"])
def active_ticket_list(message):
    user = message.user
    if user == None:
        bot.send_message(message.chat.id, "Для того, чтобы просмотреть список тикетов, необходимо зарегистрироваться в "
                         "системе. Воспользуйтесь командой /start или /superuser_init.")
    elif user.role_id == 3:
        ans = ''
        for ticket in user.get_active_tickets(session):
            ans += 'Ticket id: ' + str(ticket.id) + '\n'
            ans += 'Title: ' + ticket.title + '\n' + 'Manager_id: '
            if ticket.manager_id == None:
                ans += "Менеджер еще не найден. Поиск менеджера..." + '\n'
            else:
                ans += "Manager_id: " + str(ticket.manager_id) + '\n'
            ans += "Start data: " + str(ticket.start_date) + '\n\n'
        bot.send_message(message.chat.id, "Список активных тикетов:\n\n" + ans)
    else:
        ans = ''
        #нужно отсортировать, но у меня такое подозрение, что они уже отсортированные
        for ticket in user.get_active_tickets(session):
            ans += 'Ticket id: ' + str(ticket.id) + '\n'
            ans += 'Title: ' + ticket.title + '\n'
            ans += 'Manager_id: ' + str(ticket.manager_id) + '\n'
            ans += "Client_id: " + str(ticket.client_id) + '\n'
            messages = Message.get(session, ticket.id, ticket.client_id)
            ans += "Wait time: " + (str(datetime.now() - messages[0].date))[:8] + "\n"
            client = User.find_by_id(session, ticket.client_id)
            if client.identify_ticket(session) == ticket.id:
                ans += "Status: Клиент ожидает ответа на этот тикет!\n"
            else:
                ans += "Status: Работа по тикету приостановлена.\n"
            ans += "Start date: " + str(ticket.start_date) + '\n\n'
        if ans == '':
            bot.send_message(message.chat.id, "За Вами еще не закреплен ни один тикет.")
        else:
            bot.send_message(message.chat.id, "Список активных тикетов:\n\n" + ans)




@bot.message_handler(commands = ["ticket_id"])
def chose_ticket(message):
    user = message.user
    if user == None:
        bot.send_message(message.chat.id, "Для того, чтобы просмотреть список тикетов, необходимо зарегистрироваться в " \
                         "системе. Воспользуйтесь командой /start или /superuser_init.")
    elif user.role_id == 3:
        bot.send_message(message.chat.id, "Введите номер тикета, на который Вы хотите переключиться. Чтобы посмотреть список "\
                         "активных тикетов, Вы можете воспользоваться командой /ticket_list, а затем снова /ticket_id.")
        bot.register_next_step_handler(message, switch_for_client)
    else:
        bot.send_message(message.chat.id, "Введите номер тикета, который Вы хотите просмотреть. Для просмотра активных "\
                         "тикетов Вы можете воспользоваться командой /ticket_list, а затем снова /ticket_id.")
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
        ticket = Ticket.get_by_id(session, message.text)
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
            ans += "Start data: " + str(ticket.start_date) + '\n\n'
            ans += "История переписки:\n\n"
            messages = ticket.get_all_messages(message.session)
            for message in messages:
                ans += str(message.date) + "\n"
                role = User.find_by_id(message.session, message.sender_id).role_id
                ans += RoleNames(role).name + ": " + message.body + "\n\n"
            bot.send_message(chat_id, ans)



#Закрытие тикета.
@bot.message_handler(commands = ["ticket_close"])
def close_ticket(message):
    user = User.find_by_id(message.session, message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "Для того, чтобы закрыть тикет, необходимо зарегистрироваться в " \
                         "системе. Воспользуйтесь командой /start или /superuser_init.")
    elif user.role_id == RoleNames.MANAGER.value:
        bot.send_message(message.chat.id, "Данная команда не предназначена для менеджеров. Воспользуйтесь командой "\
                         "/help, чтобы просмотреть список возможных команд.")
    else:
        bot.send_message(message.chat.id, "Введите номер тикета, которвый Вы хотите закрыть. Для просмотра активных "\
                         "тикетов Вы можете воспользоваться командой /ticket_list.")
        bot.register_next_step_handler(message, ticket_close)
def ticket_close(message):
    ticket = Ticket.get_by_id(message.text)
    if not ticket:
        bot.send_message(message.chat.id, "Введен некорреткный номер тикета. Попробуйте еще раз.")
    if User.find_by_id(ticket.sender_id).role_id == RoleNames.ADMIN.value:
        bot.send_message(message.chat.id, f"Тикет {message.text} был закрыт по решению администратора. Для уточнения информации "\
                "обратитесь к менеджеру.")
    else:
        bot.send_message(message.chat.id, "Тикет успешно закрыт.")
    ticket.close(message.session)


@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/manager create')
def create_manager(message):
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif (len(args)) != 2:
        bot.send_message(
            message.chat.id, "Много аргументов: команда должна быть /manager create")
    else:
        if user.role_id != RoleNames.ADMIN.value:
            bot.send_message(
                message.chat.id, f"Извините. У вас недостаточно прав, вы - {RoleNames(user.role_id).name}")
        else:
            new_token = Token.generate(message.session, RoleNames.MANAGER.value)
            bot.send_message(
                message.chat.id, f"{new_token.value}\nТокен создан - срок действия 24 часа")


@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/admin create')
def create_admin(message):
    args = message.text.split()
    user = message.user
    print(user)
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif (len(args)) != 2:
        bot.send_message(
            message.chat.id, "Много аргументов: команда должна выглядеть так /admin create")
    else:
        if user.role_id != RoleNames.ADMIN.value:
            bot.send_message(
                message.chat.id, f"Извиите. У вас недостаточно прав, вы - {RoleNames(user.role_id).name}")
        else:
            new_token = Token.generate(message.session, RoleNames.ADMIN.value)
            print("GGG")
            bot.send_message(
                message.chat.id, f"{new_token.value}\nТокен создан - срок действия 24 часа")


@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/manager list')
def get_manager_list(message):
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif len(args) != 2:
        bot.send_message(
            message.chat.id, "Неверное использование команды. Шаблон: /manager list")
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
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    else:
        bot.send_message(
            message.chat.id, f"Ваша текущая роль - {RoleNames(user.role_id).name}")


# TODO TOMMOROW
# удаление менеджера
@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/manager remove')
def manager_remove(message):
    args = message.text.split()
    user = message.user
    if not user:
        bot.send_message(
            message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif len(args) != 3:
        bot.send_message(
            message.chat.id, "Неверное использование команды. Шаблон: /manager remove <manager id>")
    elif user.role_id != RoleNames.ADMIN.value:
        bot.send_message(
            message.chat.id, "Извините, эта команда доступна только для администраторов приложения.")
    else:
        """
            Что тут происходит?
        """
        global manager_id
        manager_id = args[2]
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
                        message.chat.id, "Отменяем операцию удаления")

# TODO команды менеджера:
# отказ менеджера от тикета


def describe(message):
    if not message.text:
        bot.send_message(chat, "Описание отказа от тикета обязательно.\n \
            Опишите причину закрытия тикета\n")
        bot.register_next_step_handler(message, describe)
    else:
        global tick_id
        ticket = Ticket.get_by_id(message.session,tick_id)
        ticket.put_refuse_data(message.session, message.text)
        ticket.reappoint(message.session)
        bot.send_message(message.chat.id, f"Вы отказались от тикета {tick_id}\n"
        "Для проверки воспользуйтесь командой /ticket_list")

@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/ticket refuse')
def ticket_refuse(message):
    args = message.text.split()
    user = message.user
    chat = message.chat.id
    if len(args) != 3:
        bot.send_message(
            chat, "Неверное использование команды. Шаблон: /ticket refuse <ticket id>")
    elif user.role_id != RoleNames.MANAGER.value:
        bot.send_message(chat, f"Извините, ваша роль не позволяет воспользоваться командой, \
            нужно быть manager/nВаша роль {RoleNames(User.find_by_conversation(message.session, chat).role_id).name}")
    elif not Ticket.get_by_id(message.session, args[2]):
        bot.send_message(chat, "Извините, номер данного тикета не найден в базе")
    else:
        global tick_id
        tick_id = args[2]
        bot.send_message(chat, "Опишите причину закрытия тикета\n")
        bot.register_next_step_handler(message, describe)


# ответ менеджера на тикет
@bot.message_handler(commands=["message"])
def manager_answer(message):
    keyboard = types.InlineKeyboardMarkup()
    key_history = types.InlineKeyboardButton(text="Просмотреть историю сообщений клиента", callback_data="История")
    keyboard.add(key_history)
    key_reply = types.InlineKeyboardButton(text="Выбрать тикет для ответа", callback_data='Ответ')
    keyboard.add(key_reply)
    key_show = types.InlineKeyboardButton(text="Просмотреть активные тикеты", callback_data='Просмотр')
    keyboard.add(key_show)
    bot.send_message(message.chat.id, "Что Вы хотите сделать?", reply_markup=keyboard)
    @bot.callback_query_handler(func=lambda callback: True)
    def caller_worker(callback):
        if callback.data == "Просмотр":
            active_ticket_list(message)
        if callback.data == "История":
            bot.send_message(message.chat.id, "Введите client_id:")
            bot.register_next_step_handler(message, chose_id)
        if callback.data == "Ответ":
            bot.send_message(message.chat.id, "Введите client_id:")
            bot.register_next_step_handler(message, get_reply_id)
'''def chose_id(message):
    client_id = message.text
    chat_id = message.chat.id
    messages = session.query(Message).filter(Message.sender_id==client_id)
    messages = messages[:20]
    ans = ''
    for message in messages:
        ans += "Date: " + str(message.date) + "\n"
        ans += "Message: " + message.body + "\n\n"
    if ans == '':
        bot.send_message(chat_id, "История сообщений пустая.")
    else:
        bot.send_message(chat_id, "История последних сообщений клиента:\n\n" + ans)
def get_reply_id(message):
    Message.add(session, message.text, None, message.chat.id)
    bot.register_next_step_handler(message, get_reply)
def get_reply(message):
    chat_id = message.chat.id
    client_id = session.query(Message).filter(Message.sender_id==message.chat.id).body
    client = User.find_by_id(session, client_id)
    ticket = client.identify_ticket(session)
    reply = message.text
    Message.add(session, reply, ticket.id, message.chat.id)
    message = Message.get(session, ticket_id, message.chat.id)
    bot.send_message(client.id, message)
    bot.send_message(chat_id, "Ответ отправлен.")'''

# Команды адмиинистратора:


# отмена операции(удаления менеджера)
@bot.message_handler(commands=["cancel"])
def cancel(message):
    pass

@bot.middleware_handler(update_types=['message'])
def session_middleware(bot_instance, message):
    """
       Завершение сессии БД
    """
    message.session.close()

bot.polling(none_stop=True)
