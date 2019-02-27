# Google plugin
# Commands:
#   - /google, /g
# Monitors: None
# Schedules: None
# Configuration:
#  csekey: Google Custom Search Engine key
#  apikey: Custom Search JSON API Key

import requests
import urllib.parse
from .basic import CommandBase, CommandInfo, bot_command

class Google(CommandBase):
    name = "Google"
    safename = "google"
    def __init__(self, logger):
        super().__init__(logger)
        self.to_register = [
            CommandInfo("google", self.execute, "Send a Google search link.", alias='g'),
            CommandInfo("gimage", self.execute_image, "Returns the first Google Image result for a query", alias='gi')
        ]
    def load_config(self, confdict):
        self.csekey = confdict['csekey']
        self.apikey = confdict['apikey']
    def get_help_msg(self, cmd):
        if cmd == "google" or cmd == "g":
            return "/{} <search> will produce a direct link to the Google search results for that query.".format(cmd)
        else:
            return "/{} <search> will send the first Google Image result to the chat.".format(cmd)
    @bot_command
    def execute(self, bot, update, args):
        search = ' '.join(args)
        gurl = 'https://www.google.ca/search?q={}'.format(urllib.parse.quote_plus(search))
        output = '<a href="{}">view results</a>'.format(gurl)
        bot.send_message(chat_id = update.message.chat_id,
                         text = output,
                         parse_mode = 'HTML',
                         disable_notification = True,
                         disable_web_page_preview = True)
    @bot_command
    def execute_image(self, bot, update, args):
        search = ' '.join(args)
        searchparams = {
            'key': self.apikey,
            'cx': self.csekey,
            'q': search,
            'num': 1,
            'imgSize': 'large',
            'searchType': 'image'
        }
        query = requests.get('https://www.googleapis.com/customsearch/v1', params = searchparams).json()
        if (not 'items' in query) or len(query['items']) < 1:
            bot.send_message(chat_id = update.message.chat_id,
                             text = 'No image results.',
                             disable_notification = True)
        else:
            bot.send_photo(chat_id = update.message.chat_id,
                           photo = query['items'][0]['link'])

