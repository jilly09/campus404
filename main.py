import telebot
from telebot import types
import config
import database
import random
import string
from fuzzywuzzy import fuzz
import time

bot = telebot.TeleBot(config.bot_token, parse_mode=None)

database.start()
pages = {}
data = {}

def randstr(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
	db = database.connect()
	res = db[1].execute("SELECT * FROM users WHERE tgid=?", (message.chat.id,))
	result = res.fetchall()
	if result == []:
		db[1].execute("INSERT INTO users (tgid, desc, name, reputation, interests, school) VALUES (?,?,?,?,?,?)", (message.chat.id, "", message.chat.first_name, 0, "", ""))
		db[0].commit()
		res = db[1].execute("SELECT * FROM users WHERE tgid=?", (message.chat.id,))
		result = res.fetchall()
	if result[0][2] != message.chat.first_name:
		db[1].execute("UPDATE users SET name=? WHERE tgid=?", (message.chat.first_name, message.chat.id))
		db[0].commit()
	if message.text == "/start" or message.text == "/menu":
		bot.send_message(message.chat.id, config.start_msg+"\n"+config.quick_start_msg)
	elif "/menu" not in message.text:
		if "g" not in message.text and "i" not in message.text:
			community = int(message.text.split()[1])
			db = database.connect()
			res = db[1].execute("SELECT * FROM communities WHERE id=?", (community,))
			result = res.fetchall()

			res2 = db[1].execute("SELECT * FROM members WHERE community=?", (community,))
			result2 = res2.fetchall()

			if result != []:
				bot.send_message(message.chat.id, f"**{result[0][2]}**\n\nОписание: {result[0][3]}\n\nШкола: {result[0][4]}\n\nСвязаться: {result[0][5]}", parse_mode="MARKDOWN")
				if result[0][1] == message.chat.id:
					membersstr = ""
					if result2 != []:
						for i in result2:
							res3 = db[1].execute("SELECT * FROM users WHERE tgid=?", (i[2],))
							result3 = res3.fetchone()
							membersstr+= f"\n[{result3[2]}](tg://user?id={result3[0]})"
					else:
						membersstr = "\nПока здесь пусто."
					bot.send_message(message.chat.id, "Участники:"+membersstr+f"\n[Снегерировать одноразовую ссылку-приглашение](https://t.me/campus404bot?start=g{result[0][0]})", parse_mode="MARKDOWN")
				else:
					ok = False
					for i in result2:
						if i[2] == message.chat.id:
							ok = True
							break
					if ok:
						membersstr = ""
						for i in result2:
							res3 = db[1].execute("SELECT * FROM users WHERE tgid=?", (i[2],))
							result3 = res3.fetchone()
							membersstr+= f"\n[{result3[2]}](tg://user?id={result3[0]})"
						bot.send_message(message.chat.id, "Участники:"+membersstr, parse_mode="MARKDOWN")

			db[1].close()
			db[0].close()

		elif "i" in message.text:
			secret = message.text.split()[1].replace("i_", "")
			db = database.connect()
			res3 = db[1].execute("SELECT * FROM links WHERE secret=?", (secret,))
			result3 = res3.fetchall()
			if result3 == []:
				return

			res = db[1].execute("SELECT * FROM communities WHERE id=?", (result3[0][2],))
			result = res.fetchall()
			res2 = db[1].execute("SELECT * FROM members WHERE community=? AND member_id=?", (result[0][0], message.chat.id))
			result2 = res2.fetchall()
			if result != [] and result2 == []:
				db[1].execute("INSERT INTO members (community, member_id) VALUES(?,?)", (result[0][0], message.chat.id))
				db[1].execute("DELETE FROM links WHERE secret=?", (secret,))
				db[0].commit()
				db[1].close()
				db[0].close()
				bot.send_message(message.chat.id, f"**{result[0][2]}**\n\nОписание: {result[0][3]}\n\nШкола: {result[0][4]}\n\nСвязаться: {result[0][5]}", parse_mode="MARKDOWN")
				bot.send_message(message.chat.id, "Ты был(а) добавлен(а) в сообщество")

		elif "g" in message.text:
			community = int(message.text.split()[1].replace("g", ""))
			db = database.connect()
			res = db[1].execute("SELECT * FROM communities WHERE id=?", (community,))
			result = res.fetchall()
			if result != [] and result[0][1] == message.chat.id:
				secret = randstr(15)
				db[1].execute("INSERT INTO links (secret, community) VALUES(?, ?)", (secret, community))
				db[0].commit()
				db[1].close()
				db[0].close()
				bot.send_message(message.chat.id, f"Отправь эту ссылку пользователю, которого хочешь пригласить.\nПомни, ссылка сработает только 1 раз.\n\nt.me/campus404bot?start=i_{secret}")


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, config.help_msg)

@bot.message_handler(commands=["communities"])
def communities(message):
	bot.send_message(message.chat.id, "Создать сообщество - /newcommunity")

	db = database.connect()
	res = db[1].execute("SELECT * FROM communities WHERE admin_id=?", (message.chat.id,))
	result = res.fetchall()
	if result != []:
		comstring = ""
		for i in result:
			comstring += f"\n[{i[2]}](https://t.me/campus404bot?start={i[0]})"
		bot.send_message(message.chat.id, "Созданные тобой сообщества: "+comstring, parse_mode="MARKDOWN")

	res2 = db[1].execute("SELECT * FROM members WHERE member_id=?", (message.chat.id,))
	result2 = res.fetchall()
	if result == [] and result2 == []:
		bot.send_message(message.chat.id, "Ты не состоишь не в одном из сообществ")
	elif result2 != []:
		comstring = ""
		for i in result2:
			res5 = db[1].execute("SELECT * FROM communities WHERE id=?", (i[1],))
			result5 = res.fetchall()
			comstring += f"\n[{result5[0][2]}](https://t.me/campus404bot?start={i[1]})"
		bot.send_message(message.chat.id, "Сообщества, в которых ты состоишь: "+comstring, parse_mode="MARKDOWN")

	db[1].close()
	db[0].close()

@bot.message_handler(commands=["findlm"])
def findlm(message):
	db = database.connect()
	res = db[1].execute("SELECT * FROM users WHERE tgid=?", (message.chat.id,))
	result = res.fetchone()
	if result[1] == "" or result[5] == "" or result[6] == "":
		pages[message.chat.id] = "addschool"
		data[message.chat.id] = {}

		markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
		item1=types.KeyboardButton("Отмена")
		markup.add(item1)
		bot.send_message(message.chat.id, "Отправь в чат официальное короткое название школы, в которой ты учишься.\nПример: СУНЦ МГУ", reply_markup=markup)
	else:
		users=[]
		result2 = db[1].execute("SELECT * FROM users").fetchall()
		for i in result2:
			if message.chat.id == i[0]:
				continue
			school_score = fuzz.WRatio(i[6], result[6])
			if school_score < 80:
				continue
			interests_score = fuzz.WRatio(i[5], result[5])
			desc_score = fuzz.WRatio(i[1], result[1])
			final_score = interests_score+desc_score+(i[3]*2)
			users.append([final_score, i])
		def sortfunc(a):
			return a[0]
		users.sort(key=sortfunc, reverse=True)
		count=0
		max = 5
		usersstring=""
		for i in users:
			usersstring+=f"\n\n[{i[1][2]}](tg://user?id={i[1][0]})\n{i[1][5]}\n{i[1][1]}\n{i[1][6]}\nРепутация:{i[1][3]}"
			count+=1
			if count == max:
				break
		if usersstring == "":
			usersstring = "Здесь пока пусто."
		bot.send_message(message.chat.id, usersstring, parse_mode="MARKDOWN")

@bot.message_handler(commands=["newcommunity"])
def newc(message):
	pages[message.chat.id] = "newcname"
	data[message.chat.id] = {}

	markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
	item1=types.KeyboardButton("Отмена")
	markup.add(item1)
	bot.send_message(message.chat.id, "Окей, отправь в чат название сообщества", reply_markup=markup)

@bot.message_handler(commands=["reputation"])
def reput(message):
	bot.send_message(message.chat.id, config.reput_msg, parse_mode="MARKDOWN")
	db = database.connect()
	res = db[1].execute("SELECT * FROM users WHERE tgid=?", (message.chat.id,))
	result = res.fetchone()
	bot.send_message(message.chat.id, f"Ваша репутация: {result[3]}")

@bot.message_handler(commands=["search"])
def search(message):
	pages[message.chat.id] = "search"
	data[message.chat.id] = {}

	markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
	item1=types.KeyboardButton("Отмена")
	markup.add(item1)
	bot.send_message(message.chat.id, "Окей, отправь в чат имя человека в Telegram.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def all(message):
	if message.text == "Отмена":
		data[message.chat.id] = {}
		pages[message.chat.id] = ""
		markup = types.ReplyKeyboardRemove(selective=False)
		bot.send_message(message.chat.id, "Отменено", reply_markup=markup)

	elif message.chat.id not in pages.keys() or pages[message.chat.id] == "":
		bot.send_message(message.chat.id, "Я не понял смысла этого сообщения.\nПерейти в меню - /menu")

	elif pages[message.chat.id] == "newcname":
		data[message.chat.id]["newcname"] = message.text
		pages[message.chat.id] = "newcdesc"

		markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
		item1=types.KeyboardButton("Отмена")
		markup.add(item1)
		bot.send_message(message.chat.id, "Отправь в чат описание сообщества", reply_markup=markup)

	elif pages[message.chat.id] == "newcdesc":
		data[message.chat.id]["newcdesc"] = message.text
		pages[message.chat.id] = "newccontact"

		markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
		item1=types.KeyboardButton("Отмена")
		markup.add(item1)
		bot.send_message(message.chat.id, "Отправь в чат ссылку или @username на основной ресурс сообщества (канал/группа/сайт)", reply_markup=markup)

	elif pages[message.chat.id] == "newccontact":
		data[message.chat.id]["newccontact"] = message.text
		pages[message.chat.id] = "newcschool"

		markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
		item1=types.KeyboardButton("Отмена")
		markup.add(item1)
		bot.send_message(message.chat.id, "Отправь в чат официальное короткое название школы, в которой будет сообщество.\nПример: СУНЦ МГУ", reply_markup=markup)

	elif pages[message.chat.id] == "newcschool":
		data[message.chat.id]["newcschool"] = message.text

		db = database.connect()
		db[1].execute("INSERT INTO communities (admin_id, title, desc, school, contacts) VALUES(?,?,?,?,?)",
			(message.chat.id, data[message.chat.id]["newcname"],
			data[message.chat.id]["newcdesc"], data[message.chat.id]["newcschool"],
			data[message.chat.id]["newccontact"])
		)
		db[0].commit()
		db[1].close()
		db[0].close()

		data[message.chat.id] = {}
		pages[message.chat.id] = ""
		markup = types.ReplyKeyboardRemove(selective=False)
		bot.send_message(message.chat.id, "Сообщество успешно создано!", reply_markup=markup)

	elif pages[message.chat.id] == "search":
		db = database.connect()
		res = db[1].execute("SELECT * FROM users")
		result = res.fetchall()

		users = []

		for i in result:
			if i[0] == message.chat.id:
				continue
			score = fuzz.WRatio(i[2], message.text)
			if score < 70:
				continue
			users.append([score, i])

		def sortfunc(a):
			return a[0]
		users.sort(key=sortfunc, reverse=True)
		print(users)
		count=0
		max = 20
		usersstring=""
		for i in users:
			usersstring+="\n"+str(count+1)+f") [{i[1][2]}](tg://user?id={i[1][0]})"
			count+=1
			if count == max:
				break
		data[message.chat.id]["search"] = users
		pages[message.chat.id] = "selectperson"

		markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
		item1=types.KeyboardButton("Отмена")
		markup.add(item1)
		bot.send_message(message.chat.id, "Результаты поиска:"+usersstring+"\n\nОтправь в чат номер нужного человека", parse_mode="MARKDOWN", reply_markup=markup)

	elif pages[message.chat.id] == "selectperson":
		person = []
		try:
			person = data[message.chat.id]["search"][int(message.text)-1]
			data[message.chat.id]["person"] = person
			pages[message.chat.id] = "selectreput"
			markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
			item1=types.KeyboardButton("Повысить репутацию на 1")
			item2=types.KeyboardButton("Понизить репутацию на 1")
			item3=types.KeyboardButton("Отмена")
			markup.add(item1)
			markup.add(item2)
			markup.add(item3)
			bot.send_message(message.chat.id, f"{person[1][2]}\nРепутация: {person[1][3]}", reply_markup=markup)
		except:
			bot.send_message(message.chat.id, "Некорректные данные")

	elif pages[message.chat.id] == "selectreput":
		db = database.connect()
		user = db[1].execute("SELECT * FROM users WHERE tgid=?", (message.chat.id,)).fetchone()
		person = data[message.chat.id]["person"]
		if user[4] == None or int(time.time()) - user[4] > 86400:
			if message.text == "Повысить репутацию на 1":
				db[1].execute("UPDATE users SET reputation=reputation+1 WHERE tgid=?", (person[1][0],))
				markup = types.ReplyKeyboardRemove(selective=False)
				bot.send_message(message.chat.id, "Репутация повышена!\nМеню - /menu", reply_markup=markup)

			elif message.text == "Понизить репутацию на 1":
				db[1].execute("UPDATE users SET reputation=reputation-1 WHERE tgid=?", (person[1][0],))
				markup = types.ReplyKeyboardRemove(selective=False)
				bot.send_message(message.chat.id, "Репутация понижена!\nМеню - /menu", reply_markup=markup)
			print("ok!")
			db[1].execute("UPDATE users SET last_reput=? WHERE tgid=?", (int(time.time()), message.chat.id,))
			db[0].commit()
			db[1].close()
			db[0].close()
		else:
			markup = types.ReplyKeyboardRemove(selective=False)
			bot.send_message(message.chat.id, f"Не так быстро!\nНужно подождать еще {(86400-(int(time.time()) - user[4])) // 3600} часов {(86400-(int(time.time()) - user[4])) % 3600 // 60} минут\nМеню - /menu", reply_markup=markup)

	elif pages[message.chat.id] == "addschool":
		db = database.connect()
		res = db[1].execute("UPDATE users SET school=? WHERE tgid=?", (message.text, message.chat.id,))
		db[0].commit()
		pages[message.chat.id] = "addinterests"

		markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
		item1=types.KeyboardButton("Отмена")
		markup.add(item1)
		bot.send_message(message.chat.id, "Отправь в чат 3-5 своих главных интересов через запятую.", reply_markup=markup)

	elif pages[message.chat.id] == "addinterests":
		db = database.connect()
		res = db[1].execute("UPDATE users SET interests=? WHERE tgid=?", (message.text, message.chat.id,))
		db[0].commit()
		pages[message.chat.id] = "adddesc"

		markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
		item1=types.KeyboardButton("Отмена")
		markup.add(item1)
		bot.send_message(message.chat.id, "Расскажи немного о себе. Не пиши слишком много, но и не слишком мало.\nПожалуйста, укажи свой @username или любой другой канал связи. Telegram жестко ограничивает ботов, и мы не можем делать это автоматически.", reply_markup=markup)

	elif pages[message.chat.id] == "adddesc":
		db = database.connect()
		res = db[1].execute("UPDATE users SET desc=? WHERE tgid=?", (message.text, message.chat.id,))
		db[0].commit()
		pages[message.chat.id] = ""

		markup = types.ReplyKeyboardRemove(selective=False)
		bot.send_message(message.chat.id, "Спасибо, мы учтем эти данные при подборе рекомендаций.\nНайти единомышленников - /findlm", reply_markup=markup)

bot.polling()
