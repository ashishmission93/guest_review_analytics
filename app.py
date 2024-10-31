import subprocess
import sys
import os
import openai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import time

# Function to install necessary packages if missing
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of required packages
required_packages = ['Flask', 'openai', 'python-dotenv', 'gunicorn']

# Install each required package
for package in required_packages:
    try:
        __import__(package)  # Try to import the package
    except ImportError:
        install(package)  # If the package is not found, install it

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# A global list to maintain conversation history between the user and the bot
conversation_history = []

# Helper function to format messages with timestamps
def format_message(sender, message):
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    return {"sender": sender, "message": message, "timestamp": timestamp}

# Home route that loads the chat interface
@app.route("/")
def home():
    return render_template("index.html")

# Chat endpoint to handle user messages
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    
    if not user_message:
        return jsonify({"response": "Please enter a message to start the chat!"})

    # Append the user's message to the conversation history
    conversation_history.append(format_message("You", user_message))
    
    try:
        # Insert initial conversation context to make the bot behave like a hotel concierge
        messages = [{"role": "system", "content": "You are a helpful hotel concierge bot."}]
        
        # Add the conversation history (user and bot messages) to provide context
        for msg in conversation_history:
            role = "user" if msg["sender"] == "You" else "assistant"
            messages.append({"role": role, "content": msg["message"]})

        # Call the OpenAI API with the conversation history to get a dynamic response from GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use GPT-4 model for enhanced capabilities
            messages=messages,
            max_tokens=300  # You can adjust the token limit based on your needs
        )
        
        # Extract the bot's response
        bot_response = response.choices[0].message["content"].strip()
        
        # Append the bot's response to the conversation history
        conversation_history.append(format_message("Bot", bot_response))
        
    except openai.error.InvalidRequestError as e:
        bot_response = "Sorry, there was a problem with the request. Please try again later."
        print(f"InvalidRequestError: {e}")
        
    except openai.error.RateLimitError as e:
        bot_response = "Sorry, I'm receiving too many requests at the moment. Please try again after a few seconds."
        print(f"RateLimitError: {e}")
        
    except Exception as e:
        bot_response = "Sorry, I couldn't process your request. Please try again."
        print(f"Error occurred: {e}")

    # Return the bot's response as JSON
    return jsonify({"response": bot_response, "history": conversation_history})

# Endpoint to clear the conversation history (to restart the chat)
@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    global conversation_history
    conversation_history = []
    return jsonify({"message": "Chat history cleared successfully!"})

if __name__ == "__main__":
    app.run(debug=True)
