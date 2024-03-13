# -*- coding: utf-8 -*-
import os

from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner


def set_signer():
    home = os.path.expanduser('~')
    keys_path = os.path.join(home, '.android')
    if not os.path.exists(keys_path):
        os.mkdir(keys_path)

    if not os.path.exists(os.path.join(keys_path, 'adbkey')):
        keygen(os.path.join(keys_path, 'adbkey'))

    with open(os.path.join(keys_path, 'adbkey')) as f:
        private = f.read()
    with open(os.path.join(keys_path, 'adbkey.pub')) as f:
        public = f.read()

    signer = PythonRSASigner(public, private)
    return signer
