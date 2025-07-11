# 💬 Botcasso — Self-Hosted Telegram Expense Tracker

A minimalist, self-hosted Telegram bot that helps you log daily expenses through natural language — via simple chat messages. No dashboards, no friction.

---

## 🚀 Why I Built This

I’ve tried budgeting apps, Notion templates, spreadsheets… but none of them stuck.

They were either too complex, required too many taps, or simply felt disconnected from my real-time spending behavior.

So I built something closer to how I already act: **I just text it.**

---

## 🛠️ What It Does

You just send a message to the bot like:

```
Coffee 3.5
Uber 16
Groceries 42.9
```

It:
- ✅ Parses the amount and text
- ✅ Auto-tags the category (`"coffee"` → *Food & Drinks*)
- ✅ Stores your expenses locally (no cloud!)
- ✅ Sends a **weekly summary report** back to you

---

## ⚙️ Tech Stack

- Python 🐍
- [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot)
- Local storage via CSV / JSON
- No database, no web server

---

## 🧪 Getting Started

### 1. Clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/telegram-invoice-bot.git
cd telegram-invoice-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
# or manually:
pip install python-telegram-bot==20.7
```

### 3. Run the bot

Create a bot on Telegram via [@BotFather](https://t.me/BotFather) and get your token.

Then run:

```bash
export BOT_TOKEN="your-token-here"
python bot.py
```

---

## 📊 Example Output

```
🧾 Weekly Summary:
- Food & Drinks: $23.5
- Transport: $45.0
- Subscriptions: $9.99
```

---

## 🧱 File Structure

```
├── bot.py              # Main bot logic
├── invoices.csv        # Expense data storage
├── README.md           # This file
└── requirements.txt    # Dependencies
```

---

## 🔮 Planned Features

- [ ] CSV export
- [ ] Google Sheets sync
- [ ] Smarter NLP classification
- [ ] Multi-user support

---

## 🛡️ Privacy & Hosting

- No third-party APIs
- 100% local
- You control your data

---

## 🧠 Inspired By

This was originally a weekend project — but has since made me more mindful about small, recurring expenses.

Typing into chat feels more *real* than clicking buttons in an app.

---

## 💬 Got Feedback?

Built something similar? Want to suggest a feature?  
Open an issue or drop a pull request!

---

## 📄 License

MIT License
