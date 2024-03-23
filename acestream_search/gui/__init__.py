import logging
import os
import re
import shutil
import threading
import tkinter as tk
import webbrowser
from functools import partial
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from acestream_search.adb import Client
from acestream_search.adb.discover import discover_adb_devices
from acestream_search.adb.server import run_adb_command
from acestream_search.common.constants import CATEGORIES
from acestream_search.events import get_events
from acestream_search.events import get_events_table
from acestream_search.gui.hyperlink import HyperlinkManager
from acestream_search.log import FORMAT
from acestream_search.log import logger


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
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)


class GuiApp():
    root = tk.Tk()
    root.title('Acestream Search - GUI')
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    main_frame = ttk.Frame(root, padding='20')
    main_frame.grid(row=0, column=0, sticky=(tk.NSEW))
    main_frame.columnconfigure(3, weight=1)
    main_frame.rowconfigure(9, weight=1)

    log_label = ttk.Label(main_frame, text='Console:')
    log_label.grid(row=0, column=0, sticky=tk.W)  # Place log label in row 0

    log_text = ScrolledText(
        main_frame, width=155, height=5, wrap=tk.WORD, font=('Courier', 9)
    )
    log_text.grid(row=1, column=0, pady=5, columnspan=4, sticky=(tk.EW))
    log_text.config(state=tk.DISABLED)

    # Set up logging
    text_handler = TextHandler(log_text)
    logger.addHandler(text_handler)

    category_label = ttk.Label(main_frame, text='Category:')
    category_label.grid(row=2, column=0, sticky=tk.W)

    categories = ['All'] + list(CATEGORIES.keys())

    category_var = tk.StringVar()
    category_combobox = ttk.Combobox(
        main_frame, textvariable=category_var, values=categories
    )
    category_combobox.grid(row=2, column=1, sticky=tk.W)
    category_combobox.current(0)

    search_label = ttk.Label(main_frame, text='Search Text:')
    search_label.grid(row=3, column=0, sticky=tk.W)

    search_entry = ttk.Entry(main_frame)
    search_entry.grid(row=3, column=1, sticky=tk.W)

    hours_label = ttk.Label(main_frame, text='Hours:')
    hours_label.grid(row=4, column=0, sticky=tk.W)

    hours_entry = ttk.Entry(main_frame)
    hours_entry.grid(row=4, column=1, sticky=tk.W)
    hours_entry.insert(tk.END, '1')

    ip_label = ttk.Label(main_frame, text='Android device IP: ')
    ip_label.grid(row=5, column=0, sticky=tk.W)
    ip_var = tk.StringVar()
    ip_combobox = ttk.Combobox(main_frame, textvariable=ip_var)
    ip_combobox.grid(row=5, column=1, sticky=tk.W)
    ip_warning = ttk.Label(
        main_frame,
        text='(Android devices must have remote ADB '
        'debugging enabled and Ace Stream app installed)'
    )
    ip_warning.grid(row=5, column=3, sticky=tk.W)

    show_empty_var = tk.BooleanVar()
    show_empty_checkbox = ttk.Checkbutton(
        main_frame, text='Show Empty', variable=show_empty_var
    )
    show_empty_checkbox.grid(row=6, column=0, sticky=tk.W)

    result_label = ttk.Label(main_frame, text='Results:')
    result_label.grid(row=8, column=0, sticky=tk.W)

    # Create a ScrolledText with horizontal scrolling
    result_text = ScrolledText(
        main_frame, width=155, height=20, wrap=tk.WORD, font=('Courier', 9)
    )
    result_text.grid(row=9, column=0, columnspan=4, pady=5, sticky=tk.NSEW)
    result_text.config(state=tk.DISABLED, foreground='blue3')

    adb_client = Client()

    def __init__(self):
        self.search_button = ttk.Button(
            self.main_frame,
            text='Search Streams',
            command=self.start_search_thread
        )
        self.search_button.grid(
            row=7, column=0, columnspan=4, pady=5, sticky=(tk.EW)
        )
        self.refresh_adb_button = ttk.Button(
            self.main_frame,
            text='Refresh Devices',
            command=self.start_refresh_adb_thread
        )
        self.refresh_adb_button.grid(
            row=5, column=2, padx=5, sticky=(tk.W)
        )
        self.root.protocol('WM_DELETE_WINDOW', self.window_exit)

    def discover_devices(self):
        self.refresh_adb_button.config(state=tk.DISABLED)
        self.ip_combobox.config(state=tk.DISABLED)
        ips = discover_adb_devices()
        self.ip_combobox.config(values=ips)
        if ips:
            self.ip_combobox.current(0)
        self.refresh_adb_button.config(state=tk.NORMAL)
        self.ip_combobox.config(state=tk.NORMAL)

    def play_on_android(self, link):
        threading.Thread(
            target=self.adb_client.play_stream,
            daemon=True,
            args=(self.ip_var.get(), link)
        ).start()

    def search_streams(self):
        """Function to initiate the search process."""

        # Clear the result_text widget
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete('1.0', tk.END)
        self.result_text.config(state=tk.DISABLED)

        try:
            hours = int(self.hours_entry.get())
        except ValueError:
            logger.error(
                'Parameter "Hours" must be an integer, '
                f'"{self.hours_entry.get()}" is not a valid value'
            )
            return

        category = self.category_var.get()
        if category not in self.categories:
            logger.error(f'"{category}" is not a valid category')
            return
        if category == 'All':
            category = None

        search_text = self.search_entry.get()
        show_empty = self.show_empty_var.get()

        # Disable the button while search is in progress
        self.search_button.config(state=tk.DISABLED)

        events = get_events(search_text, hours, category, show_empty, True)
        table = get_events_table(events)

        if table:
            chunks = re.split(
                '(acestream:\\/\\/\\S+ \\(Play on Android\\))',
                table
            )
            self.result_text.config(state=tk.NORMAL)
            self.result_text.insert(tk.END, '\n')
            hyperlinks = HyperlinkManager(self.result_text)
            for chunk in chunks:
                if chunk.startswith('acestream://'):
                    link = chunk.split()[0]
                    self.result_text.insert(
                        tk.END,
                        link,
                        hyperlinks.add(partial(webbrowser.open, link))
                    )
                    self.result_text.insert(tk.END, ' ')
                    self.result_text.insert(
                        tk.END,
                        '(Play on Android)',
                        hyperlinks.add(partial(self.play_on_android, link))
                    )
                else:
                    self.result_text.insert(tk.END, chunk)
            self.result_text.insert(tk.END, '\n')
            self.result_text.config(state=tk.DISABLED)

        # Enable the button after the search is finished
        self.search_button.config(state=tk.NORMAL)

    def start_search_thread(self):
        threading.Thread(target=self.search_streams, daemon=True).start()

    def start_refresh_adb_thread(self):
        threading.Thread(target=self.discover_devices, daemon=True).start()

    def cleanup(self):
        if self.adb_client.server_running:
            logger.info('Stopping ADB server')
            self.adb_client.server_running = not run_adb_command(
                self.adb_client.adb_path, 'kill-server'
            )
        if not self.adb_client.server_running and self.adb_client.adb_path:
            temp_dir = os.path.join(self.adb_client.adb_path, 'platform-tools')
            shutil.rmtree(temp_dir)
            logger.info(
                f'Deleted temp directory with adb binary "{temp_dir}"'
            )

    def window_exit(self):
        self.cleanup()
        self.root.destroy()

    def run(self):
        self.start_refresh_adb_thread()
        self.root.mainloop()
