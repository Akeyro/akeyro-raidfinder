import tkinter as tk
import tkinter.scrolledtext as tkst
import threading
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import re
import pyperclip
import os
import sys

consumer_key = "TWITTER_CONSUMER_KEY"
consumer_secret = "TWITTER_CONSUMER_SECRET"
access_key = "TWITTER_ACCESS_KEY"
access_secret = "TWITTER_ACCESS_SECRET"
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
keywords = ["参加者募集！", ":参戦ID", "I need backup!", ":Battle ID"]
is_running = False

datafile = "icon.ico"
if not hasattr(sys, "frozen"):
    datafile = os.path.join(os.path.dirname(__file__), datafile)
else:
    datafile = os.path.join(sys.prefix, datafile)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class listener(StreamListener):
    def __init__(self, app):
        self.app = app
        self.gui = self.app.gui
        self.textbox = self.app.textbox
        super().__init__()

    def on_status(self, status):
        if is_running is False:
            return False
        source = 'グランブルー ファンタジー'
        if status.source == source:
            en_name = self.app.en_var.get().strip()
            jp_name = self.app.jp_var.get().strip()
            if en_name == "" or jp_name == "":
                return
            raid = RaidObject(status.text)
            if en_name in raid.name or jp_name in raid.name:
                self.textbox.config(state=tk.NORMAL)
                self.textbox.insert("1.0", f"{raid.name}\n{raid.id}\n")
                self.textbox.config(state=tk.DISABLED)
                if self.app.cb_copy.get():
                    pyperclip.copy(raid.id)

    def on_error(self, status_code):
        self.textbox.config(state=tk.NORMAL)
        self.textbox.insert("1.0", f"ERROR: CODE {status_code}\n")
        self.textbox.config(state=tk.DISABLED)
        if status_code == 420:
            # returning False in on_error disconnects the stream
            return False


class RaidObject:
    def __init__(self, text):
        self.id = re.search("(.*)([0-9A-F]{8})", text).group(2)
        self.name = text.split("\n")[2]


class GUI:
    def __init__(self, gui):
        self.gui = gui
        self.gui.protocol("WM_DELETE_WINDOW", self.close)
        self.thread = None
        self.en_var = tk.StringVar()
        self.jp_var = tk.StringVar()
        self.is_pinned = False

        # Frame for the english filter bar
        en_frame = tk.Frame(self.gui)
        en_label = tk.Label(en_frame, text='English raid name', font=('calibre', 10, 'bold'), anchor=tk.W, width=20)
        en_label.grid(row=0, column=0)
        self.en_entry = tk.Entry(en_frame, textvariable=self.en_var, width=25)
        self.en_entry.grid(row=0, column=1)
        en_frame.grid(row=0)

        # Frame for japanese filter bar
        jp_frame = tk.Frame(self.gui)
        jp_label = tk.Label(jp_frame, text='Japanese raid name', font=('calibre', 10, 'bold'), anchor=tk.W, width=20)
        jp_label.grid(row=1, column=0)
        self.jp_entry = tk.Entry(jp_frame, textvariable=self.jp_var, width=25)
        self.jp_entry.grid(row=1, column=1)
        jp_frame.grid(row=1)

        # Copy to clipboard checkbox
        self.cb_copy = tk.BooleanVar()
        clipboard_check = tk.Checkbutton(
            self.gui,
            text="Automatically copy raid ID to clipboard",
            variable=self.cb_copy,
            anchor=tk.W,
            width=42
        )
        clipboard_check.grid(row=2)

        # Buttons
        buttons_frame = tk.Frame(self.gui)
        start_button = tk.Button(buttons_frame, text="Start", command=self.start_stream)
        start_button.grid(row=0, column=0)
        stop_button = tk.Button(buttons_frame, text="Stop", command=self.stop_stream)
        stop_button.grid(row=0, column=1)
        clear_button = tk.Button(buttons_frame, text="Clear", command=self.clear_stream)
        clear_button.grid(row=0, column=2)
        self.pin_button = tk.Button(buttons_frame, text="Pin", command=self.pin_window)
        self.pin_button.grid(row=0, column=3)
        buttons_frame.grid(row=3)

        # Scrolling text
        self.textbox = tkst.ScrolledText(
            master=self.gui,
            wrap=tk.WORD,
            width=35,
            height=10
        )
        self.textbox.config(state=tk.DISABLED)
        self.textbox.grid(row=4)

        # Footer
        footer_frame = tk.Frame(self.gui)
        self.footer_txt = tk.Label(footer_frame, text="Raidfinder on standby...")
        self.footer_txt.grid(row=0, column=0, sticky="W")
        footer_frame.grid(row=5, sticky="W")

    def start_stream(self):
        global is_running
        if not is_running:
            is_running = True
            self.footer_txt['text'] = "Stream running"
            self.thread = threading.Thread(target=self._record)
            self.thread.start()

    def stop_stream(self):
        global is_running
        if is_running:
            is_running = False
            self.footer_txt['text'] = "Stream stopped"
            self.thread.join()

    def clear_stream(self):
        self.textbox.config(state=tk.NORMAL)
        self.textbox.delete('1.0', tk.END)
        self.textbox.config(state=tk.DISABLED)

    def pin_window(self):
        self.is_pinned = not self.is_pinned
        self.gui.attributes('-topmost', self.is_pinned)
        self.gui.update()
        if self.is_pinned:
            self.pin_button['relief'] = tk.SUNKEN
        else:
            self.pin_button['relief'] = tk.RAISED

    def close(self):
        global is_running
        if is_running:
            is_running = False
        self.gui.quit()

    def _record(self):
        global is_running

        twitterStream = Stream(auth, listener(self))
        twitterStream.filter(track=keywords)


main = tk.Tk()
main.title("Akeyro's Raidfinder")
main.iconbitmap(default=resource_path(datafile))
main.resizable(False, False)
MyGui = GUI(main)
main.mainloop()
