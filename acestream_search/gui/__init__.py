# -*- coding: utf-8 -*-

import logging
import tkinter as tk
import threading

from acestream_search.common.constants import CATEGORIES
from acestream_search.log import logger, FORMAT
from acestream_search.events import get_events, get_events_table
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class TextHandler(logging.Handler):
    """Logging handler to redirect logs to Tkinter ScrolledText widget."""

    def __init__(self, text_widget: ScrolledText):
        super().__init__()
        self.text_widget = text_widget

    def format(self, record):
        formatter = logging.Formatter(FORMAT)
        return formatter.format(record)

    def emit(self, record):
        """Override emit method to insert logs into the ScrolledText widget."""

        msg = self.format(record)
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, msg + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)


class GuiApp():
    root = tk.Tk()
    root.title("Acestream Search - GUI")

    main_frame = ttk.Frame(root, padding="20")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    log_label = ttk.Label(main_frame, text="Console:")
    log_label.grid(row=0, column=0, sticky=tk.W)  # Place log label in row 0

    log_text = ScrolledText(
        main_frame, width=170, height=5, wrap=tk.WORD, font=("Courier", 9)
    )
    log_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
    log_text.config(state=tk.DISABLED)

    # Set up logging
    text_handler = TextHandler(log_text)
    logger.addHandler(text_handler)

    category_label = ttk.Label(main_frame, text="Category:")
    category_label.grid(row=2, column=0, sticky=tk.W)

    categories = ["All"] + list(CATEGORIES.keys())

    category_var = tk.StringVar()
    category_combobox = ttk.Combobox(
        main_frame, textvariable=category_var, values=categories
    )
    category_combobox.grid(row=2, column=1, sticky=tk.W)
    category_combobox.current(0)

    search_label = ttk.Label(main_frame, text="Search Text:")
    search_label.grid(row=3, column=0, sticky=tk.W)

    search_entry = ttk.Entry(main_frame)
    search_entry.grid(row=3, column=1, sticky=tk.W)

    hours_label = ttk.Label(main_frame, text="Hours:")
    hours_label.grid(row=4, column=0, sticky=tk.W)

    hours_entry = ttk.Entry(main_frame)
    hours_entry.grid(row=4, column=1, sticky=tk.W)
    hours_entry.insert(tk.END, "1")

    show_empty_var = tk.BooleanVar()
    show_empty_checkbox = ttk.Checkbutton(
        main_frame, text="Show Empty", variable=show_empty_var
    )
    show_empty_checkbox.grid(row=5, column=0, columnspan=2, sticky=tk.W)

    result_label = ttk.Label(main_frame, text="Results:")
    result_label.grid(row=7, column=0, sticky=tk.W)

    # Create a ScrolledText with horizontal scrolling
    result_text = ScrolledText(
        main_frame, width=170, height=20, wrap=tk.WORD, font=("Courier", 9)
    )
    result_text.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E))
    result_text.config(state=tk.DISABLED)

    # Create a horizontal scrollbar
    xscrollbar = ttk.Scrollbar(
        main_frame,
        orient="horizontal",
        command=result_text.xview
    )
    xscrollbar.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E))

    # Connect the horizontal scrollbar with the ScrolledText widget
    result_text.config(xscrollcommand=xscrollbar.set)

    main_frame.columnconfigure(1, weight=1)

    def __init__(self):
        self.search_button = ttk.Button(
            self.main_frame,
            text="Search Streams",
            command=self.start_search_thread
        )
        self.search_button.grid(
            row=6, column=0, columnspan=2, sticky=(tk.E, tk.W)
        )

    def search_streams(self):
        """Function to initiate the search process."""

        # Clear the result_text and log_text widgets
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state=tk.DISABLED)

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

        try:
            hours = int(self.hours_entry.get())
        except ValueError:
            logger.error(
                'Parameter "Hours" must be an integer, '
                f'"{self.hours_entry.get()}" is not a valid value'
            )
            return

        category = self.category_var.get()
        if category == 'All':
            category = None

        search_text = self.search_entry.get()
        show_empty = self.show_empty_var.get()

        self.search_button.config(
            state=tk.DISABLED
        )  # Disable the button while search is in progress

        events = get_events(search_text, hours, category, show_empty)
        table = get_events_table(events)

        if table:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.insert(tk.END, f'\n{table}\n')
            self.result_text.see(tk.END)
            self.result_text.config(state=tk.DISABLED)

        self.search_button.config(
            state=tk.NORMAL
        )  # Enable the button after the search is finished

    def start_search_thread(self):
        threading.Thread(target=self.search_streams, daemon=True).start()

    def run(self):
        self.root.mainloop()
