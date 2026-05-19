import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from src.gui.main_window import LittleGreyGUI


class TestLittleGreyGUI:
    @pytest.fixture(autouse=True)
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.messages = []
        self.gui = LittleGreyGUI(on_send=lambda t: self.messages.append(t))
        yield
        self.gui.destroy()
        self.root.destroy()

    def test_init(self):
        assert self.gui.root is not None
        assert self.gui.title_label.cget('text') == 'LittleGrey'

    def test_add_user_message(self):
        self.gui.add_user_message('Hello')
        self.gui.chat_display.config(state=tk.NORMAL)
        content = self.gui.chat_display.get(1.0, tk.END)
        assert 'You: Hello' in content

    def test_add_agent_message(self):
        self.gui.add_agent_message('Hi there!')
        self.gui.chat_display.config(state=tk.NORMAL)
        content = self.gui.chat_display.get(1.0, tk.END)
        assert 'LittleGrey: Hi there!' in content

    def test_add_system_message(self):
        self.gui.add_system_message('System started')
        self.gui.chat_display.config(state=tk.NORMAL)
        content = self.gui.chat_display.get(1.0, tk.END)
        assert '[System started]' in content

    def test_set_status(self):
        self.gui.set_status('Thinking...')
        assert self.gui.status_label.cget('text') == 'Thinking...'

    def test_clear_chat(self):
        self.gui.add_user_message('Test')
        self.gui.clear_chat()
        self.gui.chat_display.config(state=tk.NORMAL)
        content = self.gui.chat_display.get(1.0, tk.END)
        assert content.strip() == ''

    def test_on_send_calls_callback(self):
        self.gui.input_var.set('Test message')
        self.gui._on_send()
        assert len(self.messages) == 1
        assert self.messages[0] == 'Test message'

    def test_on_send_empty_does_nothing(self):
        self.gui.input_var.set('')
        self.gui._on_send()
        assert len(self.messages) == 0

    def test_on_enter_triggers_send(self):
        self.gui.input_var.set('Enter test')
        self.gui._on_enter()
        assert len(self.messages) == 1
        assert self.messages[0] == 'Enter test'
