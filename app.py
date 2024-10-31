import os
import pandas as pd
import openai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from textblob import TextBlob  # For simple sentiment analysis

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Sentiment analysis function
def analyze_sentiment(text):
    analysis = TextBlob(text)
    return "positive" if analysis.sentiment.polarity > 0 else "negative" if analysis.sentiment.polarity < 0 else "neutral"

# Home route - Dashboard
@app.route("/")
def home():
    return render_template("dashboard.html")

# Route to handle CSV upload and sentiment analysis
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if file:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        # Read CSV and perform sentiment analysis
        df = pd.read_csv(filepath)
        df["sentiment"] = df["review"].apply(analyze_sentiment)
        
        # Generate summary statistics
        sentiment_counts = df["sentiment"].value_counts().to_dict()
        return jsonify({
            "sentiment_counts": sentiment_counts,
            "data": df.to_dict(orient="records")
        })

if __name__ == "__main__":
    app.run(debug=True)
