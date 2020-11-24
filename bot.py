#!/usr/bin/env python3

import dotenv
dotenv.load_dotenv()
import os
import json
import textwrap
import discord as dc
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import *

BPATH: str = os.path.abspath(os.path.dirname(__file__))

class MissingFontError(Exception):
    pass

class MissingMemeJPGError(Exception):
    pass

class TooFewArgumentsError(Exception):
    pass

class MemeTemplate(object):
    def __init__(self, im_path: str, config: Union[object, List[object]], font_path: str):
        self.im_path: str = im_path
        self.config: Union[object, List[object]] = config
        self.font_path: ImageFont = font_path

    def make(self, txt: str) -> BytesIO:
        if type(self.config) == list:
            if len(self.config) > len(txt.split(',')):
                raise TooFewArgumentsError()
            config = self.config
            parts = txt.split(',')
        else:
            config = [self.config,]
            parts = [txt]
        im = Image.open(self.im_path)
        dr = ImageDraw.Draw(im)
        io = BytesIO()
        for i, c in enumerate(config):
            dr.multiline_text(tuple(c['from']), '\n'.join(textwrap.wrap(parts[i].strip(), width=c['width'])), fill=tuple(c['colour']), font=ImageFont.truetype(self.font_path, size=c['font_size']))
        im.save(io, format='PNG')
        im.close()
        ret = BytesIO(io.getvalue())
        io.close()
        return ret

class Gagmachine(dc.Client):
    def __init__(self, tkn: str, meme_path: str = os.path.join(BPATH, 'memes'), asset_path: str = os.path.join(BPATH, 'assets')):
        super().__init__()
        self.__tkn: str = tkn
        self.meme_path: str = meme_path
        self.asset_path: str = asset_path
        self.__cmds: Dict[str, Callable[Any, None]] = {
            'ping': self.pong,
            'refresh': self.refresh,
            '*': self.list_all,
        }
        self.__memes: Dict[str, MemeTemplate] = {}
        if not os.path.isfile(os.path.join(self.asset_path, 'font.ttf')):
            raise MissingFontError()
        self.scan_memes()

    def scan_memes(self) -> None:
        self.__memes = {}
        for f in os.listdir(self.meme_path):
            fname, ext = os.path.splitext(f)
            if ext == '.json':
                imfile = os.path.join(self.meme_path, f'{fname}.jpg')
                if not os.path.isfile(imfile):
                    raise MissingMemeJPGError()
                with open(os.path.join(self.meme_path, f), 'r') as f:
                    self.__memes[fname] = MemeTemplate(imfile, json.load(f), os.path.join(self.asset_path, 'font.ttf'))

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
        for k, v in self.__memes.items():
            if k == msg.content.split(' ')[1]:
                await self.send_meme(msg, v)
                return
        await msg.channel.send('I ain\'t got no idea whatcha said!')

    async def pong(self, msg: dc.Message) -> None:
        await msg.channel.send('Pong!')

    async def refresh(self, msg: dc.Message) -> None:
        self.scan_memes()
        await msg.channel.send(f'Scanned for new meme templates ... Found {len(self.__memes)} ... ')

    async def list_all(self, msg: dc.Message) -> None:
        await msg.channel.send('Alwight geezer, here be all ma templates:')
        await msg.channel.send('\n'.join(f'- {meme}' for meme in self.__memes.keys()))

    async def send_meme(self, msg: dc.Message, meme: MemeTemplate) -> None:
        if len(msg.content.split(' ')) < 3:
            await msg.channel.send('Ya do need to provide some text, ya geezer!')
            return
        try:
            f = meme.make(' '.join(msg.content.split(' ')[2:]))
        except:
            await msg.channel.send('Ya need to give me some more arguments, ya geezer!')
            return
        await msg.channel.send(file=dc.File(f, 'meme.png'))
        await msg.delete()
        f.close()

def main():
    if not os.environ['GAG_TKN']:
        print('\033[33m[-] Missing "GAG_TKN" in environment variables ... Exiting! \033[0m')
        os._exit(1)
    TKN: str = os.environ['GAG_TKN']

    cl: Gagmachine = Gagmachine(TKN)
    cl.run()

if __name__ == '__main__':
    main()