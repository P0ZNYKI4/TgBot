# cd D:\Python\Заказы\TgBot & D: & python TelegrammBot.py

# cd /home/poznyki4/Python/TgBot
# python3 TelegrammBot.py

import os
import re
import telebot
from telebot import types
from datetime import date
import pandas
from Token import TOKEN
#import psutil



"""
Установить
pip install openpyxl
pip install pyTelegramBotAPI
pip install pandas
pip install Jinja2
"""

bot = telebot.TeleBot(TOKEN)

# хранит id водителей, заполняющий незаконченный отчёт и их продвижение в заполнении этого отчета
not_ready_report: dict = dict() # {id: [пункт отчёта, [create_date, 1, 2, 3, 4, 5]]}

# хранит id водителей, заполняющий почти законченный отчёт и их продвижение в заполнении этого отчета
ready_report: dict = dict()  # {id: [пункт отчёта, [1, 2, 3, 4, 5, 6, 7, 8, 9]]}

# хранит id директора во время входа
director_id: set = set()

# получение отчёта {id: [0, time_1, time_2]}
receive_report: dict = dict()

"""
Отчёт

1. номер маршрутного листа
2. фио
3. гос номер
4. время начала
5. пробег авто

закрыть смену
6. время конец
7. пробег авто
8. заправки в литрах
9. всего рейсов


Хранение незаконченного отчёта
[chat.id, create_date, 1, 2, 3, 4]

Хранение законченного отчёта
[create_date, 1, 2, 3, 4, 5, 6, 7, 8, 9]
"""

# инициалазация файлов

if not os.path.exists("NotReadyReport.txt"):
	my_file = open("NotReadyReport.txt", "w+")
	my_file.close()


if not os.path.exists("Reports.txt"):
	my_file = open("Reports.txt", "w+")
	my_file.close()


@bot.message_handler(commands=['start'])
def start(message):

	if message.chat.id in director_id:
		director_id.remove(message.chat.id)

	bot.send_message(
		message.chat.id,
		f"Здравствуте, {message.from_user.first_name}, пожалуйста авторизуйтесь! /registration"
	)


@bot.message_handler(commands=['registration'])
def registration(message):

	if message.chat.id in director_id:
		director_id.remove(message.chat.id)

	markup = types.InlineKeyboardMarkup()

	director = types.InlineKeyboardButton("Руководитель", callback_data="director_input")
	driver = types.InlineKeyboardButton("Водитель", callback_data="driver_menu_open")

	markup.add(director, driver)

	bot.send_message(message.chat.id, "Авторизация", reply_markup=markup)



@bot.callback_query_handler(func=lambda call: True)
def callback(call):

	# кнопки
	if call.message:

		# переход в меню водителей
		if call.data == 'driver_menu_open':
			driver_menu(call.message, True)

		# открытие отчёта
		elif call.data == 'open_report':

			if call.message.chat.id in director_id:
				director_id.remove(call.message.chat.id)

			not_ready_report[call.message.chat.id] = [1,
				[DateManagement().create_date_today(), None, None, None, None, None]
			]
			send_number_quest(bot, call.message.chat.id, 1)

		# закрытие отчёта
		elif call.data == "close_report":

			FileManagemen().del_space("NotReadyReport.txt")

			report_now = FileManagemen().get_an_incomplete_report(call.message.chat.id)

			if not (report_now is None):
				ready_report[call.message.chat.id] = report_now

				send_number_quest(bot, call.message.chat.id, 6)

			else:
				bot.send_message(
					call.message.chat.id,
					"Ваш отчёт не найден, переход в главное меню"
				)
				driver_menu(call.message, True)

		# вход за руководителя
		elif call.data == "director_input":

			markup = types.InlineKeyboardMarkup()

			director_id.add(call.message.chat.id)

			bot.send_message(
				call.message.chat.id,
				"Введите пароль, или авторизуйтесь как водитель /registration",
				reply_markup=markup
			)

		# хранилище
		elif call.data == "storage":
			storage_menu(call.message)

		# память сервера
		elif call.data == "send_storage":
			send_storage(call.message)

		# регистрация
		elif call.data == "registration":
			registration(call.message)

		# вход за админа
		elif call.data == "AdminMenu":
			director_menu(call.message)

		# отправка файла exel
		elif call.data == "send_exel":

			receive_report[call.message.chat.id] = [0, None, None]

			send_range_date(call.message.chat.id, receive_report[call.message.chat.id][0])

		# удаление всех отчётов
		elif call.data == "del_repors_all":
			FileManagemen().del_repors_all()
			send_storage(call.message)

	

def driver_menu(message, open_report: bool):

	markup = types.InlineKeyboardMarkup()
	
	if open_report:
		button_1 = types.InlineKeyboardButton("🚛 Открыть смену 🚛", callback_data="open_report")
	else:
		button_1 = types.InlineKeyboardButton("🚛 Закрыть смену 🚛", callback_data="close_report")

	markup.add(button_1)

	bot.send_message(message.chat.id, "_____Меню_____", reply_markup=markup)


# прохождение отчёта
@bot.message_handler()
def filling_report(message):

	# незаполненный отчёт
	if message.chat.id in not_ready_report:

		if check_pattern(message.chat.id,
							not_ready_report[message.chat.id][0], message.text):

			not_ready_report[message.chat.id][1][
				not_ready_report[message.chat.id][0]
			] = message.text

			not_ready_report[message.chat.id][0] += 1
		else:
			bot.send_message(
				message.chat.id,
				"❌Проверьте шаблон ввода и введите еще раз"
			)

		if not_ready_report[message.chat.id][0] != 6:
			send_number_quest(
				bot,
				message.chat.id,
				not_ready_report[message.chat.id][0]
			)
		else:
			# создание не готового отчёта
			FileManagemen().create_not_ready_report(
				report_data=not_ready_report[message.chat.id][1],
				driver_id=[message.chat.id]
			)

			bot.send_message(
				message.chat.id,
				"📩 Отчёт сохранен в базе, когда закончите смену, нажмите на кнопку " +
				"\"Закрыть смену\" и заполните отчёт до конца. Аккуратнее за рулем!"
			)

			# удаление временных данных
			del not_ready_report[message.chat.id]

			driver_menu(message, False)

	# заполненный отчёт
	elif message.chat.id in ready_report:

		if check_pattern(message.chat.id,
							ready_report[message.chat.id][0], message.text):

			ready_report[message.chat.id][1][
				ready_report[message.chat.id][0]
			] = message.text

			ready_report[message.chat.id][0] += 1
		else:
			bot.send_message(
				message.chat.id,
				"❌Проверьте шаблон ввода и введите еще раз"
			)


		if ready_report[message.chat.id][0] != 10:
			send_number_quest(
				bot,
				message.chat.id,
				ready_report[message.chat.id][0]
			)
		else:
			
			# удаление незаконченного отчёта из файла
			FileManagemen().del_not_ready_report(message.chat.id)

			# создание готового отчёта
			FileManagemen().create_ready_report(
				report_data=ready_report[message.chat.id][1]
			)

			bot.send_message(message.chat.id,"📩 Отчёт сохранен в базе")

			# удаление временных данных
			del ready_report[message.chat.id]

			driver_menu(message, True)

	# получение данных о отчёте (exel)
	elif message.chat.id in receive_report:

		# корректность ввода
		if check_pattern(message.chat.id, -100, message.text):

			receive_report[message.chat.id][0] += 1

			receive_report[message.chat.id][receive_report[message.chat.id][0]] = message.text

			send_range_date(message.chat.id, receive_report[message.chat.id][0])
			
			if receive_report[message.chat.id][0] == 2:

				# отправка
				
				file_name = (
					receive_report[message.chat.id][1].replace(":", "-") + " - " +
					receive_report[message.chat.id][2].replace(":", "-")
				)

				FileManagemen().create_table(
					receive_report[message.chat.id][1],
					receive_report[message.chat.id][2],
					file_name
				)

				with open(f"{file_name}.xlsx", "rb") as f:
					bot.send_document(message.chat.id, f)

				os.remove(f"{file_name}.xlsx")

				del receive_report[message.chat.id]

				director_menu(message)
				

		else:
			send_number_quest(bot, message.chat.id, -1)
			send_range_date(message.chat.id, receive_report[message.chat.id][0])

	# регистрация директора
	elif message.chat.id in director_id:

		if message.text == "QQQQQ":
			bot.send_message(
				message.chat.id,
				"🧑‍💻"#"✅"
			)

			director_id.remove(message.chat.id)

			director_menu(message)
		else:
			bot.send_message(
				message.chat.id,
				"❌ Не верный пароль"
			)

	


def director_menu(message):
	"""Меню директора"""

	bot.delete_message(message.chat.id, message.message_id)

	markup = types.InlineKeyboardMarkup(row_width=2)
	
	button_1 = types.InlineKeyboardButton("Хранилище", callback_data="storage")
	button_2 = types.InlineKeyboardButton("Выйти из аккаунта", callback_data="registration")
	button_3 = types.InlineKeyboardButton("Получить отчёт", callback_data="send_exel")

	markup.add(button_1, button_2, button_3)

	bot.send_message(message.chat.id, "__AdminMenu__", reply_markup=markup)


def storage_menu(message, text="__Хранилище__"):
	"""Управление хранилищем"""

	bot.delete_message(message.chat.id, message.message_id)

	markup = types.InlineKeyboardMarkup(row_width=2)
	
	button_1 = types.InlineKeyboardButton("Памать сервера", callback_data="send_storage")
	button_2 = types.InlineKeyboardButton("Очистить память", callback_data="del_repors_all")
	button_3 = types.InlineKeyboardButton("⬅Назад", callback_data="AdminMenu")

	markup.add(button_1, button_2, button_3)

	bot.send_message(message.chat.id, text, reply_markup=markup)


def send_number_quest(bot, driver_id: int, quest_num: int) -> None:

	"""Отправляет текст пункта из отчёта, который сейчас будет заполнен"""

	if quest_num == 1:
		bot.send_message(driver_id, "Номер маршрутного листа:")
	elif quest_num == 2:
		bot.send_message(driver_id, "(Фамилия И.О.):")
	elif quest_num == 3:
		bot.send_message(driver_id, "Гос. номер авто:")
	elif quest_num == 4:
		bot.send_message(driver_id, "⏱️Время начала смены (ЧЧ:ММ):")
	elif quest_num == 5 or quest_num == 7:
		bot.send_message(driver_id, "Введите текущий пробег автомобиля:")
	elif quest_num == 6:
		bot.send_message(driver_id, "⏱️Время конца смены (ЧЧ:ММ):")
	elif quest_num == 8:
		bot.send_message(driver_id, "Заправки: (Литров)")
	elif quest_num == 9:
		bot.send_message(driver_id, "Всего рейсов:")
	elif quest_num == -1:
		bot.send_message(
			driver_id,
			"❌Введенные Вами данные некорректные, посмотрите на " +
			"шаблон указанный в скобках и введите ещё раз."
		)



	"""
	match quest_num:
		case 1:
			bot.send_message(driver_id, "Номер маршрутного листа:")
		case 2:
			bot.send_message(driver_id, "(Фамилия И.О.):")
		case 3:
			bot.send_message(driver_id, "Гос. номер авто:")
		case 4:
			bot.send_message(driver_id, "⏱️Время начала смены (ЧЧ:ММ):")
		case 5 | 7:
			bot.send_message(driver_id, "Введите текущий пробег автомобиля:")
		case 6:
			bot.send_message(driver_id, "⏱️Время конца смены (ЧЧ:ММ):")
		case 8:
			bot.send_message(driver_id, "Заправки: (Литров)")
		case 9:
			bot.send_message(driver_id, "Всего рейсов:")
		case -1:
			bot.send_message(
				driver_id,
				"❌Введенные Вами данные некорректные, посмотрите на " +
				"шаблон указанный в скобках и введите ещё раз."
			)
	"""


def send_range_date(director_id: int, quest_num: int) -> None:
	"""Отправляет формат ввода данных"""

	if quest_num == 0:
		bot.send_message(
			director_id,
			"Введите дату в формате (ДД:ММ:ГГГГ)\nС которой будет заполняться таблица "
		)
	elif quest_num == 1:
		bot.send_message(
			director_id,
			"Введите дату в формате (ДД:ММ:ГГГГ)\nГде будет заканчиваться таблица "
		)



def send_storage(message) -> None:
	"""Отправляет сколько памаяти на сервере"""

	dick = round(100 - psutil.disk_usage("/home").percent, 1)
	memory = round(100 - psutil.virtual_memory().percent, 1)

	txt_new = (
		"__Хранилище__\n" +
		f"Свободное место на диске: {dick} %\n" +
		f"Свободное ОЗУ: {memory} %"
	)

	storage_menu(message, txt_new)

	#bot.edit_message_text(txt_new, chat_id=message.chat.id, message_id=message.id)

		
class FileManagemen:

	"""Класс управляет файловой системой"""

	def create_not_ready_report(self, report_data: list, driver_id: list) -> None:
		"""Создание незаконченного отчета"""
		with open("NotReadyReport.txt", "a") as f:
			f.write(f"{driver_id + report_data}\n")


	def create_ready_report(self, report_data: list) -> None:
		"""Создание законченного отчёта"""
		with open("Reports.txt", "a") as f:
			f.write(f"{report_data}\n")


	def get_an_incomplete_report(self, driver_id: int) -> list: # -> list | None:
		"""Получение инфы о не законченном отчёте"""
		with open("NotReadyReport.txt", "r") as f:

			lines = f.readlines()

			if lines != ["\n"]:
				for i in lines:
					i = eval(i)
					if i[0] == driver_id:
						return [6, i[1:] + [None, None, None, None]]
		return None


	def del_repors_all(self) -> None:
		"""Удаление всех отчётов"""
		with open("Reports.txt", "w") as f:
			...


	def check_id(self, driver_id: int) -> bool:
		"""Проверяет id в списке незаконченных отчетов"""
		with open("NotReadyReport.txt", "r") as f:
			lines = f.readlines()
			
		for i in lines:
			if int(i[0]) == driver_id:
				return True

		return False


	def del_space(self, file_dir: str) -> None:
		"""Удаление пустых строчек в файле"""
		with open(file_dir, "r") as f:
			lines = f.readlines()

		with open(file_dir,"w") as f:
			for i in lines:
				if i != "\n":
					f.write(i)


	def del_not_ready_report(self, driver_id: int) -> None:
		"""Удаляет незаконченный отчёт"""

		with open("NotReadyReport.txt", "r") as f:
			lines = f.readlines()

		with open("NotReadyReport.txt", "w") as f:

			for i in lines:

				if eval(i)[0] != driver_id:
					f.write(i)


	def create_table(self, start_time, end_time, file_name) -> None:
		"""Создает таблицу exel"""

		"""
		1. номер маршрутного листа
		2. фио
		3. гос номер
		4. время
		5. пробег авто

		закрыть смену
		6. время конец
		7. пробег авто
		8. заправки литры
		9. всего рейсов
		"""

		start_time = start_time.replace(":", " ", 3).split()
		end_time = end_time.replace(":", " ", 3).split()


		for i in range(3):
			start_time[i] = int(start_time[i])
			end_time[i] = int(end_time[i])

		# var
		start_day, start_month, start_year = start_time
		end_day, end_month, end_year = end_time

		data: dict = {
			"Дата": [],
			"Выезд": [],
			"Возвращение": [],
			"№ мар. листа": [],
			"Водитель": [],
			"Пробег в начале": [],
			"Пробег в конце": [],
			"Заправки (Л)": [],
			"Гос. номер": [],
			"Рейсов": [],
		}

		with open("Reports.txt", "r") as f:

			lines = f.readlines()

			"""
			[день.месяц.год, 1, 2, 3, 4, 5, 6, 7, 8, 9]
			"""

			for i in lines:

				i = eval(i)

				temp_date = i[0].replace(".", " ", 3).split()

				for j in range(3):
					temp_date[j] = int(temp_date[j])

				now_day, now_month, now_year = temp_date

				if (
					# день
					start_day <= now_day <= end_day and
					start_month <= now_month <= end_month and
					start_year <= now_year <= end_year
					):

					data["Дата"].append(i[0])
					data["Выезд"].append(i[4])
					data["Возвращение"].append(i[6])
					data["№ мар. листа"].append(i[1])
					data["Водитель"].append(i[2])
					data["Пробег в начале"].append(i[5])
					data["Пробег в конце"].append(i[7])
					data["Заправки (Л)"].append(i[8])
					data["Гос. номер"].append(i[3])
					data["Рейсов"].append(i[9])

		df = pandas.DataFrame(data)

		def align(data):
			return pandas.DataFrame('text-align: center', index=data.index, columns=data.columns)

		def valign(data):
			return pandas.DataFrame('horizontal-align: middle', index=data.index, columns=data.columns)

		df = df.style.apply(align, axis=None).apply(valign, axis=None)

		df.to_excel(f"{file_name}.xlsx")








class DateManagement:

	def create_date_today(self) -> str:
		"""Текущая дата"""
		date_now = date.today()
		return f"{date_now.day}.{date_now.month}.{date_now.year}"

def check_pattern(driver_id: int, quest_num: int, text: str) -> bool:
	"""Проверка корректности"""

	if quest_num in (4, 6):
		result = re.match(r"\d{2}:\d{2}", text)
		return True if not (result is None) else False

	# для даты руководителя
	elif quest_num == -100:
		result = re.match(r"\d{2}:\d{2}:\d{4}", text)
		return True if not (result is None) else False

	return True


bot.infinity_polling(none_stop=True)

# cd D:\Python\Заказы\TgBot & D: & python TelegrammBot.py
