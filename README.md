# soraya_chatbot

This software powers the Soraya ([@SliceOfFileBot]) chatbot on Telegram. It
uses the [python-telegram-bot] library to receive and reply to messages, and
the [OpenAI] API to generate the actual reply content.

### Demo

Please note that Soraya is not programmed to interact with private messages, or
any messages circulating within arbitrary Telegram groups. Currently, it can be
interacted with only on the following public communities:

- [H2HC - Hackers to Hackers Conference](https://t.me/h2hconference)
- [Hardware Hacking Brasil](https://t.me/hardwareHackingBrasil)
- [Manutenção de Computadores e Eletrônicos](https://t.me/grupodosuportetecnico)

### Running

This project is designed to operate as a container. Simply execute the `up.sh`
script located in the root directory to set up a local testing environment.
This script will trigger the creation of an environment as outlined in the
`docker-compose.yml` file.

### Configuration

To customize the chatbot's behavior, edit the `chatbot.conf.yml` file located
in the `conf` directory.

### Contributing

Contributions are welcome! If you'd like to contribute, please fork this
repository, make your changes, and submit a pull request.
### License

This project is released under [The Unlicense].

[@SliceOfFileBot]: https://t.me/SliceOfFileBot
[OpenAI]: https://github.com/openai/openai-python
[python-telegram-bot]: https://github.com/python-telegram-bot/python-telegram-bot/
[The Unlicense]: LICENSE.txt