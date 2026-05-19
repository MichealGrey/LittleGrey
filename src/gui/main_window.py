import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Callable


class LittleGreyGUI:
    def __init__(self, on_send: Optional[Callable] = None):
        self.on_send = on_send
        self.root = tk.Tk()
        self.root.title('LittleGrey AI')
        self.root.geometry('800x600')
        self.root.minsize(600, 400)
        self._setup_styles()
        self._setup_layout()
        self._setup_widgets()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 14, 'bold'))
        style.configure('Status.TLabel', font=('Microsoft YaHei UI', 9), foreground='gray')
        style.configure('Send.TButton', font=('Microsoft YaHei UI', 10))

    def _setup_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(3, weight=1)

    def _setup_widgets(self):
        title_frame = ttk.Frame(self.root, padding='10')
        title_frame.grid(row=0, column=0, sticky='ew')
        title_frame.columnconfigure(0, weight=1)

        self.title_label = ttk.Label(title_frame, text='LittleGrey', style='Title.TLabel')
        self.title_label.grid(row=0, column=0, sticky='w')

        self.status_label = ttk.Label(title_frame, text='Ready', style='Status.TLabel')
        self.status_label.grid(row=0, column=1, sticky='e')

        self.chat_frame = ttk.Frame(self.root, padding='5')
        self.chat_frame.grid(row=1, column=0, sticky='nsew')
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(0, weight=1)

        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame, wrap=tk.WORD, state=tk.DISABLED,
            font=('Microsoft YaHei UI', 11), bg='#f5f5f5'
        )
        self.chat_display.grid(row=0, column=0, sticky='nsew')

        self.chat_display.tag_configure('user', justify='right', foreground='#1976D2')
        self.chat_display.tag_configure('agent', justify='left', foreground='#388E3C')
        self.chat_display.tag_configure('system', justify='center', foreground='#757575')

        separator = ttk.Separator(self.root, orient='horizontal')
        separator.grid(row=2, column=0, sticky='ew', pady=5)

        input_frame = ttk.Frame(self.root, padding='5')
        input_frame.grid(row=3, column=0, sticky='ew')
        input_frame.columnconfigure(0, weight=1)

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            input_frame, textvariable=self.input_var,
            font=('Microsoft YaHei UI', 11)
        )
        self.input_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.input_entry.bind('<Return>', self._on_enter)

        self.send_button = ttk.Button(
            input_frame, text='Send', command=self._on_send,
            style='Send.TButton'
        )
        self.send_button.grid(row=0, column=1)

    def _on_enter(self, event=None):
        self._on_send()
        return 'break'

    def _on_send(self):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set('')
        self.add_user_message(text)
        if self.on_send:
            self.status_label.config(text='Thinking...')
            self.root.update()
            self.on_send(text)
            self.status_label.config(text='Ready')

    def add_user_message(self, text: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f'You: {text}\n\n', 'user')
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def add_agent_message(self, text: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f'LittleGrey: {text}\n\n', 'agent')
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def add_system_message(self, text: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f'[{text}]\n\n', 'system')
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def set_status(self, text: str):
        self.status_label.config(text=text)

    def clear_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def run(self):
        self.root.mainloop()

    def destroy(self):
        self.root.destroy()


if __name__ == '__main__':
    def dummy_send(text):
        gui.add_agent_message(f'Echo: {text}')
    gui = LittleGreyGUI(on_send=dummy_send)
    gui.run()
