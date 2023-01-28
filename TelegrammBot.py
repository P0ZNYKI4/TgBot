# cd D:\Python\Заказы\TgBot & D: & python TelegrammBot.py

import telebot
from telebot import types
from datetime import date
from Token import TOKEN
import os

bot = telebot.TeleBot(TOKEN)

# хранит id водителей, заполняющий незаконченный отчёт и их продвижение в заполнении этого отчета
not_ready_report: dict = dict() # {id: [пункт отчёта, [create_date, 1, 2, 3, 4, 5]]}

# хранит id водителей, заполняющий почти законченный отчёт и их продвижение в заполнении этого отчета
ready_report: dict = dict()  # {id: [пункт отчёта, [1, 2, 3, 4, 5, 6, 7, 8, 9]]}

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
	bot.send_message(
		message.chat.id,
		"Добро пожаловать, пожалуйста авторизуйтесь! /registration"
	)


@bot.message_handler(commands=['registration'])
def registration(message):

	markup = types.InlineKeyboardMarkup()

	director = types.InlineKeyboardButton("Руководитель", callback_data="start")
	driver = types.InlineKeyboardButton("Водитель", callback_data="driver_menu_open")

	markup.add(director, driver)

	bot.send_message(message.chat.id, "Авторизация", reply_markup=markup)



@bot.callback_query_handler(func=lambda call: True)
def callback(call):

	#global not_ready_report

	# кнопки
	if call.message:

		# переход в меню водителей
		if call.data == 'driver_menu_open':
			driver_menu(call.message, True)

		# открытие отчёта
		elif call.data == 'open_report':

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

		# записывается ответ на текущий вопрос

		# not_ready_report = {id: [пункт отчёта, [1, 2, 3, 4, 5]]}
		not_ready_report[message.chat.id][1][
			not_ready_report[message.chat.id][0]
		] = message.text

		not_ready_report[message.chat.id][0] += 1

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
	if message.chat.id in ready_report:

		# записывается ответ на текущий вопрос

		ready_report[message.chat.id][1][
			ready_report[message.chat.id][0]
		] = message.text

		ready_report[message.chat.id][0] += 1


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


def send_number_quest(bot, driver_id: int, quest_num: int):

	"""Отправляет текст пункта из отчёта, который сейчас будет заполнен"""

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


	def get_an_incomplete_report(self, driver_id: int) -> list | None:
		"""Получение инфы о не законченном отчёте"""
		with open("NotReadyReport.txt", "r") as f:

			lines = f.readlines()

			if lines != ["\n"]:
				for i in lines:
					i = eval(i)
					if i[0] == driver_id:
						return [6, i[1:] + [None, None, None, None]]
		return None


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

class DateManagement:

	def create_date_today(self) -> str:
		"""Текущая дата"""
		date_now = date.today()
		return f"{date_now.day}.{date_now.month}.{date_now.year}"


bot.infinity_polling(none_stop=True)

# cd D:\Python\Заказы\TgBot & D: & python TelegrammBot.py
