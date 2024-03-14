# Sourced from:
# https://github.com/codewithdev/Code-Snippets/blob/master/tkinter/tkHyperlinkManager.py
from tkinter import CURRENT


class HyperlinkManager:

    def __init__(self, text):

        self.text = text

        self.text.tag_config('hyper', foreground='blue4', underline=1)

        self.text.tag_bind('hyper', '<Enter>', self._enter)
        self.text.tag_bind('hyper', '<Leave>', self._leave)
        self.text.tag_bind('hyper', '<Button-1>', self._click)

        self.reset()

    def reset(self):
        self.links = {}

    def add(self, action):
        tag = 'hyper-%d' % len(self.links)
        self.links[tag] = action
        return 'hyper', tag

    def _enter(self, event):
        self.text.config(cursor='hand2')

    def _leave(self, event):
        self.text.config(cursor='')

    def _click(self, event):
        for tag in self.text.tag_names(CURRENT):
            if tag[:6] == 'hyper-':
                self.links[tag]()
                return
