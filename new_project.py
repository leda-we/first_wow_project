import socket
from tkinter import *

import os
from dotenv import load_dotenv
from openai import OpenAI
import threading
import time
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import json


def search_internet(query, max_results=3):
	try:
		results = []
		# Иногда помогает задать таймаут и свежую версию пакета
		with DDGS(timeout=10) as ddgs:
			for r in ddgs.text(query, max_results=max_results, safesearch="moderate", region="wt-wt"):
				results.append({
					'title': r.get('title') or '',
					'body': r.get('body') or '',
					'url': r.get('href') or r.get('url') or ''
				})
		print(f"[web] Найдено результатов: {len(results)} по запросу: {query}")
		return results
	except Exception as e:
		print(f"[web] Ошибка поиска: {e}")
		return []

def search_local_database(query):
	try:
		if not os.path.exists('local_knowledge.json'):
			return []
		
		with open('local_knowledge.json', 'r', encoding='utf-8') as f:
			knowledge_base = json.load(f)
		
		query_words = query.lower().split()
		results = []

		for item in knowledge_base:
			title = item.get('title', '').lower()
			content = item.get('content', '').lower()

			matches = sum(1 for word in query_words if word in title or word in content)
			if matches > 0:
				results.append({
					'title': item.get('title', ''),
					'content': item.get('content', ''),
					'relevance': matches / len(query_words)
				})
		
		results.sort(key=lambda x: x['relevance'], reverse=True)
		return results[:3]

	except Exception as e:
		print(f'Ошибка в локальной базе: {e}')

def create_local_knowledge_base():
	sample_data = [
		{
            "title": "Python программирование",
            "content": "Python - это высокоуровневый язык программирования с простым синтаксисом. Подходит для веб-разработки, анализа данных, машинного обучения."
        },
        {
            "title": "Tkinter GUI",
            "content": "Tkinter - это стандартная библиотека Python для создания графических интерфейсов. Включает виджеты: Button, Entry, Text, Label."
        },
        {
            "title": "Сокеты в Python",
            "content": "Сокеты позволяют программам общаться по сети. UDP сокеты используются для быстрой передачи данных без гарантии доставки."
        }
	]
	with open('local_knowledge.json', 'w', encoding='utf-8') as f:
		json.dump(sample_data, f, ensure_ascii = False, indent = 2)
	print('Создана локальная база знаний с примерами')

def add_to_knowledge_base(title, content):
	try:
		if os.path.exists('local_knowledge.json'):
			with open('local_knowledge.json', 'r', encoding='utf-8') as f:
				knowledge_base = json.load(f)
		else:
			knowledge_base = []
		
		knowledge_base.append({
			'title': title,
			'content': content,
		})

		with open('local_knowledge.json', 'r', encoding='utf-8') as f:
			json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

		print(f'Добавлено в базу знаний: {title}')
	
	except Exception as e:
		print(f'Ошибка добавлении в базу: {e}')



load_dotenv()

LM_BASE_URL = os.getenv("LM_BASE_URL", "http://localhost:1234/v1")
LM_MODEL = os.getenv("LM_MODEL", "lmstudio-community/llama-3.1-8b-instruct")
LM_API_KEY = os.getenv("LM_API_KEY", "lm-studio")

client = OpenAI(base_url=LM_BASE_URL, api_key=LM_API_KEY)
def test_lm_studio():
    try:
        response = client.chat.completions.create(
            model=LM_MODEL,
            messages=[{"role": "user", "content": "Привет"}],
            temperature=0.7,
        )
        print("LM Studio работает!")
        return True
    except Exception as e:
        print(f"Ошибка подключения к LM Studio: {e}")
        return False


if not test_lm_studio():
    print("Проверьте, что LM Studio запущен!")


def ai_reply(messages):
	response = client.chat.completions.create(
		model=LM_MODEL,
		messages=messages,
		temperature=0.7,
	)
	return response.choices[0].message.content.strip()
tk=Tk()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind(('0.0.0.0',11719))


needs_search = True


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)

text=StringVar()
name=StringVar()
name.set('You')
text.set('')
tk.title('EEEE')
tk.geometry('400x300')

if not os.path.exists('local_knowledge.json'):
	create_local_knowledge_base()

log = Text(tk)
nick = Entry(tk, textvariable=name)
nick.config(state='disabled')
msg = Entry(tk, textvariable=text)
msg.pack(side='bottom', fill='x', expand='true')
nick.pack(side='bottom', fill='x', expand='true')
log.pack(side='top', fill='both',expand='true')


def sendproc(event):
    if event.keysym == 'Return':
        user_text = text.get()
        user_message = name.get() + ':' + text.get()
        user_message_encoded = user_message.encode('utf-8')
        sock.sendto(user_message_encoded, ('255.255.255.255', 11719))
        
   
        log.insert(END, user_message + '\n')
        log.see(END)

        text.set('')

        threading.Thread(target=get_ai_response, args=(user_text,), daemon=True).start()
        
        return 'break'
    
def show_typing_indicator():
    dots = ""
    for i in range(3):
        dots += "."
        typing_text = f"Typing{dots}"
        log.insert(END, typing_text + '\n')
        log.see(END)
        time.sleep(1)

        log.delete("end-2l", "end-1l")

def get_ai_response(user_text):
    try:

        typing_thread = threading.Thread(target=show_typing_indicator, daemon=True)
        typing_thread.start()
        
        search_keywords = ['что такое', 'как работает', 'объясни', 'расскажи о', 'информация о', 'что значит']
        needs_search = any(keyword in user_text.lower() for keyword in search_keywords)

        context = ''

        if needs_search:
            # Сначала пробуем интернет
            internet_results = search_internet(user_text)
            
            if internet_results:
                context = "Информация из интернета:\n"
                for i, result in enumerate(internet_results, 1):
                    context += f"{i}. {result['title']}\n{result['body']}\n\n"
            else:
                # Если интернета нет, ищем в локальной базе
                local_results = search_local_database(user_text)
                if local_results:
                    context = "Информация из локальной базы:\n"
                    for i, result in enumerate(local_results, 1):
                        context += f"{i}. {result['title']}\n{result['content']}\n\n"

        messages = [
            {"role": "system", "content": "Ты дружелюбный помощник. Отвечай кратко на русском языке. Если есть дополнительная информация, используй её для ответа."},
            {"role": "user", "content": f'Вопрос: {user_text}\n\n{context}'} 
        ]
        
        print(f"Отправляю ИИ вопрос: '{user_text}'")
        
        answer = ai_reply(messages)
        
        log.delete("end-2c", END)
        
        ai_message = '\n' + f"ИИ: {answer}"
        log.insert(END, ai_message + '\n')
        log.see(END)
        
    except Exception as e:
        log.delete("end-2c", END)
        error_message = f"Ошибка ИИ: {str(e)}"
        log.insert(END, error_message + '\n')
        log.see(END)



msg.bind('<KeyPress>',sendproc)   

msg.focus_set()


tk.mainloop()
# python .\new_project.py