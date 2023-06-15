from vk_api.longpoll import VkLongPoll, VkEventType
import datetime
import vk_api
from config import user_token, group_token
from random import randrange
from pprint import pprint
from db import *


class Bot:
    def __init__(self):
        print('Бот создан!')
        self.vk_user = vk_api.VkApi(
            token=user_token)  # Создаем переменную сессии, авторизованную личным токеном пользователя.
        self.vk_user_got_api = self.vk_user.get_api()  # # переменную сессии vk_user подключаем к api списку методов.
        self.vk_group = vk_api.VkApi(token=group_token)  # Создаем переменную сесии, авторизованную токеном сообщества.
        self.vk_group_got_api = self.vk_group.get_api()  # переменную сессии vk_group подключаем к api списку методов.
        self.longpoll = VkLongPoll(
            self.vk_group)  # переменную сессии vk_group_got_api подключаем к Long Poll API,
        

    def send_msg(self, user_id, message):
        """Функция отправки сообщений пользователю. 
        Принимает идентификатор пользователя user_id и текст сообщения message"""
        try:
            self.vk_group_got_api.messages.send(
                user_id=user_id,
                message=message,
                random_id=randrange(10 ** 7)
            )
            return True  # Успешная отправка сообщения
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            return False  # Ошибка при отправке сообщения

    def get_user_name(self, user_id):
        """
        Получение имени пользователя, который написал боту.
        Принимает идентификатор пользователя user_id.
        Возвращает имя пользователя или отправляет сообщение об ошибке.
        """
        try:
            user_info = self.vk_group_got_api.users.get(user_id=user_id)
            name = user_info[0].get('first_name')
            if name is not None:
                return name
            else:
                error_message = "Ошибка: имя пользователя не найдено"
        except KeyError as e:
            error_message = f"Ошибка: {e}"
        
        self.send_msg(user_id, error_message)

    def naming_of_years(self, years, till=True):
        """
        Функция для формирования строки с числом лет/год для возраста.
        Принимает возраст years и флаг till, указывающий, нужно ли использовать слово 'года' или 'лет'.
        """
        name_years_singular = [1, 21, 31, 41, 51, 61, 71, 81, 91, 101]
        name_years_plural = [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54, 62, 63, 64]

        if till:
            if years in name_years_singular:
                return f'{years} года'
            else:
                return f'{years} лет'
        else:
            if years == 1 or years % 10 == 1 and years != 11:
                return f'{years} год'
            elif years in name_years_plural:
                return f'{years} года'
            else:
                return f'{years} лет'

    def input_looking_age(self, user_id, age):
        """
        Обработка введенного возраста пользователем.
        Принимает идентификатор пользователя user_id и введенный возраст age.
        """
        try:
            age_from, age_to = None, None
            ages = age.split("-")
            if len(ages) == 2:
                age_from = int(ages[0])
                age_to = int(ages[1])
                if age_from == age_to:
                    self.send_msg(user_id, f'Ищем возраст {self.naming_of_years(age_to, False)}')
                else:
                    self.send_msg(user_id, f'Ищем возраст в пределах от {age_from} до {self.naming_of_years(age_to, True)}')
            else:
                age_to = int(ages[0])
                self.send_msg(user_id, f'Ищем возраст {self.naming_of_years(age_to, False)}')

        except ValueError:
            self.send_msg(user_id, 'Ошибка ввода: введите числовой формат возраста')

        return age_from, age_to

    def get_years_of_person(self, bdate: str) -> str:
        """
        Определение возраста пользователя на основе даты рождения.
        Принимает строку с датой рождения bdate и возвращает строку с возрастом пользователя.
        """
        bdate_splited = bdate.split(".")
        month_dict = {
            "1": "января",
            "2": "февраля",
            "3": "марта",
            "4": "апреля",
            "5": "мая",
            "6": "июня",
            "7": "июля",
            "8": "августа",
            "9": "сентября",
            "10": "октября",
            "11": "ноября",
            "12": "декабря"
        }

        try:
            reverse_bdate = datetime.date(int(bdate_splited[2]), int(bdate_splited[1]), int(bdate_splited[0]))
            today = datetime.date.today()
            years = today.year - reverse_bdate.year

            if (reverse_bdate.month > today.month) or (reverse_bdate.month == today.month and reverse_bdate.day > today.day):
                years -= 1

            return self.naming_of_years(years, False)

        except IndexError:
            month = month_dict.get(bdate_splited[1])
            if month is not None:
                return f'День рождения {int(bdate_splited[0])} {month}.'
            else:
                return 'Некорректный формат даты рождения.'

    def get_age_of_user(self, user_id):
        """Определение возраста пользователя. Принимает идентификатор пользователя user_id."""
        global age_from, age_to
        try:
            info = self.vk_user_got_api.users.get(
                user_ids=user_id,
                fields="bdate",
            )[0]['bdate']
            num_age = self.get_years_of_person(info).split()[0]
            age_from = num_age
            age_to = num_age
            if num_age == "День":
                print(f'Ваш {self.get_years_of_person(info)}')
                self.send_msg(user_id,
                              f'   Бот ищет людей вашего возраста, но в ваших настройках профиля установлен пункт "Показывать только месяц и день рождения"! \n'
                              f'   Поэтому, введите возраст поиска, на пример от 21 года и до 35 лет, в формате : 21-35 (или 21 конкретный возраст 21 год).'
                              )
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        age = event.text
                        return self.input_looking_age(user_id, age)
            return print(f'Ищем пару в пределах Вашего возраста {self.naming_of_years(age_to)}')
        except KeyError:
            print(f'День рождения скрыт настройками приватности!')
            self.send_msg(user_id,
                          f' Бот ищет людей вашего возраста, но в ваших в настройках профиля установлен пункт "Не показывать дату рождения". '
                          f'\n Поэтому, введите возраст поиска, на пример от 21 года и до 35 лет, в формате : 21-35 (или 21 конкретный возраст 21 год).'
                          )
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    age = event.text
                    return self.input_looking_age(user_id, age)

    def get_target_city(self, user_id):
        """Определение города для поиска. Принимает идентификатор пользователя user_id
        функция не отправляет что город не найден, 
        логика поведения бота - анкеты закончелись (так как поиск анкет выдает 0), 
        предлогает изменить возраст поиска и город поиска"""
        global city_id, city_title
        city_id = None  # Инициализация переменной city_id
        city_title = None  # Инициализация переменной city_title
        self.send_msg(user_id, 'Введите "Да" - поиск будет произведен в городе указанном в профиле,'
                              ' или введите название города, например: Москва')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                answer = event.text.lower()
                if answer == "да" or answer == "y":
                    info = self.vk_user_got_api.users.get(user_id=user_id, fields="city")
                    city = info[0].get('city')
                    if city:
                        city_id = city["id"]
                        city_title = city["title"]
                        return f'в городе {city_title}.'
                    else:
                        return 'Город не указан в вашем профиле. Введите название города вручную.'
                else:
                    cities = self.vk_user_got_api.database.getCities(country_id=1, q=answer.capitalize(), need_all=1, count=1000)['items']
                    matched_cities = [c for c in cities if c["title"] == answer.capitalize()]
                    if matched_cities:
                        city_id = matched_cities[0]["id"]
                        city_title = answer.capitalize()
                        return f'в городе {city_title}.'
                    else:
                        return 'Город не найден. Введите корректное название города.'

        if city_id is None or city_title is None:
            return 'Город не найден. Введите корректное название города.'

    def looking_for_gender(self, user_id):
        """Определение противоположного пола для пользователя. Принимает идентификатор пользователя user_id"""
        info = self.vk_user_got_api.users.get(user_id=user_id, fields="sex")
        user_sex = info[0].get('sex')
        
        if user_sex == 1:  # 1 — женщина, 2 — мужчина
            self.send_msg(user_id, "Ваш пол - женский. Будем искать мужчин.")
            return 2
        elif user_sex == 2:
            self.send_msg(user_id, "Ваш пол - мужской. Будем искать женщин.")
            return 1
        else:
            self.send_msg(user_id, "Информация о вашем поле недоступна или неопределена. "
                                   "Введите пол, который вы хотите найти (1 - женщины, 2 - мужчины):")
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    gender = event.text.lower()
                    if gender in ['1', 'ж', 'жен', 'женщины', 'женский']:
                        self.send_msg(user_id, "Будем искать мужчин.")
                        return 2
                    elif gender in ['2', 'м', 'муж', 'мужчины', 'мужской']:
                        self.send_msg(user_id, "Будем искать женщин.")
                        return 1
                    else:
                        self.send_msg(user_id, "Некорректный ввод. Пожалуйста, укажите пол, который вы хотите найти "
                                               "(1 - женщины, 2 - мужчины):")

    def looking_for_persons(self, user_id):
        """Поиск людей на основе полученных данных. Принимает идентификатор пользователя user_id"""
        global list_found_persons
        list_found_persons = []
        res = self.vk_user_got_api.users.search(
            sort=0, # 1 — по дате регистрации, 0 — по популярности.
            city=city_id,
            hometown=city_title,
            sex=self.looking_for_gender(user_id),   # 1— женщина, 2 — мужчина, 0 — любой (по умолчанию).
            status=1,   # 1 — не женат или не замужем, 6 — в активном поиске.
            age_from=int(age_from) - 3, # Минимальное расхождение в возрасте -3
            age_to=int(age_to) + 3, # максимальное расхождение в возрасте +3
            has_photo=1,    # 1 — искать только пользователей с фотографией, 0 — искать по всем пользователям
            count=1000,
            fields="can_write_private_message, "  # Информация о том, может ли текущий пользователь отправить личное сообщение. Возможные значения: 1 — может; 0 — не может.
                   "city, "  # Информация о городе, указанном на странице пользователя в разделе «Контакты».
                   "domain, "  # Короткий адрес страницы.
                   "home_town, "  # Название родного города.
        )
        number = 0
        for person in res["items"]:
            if not person["is_closed"] and "city" in person and person["city"]["id"] == city_id and person["city"]["title"] == city_title:
                number += 1
                id_vk = person["id"]
                list_found_persons.append(id_vk)
        print(f"Бот нашел {number} открытые профили для просмотра из {res['count']} в городе {city_title}")

    def photo_of_found_person(self, user_id):
        """Получение фотографии найденного человека. Принимает идентификатор пользователя user_id"""
        res = self.vk_user_got_api.photos.get(
            owner_id=user_id,
            album_id="profile", # wall — фотографии со стены, profile — фотографии профиля.
            extended=1, # 1 — будут возвращены дополнительные поля likes, comments, tags, can_comment, reposts. По умолчанию: 0.
            count=30
        )
        photos_dict = {}
        for photo in res['items']:
            photo_id = str(photo["id"])
            likes = photo["likes"]["count"]
            # i_comments = i["comments"]
            photos_dict[likes] = photo_id
        sorted_photos = sorted(photos_dict.items(), reverse=True)
        photo_ids = [photo[1] for photo in sorted_photos]
        attachments = []
        try:
            attachments.append('photo{}_{}'.format(user_id, photo_ids[0]))
            attachments.append('photo{}_{}'.format(user_id, photo_ids[1]))
            attachments.append('photo{}_{}'.format(user_id, photo_ids[2]))
            return attachments
        except IndexError:
            try:
                attachments.append('photo{}_{}'.format(user_id, photo_ids[0]))
                return attachments
            except IndexError:
                return []

    def get_found_person_id(self):
        """Получение уникального идентификатора найденного человека"""
        seen_person = [int(i[0]) for i in check()]  # Выбираем из БД просмотренные анкеты.
        if not seen_person:
            if list_found_persons:
                unique_person_id = list_found_persons[0]
                return unique_person_id
            else:
                return 0
        else:
            for person_id in list_found_persons:
                if person_id not in seen_person:
                    unique_person_id = person_id
                    return unique_person_id
            return 0

    def found_person_info(self, show_person_id):
        """Метод возвращает информацию о найденном пользователе на основе его идентификатора show_person_id"""
        res = self.vk_user_got_api.users.get(
            user_ids=show_person_id,
            fields="about, activities, bdate, status, can_write_private_message, city, common_count, contacts, "
                   "domain, home_town, interests, movies, music, occupation"
        )
        user_info = res[0]

        first_name = user_info.get("first_name", "")
        last_name = user_info.get("last_name", "")
        age = self.get_years_of_person(user_info.get("bdate", ""))
        vk_link = 'vk.com/' + user_info.get("domain", "")
        city = user_info.get("city", {}).get("title") or user_info.get("home_town") or ""

        info_string = f'{first_name} {last_name}, {age}, {city}. {vk_link}'
        print (info_string)
        return info_string

    def send_photo(self, user_id, message, attachments):
        """Принимает идентификатор пользователя user_id, сообщение message и список вложений attachments,
        которые являются ссылками на фотографии, далее отправляет сообщение с фотографиями указанному пользователю"""
        if not user_id or not message or not attachments:
            return False

        if not attachments:
            print("Отсутствуют фотографии для отправки.")
            return False

        self.vk_group_got_api.messages.send(
            user_id=user_id,
            message=message,
            random_id=randrange(10 ** 7),
            attachment=",".join(attachments)
        )
        return True

    def get_search_age_from_input(self, user_id):
        """Получение возраста для поиска из введенного пользователем сообщения. Принимает идентификатор пользователя user_id"""
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                age = event.text
                if "-" in age:
                    ages = age.split("-")
                    age_from = ages[0].strip()
                    age_to = ages[1].strip()
                    if age_from.isdigit() and age_to.isdigit():
                        return age_from, age_to
                    else:
                        self.send_msg(user_id, "Некорректный ввод. Пожалуйста, введите возраст в формате: 21-35 (или 21 для конкретного возраста).")
                elif age.isdigit():
                    return age, age
                else:
                    self.send_msg(user_id, "Некорректный ввод. Пожалуйста, введите возраст в формате: 21-35 (или 21 для конкретного возраста).")

    def show_found_person(self, user_id):
        """Метод отображает информацию о найденном пользователе и отправляет его фотографии пользователю ВКонтакте.
        Если в базе данных нет найденных пользователей, метод отправляет сообщение с просьбой указать критерии поиска (возраст, город).
        Затем метод ожидает ввода возраста и выполняет новый поиск пользователей на основе указанных критериев.
        Если найден пользователь, метод выводит его информацию и отправляет фотографии пользователю."""
        found_person_id = self.get_found_person_id()
        if not found_person_id:
            self.send_msg(user_id,
                          'Все анкеты ранее были просмотрены. Будет выполнен новый поиск. '
                          'Измените критерии поиска (возраст, город). '
                          'Введите возраст поиска, например, от 21 года до 35 лет '
                          'в формате: 21-35 (или 21 для конкретного возраста).')
            
            age = self.get_search_age_from_input(user_id)
            if age is None:
                return

            self.get_target_city(user_id)
            self.looking_for_persons(user_id)
            self.show_found_person(user_id)
            return
        else:
            self.send_msg(user_id, self.found_person_info(found_person_id))
            photo_attachments = self.photo_of_found_person(found_person_id)
            if photo_attachments:
                self.send_photo(user_id, 'Фото с максимальными лайками', photo_attachments)
            else:
                print("Отсутствуют фотографии для отправки.")
            insert_data_viewed(found_person_id)

bot = Bot()