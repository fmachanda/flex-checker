#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import g4f
import os
import tkinter as tk
import threading
import time

os.chdir(os.path.dirname(os.path.realpath(__file__)))

DOC_ID = '1G6SP-A4Lfw_OzWx5oDHhGdPskTB9WkTl7tZRjHZQIsY'


window = tk.Tk()
window.geometry('400x400')
tk_text = tk.Label(window, text="", wraplength=350)
tk_text.pack()

text_content = ''
text_out = ''
flex = False
unpause = threading.Event()


def authenticate():
    credentials = service_account.Credentials.from_service_account_file(
        './credentials.json'
    )
    return build('docs', 'v1', credentials=credentials)


def get_text_from_google_doc():
    global text_out, text_content, flex
    text_out += 'Reading document...\n\n'
    print('Reading document')

    service = authenticate()

    try:
        document = service.documents().get(documentId=DOC_ID).execute()
        content = document.get('body', {}).get('content', [])
        
        for element in content:
            if 'paragraph' in element.keys():
                for pieces in element['paragraph']['elements']:
                    text: str = pieces['textRun']['content']
                    if not text.isspace():
                        text_content += text

        flex = 'flex' in text_content

        time.sleep(0.1)
        print("unpausing")
        unpause.set()

    except HttpError as e:
        print(f"Error retrieving document: {e}")
        return None
    

def get_response_from_g4f():
    global text_out

    print('waiting')
    unpause.wait()
    print('done waiting')

    try:
        text_out += 'Analyzing document... (Make sure Wifi is unblocked.)\n\n'
        print('Analyzing document')
        g4f.debug.logging = False
        g4f.check_version = False

        if flex:
            command = f"I am going to show you some text. \
                Read it and give me just the name of the schedule or the schedule number that will be used tomorrow. \
                Tell me what the document says about 'flex' students on a new line! \
                Then give a very brief (10 words or less) description about what the document is about. \
                Here is the text: {text_content}"
        else:
            command = f"I am going to show you some text. \
                Read it and give me just the name of the schedule or the schedule number that will be used tomorrow. \
                If any part of the text says something about a special schedule (not schedule I) or a \'homeroom schedule\', tell me exactly what it says about them on a new line! \
                Then give a very brief (10 words or less) description about what the document is about. \
                Here is the text: {text_content}"

        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": command}],
            stream=True,
        )

        for message in response:
            text_out += message

    except RuntimeError:
        pass


def update_text():
    global tk_text
    tk_text["text"] = text_out
    window.after(ms=200, func=update_text)


if __name__ == '__main__':

    os.system('clear')

    reader = threading.Thread(target=get_text_from_google_doc)
    reader.start()

    analyzer = threading.Thread(target=get_response_from_g4f)
    analyzer.start()

    print('\n\n')

    update_text()
    window.mainloop()
