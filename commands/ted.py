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
from .basic import CommandBase, CommandInfo, CommandType, bot_command


class Ted(CommandBase):
    name = 'Ted'
    safename = 'ted'

    def __init__(self, logger):
        super().__init__(logger)
        self.sched_chats = dict()
        self.temp_upd = None
        self.to_register = [
            CommandInfo("ted", self.execute_ted, "Displays information for a specific TED Talk."),
            CommandInfo("tedr", self.execute_tedr, "Displays information for a random TED Talk."),
            CommandInfo("tedadd", self.execute_add, "Schedule a daily random TED Talk."),
            CommandInfo("teddel", self.execute_del, "Remove an existing schedule."),
            CommandInfo("ted_random", self.setup_talks, "Show scheduled daily TED Talks.", _type=CommandType.Schedule)
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
                f.write('\n'.join(' '.join(map(str, x))
                        for x in self.sched_chats.items()))
    
    def setup_talks(self, updater):
        self.temp_upd = updater
        if self.sched_chats is not None:
            for key, hour in self.sched_chats.items():
                updater.job_queue.run_daily(
                    self.talk_handler,
                    time = datetime.time(hour, 0, 0),
                    context = key
                )

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
            dmin, dsec = int(duration // 60), int(duration % 60)
            message = "<a href=\"{}\">{}</a>\n\n{}\n\n".format(data['url'], data['name'], data['description'])
            message += "Length: {:02d}:{:02d}\n".format(dmin, dsec)
            message += "Recorded on {} at {}.".format(datetime.datetime.utcfromtimestamp(data['recorded_date']).strftime('%Y-%m-%d'), data['event'])
            bot.send_message(chat_id = chatid,
                             parse_mode = ParseMode.HTML,
                             text = message,
                             disable_notification = True)
    
    def talk_handler(self, bot, job):
        try:
            if self.sched_chats is None or not job.context in self.sched_chats.keys():
                job.schedule_removal()
                return
            self.get_talk(None, bot, job.context)
            self.logger.info("ted_random schedule completed successfully.")
        except Exception as e:
            self.logger.error(e)

    @bot_command
    def execute_ted(self, bot, update, args):
        self.get_talk(args[0], bot, update.message.chat_id)
    @bot_command
    def execute_tedr(self, bot, update, args):
        self.get_talk(None, bot, update.message.chat_id)
    @bot_command
    def execute_add(self, bot, update, args):
        if len(args) != 1:
            bot.send_message(chat_id = update.message.chat_id,
                             text = "This doesn't seem like correct usage of /tedadd.",
                             disable_notification = True)
            return
        if not args[0].isdigit() and 0 <= int(args[0]) <= 23:
            bot.send_message(chat_id = update.message.chat_id,
                             text = "This is not a valid hour (0 <= hour <= 23).",
                             disable_notification = True)
            return
        if update.message.chat_id in self.sched_chats.keys():
            bot.send_message(chat_id = update.message.chat_id,
                             text = "This chat has daily TED talks scheduled already.",
                             disable_notification = True)
            return
        self.sched_chats[update.message.chat_id] = int(args[0])
        self.temp_upd.job_queue.run_daily(
            self.talk_handler,
            time = datetime.time(int(args[0]), 0, 0),
            context = update.message.chat_id
        )
        bot.send_message(chat_id = update.message.chat_id,
                         text = "Daily TED talk has been scheduled.",
                         disable_notification = True)
    @bot_command
    def execute_del(self, bot, update, args):
        if update.message.chat_id in self.sched_chats.keys():
            del self.sched_chats[update.message.chat_id]
            bot.send_message(chat_id = update.message.chat_id,
                             text = "Daily TED talks have been disabled.",
                             disable_notification = True)
