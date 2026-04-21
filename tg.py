# tg.py
import telebot
from logic import WORKING_MODELS, get_gemini_response_stream, chat_histories

# Your Telegram Bot Token
BOT_TOKEN = "8618494639:AAE4s33S3rE5IPQK1FYCLrhwF1Kjw5_Lj38"

bot = telebot.TeleBot(BOT_TOKEN)

# Dictionary to store the selected model for each user
# Format: {chat_id: model_string}
user_models = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Greets the user and shows the command menu."""
    welcome_text = (
        "🤖 *Welcome to AI Hub Bot!*\n\n"
        "I am ready to chat and help you with code, text, or anything else. "
        "I have memory context, so we can have a continuous conversation.\n\n"
        "🛠 *Available Commands:*\n"
        "/models - View the list of all available AI models\n"
        "/set <number> - Choose a specific model to chat with\n"
        "/clear - Erase our current chat memory and start fresh\n"
        "/info - Check which model is currently active\n"
        "/help - Show this message again"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['models'])
def list_models(message):
    """Shows the list of available models."""
    msg = "📚 *Available Models:*\n\n"
    for i, model in enumerate(WORKING_MODELS):
        clean_name = model.split('/')[-1]
        msg += f"*{i + 1}.* `{clean_name}`\n"
    
    msg += "\nTo select a model, type `/set <number>` (e.g., `/set 3`)."
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['set'])
def set_model(message):
    """Handles the model selection."""
    parts = message.text.split()
    
    if len(parts) == 1:
        bot.reply_to(message, "⚠️ Please provide a model number. Example: `/set 1`\nUse /models to see the list.", parse_mode="Markdown")
        return

    try:
        model_index = int(parts[1]) - 1
        
        if 0 <= model_index < len(WORKING_MODELS):
            selected_model = WORKING_MODELS[model_index]
            user_models[message.chat.id] = selected_model
            clean_name = selected_model.split('/')[-1]
            bot.reply_to(message, f"✅ Model successfully set to: *{clean_name}*", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Invalid number. Please check the list using /models.")
            
    except ValueError:
        bot.reply_to(message, "❌ Please provide a valid number. Example: `/set 1`", parse_mode="Markdown")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    """Clears the chat history for the current user."""
    chat_id = str(message.chat.id)
    
    # Access the global dictionary from logic.py and clear the specific user's memory
    if chat_id in chat_histories:
        chat_histories[chat_id] = []
        
    bot.reply_to(message, "🧹 *Chat memory cleared!*\nWe are starting with a blank slate.", parse_mode="Markdown")

@bot.message_handler(commands=['info'])
def show_info(message):
    """Shows current settings for the user."""
    chat_id = message.chat.id
    str_chat_id = str(chat_id)
    
    current_model = user_models.get(chat_id, WORKING_MODELS[0])
    clean_name = current_model.split('/')[-1]
    
    # Calculate how many messages are in the current context
    history_length = len(chat_histories.get(str_chat_id, []))
    
    info_text = (
        "📊 *Current Session Info:*\n\n"
        f"🧠 *Active Model:* `{clean_name}`\n"
        f"📝 *Messages in Memory:* `{history_length}`\n\n"
        "Use /clear to wipe the memory if the AI gets confused."
    )
    bot.reply_to(message, info_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    """Handles regular text messages and communicates with the AI backend."""
    chat_id = message.chat.id
    user_text = message.text
    
    current_model = user_models.get(chat_id, WORKING_MODELS[0])
    
    # Show typing action
    bot.send_chat_action(chat_id, 'typing')
    
    # Send a temporary waiting message
    wait_msg = bot.reply_to(message, "⏳ *Thinking...*", parse_mode="Markdown")
    
    try:
        # Fetch the stream from logic.py
        response_stream = get_gemini_response_stream(
            model_name=current_model,
            prompt=user_text,
            chat_id=str(chat_id)
        )
        
        # Combine chunks into a single response
        full_response = ""
        for chunk in response_stream:
            if chunk:
                full_response += chunk
                
        # Delete the "Thinking..." message
        bot.delete_message(chat_id, wait_msg.message_id)
            
        # Send the actual response (handling the 4096 character limit of Telegram)
        if len(full_response) > 4096:
            for x in range(0, len(full_response), 4096):
                bot.send_message(chat_id, full_response[x:x+4096])
        else:
            bot.reply_to(message, full_response)
            
    except Exception as e:
        bot.edit_message_text(f"❌ System Error: {str(e)}", chat_id, wait_msg.message_id)

if __name__ == '__main__':
    print("[*] Starting Advanced Telegram Bot...")
    bot.infinity_polling()