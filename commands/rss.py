# RSS feed plugin
# Commands:
#   - /rss
#   - /rssfeeds
#   - /rssdel
# Monitors: None
# Schedules:
#   - check_rss
# Configuration:
# command.rss:
#   data_dir: "path/to/storage"

import os
import glob
import shlex
import requests
import datetime
import feedparser
from telegram import ParseMode
from .basic import CommandBase, CommandInfo, CommandType, bot_command

class RSS(CommandBase):
    name = "RSS"
    safename = "rss"
    int_opts = {
        '2m': 120,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '2h': 7200,
        '3h': 10800,
        '6h': 21600,
        '12h': 43200,
        '24h': 86400
    }
    int_opts_r = dict((v, k) for k, v in int_opts.items())
    def __init__(self, logger):
        super().__init__(logger)
        self.to_register = [
            CommandInfo("rss", self.execute_rss, "Schedule RSS updates."),
            CommandInfo("rssfeeds", self.execute_feeds, "List feeds for this chat."),
            CommandInfo("rssdel", self.execute_feeddel, "List feeds for this chat."),
            CommandInfo("check_rss", self.setup_rss, "Check feeds.", _type=CommandType.Schedule)
        ]
        self.feeddict = dict()
    def get_help_msg(self, cmd):
        if cmd == "rss":
            ints = sorted(self.int_opts.items(), key=lambda x: x[1])
            return "Register an RSS feed with /rss <name> <url> <interval>. Valid intervals are {}.".format(', '.join(x[0] for x in ints))
        elif cmd == "rssfeeds":
            return "Call /rssfeeds with no arguments to see which feeds are registered to this chat."
        elif cmd == "rssdel":
            return "Call /rssdel <index> to delete the feed at the specified index (from /rssfeeds)."
    def load_config(self, confdict):
        self.datadir = confdict['data_dir']
        self.feeddict = dict()
        if not os.path.exists(self.datadir):
            os.mkdir(self.datadir)
        else:
            for fn in glob.glob(os.path.join(self.datadir, '*.groupfeeds')):
                shortfn = int(os.path.splitext(os.path.basename(fn))[0])
                with open(fn, 'r') as f:
                    toreg = (x.strip().split('||') for x in f.readlines())
                    self.feeddict[shortfn] = []
                    for name, feedurl, interval, lastid in toreg:
                        self.feeddict[shortfn].append((name, feedurl, int(interval), lastid))
    def on_exit(self):
        if not os.path.exists(self.datadir):
            os.mkdir(self.datadir)
        for chat_id in self.feeddict.keys():
            with open(os.path.join(self.datadir, str(chat_id) + '.groupfeeds'), 'w') as f:
                if len(self.feeddict[chat_id]) > 0:
                    self.logger.info('  Saving feeds for {}'.format(chat_id))
                f.write('\n'.join('||'.join(map(str, x)) for x in self.feeddict[chat_id]))
    def setup_rss(self, updater):
        stagger = 0
        self.temp_upd = updater
        for chatid in self.feeddict.keys():
            for feed in self.feeddict[chatid]:
                updater.job_queue.run_repeating(
                    self.check_rss, 
                    interval=datetime.timedelta(seconds=feed[2]),
                    context=(chatid, feed),
                    first = stagger
                )
                stagger += 5
    def check_rss(self, bot, job):
        chat_id, meta = job.context
        if chat_id not in self.feeddict.keys() or meta not in self.feeddict[chat_id]:
            job.schedule_removal()
            return
        self.logger.info("Checking {}".format(meta[0]))
        name, feedurl, interval, last_id = meta
        try:
            feed = feedparser.parse(feedurl)
            if len(feed['entries']) > 0:
                startidx = 0
                recentid = feed['entries'][0]['id']
                self.logger.info("  Recent ID: {} | Last Saved: {}".format(recentid, last_id))
                if recentid == last_id:
                    return
                out = "<b>{} Feed Update(s):</b>".format(name)
                outup = []
                while True:
                    if startidx >= len(feed['entries']):
                        break
                    recent = feed['entries'][startidx]
                    self.logger.info(" Checking entry with ID {}".format(recent['id']))
                    if recent['id'] != last_id:
                        outup.append('\n<a href="{}">{}</a>'.format(recent['link'],recent['title']))
                        startidx += 1
                    else:
                        break
                out += ''.join(outup[::-1])
                bot.send_message(chat_id = chat_id,
                                 parse_mode = ParseMode.HTML,
                                 text = out,
                                 disable_notification = False,
                                 disable_web_page_preview = True)
                lst = self.feeddict[chat_id]
                idx = 0
                for i in range(len(lst)):
                    if lst[i][1] == feedurl:
                        self.logger.info("Old entry: {}".format(lst[i]))
                        lst[i] = (name, feedurl, interval, recentid)
                        self.logger.info("New entry: {}".format(lst[i]))
                        idx = i
                        break
                self.feeddict[chat_id] = lst
                job.context = (chat_id, self.feeddict[chat_id][idx])
        except Exception as e:
            raise(e)
    @bot_command
    def execute_rss(self, bot, update, args):
        if len(args) != 3:
            bot.send_message(chat_id = update.message.chat_id,
                             text = "This doesn't seem like correct usage of /rss.",
                             disable_notification = True)
            return
        attempt = requests.head(args[1])
        if attempt.status_code not in (200, 429):
            bot.send_message(chat_id = update.message.chat_id,
                             text = "This doesn't seem to be a valid link.",
                             disable_notification = True)
            return
        if args[2] not in self.int_opts.keys():
            bot.send_message(chat_id = update.message.chat_id,
                             text = "This doesn't seem to be a valid interval.",
                             disable_notification = True)
            return
        interval = self.int_opts[args[2]]
        curid = feedparser.parse(args[1])['entries'][0]['id']
        if update.message.chat_id in self.feeddict.keys():
            tryx = self.feeddict[update.message.chat_id]
        else:
            self.feeddict[update.message.chat_id] = []
            tryx = []
        if args[1] not in [x[0] for x in tryx]:
            self.feeddict[update.message.chat_id].append((args[0], args[1], interval, curid))
            self.temp_upd.job_queue.run_repeating(
                self.check_rss,
                interval=datetime.timedelta(seconds=interval),
                context=(update.message.chat_id, (args[0], args[1], interval, curid))
            )
            bot.send_message(chat_id = update.message.chat_id,
                             text = "Your RSS feed has been registered.",
                             disable_notification = True)
    @bot_command
    def execute_feeds(self, bot, update, args):
        chatid = update.message.chat_id
        if chatid in self.feeddict.keys():
            if self.feeddict[chatid] is None or len(self.feeddict[chatid]) < 1:
                bot.send_message(chat_id = chatid,
                                 text = "You don't have any feeds registered.",
                                 disable_notification = True)
                return
            out = "*Your RSS feeds:*"
            for idx, item in enumerate(self.feeddict[chatid]):
                out += '\n{}: {} ({})'.format(idx, item[0], self.int_opts_r[item[2]])
            bot.send_message(chat_id = chatid,
                             parse_mode = ParseMode.MARKDOWN,
                             text = out,
                             disable_notification = False)
        else:
            bot.send_message(chat_id = chatid,
                             text = "You don't have any feeds registered.",
                             disable_notification = True)
    @bot_command
    def execute_feeddel(self, bot, update, args):
        if len(args) != 1:
            bot.send_message(chat_id = update.message.chat_id,
                             text = "This doesn't seem like correct usage of /rssdel.",
                             disable_notification = True)
            return
        chatid = update.message.chat_id
        if chatid in self.feeddict.keys():
            if self.feeddict[chatid] is None or len(self.feeddict[chatid]) < 1:
                bot.send_message(chat_id = chatid,
                                 text = "You don't have any feeds registered.",
                                 disable_notification = True)
                return
            if args[0].isdigit() and 0 <= int(args[0]) < len(self.feeddict[chatid]):
                self.feeddict[chatid].pop(int(args[0]))
                out = "Feed deleted successfully."
                if len(self.feeddict[chatid]) > 0:
                    out += "\n\n*Remaining RSS feeds:*"
                    for idx, item in enumerate(self.feeddict[chatid]):
                        out += '\n{}: {} ({})'.format(idx, item[0], self.int_opts_r[item[2]])
                else:
                    out += " You have no feeds remaining."
                bot.send_message(chat_id = chatid,
                                 parse_mode = ParseMode.MARKDOWN,
                                 text = out,
                                 disable_notification = False)
            else:
                bot.send_message(chat_id = chatid,
                                 text = "This is not a valid feed index.",
                                 disable_notification = True)
                return
        else:
            bot.send_message(chat_id = chatid,
                             text = "You don't have any feeds registered.",
                             disable_notification = True)
