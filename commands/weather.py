# Weather plugin
# Commands:
#   - /weather, /w
# Monitors: None
# Configuration:
# command.weather:
#   api_key: "OWM API Key"

import shlex
import urllib
import openweathermapy.core as owm
from telegram import ParseMode
from .basic import *

class Weather(CommandBase):
    name = "Weather"
    safename = "weather"   
    def __init__(self, logger):
        super().__init__(logger)
        self.to_register = [
            CommandInfo("weather", self.execute, "Get a location's weather.", alias="w"),
        ]
    def get_help_msg(self, cmd):
        return "Call /{} <city>,<country> where country is the 2-letter country code.".format(cmd)
    def load_config(self, confdict):
        self.settings = {
            "units": "metric",
            "lang": "en",
            "APPID": confdict["api_key"]
        }
    # https://gist.github.com/RobertSudwarts/acf8df23a16afdb5837f
    # Ultra crap but it'll do for now.
    def card(self, d):
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        ix = int((d + 11.25)/22.5 - 0.02)
        return dirs[ix % 16]
    def execute(self, bot, update):
        try:
            args = shlex.split(update.message.text)
            if len(args) != 2:
                bot.send_message(chat_id = update.message.chat_id,
                                 text = "This doesn't seem like correct usage of /weather.",
                                 disable_notification = True)
                return
            data = owm.get_current(args[1], **self.settings)
            temp, tmin, tmax = data('main.temp', 'main.temp_min', 'main.temp_max')
            form = "<b>Weather for {}, {}:</b>\n".format(data['name'], data['sys']['country'])
            form += " - {}\n".format(data['weather'][0]['description'].capitalize())
            form += " - Current {:.1f}°C / High {:.1f}°C / Low {:.1f}°C\n".format(temp, tmax, tmin)
            form += " - Wind: {:.1f} km/h".format(data['wind']['speed'])
            if 'deg' in data['wind']:
                form += " {}".format(self.card(data['wind']['deg']))
            if 'gust' in data['wind']:
                form += " (Gust: {:.1f} km/h)".format(data['wind']['gust'])
            bot.send_message(chat_id = update.message.chat_id,
                             parse_mode = ParseMode.HTML,
                             text = form,
                             disable_notification = True)
            self.logger.info("Command /weather executed successfully.")
        except urllib.error.HTTPError:
            bot.send_message(chat_id = update.message.chat_id,
                             text = "The location you chose seems to be invalid.",
                             disable_notification = True)
        except Exception as e:
            self.logger.error(e)