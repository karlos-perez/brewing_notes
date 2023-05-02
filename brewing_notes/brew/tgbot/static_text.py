access_denied = '❌ Отказано в доступе '
welcome = 'Добро пожаловать, {name}'
not_active_link = 'Ссылка уже не активна ❌'

help_text = 'Доступные команды:\n'\
            '\n'\
            '/menu - Главное меню\n'\
            '/recipe - Мои рецепты\n'\
            '/device - Подключенные устройства\n'
# Main menu
main_menu_section = 'Главное меню'
back_main_menu = '« Главное меню'
next_action = 'Выберите действие'

# Management section
management_section = 'Дежурная'
management_back_section = '« Дежурная'
management_site = 'Сайт'
management_bot = 'Бот'
statistic_site = '<b>Статистика по сайту</b>\n'\
                 '--- --- ---\n'\
                 'Пользователи:\n'\
                 '<b>Всего:</b> {users_all}\n'\
                 '<b>Посещения за сутки:</b> {users_today}\n'\
                 '<b>Новые за сутки:</b> {new_users_today}\n'\
                 '\n'\
                 'Рецепты:\n'\
                 '<b>Всего:</b> {recipes_all}\n'\
                 '<b>Опубликовано:</b> {recipes_pub}\n'\
                 '<b>На модерации:</b> {recipes_mod}\n'\
                 '<b>Черновики:</b> {recipes_draft}\n'\
                 '<b>Новые за сутки:</b> {recipes_today}\n'
statistic_bot = '<b>Статистика по Телеграму</b>\n'\
                '--- --- ---\n' \
                '<b>Всего Пользователей:</b> {users_all}\n'\
                '<b>Из них Модераторов:</b> {users_mod}\n'
today_users = '\n<b>Посещения за сутки:</b>\n'
new_today_users = '\n<b>Новые пользователи за сегодня:</b>\n'
today_recipes = '\n<b>Рецепты за сегодня:</b>\n'



# Device section
devices_section = 'Телеметрическая'
devices_back_section = '« Телеметрическая'
device_list = 'Мои подключенные устройства'
device_data = 'Последнии 10 данных'
device_not_found = 'Устройство не найдено или не активно'
device_none = 'Нет подключенных устройств'
device_error_chart = 'Не найдены данные с устройства'
device_update_data = 'Обновить данные'
device_chart = 'График'
device_info = '<b>{name} ({type})</b>\n'\
              '<b>Токен:</b> {token}\n'\
              '<b>Всего данных:</b> {count}\n'
device_bpl_last_data = '<b>Последние данные:</b> {time}\n'\
                       '\n'\
                       '<b>Температура пива:</b> {beer_temp}\N{DEGREE SIGN}C\n'\
                       '<b>Температура холодильника:</b> {fridge_temp}\N{DEGREE SIGN}C\n'\
                       '<b>Температура помещения:</b> {root_temp}\N{DEGREE SIGN}C\n'\
                       '<b>Температура устройства:</b> {aux_temp}\N{DEGREE SIGN}C\n'\
                       '<b>Плотность:</b> {gravity}\N{DEGREE SIGN}P\n'\
                       '<b>Угол:</b> {tilt}\N{DEGREE SIGN}\n'\
                       '<b>Напряжение:</b> {volt}В\n'\
                       '<b>Давление:</b> {pressure}psi\n'
device_isp_last_data = '<b>Последние данные:</b> {time}\n'\
                       '\n'\
                       '<b>Температура устройства:</b> {aux_temp}\N{DEGREE SIGN}C\n'\
                       '<b>Плотность:</b> {gravity}\N{DEGREE SIGN}P\n'\
                       '<b>Угол:</b> {tilt}\N{DEGREE SIGN}\n'\
                       '<b>Напряжение:</b> {volt}В\n'\
                       '<b>Уровень сигнала wi-fi:</b> {rssi}dBm\n'
device_not_last_data = '<b>Последние данные:</b> Отсутствуют\n'
device_not_data = 'Данные отсутствуют\n'

device_data_10 = '<b>Последние данные</b>\n'\
                 '\n'

# Recipe section
recipes_section = 'Рецептурная'
recipes_back_section = '« Рецептурная'
recipe_list = 'Мои рецепты'
recipe_not_found = 'Рецепт не найден'
recipe_info = '<b>{name}</b>\n'\
              '\n'\
              '<u>Основные параметры</u>\n'\
              '<b>Стиль:</b> {style}\n'\
              '<b>Тип:</b> {type}\n'\
              '<b>Статус:</b> {status}\n'\
              '<b>Соответствие:</b> {сonformity}\n'\
              '\n'\
              '<u>По стилю</u>\n'\
              '<b>Плотность перед кипячением:</b> {pbg}\n'\
              '<b>Начальная плотность:</b> {og}\n'\
              '<b>Конечная плотность:</b> {fg}\n'\
              '<b>Уровень алкоголя:</b> {abv}%\n'\
              '<b>Горечь (IBU):</b> {ibu}\n'\
              '<b>Цвет (SRM):</b> {srm}\n'\
              '\n'\
              '<u>Объёмы</u>\n'\
              '<b>Размер партии:</b> {batch_size}л\n'\
              '<b>Вода на затор:</b> {mash_water}л\n'\
              '<b>Вода на промывку:</b> {sparge_water}л\n'\
              '<b>Объем на кипячение:</b> {pre_boil_size}л\n'\
              '<b>Осадок после кипячения:</b> {sediment_after_boil}л\n'\
              '<b>Объём стартера:</b> {starter_volume}л\n'\
              '<b>Объём на розлив:</b> {bottling_size}л\n'\
              '\n'\
              '<u>Остальные параметры</u>\n'\
              '<b>Время кипячения:</b> {boil_time}мин\n'\
              '<b>Эфф. затирания:</b> {efficiency_mash}%\n'\
              '\n'\
              '<a href="{url}">Прямая сслыка на рецепт</a>\n'
recipe_short_link = 'Прямая сслыка на рецепт'
recipe_ingredients = 'Список ингредиентов рецепта'
recipe_list_all_ingredients = 'Список ингредиентов рецепта\n'\
                              '<b>{name}</b>\n'\
                              '\n'

# Catalog section
catalog_section = 'Справочная'

# Message text action user
new_user_register = '❗ Зарегистрировался новый пользователь:\n'\
                    '<b>Логин:</b> {login}\n'\
                    '<b>E-mail:</b> {email}\n'\
                    '<b>ip-адрес:</b> {ip}'
new_user_сonfirmation = '❗ Новый пользователь подтвердил свою почту:\n'\
                        '<b>Логин:</b> {login}\n'\
                        '<b>E-mail:</b> {email}\n'\
                        '<b>ip-адрес:</b> {ip}'
user_deleted = '❗ Пользователь удалён:\n'\
               '<b>Логин:</b> {login}\n'\
               '<b>E-mail:</b> {email}'
user_banned = '❗ Пользователь <b>{mod}</b> забанил пользователя:\n'\
               '<b>Логин:</b> {login}\n'\
               '<b>E-mail:</b> {email}'
user_banned_trying_confirm = '🚫 Забанненый пытается восстановится:\n'\
                             '<b>Логин:</b> {login}\n'\
                             '<b>E-mail:</b> {email}\n'\
                             '<b>ip-адрес:</b> {ip}'
user_trial_activate = '✅ Пользователь <b>{user}</b> активировал пробный Премиум доступ.\n'\
                      'Пробный период до: <b>{date}</b>.'
user_trial_refusal = '❌ Пользователь <b>{user}</b> отказался от пробного Премиум доступа.'


recipe_add = '❗ Пользователь <b>{user}</b> создал рецепт:\n'\
             '<b>{name}</b> \n'\
             '<bСтиль:</b> {style}'
recipe_copy = '❗ Пользователь <b>{user}</b> скопировал себе рецепт:\n'\
              '<b>{name}</b>'
recipe_on_moderation = '❗ Пользователь <b>{user}</b> отправил рецепт на модерацию:\n'\
                       '<b>{name}</b>'
recipe_on_publication = '<b>Опубликован новый рецепт</b>\n'\
                        '<b>Автор:</b> {user}\n'\
                        '<b>Стиль:</b> {style}\n'\
                        '<b>Соответствие:</b> {conf}\n'\
                        '<a href="{url}"><b>{name}</b></a>'
send_message_user = '✉ Вам пришло личное сообщение\n' \
                    '<b>От</b> {user}:\n'\
                    '<b>Отправлено:</b> {time}\n'\
                    '<b>Тема:</b> {subject}\n'\
                    '<b>Сообщение:</b>\n'\
                    '{message}...'
publication_add = 'Пользователь <b>{user}</b> написал\n'\
                  'сообщение в теме <b>{topic}</b>:\n'\
                  '{post}'
feedback_message = '📧 Через форму обратной связи пришло сообщение:\n'\
                   'Имя отправителя: <b>{name}</b>\n'\
                   'E-mail отправителя: <b>{email}</b>\n'\
                   '<b>ip-адрес:</b> {ip}\n'\
                   'Сообщение:\n'\
                   '{body}'
