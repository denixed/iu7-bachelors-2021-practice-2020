import telebot
import json
from db import session
from models.DataBaseClasses import User, Token
import string 
import random
import time
from telebot import apihelper
from telebot import types
from models.DataBaseClasses import *

cfg = json.load(open("config.json"))
token = cfg['bot']['token']
bot = telebot.TeleBot(token)


#ЭТО ГЕНЕРАТОР ТОКЕНА
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
#формирование тикета:
def generate_ticket(length = 6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for i in range(length))

#формирование токена: больше запас цифр для надежности(мнимой) - 
def generate_token(length = 10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for i in range(length))



#cоздание кастомной клавиатуры
def create_su_init_keyboard(buttons):
    keyboard = types.InlineKeyboardMarkup(row_width = 3)
    for x in buttons:
        keyboard.add(types.InlineKeyboardButton(text = x, callback_data = x))
    return keyboard



'''
@bot.message_handler(commands = ["start"])
def start_message(message):
    client = session.query(User).filter(User.id == message.from_user.id)
    if not client:
        session.add(User(id = message.from_user.id, conversation = message.chat.id, name = message.from_user.first_name, role_id = 3))
        session.commit()
        bot.send_message(message.chat.id, "Добро пожаловать в систему <Name_bot>. Для начала работы воспользуйтесь" \
                     " командой /ticket_add.")
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы в системе.  Для начала работы Вы можете воспользоваться "\
                         "командой /ticket_add для создания тикета или /ticket_list для просмотра истории Ваших тикетов." )

'''


#вход в систему: менеджер/админ
'''
@bot.message_handler(commands = ["superuser_init"])
def superuser_init(message):
    user = session.query(User).filter(User.id == message.from_user.id)
    keyboard = create_keyboard("Manager", "Admin")
    bot.send_message(message.chat.id, "Добро пожаловать в систему. Выберите свой статус:", reply_markup=keyboard)
'''
#инициализация (не вход!!!)
#TODO должна быть другая функция декоратора, потому что будет несколько клавиатур
@bot.callback_query_handler(func = lambda x: True)
def callback_handler(callback_query):
    message = callback_query.message
    text = callback_query.data
    if text == "Manager":
        manager = session.query(User).filter(User.id == message.from_user.id)
        if not manager:
            bot.send_message(message.chat.id, "Для начала работы необходимо зарегистрироваться "\
                             "в системе с помощью команды /start.")
        elif manager.role_id == 2:
            bot.send_message(message.chat.id, "Вы уже значитесь в списке менеджеров. Для входа в систему " \
                             "в качестве менеджера воспользуйтесь командой /superuser_enter.")
            #добавить функцию superuser_enter, чтобы разграничить вход и инициализацию
        else:
            bot.send_message(message.chat.id, 'Ваш запрос передан администраторам приложения. В скором времени Вам придет '\
                             'соответствующая инструкция.')
    elif text == "Admin":
        admin = session.query(User).filter(User.id == message.from_user.id)
        if not admin:
            #если это первый суперюзер - присвоить случайный токен. Действуем по принципу "кто успеет" (?)
            #Значит администратор первый. Присваиваем случайно токен.
            token = generate_token()
            session.add(Token(value = token, expires_date = time.strftime('%Y-%m-%d %H:%M:%S'), role_id = 1))
            session.add(User(id = message.from_user.id, conversation = None, name = message.from_user.first_name, role_id = 1))
            session.commit()
        elif admin.role_id == 1:
            bot.send_message(message.chat.id, "Вы уже значитесь в списке администраторов. Для входа в систему " \
                             "в качестве администратора воспользуйтесь командой /superuser_enter.")
            #добавить функцию superuser_enter, чтобы разграничить вход и инициализацию
        else:
            bot.send_message(message.chat.id, 'Ваш запрос передан администраторам приложения. В скором времени Вам придет '\
                             'соответствующая инструкция.')
        #TODO нужно это как-то отловить из бд messages ответ на это сообщение либо придумать какую-то форму ввода




            
        
#открытие нового тикета
@bot.message_handler(commands = ["ticket_add"])
def create_ticket(message):
    #я не знаю, правильно ли это работает с точки зения бд. Пока так
    #Обатите внимание на title в ticket
    user = session.query(User).filter(User.id == message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Для того, чтобы создать тикет, необходимо зарегистрироваться в " \
                         "системе. Воспользуйтесь командой /start.")
    else:
        if user.role_id != 3:
            bot.send_message(message.chat.id, "Комманда /ticket_add доступна только для клиентов.")
        else:    
            ticket = generate_ticket()
            bot.send_message(message.chat.id, Person.name + ", опишите ваш вопрос:")
            session.add(Ticket(id = ticket, manager_id = None, client_id = message.from_user.id, \
                               title = "Зачем он нужен? Дальше сообщение ловить надо.", \
                               start_date = time.strftime('%Y-%m-%d %H:%M:%S'), close_date = None))
            session.commit()





#просмотр активных тикетов
@bot.message_handler(commands = ["ticket_list"])
def active_ticket_list(message):
    user = session.query(User).filter(User.id == message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "Для того, чтобы просмотреть список тикетов, необходимо зарегистрироваться в " \
                         "системе. Воспользуйтесь командой /start или /superuser_init.")
    else:
        bot.send_message(message.chat.id, "Список активных тикетов:\n" + "\n".join(user.get_active_tickets))





@bot.message_handler(commands = ["ticket"])
def chose_ticket(message):
    user = session.query(User).filter(User.id == message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "Для того, чтобы просмотреть список тикетов, необходимо зарегистрироваться в " \
                         "системе. Воспользуйтесь командой /start или /superuser_init.")
    else:
        bot.send_message(message.chat.id, "Введите номер тикета, на который Вы хотите переключиться. Для просмотра активных "\
                         "тикетов Вы можете воспользоваться командой /ticket_list.")
        #TODO Как отловить это сообщение?





@bot.message_handler(commands = ["ticket_close"])
def close_ticket(message):
    user = session.query(User).filter(User.id == message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "Для того, чтобы закрыть тикет, необходимо зарегистрироваться в " \
                         "системе. Воспользуйтесь командой /start или /superuser_init.")
    elif user.role_id == 2:
        bot.send_message(message.chat.id, "Данная команда не предназначена для менеджеров. Воспользуйтесь командой "\
                         "/show_panel, чтобы просмотреть список возможных команд.")
        #соответственно сделать эту панель
    else:
        bot.send_message(message.chat.id, "Введите номер тикета, которвый Вы хотите закрыть. Для просмотра активных "\
                         "тикетов Вы можете воспользоваться командой /ticket_list.")
        #TODO Как отловить это сообщение?
        


'''
#(версия /manager_list Полины) Возможно, это не работает, не тестила на бд, но логика примерно такая
#TODO помещение команд в messages?
@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/manager list')
def get_manager_list(message):
    admin = User()
    admin = session.query(User).filter(User.id == message.from_user.id)
    if not admin:
        bot.send_message(message.chat.id, "Для того, чтобы воспользоваться командой, необходимо зарегистрироваться в " \
                         "системе. Воспользуйтесь командой /superuser init.")
    elif admin.role_id != 1:
        bot.send_message(message.chat.id, "Извините, эта команда доступна только для администраторов приложения.")
    else:
        if message.text != "/manager list":
            bot.send_message(message.chat.id, "Запрос должен состоять только из команды '/manager list'. Пожалуйста,"\
                         " оформите Ваш запрос корректно.")
            return 
        managers = admin.get_all_managers(session)
        if not managers:
            bot.send_message(message.chat.id,"Менеджеры не найдены. Для добавления воспользуйтесь командой" \
                "/manager create")
        else:
            bot.send_message(message.chat.id, "\n".join(managers))
'''



#Обработка входа в систему.
@bot.message_handler(commands =["start"])
def start(message):
    username = message.from_user.first_name
    chat_id = message.chat.id
    cur_role = None
    if not User.get_all_users_with_role(session, RoleNames.ADMIN.value):
        cur_role = RoleNames.ADMIN.value
    elif not User.find_by_conversation(session, chat_id):
        cur_role = RoleNames.CLIENT.value
    if cur_role:
        client = User.add_several(session, [(chat_id, username, cur_role)])
        bot.send_message(message.chat.id, "Вы успешно зарегистрировались в системе,{}\nВаша роль - {}".format(username, RoleNames(cur_role).name))
    else:
        if User.find_by_conversation(session, message.chat.id).name.lower() != username.lower()
            User.change_name(session, username, user_id = chat_id)
        bot.send_message(message.chat.id, "Вы уже зарегистрировались в системе,{}\nВаша роль - {}".format(username, RoleNames(cur_role).name))




    
@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/superuser init')
def create_superuser(message):
    args = message.text.split()
    user = User.find_by_conversation(session, conversation = message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif len(args) != 3:
        bot.send_message(message.chat.id, "Неправильное использование команды superuser\nШаблон:/superuser init TOKEN")
    elif len(args[2]) != 6:
        bot.send_message(message.chat.id, "Неправильный размер токена")
    else:
        user = User.find_by_conversation(session, conversation = message.chat.id)
        token_new = args[2]
        my_token = Token.find(session, token_new)
        if my_token:
            user.appoint(session,my_token.role_id)
            my_token.activate(session, token_new)
            bot.send_message(message.chat.id, "Токен успешно активирован, ваша роль {}".format(RoleNames(my_token.role_id).name))


    
@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/manager create')
def create_manager(message):
    args = message.text.split()
    user = User.find_by_conversation(session, conversation = message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif (len(args)) != 2:
        bot.send_message(message.chat.id, "Много аргументов: команда должна быть /manager create")
    else:
        if user.role_id != RoleNames.ADMIN.value:
            bot.send_message(message.chat.id, "Извините. У вас недостаточно прав, вы - {}".format(RoleNames(user.role_id).name))
        else:
            new_token = Token.generate(session, RoleNames.MANAGER.value)
            bot.send_message(message.chat.id, "{}\nТокен создан - срок действия 24 часа".format(new_token.value))




@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/admin create')
def create_admin(message):
    user = User.find_by_conversation(session, conversation = message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif (len(args)) != 2:
        bot.send_message(message.chat.id, "Много аргументов: команда должна выглядеть так /admin create")
    else:
        if user.role_id != RoleNames.ADMIN.value:
            bot.send_message(message.chat.id, "Извиите. У вас недостаточно прав, вы - {}".format(RoleNames(user.role_id).name))
        else:
            new_token = Token.generate(session, RoleNames.ADMIN.value)
            bot.send_message(message.chat.id, "{}\nТокен создан - срок действия 24 часа".format(new_token.value))


@bot.message_handler(func=lambda message: " ".join(message.text.split()[0:2]) == '/manager list')
def get_manager_list(message):
    args = message.text.split()
    user = User.find_by_conversation(session, conversation = message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    elif len(args) != 2:
        bot.send_message(message.chat.id, "Неверное использование команды. Шаблон: /manager list")
    elif user.role_id != RoleNames.ADMIN.value:
        bot.send_message(message.chat.id,"Извините, эта команда доступна только для администраторов приложения.")
    else:
        managers = User.get_all_users_with_role(session, RoleNames.MANAGER.value)
        if not managers:
            bot.send_message(message.chat.id,"Менеджеры не найдены, для добавления воспользуйтесь командой" \
            "/manager create")
        else:
            bot.send_message(message.chat.id, "\n".join(managers))

@bot.message_handler(commands = ["role"])
def check_role(message):
    user = User.find_by_conversation(session, conversation = message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Сначала нужно зарегистрироваться, воспользуйтесь командой /start")
    else:
        bot.send_message(message.chat.id, "Ваша текущая роль - {}".format(RoleNames(user.role_id).name)) 




#TODO команды менеджера:

#отказ менеджера от тикета
@bot.message_handler(commands = ["ticket_refuse"])
def ticket_refuse(message):
    pass

#ответ менеджера на тикет
@bot.message_handler(commands = ["message"])
def manager_answer(message):
    pass

#Команды адмиинистратора:

#получить список менеджеров
@bot.message_handler(commands = ["manager_list"])
def manager_list(message):
    pass

#удаление менеджера
@bot.message_handler(commands = ["manager_remove"])
def cancel(message):
    pass

#отмена операции(удаления менеджера)
@bot.message_handler(commands = ["cancel"])
def cancel(message):
    pass

#подтверджение операции(удаления менеджера)
@bot.message_handler(commands = ["confirm"])
def confirm(message):
    pass

bot.polling(none_stop=True)
