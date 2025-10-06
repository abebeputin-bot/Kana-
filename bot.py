import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, CallbackContext
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8422253254:AAFrac-FRl65zjZQ-T7d0B4uZ0yv90HiX2s"
ADMIN_CHAT_ID = 5763697888
CONTACT_NUMBER = "0086465604"

PRODUCTS = {
    "Mozzarella Cheese": 800,
    "Provolone Cheese": 930,
    "Chicken": 650,
    "Chicken Breast": 1080,
    "Table Butter": 240
}

CARTS = {}

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    keyboard = [[InlineKeyboardButton(p, callback_data=f"add_{p}")]
                for p in PRODUCTS.keys()]
    keyboard.append([InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        f"👋 Welcome to *Kana Foods*, {user.first_name}!
\n"
        "We deliver premium dairy & poultry products straight to your kitchen.\n\n"
        "📦 Select your product below:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("add_"):
        product = data.split("add_")[1]
        CARTS.setdefault(user_id, {})
        CARTS[user_id][product] = CARTS[user_id].get(product, 0) + 1
        query.edit_message_text(
            text=f"✅ Added *{product}* to your cart!\n\nSelect more items or view your cart.",
            parse_mode="Markdown"
        )
        start(update, context)

    elif data == "view_cart":
        show_cart(update, context, user_id)

def show_cart(update: Update, context: CallbackContext, user_id):
    query = update.callback_query
    cart = CARTS.get(user_id, {})
    if not cart:
        query.edit_message_text("🛒 Your cart is empty!")
        return

    message = "🛍 *Your Cart:*\n\n"
    total = 0
    for item, qty in cart.items():
        price = PRODUCTS[item] * qty
        message += f"{item} x{qty} = {price} ETB\n"
        total += price
    message += f"\n💰 *Total:* {total} ETB"

    keyboard = [
        [InlineKeyboardButton("✅ Place Order", callback_data="place_order")],
        [InlineKeyboardButton("🧹 Clear Cart", callback_data="clear_cart")]
    ]
    query.edit_message_text(
        text=message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def place_order(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    cart = CARTS.get(user_id, {})

    if not cart:
        query.edit_message_text("🛒 Your cart is empty!")
        return

    total = sum(PRODUCTS[item] * qty for item, qty in cart.items())
    order_text = f"🧾 *New Order from {user.first_name}:*\n\n"
    for item, qty in cart.items():
        order_text += f"{item} x{qty} = {PRODUCTS[item]*qty} ETB\n"
    order_text += f"\n💰 *Total:* {total} ETB\n📞 Contact: {CONTACT_NUMBER}"

    context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=order_text,
        parse_mode="Markdown"
    )

    query.edit_message_text(
        "✅ Your order has been placed successfully!\n\n"
        "We'll contact you soon to confirm delivery.\n"
        f"For inquiries call 📞 {CONTACT_NUMBER}"
    )

    CARTS[user_id] = {}

def clear_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    CARTS[user_id] = {}
    query.edit_message_text("🧹 Your cart has been cleared.")
    start(update, context)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_button))
    dp.add_handler(CallbackQueryHandler(place_order, pattern="place_order"))
    dp.add_handler(CallbackQueryHandler(clear_cart, pattern="clear_cart"))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
