import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
TOKEN = os.getenv("BOT_TOKEN")
GENERAL_CONTACT = '0086465604'
CUSTOMER_SERVICE_BOT = '@kana_foods_bot'

PRODUCTS = {
    "mozzarella_cheese": {"name": "🧀 Mozzarella Cheese", "price": 800, "unit": "per unit"},
    "provolone_cheese": {"name": "🧀 Provolone Cheese", "price": 930, "unit": "per unit"},
    "chicken_whole": {"name": "🐔 Whole Chicken", "price": 650, "unit": "per unit"},
    "chicken_breast": {"name": "🍗 Chicken Breast", "price": 1080, "unit": "per kg"},
    "table_butter": {"name": "🧈 Table Butter", "price": 240, "unit": "per unit"},
}

user_carts = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_product_list_keyboard():
    keyboard = []
    for key, product in PRODUCTS.items():
        button_text = f"{product['name']} - {product['price']} ({product['unit']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"add_{key}")])
    keyboard.append([InlineKeyboardButton("🛒 View Cart and Checkout", callback_data='view_cart')])
    return InlineKeyboardMarkup(keyboard)

def get_cart_summary(user_id):
    cart = user_carts.get(user_id, {})
    if not cart:
        return "Your cart is currently empty! Use /menu to start ordering.", 0
    summary = ["*🛒 Your Current Order (Kana Foods)*\n"]
    total_cost = 0
    for key, quantity in cart.items():
        if quantity > 0 and key in PRODUCTS:
            product = PRODUCTS[key]
            line_total = product['price'] * quantity
            total_cost += line_total
            summary.append(f"• {quantity}x {product['name']} @ {product['price']} = {line_total}")
    summary.append(f"\n*💰 Total Cost: {total_cost}*")
    return "\n".join(summary), total_cost

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 Hello, {user.full_name}! Welcome to the *Kana Foods* order bot.\n\n"
        "I can help you place bulk orders for high-quality food products.\n\n"
        "Use /menu to see our products or /cart to view your current order."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*🍽️ Kana Foods Product Catalog*\n\n"
        "Tap a product to add one unit to your cart. View your cart to adjust quantities.",
        reply_markup=get_product_list_keyboard(),
        parse_mode='Markdown'
    )

async def cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    summary, _ = get_cart_summary(user_id)
    keyboard = [
        [InlineKeyboardButton("✅ Checkout Order", callback_data='checkout')],
        [InlineKeyboardButton("🗑️ Clear Cart", callback_data='clear_cart')]
    ]
    await update.message.reply_text(
        summary,
        reply_markup=InlineKeyboardMarkup(keyboard) if user_carts.get(user_id) else None,
        parse_mode='Markdown'
    )

async def checkout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    summary, _ = get_cart_summary(user_id)
    if not user_carts.get(user_id):
        await update.message.reply_text("Your cart is empty. Nothing to check out.")
        return
    order_details = summary + "\n\n"
    order_details += (
        "*--- Next Steps ---*\n"
        "To finalize your order, please copy your order details above and contact us using the information below.\n\n"
        f"**📞 General Contact:** `{GENERAL_CONTACT}`\n"
        f"**👤 Your User ID:** `{user_id}`\n\n"
        "*Your cart has been cleared.* Thank you for ordering with Kana Foods!"
    )
    await update.message.reply_text(order_details, parse_mode='Markdown')
    if user_id in user_carts:
        del user_carts[user_id]

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if data.startswith('add_'):
        product_key = data[4:]
        if user_id not in user_carts:
            user_carts[user_id] = {}
        user_carts[user_id][product_key] = user_carts[user_id].get(product_key, 0) + 1
        product_name = PRODUCTS.get(product_key, {}).get("name", "Item")
        await query.edit_message_caption(
            caption=f"Added 1x {product_name}. Total in cart: {user_carts[user_id][product_key]}.",
            reply_markup=get_product_list_keyboard()
        )
    elif data == 'view_cart':
        summary, _ = get_cart_summary(user_id)
        keyboard = [
            [InlineKeyboardButton("✅ Checkout Order", callback_data='checkout')],
            [InlineKeyboardButton("🗑️ Clear Cart", callback_data='clear_cart')],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back_to_menu')]
        ]
        await query.edit_message_text(
            summary,
            reply_markup=InlineKeyboardMarkup(keyboard) if user_carts.get(user_id) else get_product_list_keyboard(),
            parse_mode='Markdown'
        )
    elif data == 'clear_cart':
        if user_id in user_carts:
            del user_carts[user_id]
            message = "🗑️ Your cart has been completely cleared."
        else:
            message = "Your cart was already empty."
        await query.edit_message_text(
            message + "\n\nUse /menu to start a new order.",
            reply_markup=get_product_list_keyboard()
        )
    elif data == 'checkout':
        await checkout_command(update, context)
    elif data == 'back_to_menu':
        await query.edit_message_text(
            "*🍽️ Kana Foods Product Catalog*\n\n"
            "Tap a product to add one unit to your cart. View your cart to adjust quantities.",
            reply_markup=get_product_list_keyboard(),
            parse_mode='Markdown'
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("cart", cart_command))
    app.add_handler(CommandHandler("checkout", checkout_command))
    app.add_handler(CallbackQueryHandler(button_callback))

    PORT = int(os.environ.get("PORT", 8443))
    webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"

    print(f"Starting webhook at {webhook_url}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()
