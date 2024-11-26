import logging
import threading
import webbrowser
from functools import partial

from acestream_search.common.constants import CATEGORIES  # noreorder
from acestream_search.channels import get_channels  # noreorder
from acestream_search.events import get_events  # noreorder
from acestream_search.log import FORMAT  # noreorder
from acestream_search.log import logger  # noreorder

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import mainthread


class MyLogsHandler(logging.Handler):

    def __init__(self, widget, level=logging.NOTSET):
        super().__init__(level=level)
        self.widget = widget

    def format(self, record):
        formatter = logging.Formatter(FORMAT)
        return formatter.format(record)

    @mainthread
    def emit(self, record):
        self.widget.text += self.format(record) + '\n'


class GuiApp(App):
    def build(self):
        self.title = 'Acestream Search'
        self.events = []
        self.channels = []

        # Main layout
        self.main_layout = BoxLayout(orientation='vertical', spacing=5)

        # Console log label
        logs_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2))
        log_label = Label(text='Logs:', size_hint=(1, 0.2))
        logs_layout.add_widget(log_label)

        # Text area for logs
        logs_text = TextInput(readonly=True)
        logs_layout.add_widget(logs_text)
        self.main_layout.add_widget(logs_layout)

        # Category label and spinner (combobox)
        category_label = Label(text='Category:')
        self.category_spinner = Spinner(
            text='All', values=['All'] + list(CATEGORIES.keys())
        )
        category_layout = BoxLayout(orientation='horizontal')
        category_layout.add_widget(category_label)
        category_layout.add_widget(self.category_spinner)

        # Search text label and input
        search_label = Label(text='Search Text:')
        self.search_input = TextInput(multiline=False)
        search_layout = BoxLayout(orientation='horizontal')
        search_layout.add_widget(search_label)
        search_layout.add_widget(self.search_input)

        # User inputs
        user_inputs = BoxLayout(orientation='vertical', size_hint=(1, 0.1))
        user_inputs.add_widget(category_layout)
        user_inputs.add_widget(search_layout)
        self.main_layout.add_widget(user_inputs)

        # Buttons
        button_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.1))
        self.search_events_button = Button(text='Search Events Streams')
        self.search_events_button.bind(
            on_press=self.start_search_events_thread
        )
        self.search_channels_button = Button(text='Search Channels Streams')
        self.search_channels_button.bind(
            on_press=self.start_search_channels_thread
        )
        button_layout.add_widget(self.search_events_button)
        button_layout.add_widget(self.search_channels_button)
        self.main_layout.add_widget(button_layout)

        # Results label and scrolled area
        results_layout = BoxLayout(
            orientation='vertical', size_hint=(1, 0.6)
        )
        result_label = Label(text='Results:', size_hint=(1, 0.1))
        result_scroll = ScrollView()
        self.result_layout = GridLayout(cols=1, size_hint_y=None)
        self.result_layout.bind(
            minimum_height=self.result_layout.setter('height')
        )
        result_scroll.add_widget(self.result_layout)
        results_layout.add_widget(result_label)
        results_layout.add_widget(result_scroll)

        self.main_layout.add_widget(results_layout)

        logger.addHandler(MyLogsHandler(logs_text, logging.INFO))

        return self.main_layout

    def start_search_events_thread(self, instance):
        self.result_layout.clear_widgets()
        self.search_events_button.disabled = True
        self.search_channels_button.disabled = True
        thread = threading.Thread(
            target=self.search_events, daemon=True
        )
        thread.start()

    def search_events(self):
        category = self.category_spinner.text
        if category == 'All':
            category = None
        self.events = get_events(
            text=self.search_input.text,
            hours=2,
            category=category,
            show_empty=False
        )
        self.populate_events()

    @mainthread
    def populate_events(self):
        for event in sorted(
            self.events,
            key=lambda x: (x['date'], x['category'], x['title'])
        ):
            i = 0
            if not event['links']:
                continue
            links_widget = ScrollView()
            links_grid_layout = GridLayout(cols=1, size_hint_y=None)
            links_grid_layout.bind(
                minimum_height=links_grid_layout.setter('height')
            )
            for link in event['links']:
                i += 1
                link_button = Button(
                    text=f'Link {i}\n(Language: {link["language"]}, '
                    f'Bitrate: {link["bitrate"]})',
                    halign='center', size_hint_y=None, padding=5
                )
                link_button.bind(texture_size=link_button.setter('size'))
                link_button.on_press = partial(webbrowser.open, link['url'])
                links_grid_layout.add_widget(link_button)
            links_widget.add_widget(links_grid_layout)
            popup_content = links_widget
            popup = Popup(
                title='Event links', size_hint=(.9, .9),
                content=popup_content
            )
            event_button = Button(
                text='\n'.join([f'[{event["category"]}]', event['title']]),
                halign='center', size_hint_y=None, padding=5
            )
            event_button.bind(texture_size=event_button.setter('size'))
            event_button.on_press = popup.open
            self.result_layout.add_widget(event_button)

        self.search_events_button.disabled = False
        self.search_channels_button.disabled = False

    def start_search_channels_thread(self, instance):
        self.result_layout.clear_widgets()
        self.search_events_button.disabled = True
        self.search_channels_button.disabled = True
        thread = threading.Thread(
            target=self.search_channels, daemon=True
        )
        thread.start()

    def search_channels(self):
        self.channels = get_channels()
        self.populate_channels()

    @mainthread
    def populate_channels(self):
        for channel in self.channels:
            channel_button = Button(
                text=channel['name'], size_hint_y=None, padding=5
            )
            channel_button.bind(texture_size=channel_button.setter('size'))
            channel_button.on_press = partial(webbrowser.open, channel['link'])
            self.result_layout.add_widget(channel_button)

        self.search_events_button.disabled = False
        self.search_channels_button.disabled = False


if __name__ == '__main__':
    GuiApp().run()
