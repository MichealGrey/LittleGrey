import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional, Callable
import json

from performance.parser import PerformanceParser
from performance.executor import PerformanceExecutor
from performance.enums import ExpressionType


class LittleGreyPerformanceGUI:
    def __init__(self, on_send: Optional[Callable] = None):
        self.on_send = on_send
        self.performance_parser = PerformanceParser()
        self.performance_executor = PerformanceExecutor()

        self.root = tk.Tk()
        self.root.title('LittleGrey AI - 多模态演出系统')
        self.root.geometry('1000x700')
        self.root.minsize(800, 500)

        self._setup_styles()
        self._setup_layout()
        self._setup_widgets()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 14, 'bold'))
        style.configure('Status.TLabel', font=('Microsoft YaHei UI', 9), foreground='gray')
        style.configure('Send.TButton', font=('Microsoft YaHei UI', 10))
        style.configure('Info.TLabel', font=('Microsoft YaHei UI', 9))
        style.configure('Expression.TLabel', font=('Microsoft YaHei UI', 11, 'bold'))

    def _setup_layout(self):
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(3, weight=1)

    def _setup_widgets(self):
        title_frame = ttk.Frame(self.root, padding='10')
        title_frame.grid(row=0, column=0, columnspan=2, sticky='ew')
        title_frame.columnconfigure(0, weight=1)

        self.title_label = ttk.Label(title_frame, text='LittleGrey AI', style='Title.TLabel')
        self.title_label.grid(row=0, column=0, sticky='w')

        self.status_label = ttk.Label(title_frame, text='Ready', style='Status.TLabel')
        self.status_label.grid(row=0, column=1, sticky='e')

        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        self.chat_frame = ttk.Frame(main_frame, padding='5')
        self.chat_frame.grid(row=0, column=0, sticky='nsew')
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

        perf_frame = ttk.LabelFrame(main_frame, text='演出状态', padding='10')
        perf_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        perf_frame.columnconfigure(0, weight=1)

        ttk.Label(perf_frame, text='当前表情:', style='Info.TLabel').grid(row=0, column=0, sticky='w', pady=2)
        self.expression_label = ttk.Label(perf_frame, text='neutral', style='Expression.TLabel')
        self.expression_label.grid(row=1, column=0, sticky='w', pady=2)

        ttk.Label(perf_frame, text='背景:', style='Info.TLabel').grid(row=2, column=0, sticky='w', pady=(10, 2))
        self.background_label = ttk.Label(perf_frame, text='无', style='Info.TLabel')
        self.background_label.grid(row=3, column=0, sticky='w', pady=2)

        ttk.Label(perf_frame, text='角色:', style='Info.TLabel').grid(row=4, column=0, sticky='w', pady=(10, 2))
        self.character_label = ttk.Label(perf_frame, text='无', style='Info.TLabel')
        self.character_label.grid(row=5, column=0, sticky='w', pady=2)

        ttk.Label(perf_frame, text='演出日志:', style='Info.TLabel').grid(row=6, column=0, sticky='w', pady=(10, 2))
        self.perf_log = scrolledtext.ScrolledText(
            perf_frame, wrap=tk.WORD, state=tk.DISABLED,
            font=('Consolas', 8), height=10, bg='#263238', fg='#aed581'
        )
        self.perf_log.grid(row=7, column=0, sticky='nsew', pady=2)
        perf_frame.rowconfigure(7, weight=1)

        separator = ttk.Separator(self.root, orient='horizontal')
        separator.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)

        input_frame = ttk.Frame(self.root, padding='5')
        input_frame.grid(row=3, column=0, columnspan=2, sticky='ew')
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

        self.test_button = ttk.Button(
            input_frame, text='测试演出', command=self._test_performance
        )
        self.test_button.grid(row=0, column=2, padx=(5, 0))

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

    def _test_performance(self):
        test_text = '[expression:HAPPY intensity:0.8]你好呀！[animation:NOD]今天天气真好[scene bg:公园 char:小灰 transition:FADE][tts voice:female speed:1.1]欢迎使用 LittleGrey！[/tts]'
        self.add_agent_message(test_text)
        self._process_performance(test_text)

    def add_user_message(self, text: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f'You: {text}\n\n', 'user')
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def add_agent_message(self, text: str):
        clean_text = self.performance_parser.clean_text(text)
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f'LittleGrey: {clean_text}\n\n', 'agent')
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self._process_performance(text)

    def _process_performance(self, text: str):
        marks = self.performance_parser.parse_text(text)
        if marks:
            results = self.performance_executor.execute(marks)
            for result in results:
                self._log_performance(result)
            self._update_performance_display()

    def _log_performance(self, result: dict):
        self.perf_log.config(state=tk.NORMAL)
        log_text = f"[{result['type']}] {result['action']}\n"
        if result['type'] == 'expression':
            log_text += f"  表情: {result['expression']} (强度: {result['intensity']})\n"
        elif result['type'] == 'animation':
            log_text += f"  动画: {result['animation']} (目标: {result['target']})\n"
        elif result['type'] == 'scene':
            log_text += f"  背景: {result['background']}, 角色: {result['character']}\n"
        elif result['type'] == 'tts':
            log_text += f"  语音: {result['text']}\n"
        self.perf_log.insert(tk.END, log_text + '\n')
        self.perf_log.see(tk.END)
        self.perf_log.config(state=tk.DISABLED)

    def _update_performance_display(self):
        state = self.performance_executor.get_state()
        self.expression_label.config(text=state['current_expression'])
        self.background_label.config(text=state['current_background'] or '无')
        self.character_label.config(text=state['current_character'] or '无')

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
        self.performance_executor.reset_state()
        self._update_performance_display()
        self.perf_log.config(state=tk.NORMAL)
        self.perf_log.delete(1.0, tk.END)
        self.perf_log.config(state=tk.DISABLED)

    def run(self):
        self.root.mainloop()

    def destroy(self):
        self.root.destroy()


if __name__ == '__main__':
    def dummy_send(text):
        gui.add_agent_message(f'Echo: {text}')
    gui = LittleGreyPerformanceGUI(on_send=dummy_send)
    gui.add_system_message('点击"测试演出"按钮查看多模态演出效果')
    gui.run()
