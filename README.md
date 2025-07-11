# telegram-invoice-bot
A Telegram bot that helps freelancers automatically generate and send professional invoices.

This project contains a simple Telegram bot that creates PDF invoices on demand. It uses the [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot) and [`reportlab`](https://www.reportlab.com/dev/install/opensource/) libraries.

## Running locally

1. **Create a bot** on Telegram with [BotFather](https://core.telegram.org/bots#botfather) and obtain its token.
2. Clone this repository and install the dependencies:

   ```bash
   pip install python-telegram-bot==20.7 reportlab
