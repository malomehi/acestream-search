# -*- coding: utf-8 -*-

import os
import platform
import requests
import subprocess
import tempfile
import zipfile

from acestream_search.log import logger

BASE_URL = 'https://dl.google.com/android/repository/platform-tools-latest'


def download_adb_binary() -> str:
    temp_dir = tempfile.mkdtemp()

    binary_url = ''
    if platform.system() == 'Darwin':
        binary_url = f'{BASE_URL}-darwin.zip'
    elif platform.system() == 'Linux':
        binary_url = f'{BASE_URL}-linux.zip'
    elif platform.system() == 'Windows':
        binary_url = f'{BASE_URL}-windows.zip'

    download_path = os.path.join(temp_dir, 'platform-tools-latest.zip')

    logger.info('Downloading ADB binary to temp location')
    b = requests.get(binary_url).content
    with open(download_path, 'wb') as f:
        f.write(b)

    with zipfile.ZipFile(download_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    if platform.system() != 'Windows':
        subprocess.run(
            ['chmod', '+x', os.path.join(temp_dir, 'platform-tools', 'adb')]
        )

    os.remove(download_path)
    logger.info('ADB binary downloaded successfully')
    return temp_dir
