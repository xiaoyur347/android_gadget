#!/usr/bin/env python3
# Note: pip3 install requests

from __future__ import print_function

import requests

http_url = "https://dl.google.com/android/repository/android-ndk-{version}-darwin-x86_64.zip"
array = [
    "r16b",
    "r15c",
    "r14b",
    "r13b",
    "r12b",
    "r11c",
    "r10e"
]

for url in array:
    url = http_url.format(version=url)
    r = requests.get(url, stream = True)
    print(url , r.headers["Last-Modified"])