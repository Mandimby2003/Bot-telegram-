import logging
import re
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define conversation states
EMAIL, INVESTMENT_INTEREST, CRYPTO_CHOICE, DEPOSIT_AMOUNT, TRANSACTION_HASH = range(5)

# Cryptocurrency addresses
CRYPTO_ADDRESSES = {
    'BTC': 'bc1qs3lcvtyvg9cp7kedh5m8vtsxlw8fd2upsuf85p',
    'TRX': 'TG3KFy2fFTW29xrSbUwB6gszXRoCRNyyQq',
    'ETH': '0x2cc1DF075FE19D46CEde20E68E8F94E62cB3D3eB',
    'DOGE': 'D6csY9GbUGax2hos7WMbioHqrYoLShfBBz',
    'USDT (TRC20)': 'TG3KFy2fFTW29xrSbUwB6gszXRoCRNyyQq'
}

# Function to get current exchange rates (placeholder)
def get_current_rates():
    # In a real system, this would make an API call to get current rates
    return {
        'BTC': 0.00009,
        'TRX': 25,
        'ETH': 0.001,
        'DOGE': 22,
        'USDT (TRC20)': 5
    }

# Function to verify transaction hash (placeholder)
def verify_transaction(crypto, amount, hash):
    # In a real system, this would check the blockchain for the transaction
    # For this example, we'll just return True if the hash is not empty
    return bool(hash.strip())

def start(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()  # Clear any existing user data
    update.message.reply_text(
        "Welcome! To get started, please enter your email address for registration."
    )
    return EMAIL

def email(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    email = update.message.text
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        update.message.reply_text("Please enter a valid email address.")
        return EMAIL
    
    logger.info("Email of %s: %s", user.first_name, email)
    context.user_data['email'] = email
    
    reply_keyboard = [['Yes', 'No']]
    update.message.reply_text(
        "Thank you for providing your email. Are you interested in investing?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return INVESTMENT_INTEREST

def investment_interest(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    logger.info("Investment interest of %s: %s", user.first_name, text)
    
    if text.lower() == 'yes':
        reply_keyboard = [['BTC', 'TRX', 'ETH'], ['DOGE', 'USDT (TRC20)']]
        update.message.reply_text(
            "Great! Please choose your preferred cryptocurrency for deposit:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return CRYPTO_CHOICE
    else:
        update.message.reply_text(
            "Thank you for your interest. If you change your mind, feel free to start over.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

def crypto_choice(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    crypto = update.message.text
    logger.info("Crypto choice of %s: %s", user.first_name, crypto)
    
    min_deposits = get_current_rates()
    if crypto not in min_deposits:
        update.message.reply_text("Please choose a valid cryptocurrency from the options provided.")
        return CRYPTO_CHOICE
    
    context.user_data['crypto'] = crypto
    
    update.message.reply_text(
        f"You've chosen {crypto}. Please enter the amount you wish to deposit. "
        f"The current minimum deposit for {crypto} is {min_deposits[crypto]} {crypto}.",
        reply_markup=ReplyKeyboardRemove()
    )
    return DEPOSIT_AMOUNT

def deposit_amount(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    amount_text = update.message.text
    crypto = context.user_data['crypto']
    
    try:
        amount = float(amount_text)
    except ValueError:
        update.message.reply_text("Please enter a valid number for the deposit amount.")
        return DEPOSIT_AMOUNT
    
    min_deposits = get_current_rates()
    if amount < min_deposits[crypto]:
        update.message.reply_text(
            f"The current minimum deposit for {crypto} is {min_deposits[crypto]} {crypto}. "
            "Please enter a higher amount."
        )
        return DEPOSIT_AMOUNT
    
    logger.info("Deposit amount of %s: %s %s", user.first_name, amount, crypto)
    context.user_data['amount'] = amount
    
    address = CRYPTO_ADDRESSES[crypto]
    update.message.reply_text(
        f"Great! You're depositing {amount} {crypto}. "
        f"Send with this address {crypto}: {address}\n\n"
        "After sending, please provide the transaction hash for verification."
    )
    return TRANSACTION_HASH

def transaction_hash(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    hash = update.message.text
    crypto = context.user_data['crypto']
    amount = context.user_data['amount']
    
    logger.info("Transaction hash from %s: %s", user.first_name, hash)
    
    update.message.reply_text("Please wait while we check your deposit...")
    
    if verify_transaction(crypto, amount, hash):
        update.message.reply_text(
            "Your deposit has been confirmed! Our team will process your investment "
            "and contact you shortly with further details."
        )
        # Here you would typically update the user's account, send notifications, etc.
    else:
        update.message.reply_text(
            "We couldn't verify your transaction. Please check the hash and try again, "
            "or contact our support team for assistance."
        )
        return TRANSACTION_HASH
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Investment process canceled. Feel free to start over when you're ready.',
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main() -> None:
    TOKEN = os.environ.get("BOT_TOKEN", "6564018550:AAHamZKCY7dmM2DHlROOJ5p8wx4Iis7pRPE")
    PORT = int(os.environ.get("PORT", "8443"))
    HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, email)],
            INVESTMENT_INTEREST: [MessageHandler(Filters.regex('^(Yes|No)$'), investment_interest)],
            CRYPTO_CHOICE: [MessageHandler(Filters.text & ~Filters.command, crypto_choice)],
            DEPOSIT_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, deposit_amount)],
            TRANSACTION_HASH: [MessageHandler(Filters.text & ~Filters.command, transaction_hash)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url=f"https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}")

    updater.idle()

if __name__ == '__main__':
    main()