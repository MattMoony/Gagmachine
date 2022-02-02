#!/usr/bin/env python3

import dotenv
dotenv.load_dotenv()
import os, re
import json
import textwrap
import datetime
import discord as dc
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import *

"""The project's base path = folder in which this python script lies"""
BPATH: str = os.path.abspath(os.path.dirname(__file__))

class MissingFontError(Exception):
    """
    The standard meme font could not be found!
    """
    pass

class MissingMemeJPGError(Exception):
    """
    A meme template configuration was found without
    a base image.    
    """
    pass

class TooFewArgumentsError(Exception):
    """
    Too few text arguments were given to a meme
    template.
    """

    def __init__(self, num: int):
        """
        Raise a new too few arguments error.

        Args:
            num (int): The actual number of arguments required.
        """
        super().__init__()
        self.num: int = num

class MemeTemplate(object):
    """
    A meme template - contains info about the
    meme's base image, such as where to place
    the meme text, etc.
    """

    def __init__(self, name: str, im_path: str, config: Union[object, List[object]], font_path: str):
        """
        Create a new meme template.

        Args:
            name (str): The name of the meme template (used by the user to choose this template).
            im_path (str): The path to the meme's base image.
            config (Union[object, List[object]]): The meme's "configuration" (position of text, etc.).
            font_path (str): Path to the font file to be used on the meme.
        """
        self.name: str = name
        self.im_path: str = im_path
        self.config: Union[object, List[object]] = config
        self.font_path: ImageFont = font_path

    def make(self, txt: str) -> BytesIO:
        """
        Generate the actual image (as raw bytes)
        by placing the given text on the meme template.

        Args:
            txt (str): The text to be placed on the image (parts separted by ',' should multiple be necessary).

        Raises:
            TooFewArgumentsError: Too few parts of text were given for the meme template.

        Returns:
            BytesIO: The generated image (as raw bytes).
        """
        if type(self.config) == list:
            if len(self.config) > len(txt.split(',')):
                raise TooFewArgumentsError(len(self.config))
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
    """
    The actual Discord bot.
    """

    def __init__(self, tkn: str, meme_path: str = os.path.join(BPATH, 'memes'), asset_path: str = os.path.join(BPATH, 'assets')):
        """
        Create a new Gagmachine.

        Args:
            tkn (str): The Discord bot's token.
            meme_path (str, optional): The path to the meme base images. Defaults to os.path.join(BPATH, 'memes').
            asset_path (str, optional): Path to the assets (fonts, etc.). Defaults to os.path.join(BPATH, 'assets').

        Raises:
            MissingFontError: Should the font for all memes 'font.ttf' not be found in asset_path.
        """
        super().__init__()
        self.__tkn: str = tkn
        self.meme_path: str = meme_path
        self.asset_path: str = asset_path
        self.__cmds: Dict[str, Callable[[dc.Message], None]] = {
            'ping': self.pong,
            'refresh': self.refresh,
            '*': self.list_all,
        }
        self.__memes: Dict[str, MemeTemplate] = {}
        if not os.path.isfile(os.path.join(self.asset_path, 'font.ttf')):
            raise MissingFontError()
        self.scan_memes()

    def scan_memes(self) -> None:
        """
        Scan the set meme_path for all images => for
        all meme base images and create MemeTemplates
        based on them.

        Raises:
            MissingMemeJPGError: Should the JSON description for an image exist without the actual image.
        """
        self.__memes = {}
        for f in os.listdir(self.meme_path):
            fname, ext = os.path.splitext(f)
            if ext == '.json':
                imfile = os.path.join(self.meme_path, f'{fname}.jpg')
                if not os.path.isfile(imfile):
                    raise MissingMemeJPGError()
                with open(os.path.join(self.meme_path, f), 'r') as f:
                    self.__memes[fname] = MemeTemplate(fname, imfile, json.load(f), os.path.join(self.asset_path, 'font.ttf'))

    def run(self) -> None:
        """
        Start the Discord bot.
        """
        super().run(self.__tkn)

    async def on_ready(self) -> None:
        """
        Called upon the bot having connected to Discord;
        prints a short status message, and changes its Discord
        presence status to the list_all command.
        """
        print(f'[bot.py]: Ready as {self.user} ... ')
        await self.change_presence(activity=dc.Activity(type=dc.ActivityType.watching, name="gag *"))

    async def on_message(self, msg: dc.Message) -> None:
        """
        Upon receiving a new message on Discord - handle
        the message and respond adequately.

        Args:
            msg (dc.Message): The message the bot has received.
        """
        if msg.author == self.user:
            return
        if not msg.content.startswith('gag '):
            if msg.content.startswith('gag'):
                await msg.channel.send(f'R u tryna talk to me? <@!{msg.author.id}>')
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
        """
        Respond to a `ping` message with the time it
        took to receive the message.

        Args:
            msg (dc.Message): The message sent to the bot.
        """
        await msg.channel.send(f'Pong! - time `{((datetime.datetime.now()-msg.created_at).microseconds)/1000:.2f}ms`')

    async def refresh(self, msg: dc.Message) -> None:
        """
        Scan the meme_path folder for new meme templates
        upon having received a `refresh` message.

        Args:
            msg (dc.Message): The message sent to the bot.
        """
        try:
            print(f'[*] Scanning for new memes, because @{msg.author.name} told me to do so ... ')
            self.scan_memes()
        except MissingMemeJPGError:
            await msg.channel.send('It seems as if ya be missing some image files in the meme folder ... betta check that out!')
            return
        await msg.channel.send(f'Scanned for new meme templates ... Found {len(self.__memes)} ... ')

    async def list_all(self, msg: dc.Message) -> None:
        """
        List all currently loaded MemeTemplates upon
        receival of a `*` message.

        Args:
            msg (dc.Message): The message received by the bot.
        """
        print(f'[*] Listing all available memes for @{msg.author.name} ... ')
        await msg.channel.send('Alwight geezer, here be all ma templates:')
        await msg.channel.send('\n'.join(f'- {meme}' for meme in self.__memes.keys()))

    async def send_meme(self, msg: dc.Message, meme: MemeTemplate) -> None:
        """
        Create a new meme based on the sent message and the
        MemeTemplate asked for in the original message.

        Args:
            msg (dc.Message): The message sent to the bot.
            meme (MemeTemplate): The meme template that the user has asked for.
        """
        if len(msg.content.split(' ')) < 3:
            await msg.channel.send('Ya do need to provide some text, ya geezer!')
            return
        await msg.delete()
        rm: dc.Message = await msg.channel.send(f'Right! <@!{msg.author.id}> I\'m on it!')
        print(f'[*] Creating meme `{meme.name}` for @{msg.author.name} ... ')
        async with msg.channel.typing():
            try:
                txt: str = ' '.join(msg.content.split(' ')[2:])
                for m in re.findall(r'<@!\d+>', txt):
                    _id: int = int(m.replace('<@!', '').replace('>', ''))
                    txt = txt.replace(m, filter(lambda u: u.id == _id, msg.mentions).__next__().name)
                f: BytesIO = meme.make(txt)
            except TooFewArgumentsError as e:
                await msg.channel.send(f'Ya need to give me some more arguments, ya geezer! Gimme `{e.num}` texts separated by a `,`!')
                await rm.delete()
                return
        m: dc.Message = await msg.channel.send(' '.join(f'<@!{u.id}>' for u in msg.mentions), file=dc.File(f, 'meme.png'))
        await rm.delete()
        await m.add_reaction('\N{THUMBS UP SIGN}')
        await m.add_reaction('\N{THUMBS DOWN SIGN}')
        f.close()

def main():
    """
    The program's main entrypoint.
    """
    if not os.environ['GAG_TKN']:
        print('[-] Missing "GAG_TKN" in environment variables ... Exiting!')
        os._exit(1)
    TKN: str = os.environ['GAG_TKN']

    cl: Gagmachine = Gagmachine(TKN)
    cl.run()

if __name__ == '__main__':
    main()