import os
from io import BytesIO
import csv
import smtplib
from email.message import EmailMessage
from datetime import datetime

from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# States for the conversation
# Client -> Date -> Items (name & amount loop) -> Tax -> Sender -> optional Email
CLIENT, DATE, ITEM_NAME, ITEM_AMOUNT, TAX, SENDER, EMAIL = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with instructions."""
    await update.message.reply_text(
        "Welcome! Use /invoice to create a new invoice or /last_invoice to retrieve the previous one."
    )


async def invoice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Begin invoice creation process."""
    context.user_data.clear()
    context.user_data["items"] = []
    await update.message.reply_text("Please enter the client name:")
    return CLIENT


async def client_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store client name and ask for date."""
    context.user_data["client_name"] = update.message.text
    await update.message.reply_text(
        "Enter invoice date (YYYY-MM-DD) or /skip for today:" 
    )
    return DATE


async def date_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store provided date or today's date."""
    context.user_data["date"] = update.message.text
    return await prompt_item_name(update, context)


async def skip_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["date"] = datetime.today().strftime("%Y-%m-%d")
    return await prompt_item_name(update, context)


async def prompt_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter item name or /done when finished:")
    return ITEM_NAME


async def item_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_item_name"] = update.message.text
    await update.message.reply_text("Enter amount for this item:")
    return ITEM_AMOUNT


async def item_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number:")
        return ITEM_AMOUNT
    context.user_data["items"].append({"name": context.user_data.pop("current_item_name"), "amount": amount})
    return await prompt_item_name(update, context)


async def items_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter tax percentage or /skip:")
    return TAX


async def tax_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["tax"] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number:")
        return TAX
    await update.message.reply_text("Enter sender information (company or your name):")
    return SENDER


async def skip_tax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["tax"] = 0.0
    await update.message.reply_text("Enter sender information (company or your name):")
    return SENDER


async def sender_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["sender"] = update.message.text
    pdf_bytes, total = generate_invoice(context.user_data)
    context.user_data["last_invoice"] = pdf_bytes.getvalue()
    await update.message.reply_document(document=InputFile(pdf_bytes, filename="invoice.pdf"))
    save_history(context.user_data["client_name"], context.user_data.get("date"), total)
    await update.message.reply_text("Enter email address to send invoice or /skip:")
    return EMAIL


async def email_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    try:
        send_email(BytesIO(context.user_data["last_invoice"]), email)
        await update.message.reply_text("Invoice sent via email!")
    except Exception as exc:
        await update.message.reply_text(f"Failed to send email: {exc}")
    return ConversationHandler.END


async def skip_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Invoice creation finished.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Invoice creation canceled.")
    return ConversationHandler.END

async def last_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resend the last generated invoice."""
    pdf = context.user_data.get("last_invoice")
    if pdf:
        await update.message.reply_document(InputFile(BytesIO(pdf), filename="invoice.pdf"))
    else:
        await update.message.reply_text("No invoice available.")


def generate_invoice(data: dict) -> tuple[BytesIO, float]:
    """Create a PDF invoice and return it with the total amount."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Date: {data['date']}")
    c.drawString(50, height - 100, f"Bill To: {data['client_name']}")
    c.drawString(50, height - 120, f"From: {data['sender']}")

    y = height - 160
    c.drawString(50, y, "Items:")
    y -= 20
    subtotal = 0.0
    for item in data["items"]:
        c.drawString(60, y, f"{item['name']}: ${item['amount']:.2f}")
        subtotal += item['amount']
        y -= 20

    c.drawString(50, y, f"Subtotal: ${subtotal:.2f}")
    y -= 20
    total = subtotal
    tax = data.get("tax", 0.0)
    if tax:
        tax_amount = subtotal * tax / 100
        c.drawString(50, y, f"Tax ({tax:.2f}%): ${tax_amount:.2f}")
        total += tax_amount
        y -= 20

    c.drawString(50, y, f"Total: ${total:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer, total


def save_history(client: str, date: str, total: float) -> None:
    """Append invoice info to a CSV file."""
    file = "invoices.csv"
    write_header = not os.path.exists(file)
    with open(file, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["client", "date", "total"])
        writer.writerow([client, date, f"{total:.2f}"])


def send_email(pdf: BytesIO, recipient: str) -> None:
    """Send PDF via SMTP as an attachment."""
    smtp_host = os.environ.get("SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SMTP_PORT", "25"))
    sender_email = os.environ.get("SMTP_SENDER", "noreply@example.com")

    msg = EmailMessage()
    msg["Subject"] = "Invoice"
    msg["From"] = sender_email
    msg["To"] = recipient
    msg.set_content("Please find attached invoice.")
    msg.add_attachment(
        pdf.getvalue(),
        maintype="application",
        subtype="pdf",
        filename="invoice.pdf",
    )

    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.send_message(msg)


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("Please set the BOT_TOKEN environment variable.")

    application = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("invoice", invoice_command)],
        states={
            CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_received)],
            DATE: [CommandHandler("skip", skip_date), MessageHandler(filters.TEXT & ~filters.COMMAND, date_received)],
            ITEM_NAME: [CommandHandler("done", items_done), MessageHandler(filters.TEXT & ~filters.COMMAND, item_name_received)],
            ITEM_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, item_amount_received)],
            TAX: [CommandHandler("skip", skip_tax), MessageHandler(filters.TEXT & ~filters.COMMAND, tax_received)],
            SENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, sender_received)],
            EMAIL: [CommandHandler("skip", skip_email), MessageHandler(filters.TEXT & ~filters.COMMAND, email_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("last_invoice", last_invoice))
    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()