**this project is now in maintenance mode -- I will only be bugfixing, no new features will be added**

# kadebot

A Telegram chat bot, built in Python. This was not designed for mass-usage, rather you should host this yourself for a small number of chats. This was primarily designed around being used in one chat and some parts might not be able to scale as well. It was probably also not designed with good practices in mind, and there are absolutely no tests whatsoever.

# Configuration

The base set of configuration requires you to specify your Telegram bot token, any administrators (people you want to have access to /reload, /update, /kill), and you may disable any command, monitor, scheduled task, or even entire module you don't want to use. For example, your base section may look like this:
```yaml
base:
  api_key: "notarealkey"
  admins:
    - 1234567890
    - 8888888888
  disabled:
    - t
    - randomaww
  disabled_monitors: []
  disabled_schedules: []
  disabled_modules:
    - SonnetGen
```
Configuration for individual commands can be seen in the command file itself, or refer to the `default.yaml` to see what options are available.

# Development

1. Clone the repository.
2. Install the required dependencies for whichever modules you are using. If you want to use everything:
   ```
   pip install python-telegram-bot ruamel.yaml requests omdb praw translate wikipedia wolframalpha markovify openweathermapy emoji feedparser py_expression_eval
   ```
   or
   ```
   pip install -r requirements.txt
   ```
   You may need to run as `sudo` or with the `--user` flag if you don't have `sudo` priveledges. You will also need [populartimes](https://github.com/m-wrzr/populartimes) which is not available on PyPi if you plan on setting up the `/popular` command.
3. Get a bot token for Telegram, through @BotFather.
4. Get your user ID for Telegram, through @myidbot.
5. Modify `default.yaml` and configure whatever you would like. Optionally, copy the configuration to `~/.config/kadebot/kadebot.yaml` to avoid using the `--config` option.
6. Configure each plugin's configuration as specified in their files.
7. Run the bot in one of a few ways:
   ```
   ./kadeboy.py
   ./kadebot.py --config file.yaml
   python3 kadebot.py --config file.yaml
   ```
