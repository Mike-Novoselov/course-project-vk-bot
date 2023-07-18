from vk_api.longpoll import VkLongPoll, VkEventType
import datetime
import vk_api
from config import user_token, group_token
from random import randrange
from db import check, insert_data_viewed


class Bot:
    def __init__(self):
        print('Бот создан!')
        self.vk_user = vk_api.VkApi(token=user_token)  # Создаем переменную сессии, авторизованную личным токеном пользователя.
        self.vk_user_got_api = self.vk_user.get_api()  # # переменную сессии vk_user подключаем к api списку методов.
        self.vk_group = vk_api.VkApi(token=group_token)  # Создаем переменную сесии, авторизованную токеном сообщества.
        self.vk_group_got_api = self.vk_group.get_api()  # переменную сессии vk_group подключаем к api списку методов.
        self.longpoll = VkLongPoll(self.vk_group)  # переменную сессии vk_group_got_api подключаем к Long Poll API,
        self.age_from = None
        self.age_to = None
        self.city_id = None
        self.city_title = None
        self.list_found_persons = []        

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

    def get_user_info(self, user_id):
        """
        Получение информации о пользователе, включая имя, возраст, город и пол.
        Принимает идентификатор пользователя user_id.
        Возвращает словарь с информацией о пользователе или отправляет сообщение об ошибке.
        """
        try:
            user_info_list = self.vk_group_got_api.users.get(
                user_id=user_id,
                fields="bdate,sex,city",
            )
            user_info = user_info_list[0]
            name = user_info.get('first_name')
            bdate = user_info.get('bdate')
            sex = user_info.get('sex')
            city = user_info.get('city')

            if name is not None and bdate is not None and sex is not None and city is not None:
                return {
                    'name': name,
                    'bdate': bdate,
                    'sex': sex,
                    'city': city
                }
            else:
                error_message = "Ошибка: недостаточно данных о пользователе"
                self.send_msg(user_id, error_message)
        except KeyError:
            error_message = "Ошибка: пользователь не найден"
            self.send_msg(user_id, error_message)

    def process_user_data(self, user_id):
        """
        Обработка данных о пользователе, включая имя, возраст, город и пол.
        Принимает идентификатор пользователя user_id.
        Возвращает словарь с данными о пользователе или отправляет сообщение об ошибке.
        """
        user_info = self.get_user_info(user_id)
        
        if user_info:
            name = user_info.get('name')
            bdate = user_info.get('bdate')
            sex = user_info.get('sex')
            city = user_info.get('city')
            
            if name is None or bdate is None or sex is None or city is None:
                error_message = "Ошибка: недостаточно данных о пользователе"
                self.send_msg(user_id, error_message)
                return None
            
            return {
                'name': name,
                'bdate': bdate,
                'sex': sex,
                'city': city
            }
        else:
            error_message = "Ошибка: информация о пользователе не найдена"
            self.send_msg(user_id, error_message)
            return None


    def get_user_name(self, user_id):
        """
        Получение имени пользователя, который написал боту.
        Принимает идентификатор пользователя user_id.
        Возвращает имя пользователя или отправляет сообщение об ошибке.
        """
        try:
            user_data = self.process_user_data(user_id)
            
            if user_data:
                return user_data['name']
            else:
                error_message = "Ошибка: имя пользователя не найдено"
        except KeyError as e:
            error_message = f"Ошибка: {e}"
        
        self.send_msg(user_id, error_message)

    def get_age_of_user(self, user_id):
        """Определение возраста пользователя. Принимает идентификатор пользователя user_id."""
        
        user_data = self.process_user_data(user_id)
        
        if user_data:
            try:
                bdate = user_data['bdate']
                num_age = self.get_years_of_person(bdate).split()[0]
                self.age_from = num_age
                self.age_to = num_age
                
                if num_age == "День":
                    print(f'Ваш {self.get_years_of_person(bdate)}')
                    self.send_msg(user_id, f'   Бот ищет людей вашего возраста, но в ваших настройках профиля установлен пункт "Показывать только месяц и день рождения"! \n'
                                        f'   Поэтому, введите возраст поиска, например, от 21 года до 35 лет, в формате: 21-35 (или 21 конкретный возраст 21 год).')
                    for event in self.longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            age = event.text
                            return self.input_looking_age(user_id, age)
                
                return print(f'Ищем пару в пределах Вашего возраста {self.naming_of_years(self.age_to)}')
            except KeyError:
                raise ValueError("Ошибка: информация о дате рождения пользователя не найдена")
        else:
            raise ValueError("Ошибка: информация о пользователе не найдена")

    def get_target_city(self, user_id):
        """Определение города для поиска. Принимает идентификатор пользователя user_id."""
        self.city_id = None  # Инициализация атрибута city_id
        self.city_title = None  # Инициализация атрибута city_title
        
        user_data = self.process_user_data(user_id)
        
        if user_data:
            city = user_data['city']
            
            if city:
                self.city_id = city.get('id')
                self.city_title = city.get('title')
                self.send_msg(user_id, f'Вы указали город {self.city_title}. Хотите ли поискать анкеты в этом городе?')
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        answer = event.text.lower()
                        
                        if answer == "да" or answer == "y":
                            return f'в городе {self.city_title}.'
                        
                        else:
                            self.send_msg(user_id, 'Введите название города, например: Москва')
                            for event in self.longpoll.listen():
                                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                    answer = event.text
                                    cities = self.vk_user_got_api.database.getCities(country_id=1, q=answer.capitalize(), need_all=1, count=100)['items']
                                    matched_cities = [c for c in cities if c["title"] == answer.capitalize()]
                                    
                                    if matched_cities:
                                        self.city_id = matched_cities[0]["id"]
                                        self.city_title = answer.capitalize()
                                        self.send_msg(user_id, f'Вы указали город {self.city_title}. Хотите ли поискать анкеты в этом городе?')
                                        for event in self.longpoll.listen():
                                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                                answer = event.text.lower()
                                                
                                                if answer == "да" or answer == "y":
                                                    return f'в городе {self.city_title}.'
                                                
                                                else:
                                                    self.send_msg(user_id, 'Введите "Да" - чтобы поискать анкеты в этом городе, или введите название города, например: Москва')
                                                    for event in self.longpoll.listen():
                                                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                                            answer = event.text.lower()
                                                            
                                                            if answer == "да" or answer == "y":
                                                                return f'в городе {self.city_title}.'
                                                            
                                                            else:
                                                                cities = self.vk_user_got_api.database.getCities(country_id=1, q=answer.capitalize(), need_all=1, count=100)['items']
                                                                matched_cities = [c for c in cities if c["title"] == answer.capitalize()]
                                                                
                                                                if matched_cities:
                                                                    self.city_id = matched_cities[0]["id"]
                                                                    self.city_title = matched_cities[0]["title"]
                                                                    return f'в городе {self.city_title}.'
                                                                else:
                                                                    self.send_msg(user_id, 'Город не найден. Введите корректное название города.')
                                                                    return 'Город не найден. Введите корректное название города.'
            else:
                self.send_msg(user_id, 'Город не найден. Введите корректное название города.')
                return 'Город не найден. Введите корректное название города.'

    def looking_for_gender(self, user_id):
        """Определение противоположного пола для пользователя. Принимает идентификатор пользователя user_id"""
        user_data = self.process_user_data(user_id)
        
        if user_data:
            user_sex = user_data['sex']
            
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
        else:
            self.send_msg(user_id, "Информация о вас недоступна. Пожалуйста, обновите ваш профиль в социальной сети.")
            return None

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

#_________________________________________________________
    # def looking_for_persons(self, user_id):
    #     """Поиск людей на основе полученных данных. Принимает идентификатор пользователя user_id"""
    #     self.list_found_persons = []
    #     viewed_ids = set(check())  # Получение множества уже просмотренных анкет
    #     res = self.vk_user_got_api.users.search(
    #         sort=0,
    #         city=self.city_id,
    #         hometown=self.city_title,
    #         sex=self.looking_for_gender(user_id),
    #         status=1,
    #         age_from=int(self.age_from) - 3,
    #         age_to=int(self.age_to) + 3,
    #         has_photo=1,
    #         count=1000,
    #         fields="can_write_private_message,city,domain,home_town"
    #     )
    #     if "items" in res:
    #         number = 0
    #         for person in res["items"]:
    #             if not person["is_closed"] and "city" in person and person["city"].get("id") == self.city_id and person["city"].get("title") == self.city_title:
    #                 number += 1
    #                 id_vk = person["id"]
    #                 if id_vk not in viewed_ids:
    #                     self.list_found_persons.append(id_vk)
    #     else:
    #         print("Ошибка при получении данных от API")

    #     if self.list_found_persons:
    #         first_person_id = self.list_found_persons[0]
    #         self.send_person_profile(user_id, first_person_id)  # Отправка профиля анкеты пользователю

    #     print(f"Бот нашел {number} открытых профилей для просмотра в городе {self.city_title}")
    


    # def send_person_profile(self, user_id, person_id):
    #     """Отправка профиля найденной анкеты пользователю.
    #     Принимает идентификатор пользователя user_id и идентификатор анкеты person_id."""
    #     try:
    #         person_info = self.get_user_info(person_id)
            
    #         name = person_info.get('name')
    #         bdate = person_info.get('bdate')
    #         sex = person_info.get('sex')
    #         city = person_info.get('city')
            
    #         profile_message = f"Имя: {name}\n" \
    #                           f"Дата рождения: {bdate}\n" \
    #                           f"Пол: {sex}\n" \
    #                           f"Город: {city}"
            
    #         self.send_msg(user_id, profile_message)
    #         insert_data_viewed(person_id)  # Добавление идентификатора просмотренной анкеты в базу данных
            
    #     except Exception as e:
    #         error_message = f"Ошибка при отправке профиля анкеты: {e}"
    #         self.send_msg(user_id, error_message)

#_________________________________________________________





    def looking_for_persons(self, user_id):
        """Поиск людей на основе полученных данных. Принимает идентификатор пользователя user_id"""
        self.list_found_persons = []
        res = self.vk_user_got_api.users.search(
            sort=0,  # 1 — по дате регистрации, 0 — по популярности.
            city=self.city_id,
            hometown=self.city_title,
            sex=self.looking_for_gender(user_id),  # 1— женщина, 2 — мужчина, 0 — любой (по умолчанию).
            status=1,  # 1 — не женат или не замужем, 6 — в активном поиске.
            age_from=int(self.age_from) - 3,  # Минимальное расхождение в возрасте -3
            age_to=int(self.age_to) + 3,  # максимальное расхождение в возрасте +3
            has_photo=1,  # 1 — искать только пользователей с фотографией, 0 — искать по всем пользователям
            count=100,
            fields="can_write_private_message, "  # Информация о том, может ли текущий пользователь отправить личное сообщение. Возможные значения: 1 — может; 0 — не может.
                   "city, "  # Информация о городе, указанном на странице пользователя в разделе «Контакты».
                   "domain, "  # Короткий адрес страницы.
                   "home_town, "  # Название родного города.
        )
        if "items" in res:
            number = 0
            for person in res["items"]:
                if not person["is_closed"] and "city" in person and person["city"].get("id") == self.city_id and person["city"].get("title") == self.city_title:
                    number += 1
                    id_vk = person["id"]
                    self.list_found_persons.append(id_vk)
            print(f"Бот нашел {number} открытые профили для просмотра из {res['count']} в городе {self.city_title}")
        else:
            print("Ошибка при получении данных от API")

    def photo_of_found_person(self, user_id):
        """Получение фотографии найденного человека. Принимает идентификатор пользователя user_id"""
        res = self.vk_user_got_api.photos.get(
            owner_id=user_id,
            album_id="profile",  # wall — фотографии со стены, profile — фотографии профиля.
            extended=1,  # 1 — будут возвращены дополнительные поля likes, comments, tags, can_comment, reposts. По умолчанию: 0.
            count=30
        )
        photos_dict = {}
        for photo in res.get('items', []):
            photo_id = str(photo.get("id"))
            likes = photo.get("likes", {}).get("count")
            if likes is not None:
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
            if self.list_found_persons:
                unique_person_id = self.list_found_persons[0]
                return unique_person_id
            else:
                return 0
        else:
            for person_id in self.list_found_persons:
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
        if res:
            user_info = res[0]

            first_name = user_info.get("first_name", "")
            last_name = user_info.get("last_name", "")
            age = self.get_years_of_person(user_info.get("bdate", ""))
            vk_link = 'vk.com/' + user_info.get("domain", "")
            city = user_info.get("city", {}).get("title") or user_info.get("home_town") or ""

            info_string = f'{first_name} {last_name}, {age}, {city}. {vk_link}'
            print(info_string)
            return info_string
        else:
            print("Ошибка при получении информации о пользователе")
            return ""

    def send_photo(self, user_id, message, attachments):
        """Принимает идентификатор пользователя user_id, сообщение message и список вложений attachments,
        которые являются ссылками на фотографии, далее отправляет сообщение с фотографиями указанному пользователю"""
        if not user_id or not message or not attachments:
            return False

        if not attachments:
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
                return
            insert_data_viewed(found_person_id)

bot = Bot()
