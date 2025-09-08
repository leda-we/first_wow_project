import socket
from tkinter import *

# import os
# from dotenv import load_dotenv
# from openai import OpenAI
# load_dotenv()

# LM_BASE_URL = os.getenv("LM_BASE_URL", "http://localhost:1234/v1")
# LM_MODEL = os.getenv("LM_MODEL", "lmstudio-community/llama-3.1-8b-instruct")
# LM_API_KEY = os.getenv("LM_API_KEY", "lm-studio")

# client = OpenAI(base_url=LM_BASE_URL, api_key=LM_API_KEY)

# def ai_reply(messages):
# 	response = client.chat.completions.create(
# 		model=LM_MODEL,
# 		messages=messages,
# 		temperature=0.7,
# 	)
# 	return response.choices[0].message.content.strip()
tk=Tk()

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

log = Text(tk)
nick = Entry(tk, textvariable=name)
nick.config(state='disabled')
msg = Entry(tk, textvariable=text)
msg.pack(side='bottom', fill='x', expand='true')
nick.pack(side='bottom', fill='x', expand='true')
log.pack(side='top', fill='both',expand='true')

def loopproc():
	log.see(END)
	s.setblocking(False)
	try:
		message = s.recv(128)
		message = message.decode('utf-8') 
		log.insert(END,message+'\n')
	except:
		tk.after(1,loopproc)
		return
	tk.after(1,loopproc)
	return

def sendproc(event):
    if event.keysym =='Return':
        message = name.get()+':'+text.get()
        message = message.encode('utf-8')
        sock.sendto (message,('255.255.255.255',11719))
        text.set('')
        return 'break'
    
# if __name__ == "__main__":
# 	print("Чат с ИИ (LM Studio). Напишите 'выход' для завершения.")
# 	dialog = [
# 		{"role": "system", "content": "Ты дружелюбный помощник и отвечаешь кратко на русском."}
# 	]
# 	while True:
# 		user_text = input("Вы: ").strip()
# 		if user_text.lower() in {"выход", "exit", "quit"}:
# 			print("Пока!")
# 			break
# 		dialog.append({"role": "user", "content": user_text})
# 		answer = ai_reply(dialog)
# 		print(f"ИИ: {answer}")
# 		dialog.append({"role": "assistant", "content": answer})

msg.bind('<KeyPress>',sendproc)   

msg.focus_set()

tk.after(1,loopproc)
tk.mainloop()
