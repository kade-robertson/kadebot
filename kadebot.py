#!/usr/bin/python3

import os
import argparse

from commands.cat import Cat

from telegram.ext import Updater
from telegram.ext import CommandHandler
from ruamel.yaml import YAML
yaml = YAML(typ="safe", pure=True)

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

baseconf = dict()
commands = [Cat(logging)]

def main():
    updater = Updater(token = baseconf["api_key"])
    dispatcher = updater.dispatcher
    for cmd in commands:
        for name, func in cmd.to_register:
            print(name)
            dispatcher.add_handler(CommandHandler(name, func))
    updater.start_polling()

def load_config(filename):
    global baseconf
    conf = dict()
    with open(filename, 'r') as f:
        conf = yaml.load(f)
    baseconf = conf["base"]
    for cmd in commands:
        section = "command.{}".format(cmd.safename)
        if section in conf.keys():
            cmd.load_config(conf[section])
        
if __name__ == "__main__":
    parser  = argparse.ArgumentParser()
    parser.add_argument("--config", help="configuration file to use", type=str)
    args = parser.parse_args()
    if os.path.exists(args.config):
        load_config(args.config)
    main()