# -*- coding: utf-8 -*-
import os
import subprocess

from adb_shell.adb_device import AdbDeviceTcp

from acestream_search.adb.auth import set_signer
from acestream_search.log import logger


def run_adb_command(adb_path: str, command: str) -> bool:
    binary = os.path.join(adb_path, 'platform-tools', 'adb')
    try:
        subprocess.run(
            [binary, command],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
    except subprocess.CalledProcessError as e:
        logger.err(f'Error running ADB command: {e}')
        return False

    return True


def connect(ip: str) -> AdbDeviceTcp:
    device = AdbDeviceTcp(ip)
    signer = set_signer()
    logger.info(
        f'Trying to connect to Adroid device: {ip} '
        '(will timeout after 60s)'
    )
    try:
        device.connect(rsa_keys=[signer], auth_timeout_s=60)
    except Exception as e:
        logger.error(f'Error connecting to device: {e}')
        return None
    logger.info(f'Connected to Adroid device: {ip}')
    return device
