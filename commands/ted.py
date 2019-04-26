# Ted plugin
# Commands:
#   - /ted
#   - /tedr
#   - /tedadd
#   - /teddel
# Configuration:
# command.ted:
#   datfile: "path/to/file.txt"

import os
import requests
import datetime
from telegram import ParseMode
from .basic import CommandBase, CommandInfo, bot_command

class Ted(commandBase):
    name = 'Ted'
    safename = 'ted'
    def __init__(self, logger):
        super().__init__(logger)
        self.sched_chats = dict()
        self.to_register = [
            CommandInfo("ted", self.execute_ted, "Displays information for a specific TED Talk."),
            CommandInfo("tedr", self.execute_tedr, "Displays information for a random TED Talk."),
            # CommandInfo("tedadd", self.execute_add, "Schedule a daily random TED Talk."),
            # CommandInfo("teddel", self.execude_del, "Remove an existing schedule.")
        ]
    def get_help_msg(self, cmd):
        if cmd == "ted":
            return "Call /ted with a talk ID or slug to get information."
        elif cmd == "tedr":
            return "Call /tedr to get information for a random TED Talk."
        elif cmd == "tedadd":
            return "Call /tedadd <hour> to schedule a random TED Talk to be posted."
        elif cmd == "teddel":
            return "Call /teddel to remove an existing schedule for the current chat."
    def load_config(self, confdict):
        self.regfile = confdict['datfile']
        if os.path.isfile(self.regfile):
            with open(self.regfile, 'r') as f:
                lines = [x.strip().split(' ') for x in f.readlines()]
                for chat, hour in lines:
                    self.sched_chats[int(chat)] = int(hour)
    def on_exit(self):
        if os.path.isfile(self.regfile):
            os.remove(self.regfile)
        if self.sched_chats:
            with open(self.regfile, 'w') as f:
                f.write('\n'.join(' '.join(map(str, x)) for x in self.sched_chats.items()))
    def get_talk(self, id_or_slug, bot, chatid):
        data = None
        if not id_or_slug:
            data = requests.get('https://ted.kaderobertson.pw/random').json()
        elif id_or_slug.isdigit():
            data = requests.get('https://ted.kaderobertson.pw/id/' + id_or_slug).json()
        else:
            data = requests.get('https://ted.kaderobertson.pw/slug/' + id_or_slug).json()
        if not data:
            raise Exception("Couldn't get a valid TED talk.")
         else:
            duration = data['talks'][0]['duration']
            dmin, dsec = (duration / 60).zfill(2), (duration % 60).zfill(2)
            message = "<b>{}</b>\n\n{}\n\n".format(data['name'], data['description'])
            message += "Talk: {}\n\nLength: {}:{}\n\n".format(data['url'], dmin, dsec)
            message += "Recorded on {}".format(atetime.datetime.utcfromtimestamp(data['recorded_date'])).strftime('%Y-%m-%d')
            bot.send_message(chat_id = chatid,
                             parse_mode = ParseMode.HTML,
                             text = message,
                             disable_notification = True)
    @bot_command
    def execute_ted(self, bot, update, args):
        self.get_talk(args[0], bot, update.message.chat_id)
    @bot_command
    def execute_tedr(self, bot, update, args):
        self.get_talk(None, bot, update.message.chat_id)
        
        
