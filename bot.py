#!/usr/bin/env python3

import dotenv
dotenv.load_dotenv()
import os
import json
import discord as dc
from typing import *

BPATH: str = os.path.abspath(os.path.dirname(__file__))

class MissingFontError(Exception):
    pass

class MissingMemeJPGError(Exception):
    pass

class Meme(object):
    def __init__(self, im_path: str, config: object):
        self.im_path: str = im_path
        self.config: object = config

class Gagmachine(dc.Client):
    def __init__(self, tkn: str, meme_path: str = os.path.join(BPATH, 'memes'), asset_path: str = os.path.join(BPATH, 'assets')):
        super().__init__()
        self.__tkn: str = tkn
        self.meme_path: str = meme_path
        self.asset_path: str = asset_path
        self.__cmds: Dict[str, Callable[dc.Message, None]] = {
            'ping': self.pong,
            'refresh': self.refresh,
        }
        self.__memes: List[Meme] = []
        if not os.path.isfile(os.path.join(self.asset_path, 'font.ttf')):
            raise MissingFontError()
        self.scan_memes()

    def scan_memes(self) -> None:
        self.__memes = []
        for f in os.listdir(self.meme_path):
            fname, ext = os.path.splitext(f)
            if ext == '.json':
                imfile = os.path.join(self.meme_path, f'{fname}.jpg')
                if not os.path.isfile(imfile):
                    raise MissingMemeJPGError()
                with open(os.path.join(self.meme_path, f), 'r') as f:
                    self.__memes.append(Meme(imfile, json.load(f)))

    def run(self) -> None:
        super().run(self.__tkn)

    async def on_ready(self) -> None:
        print(f'[bot.py]: Ready as {self.user} ... ')

    async def on_message(self, msg: dc.Message) -> None:
        if msg.author == self.user:
            return
        if not msg.content.startswith('gag '):
            return
        if not msg.content.split(' ')[1:]:
            await msg.channel.send('Don\'t chat to me \'less you got some\'in to say!')
            return
        for k, v in self.__cmds.items():
            if k == msg.content.split(' ')[1]:
                await v(msg)
                return
        await msg.channel.send('I ain\'t got no idea whatcha said!')

    async def pong(self, msg: dc.Message) -> None:
        await msg.channel.send('Pong!')

    async def refresh(self, msg: dc.Message) -> None:
        self.scan_memes()
        await msg.channel.send(f'Scanned for new meme templates ... Found {len(self.__memes)} ... ')

def main():
    if not os.environ['GAG_TKN']:
        print('\033[33m[-] Missing "GAG_TKN" in environment variables ... Exiting! ')
        os._exit(1)
    TKN: str = os.environ['GAG_TKN']

    cl: Gagmachine = Gagmachine(TKN)
    cl.run()

if __name__ == '__main__':
    main()