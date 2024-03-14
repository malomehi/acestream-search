import ipaddress

from acestream_search.adb.download import download_adb_binary
from acestream_search.adb.server import connect
from acestream_search.adb.server import run_adb_command
from acestream_search.log import logger


class Client():
    def __init__(self):
        self.adb_path = None
        self.server_running = False
        self.devices = {}

    def play_stream(self, ip: str, link: str):
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            logger.error(f'"{ip}" is not a valid IP address')
            return
        if not self.adb_path:
            self.adb_path = download_adb_binary()
        if not self.server_running:
            if run_adb_command(self.adb_path, 'kill-server'):
                logger.info('Starting ADB server')
                self.server_running = run_adb_command(
                    self.adb_path, 'start-server'
                )
        if not self.server_running:
            return
        if not self.devices.get(ip) or not self.devices.get(ip).available:
            self.devices[ip] = connect(ip)
        if not self.devices.get(ip):
            return
        logger.info('Sending acestream link to Android device')
        self.devices.get(ip).shell(
            f'am start -a android.intent.action.VIEW -d {link}'
        )
