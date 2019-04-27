# Cat plugin
# Commands:
#   - /cat
# Configuration: None

import requests
from .basic import CommandBase, CommandInfo, bot_command

class Cat(CommandBase):
    name = "Cat"
    safename = "cat"
    def __init__(self, logger):
        super().__init__(logger)
        self.to_register = [
            CommandInfo("cat", self.execute, "Displays a random cat image.")
        ]
    def get_help_msg(self, cmd):
        return "Call /cat with no arguments."
    @bot_command
    def execute(self, bot, update, args):
        data = requests.head("https://api.thecatapi.com/api/images/get")
        bot.send_photo(chat_id = update.message.chat_id, 
                       photo = data.headers["Location"],
                       disable_notification = True)
