import os
import pandas as pd
import openai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from textblob import TextBlob
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Sentiment analysis with TextBlob
def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.3:
        return "positive", polarity
    elif polarity < -0.3:
        return "negative", polarity
    else:
        return "neutral", polarity

# Enhanced sentiment analysis using OpenAI
def advanced_sentiment_analysis(text):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Classify the sentiment and main emotion in this review: '{text}'",
            max_tokens=50
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Unable to classify sentiment with OpenAI."

# Home route - Dashboard
@app.route("/")
def home():
    return render_template("dashboard.html")

# Route to handle CSV upload, filtering, and analysis
@app.route("/upload", methods=["POST"])
def upload():
    # Check for file upload
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if file:
        # Save the uploaded file
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        # Read CSV and perform sentiment analysis
        try:
            df = pd.read_csv(filepath)
            if "review" not in df.columns or "rating" not in df.columns or "date" not in df.columns:
                return jsonify({"error": "CSV file must contain 'date', 'review', and 'rating' columns"}), 400
            
            # Convert date column to datetime format for filtering
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
            df = df.dropna(subset=["date"])

            # Perform TextBlob-based sentiment analysis
            df[["sentiment", "polarity"]] = df["review"].apply(lambda text: pd.Series(analyze_sentiment(text)))
            
            # Filter data if date range is provided
            start_date = request.form.get("start_date")
            end_date = request.form.get("end_date")
            if start_date and end_date:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            # Filter data by rating if provided
            min_rating = int(request.form.get("min_rating", 1))
            max_rating = int(request.form.get("max_rating", 5))
            df = df[(df["rating"] >= min_rating) & (df["rating"] <= max_rating)]

            # Perform advanced sentiment analysis using OpenAI
            df["advanced_sentiment"] = df["review"].apply(advanced_sentiment_analysis)

            # Calculate summary statistics
            avg_rating = df["rating"].mean()
            sentiment_counts = df["sentiment"].value_counts().to_dict()

            # Highlight most positive and negative reviews
            most_positive_review = df.loc[df["polarity"].idxmax()]["review"]
            most_negative_review = df.loc[df["polarity"].idxmin()]["review"]

            # Prepare data for response
            data = {
                "avg_rating": avg_rating,
                "sentiment_counts": sentiment_counts,
                "most_positive_review": most_positive_review,
                "most_negative_review": most_negative_review,
                "reviews": df[["date", "review", "rating", "sentiment", "advanced_sentiment"]].to_dict(orient="records")
            }
            return jsonify(data)
        
        except Exception as e:
            print(f"Error processing file: {e}")
            return jsonify({"error": "An error occurred while processing the file"}), 500

    return jsonify({"error": "File upload failed"}), 400

if __name__ == "__main__":
    app.run(debug=True)
