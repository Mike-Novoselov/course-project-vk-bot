from vk_api.longpoll import VkEventType, VkLongPoll
from bot import bot
from db import delete_table_viewed, create_table_viewed


def event_listener():
    for event in bot.longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            request = event.text.lower()
            user_id = event.user_id

            if request == 'поиск' or request == 'f':
                bot.get_age_of_user(user_id)
                bot.get_target_city(user_id)
                bot.looking_for_persons(user_id)
                bot.show_found_person(user_id)

            elif request == 'удалить' or request == 'd':
                delete_table_viewed()
                create_table_viewed()
                bot.send_msg(user_id, 'База данных очищена! Сейчас наберите "Поиск" или "F"')

            elif request == 'смотреть' or request == 'далее' or request == 's':
                if bot.get_found_person_id() != 0:
                    bot.show_found_person(user_id)
                else:
                    bot.send_msg(user_id, 'В начале наберите "Поиск" или "F"')

            else:
                bot.send_msg(user_id, f'{bot.get_user_name(user_id)}, бот готов к поиску. Наберите:\n'
                                      f'"Поиск" или "F" - поиск людей.\n'
                                      f'"Удалить" или "D" - удалить старую базу данных и создать новую.\n'
                                      f'"Смотреть" или "Далее" или "S" - просмотр следующей записи в базе данных.')


if __name__ == '__main__':
    event_listener()
