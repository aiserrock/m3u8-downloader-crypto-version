#!/usr/bin/env python3
import concurrent.futures
import os
import re
import sys
import json
import time
import argparse
from base64 import b64decode
from functools import partial

from lxml.html import fromstring

import requests

XOR_KEY = 'bla_bla_bla'

headers = {
    'authority': 'play.boomstream.com',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'accept-language': 'en-US,en;q=0.9,ru;q=0.8,es;q=0.7,de;q=0.6'}


class App():

    def __init__(self):
        parser = argparse.ArgumentParser(description='boomstream.com downloader')
        parser.add_argument('--url', type=str, required=False)
        parser.add_argument('--pin', type=str, required=False)
        parser.add_argument('--use-cache', action='store_true', required=False)
        parser.add_argument('--resolution', type=str, required=False)
        self.args = parser.parse_args()



    def get_xmedia_ready(self, chunklist):
        """
        X-MEDIA-READY contains a value that is used to calculate IV for AES-128 and a URL
        to obtain AES-128 encryption key.
        """
        for line in chunklist.split('\n'):
            if line.split(':')[0] == '#EXT-X-MEDIA-READY':
                return line.split(':')[1]

        raise Exception("Could not find X-MEDIA-READY")

    def decrypt(self, source_text, key):
        result = ''
        while len(key) < len(source_text):
            key += key

        for n in range(0, len(source_text), 2):
            c = int(source_text[n:n + 2], 16) ^ ord(key[(int(n / 2))])
            result = result + chr(c)

        return result

    def encrypt(self, source_text, key):
        result = ''

        while len(key) < len(source_text):
            key += key

        for i in range(0, len(source_text)):
            result += '%0.2x' % (ord(source_text[i]) ^ ord(key[i]))

        return result

    def get_aes_key(self, key_url, xmedia_ready):
        """
        Returns IV and 16-byte key which will be used to decrypt video chunks
        """
        decr = self.decrypt(xmedia_ready, XOR_KEY)
        print('Decrypted X-MEDIA-READY: %s' % decr)

        key = None
        iv = ''.join(['%0.2x' % ord(c) for c in decr[20:36]])

        print('key url = %s' % key_url)

        r = requests.get(key_url, headers=headers)
        key = r.text
        print("IV = %s" % iv)
        print("Key = %s" % key)
        return iv, key

    def download_line(app, line, i, key, iv):
        # Convert the key to format suitable for openssl command-line tool
        hex_key = ''.join(['%0.2x' % ord(c) for c in key])

        if not line.startswith("https://"):
            return

        outf = os.path.join(key, "%0.5d" % i ) + ".ts"
        if os.path.exists(outf):
            print("Chunk #%s exists [%s]" % (i, outf))
            return
        print("Downloading chunk #%s" % i)
        os.system('curl -s "%s" | openssl aes-128-cbc -K "%s" -iv "%s" -d > %s' % \
                  (line, hex_key, iv, outf))

    def download_chunks(self, chunklist, iv, key):
        lines = []
        for line in chunklist.split('\n'):
            if line.startswith('https://'):
                lines.append(line)

        if not os.path.exists(key):
            os.mkdir(key)

        executor = concurrent.futures.ProcessPoolExecutor(10)
        futures = [executor.submit(self.download_line, line, index, key, iv) for (index, line) in enumerate(lines)]
        ok = concurrent.futures.wait(futures)

    def merge_chunks(self, key):
        """
        Merges all chunks into one file and encodes it to MP4
        """
        print("Merging chunks...")
        os.system("cat %s/*.ts > %s.ts" % (key, key,))
        print("Encoding to MP4")
        os.system('./ffmpeg -i %s.ts -c copy video.mp4' % key)

    def get_title(self):
        return self.config['entity']['title']

    def run(self):
        f = open("playlist.txt", "r")
        chunklist = f.read()

        xmedia_ready = self.get_xmedia_ready(chunklist)
        key_url = "https://play.boomstream.com/api/process/2e282314242415150119190f590e1e570207660e0954565c523b53080039075b025b5853395b0f576d570e510154053d5b0d5569"

        print('X-MEDIA-READY: %s' % xmedia_ready)
        iv, key = self.get_aes_key(key_url, xmedia_ready)

        self.download_chunks(chunklist, iv, key)
        self.merge_chunks(key)


if __name__ == '__main__':
    app = App()
    sys.exit(app.run())
