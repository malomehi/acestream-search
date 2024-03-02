import logging
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import subprocess
import threading
import os
import queue  # Import queue for inter-thread communication
from acestream_search import CATEGORIES


class TextHandler(logging.Handler):
    """Custom logging handler to redirect logs to a Tkinter ScrolledText widget."""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        """Override emit method to insert logs into the ScrolledText widget."""
        msg = self.format(record)
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, msg + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)


def run_search_command(command, log_queue, result_queue, button):
    """Function to run the search command in a separate thread."""
    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        while True:
            output = process.stdout.readline()
            if not output:
                break
            if output.startswith("[INFO]"):
                log_queue.put(output.strip())  # Put output in log queue
            else:
                result_queue.put(
                    output.strip()
                )  # Put output in result queue

        process.stdout.close()
        process.wait()
    except subprocess.CalledProcessError as e:
        log_queue.put(f"Error: {e.stderr}")  # Put error in log queue
    finally:
        button.config(
            state=tk.NORMAL
        )  # Enable the button after the search is finished


def display_log(log_queue, text_widget):
    """Function to display log messages in the ScrolledText widget."""
    while True:
        output = log_queue.get()
        if output is None:
            break
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, output + "\n")
        text_widget.see(tk.END)
        text_widget.config(state=tk.DISABLED)


def display_results(result_queue, text_widget):
    """Function to display search results in the ScrolledText widget."""
    while True:
        output = result_queue.get()
        if output is None:
            break
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, output + "\n")
        text_widget.see(tk.END)
        text_widget.config(state=tk.DISABLED)


def search_streams():
    """Function to initiate the search process."""
    # Clear the result_text and log_text widgets
    result_text.config(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    result_text.config(state=tk.DISABLED)

    log_text.config(state=tk.NORMAL)
    log_text.delete("1.0", tk.END)
    log_text.config(state=tk.DISABLED)

    search_button.config(
        state=tk.DISABLED
    )  # Disable the button while search is in progress
    category = category_var.get()
    search_text = search_entry.get()
    hours = hours_entry.get()
    show_empty = show_empty_var.get()

    current_directory = os.path.dirname(os.path.abspath(__file__))
    acestream_search_script = os.path.join(current_directory, "acestream_search.py")

    command = ["python3", acestream_search_script]

    if category != "All":
        command.extend(["--category", category])

    command.extend(["--search", search_text, "--hours", hours])

    if show_empty:
        command.append("--show-empty")

    # Create queues for inter-thread communication
    log_queue = queue.Queue()
    result_queue = queue.Queue()

    # Start a thread to run the search command
    threading.Thread(
        target=run_search_command,
        args=(command, log_queue, result_queue, search_button),
        daemon=True,
    ).start()

    # Start threads to display log and search results
    threading.Thread(
        target=display_log, args=(log_queue, log_text), daemon=True
    ).start()
    threading.Thread(
        target=display_results, args=(result_queue, result_text), daemon=True
    ).start()


root = tk.Tk()
root.title("Acestream Search - GUI")

main_frame = ttk.Frame(root, padding="20")
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

log_label = ttk.Label(main_frame, text="Console:")
log_label.grid(row=0, column=0, sticky=tk.W)  # Place the log label in row 0

log_text = ScrolledText(
    main_frame, width=170, height=5, wrap=tk.WORD, font=("Courier", 9)
)
log_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
log_text.config(state=tk.DISABLED)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
format = "[%(levelname)s] %(message)s"
formatter = logging.Formatter(format)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

text_handler = TextHandler(log_text)
text_handler.setFormatter(formatter)
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

search_button = ttk.Button(main_frame, text="Search Streams", command=search_streams)
search_button.grid(row=6, column=0, columnspan=2, sticky=(tk.E, tk.W))

result_label = ttk.Label(main_frame, text="Results:")
result_label.grid(row=7, column=0, sticky=tk.W)

# Create a ScrolledText with horizontal scrolling
result_text = ScrolledText(
    main_frame, width=170, height=20, wrap=tk.WORD, font=("Courier", 9)
)
result_text.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E))
result_text.config(state=tk.DISABLED)

# Create a horizontal scrollbar
xscrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=result_text.xview)
xscrollbar.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E))

# Connect the horizontal scrollbar with the ScrolledText widget
result_text.config(xscrollcommand=xscrollbar.set)

main_frame.columnconfigure(1, weight=1)

root.mainloop()
