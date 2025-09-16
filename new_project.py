import socket
from tkinter import *
import customtkinter as ctk
import os
from dotenv import load_dotenv
from openai import OpenAI
import threading
from ddgs import DDGS
import json

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')


dialog_history = [
	{"role": "system", "content": "Ты дружелюбный помощник и отвечаешь на русском. Держи нить разговора; если пользователь просит 'расскажи больше', продолжай тему последнего обсуждаемого объекта без смены темы."}
]
long_term_summary = ""  # краткая выжимка памяти
current_subject = ""    # текущая тема/объект
MAX_TURNS = 12          # сколько последних реплик держать в окне (user+assistant)
SUMMARY_EVERY = 6       # каждые N пользовательских сообщений обновлять выжимку
user_turns_count = 0
last_user_text = ""
last_ai_answer = ""
def search_internet(query, max_results=3):
    try:
        results = []
        with DDGS(timeout=10) as ddgs:
            for r in ddgs.text(query, max_results=max_results, safesearch="moderate", region="wt-wt"):
                results.append({
                    'title': r.get('title') or '',
                    'body': r.get('body') or '',
                    'url': r.get('href') or r.get('url') or ''
                })
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

		with open('local_knowledge.json', 'w', encoding='utf-8') as f:
			json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

		print(f'Добавлено в базу знаний: {title}')
	
	except Exception as e:
		print(f'Ошибка добавлении в базу: {e}')



load_dotenv()

LM_BASE_URL = os.getenv("LM_BASE_URL", "http://localhost:1234/v1")
LM_MODEL = os.getenv("LM_MODEL", "lmstudio-community/llama-3.1-8b-instruct")
LM_API_KEY = os.getenv("LM_API_KEY", "lm-studio")

client = OpenAI(base_url=LM_BASE_URL, api_key=LM_API_KEY)
def ai_reply(messages, temperature=0.5, top_p=0.9, max_tokens=256):
    try:
        response = client.chat.completions.create(
            model=LM_MODEL,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=False,
        )
        choice = response.choices[0]
        # OpenAI SDK returns either .message or .delta depending on stream
        content = getattr(choice.message, "content", None)
        if content is None and isinstance(choice, dict):
            content = choice.get("message", {}).get("content")
        return (content or "").strip()
    except Exception as e:
        return f"[Ошибка при обращении к модели: {e}]"
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
def on_add_to_knowledge():
    q = (last_user_text or "").strip()
    a = (last_user_text or "").strip()
    if not q or not a:
        log.insert(END, 'Нет данных для сохранения. Сначала задайте вопрос и дождитесь ответа.\n')
        log.see(END)
        return
    add_to_knowledge_base(title=q, content=a)
    log.insert(END, f'Сохранено в базу: {q[:40]}...\n')
    log.see(END)

if not test_lm_studio():
    print("Проверьте, что LM Studio запущен!")


tk = ctk.CTk()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind(('0.0.0.0',11719))




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


log = ctk.CTkTextbox(tk)
typing_var = StringVar(value="")
typing_label = ctk.CTkLabel(tk, textvariable=typing_var, anchor='w')
typing_label.pack(side='bottom', fill='x')
msg = ctk.CTkEntry(tk, textvariable=text)
msg.pack(side='bottom', fill='x', expand='true')
save_btn = ctk.CTkButton(tk, 
    text='Добавить в базу знаний', 
    command=on_add_to_knowledge,
    corner_radius=12,              # округление
    width=140,                     # компактная ширина
    height=32,                     # компактная высота
    fg_color="#2b8a3e",            # основной цвет (зелёный)
    hover_color="#237032",         # цвет наведения
    text_color="white")
save_btn.pack(side='bottom', padx = 10, pady = 6)
log.pack(side='top', fill='both',expand='true')
log.configure(height = 20)
msg.configure(height = 30)




def sendproc(event):
    
    if event.keysym == 'Return':
        global current_subject, last_user_text
        user_text = text.get()
        user_message = name.get() + ': ' + user_text
        sock.sendto(user_message.encode('utf-8'), ('255.255.255.255', 11719))
        if not user_text.strip():
            return 'break'
        last_user_text = user_text

        if len(user_text.strip()) >= 3:
            current_subject = user_text

        dialog_history.append({'role': 'user', 'content': user_text})
        if len(dialog_history) > 1 + MAX_TURNS*2:
            dialog_history[:] = dialog_history[:1] + dialog_history[-MAX_TURNS*2:]

        log.insert(END, user_message + '\n')
        log.see(END)
        text.set('')

        threading.Thread(target=get_ai_response, args=(user_text,), daemon=True).start()
        return 'break'

typing_running = False

def start_typing_indicator():
	global typing_running
	typing_running = True
	_typing_tick(0)

def _typing_tick(step):
	if not typing_running:
		return
	dots = "." * ((step % 3) + 1)
	typing_var.set(f"ИИ печатает{dots}")
	tk.after(500, lambda: _typing_tick(step + 1))

def stop_typing_only():
	global typing_running
	typing_running = False
	typing_var.set("")

def stop_typing_and_show(answer_text):
    global typing_running
    typing_running = False
    try:
        log.delete("end-2l", "end-1l")
    except:
        pass
    log.insert(END, "\n" )
    log.see(END)
# + f"ИИ: {answer_text}\n"
def stop_typing_and_show_error(e):
    global typing_running
    typing_running = False
    try:
        log.delete("end-2l", "end-1l")
    except:
        pass
    log.insert(END, f"Ошибка ИИ: {str(e)}\n")
    log.see(END)

def ai_reply_stream(messages, on_token):
    stream = client.chat.completions.create(
        model=LM_MODEL,
        messages=messages,
        temperature=0.5,
        top_p=0.9,
        max_tokens=256,
        stream=True,
    )
    for chunk in stream:
        choice = chunk.choices[0]
        delta = choice.delta
        content_piece = getattr(delta, "content", None)
        if content_piece is None and isinstance(delta, dict):
            content_piece = delta.get("content")
        if content_piece:
            on_token(content_piece)


def get_ai_response(user_text):
    try:
        global user_turns_count, long_term_summary  # ВАЖНО: вы их меняете

        # Запускаем индикатор печати в главном потоке
        tk.after(0, start_typing_indicator)
        tk.after(0, lambda: log.insert(END, "\nИИ: "))

        # Нужен ли веб-поиск
        search_keywords = ['что такое', 'как работает', 'объясни', 'расскажи о', 'расскажи про', 'информация о', 'что значит', 'кто такой']  # запятая добавлена
        needs_search = any(keyword in user_text.lower() for keyword in search_keywords)

        context = ''
        if needs_search:
            internet_results = search_internet(user_text)
            if internet_results:
                context = "Информация из интернета:\n"
                for i, result in enumerate(internet_results, 1):
                    url = result.get('url') or ''
                    context += f"{i}. {result['title']}\n{result['body']}\nИсточник: {url}\n\n"
            else:
                local_results = search_local_database(user_text)
                if local_results:
                    context = "Информация из локальной базы:\n"
                    for i, result in enumerate(local_results, 1):
                        context += f"{i}. {result['title']}\n{result['content']}\n\n"

        # “Расскажи больше” — продолжить текущую тему
        lt = user_text.lower()
        if any(kw in lt for kw in ["расскажи больше", "подробнее", "ещё", "еще", "больше информации"]) and current_subject:
            user_text = f'{user_text}\nПродолжай про: {current_subject}'

        # Сообщения для модели: системка с выжимкой + хвост диалога + новый вопрос
        system_with_memory = {
            "role": "system",
            "content": (
                "Ты дружелюбный помощник и отвечаешь на русском. "
                "Держи нить разговора и опирайся на выжимку памяти.\n\n"
                f"Память (summary): {long_term_summary[:2000]}"
            )
        }
        tail = [m for m in dialog_history[1:]][-MAX_TURNS*2:]
        messages = [system_with_memory] + tail + [{'role': 'user', 'content': f'Вопрос: {user_text}\n\n{context}'}]

        # ЕДИНСТВЕННЫЙ вызов модели
        # tk.after(0, lambda: log.insert(END, "\nИИ: "))

        collected = []

        def on_token(token):
            collected.append(token)
            # безопасно обновляем GUI
            tk.after(0, lambda: (log.insert(END, token), log.see(END)))

        ai_reply_stream(messages, on_token)

        answer = "".join(collected).strip()
        global last_ai_answer
        last_ai_answer = answer

        # убрать индикатор и дописать перевод строки
        tk.after(0, lambda: (
            stop_typing_and_show(""),  # остановить индикатор
            log.insert(END, "\n"),
            log.see(END)
        ))

        
        # Обновляем память
        dialog_history.append({'role': 'assistant', 'content': answer})
        user_turns_count += 1
        if user_turns_count % SUMMARY_EVERY == 0:
            try:
                summary_prompt = [
                    {"role": "system", "content": "Суммаризируй диалог кратко (факты, предпочтения, контекст), чтобы помочь продолжать разговор последовательно. Язык — русский."},
                    {"role": "user", "content":
                        f"Текущая выжимка:\n{long_term_summary}\n\nНовые реплики:\n" +
                        "\n".join(f"{m['role']}: {m['content']}" for m in dialog_history[-MAX_TURNS*2:])}
                ]
                new_summary = ai_reply(summary_prompt)
                long_term_summary = (long_term_summary + "\n" + new_summary).strip()
                if len(long_term_summary) > 4000:
                    long_term_summary = long_term_summary[-4000:]
            except Exception:
                pass

        # Остановить индикатор и показать ответ — ТОЛЬКО из главного потока
        tk.after(0, lambda: (stop_typing_only(), log.insert(END, "\n"), log.see(END)))

    except Exception as e:
        tk.after(0, lambda err=e: (stop_typing_only(), log.insert(END, f"Ошибка ИИ: {err}\n"), log.see(END)))



msg.bind('<Return>',sendproc)   

msg.focus_set()


tk.mainloop()
# python .\new_project.py