#!/usr/bin/env python3

import dotenv
dotenv.load_dotenv()

import os
import discord as dc

class Gagmachine(dc.Client):
    def __init__(self, tkn: str):
        super().__init__()
        self.__tkn: str = tkn
        self.__cmds = {
            'ping': self.pong,
        }

    def run(self) -> None:
        super().run(self.__tkn)

    async def on_ready(self) -> None:
        print(f'[bot.py]: Ready as {self.user} ... ')

    async def on_message(self, msg: dc.Message) -> None:
        if msg.author == self.user:
            return
        if not msg.content.split(' ')[1:]:
            await msg.channel.send('Don\'t chat to me \'less you got some\'in to say!')
            return
        for k, v in self.__cmds.items():
            if k.startswith(msg.content.split(' ')[1]):
                await v(msg)
                return
        await msg.channel.send('I ain\'t got no idea whatcha said!')

    async def pong(self, msg: dc.Message) -> None:
        await msg.channel.send('Pong!')

def main():
    if not os.environ['GAG_TKN']:
        print('\033[33m[-] Missing "GAG_TKN" in environment variables ... Exiting! ')
        os._exit(1)
    TKN: str = os.environ['GAG_TKN']

    cl: Gagmachine = Gagmachine(TKN)
    cl.run()

if __name__ == '__main__':
    main()