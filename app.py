import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from textblob import TextBlob
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Sentiment analysis function using TextBlob
def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.3:
        return "positive", polarity
    elif polarity < -0.3:
        return "negative", polarity
    else:
        return "neutral", polarity

# Home route - Renders the main dashboard
@app.route("/")
def home():
    return render_template("dashboard.html")

# Route to handle CSV file upload and analyze reviews
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if file:
        try:
            # Load the CSV file into a DataFrame
            df = pd.read_csv(file)
            if "date" not in df.columns or "review" not in df.columns or "rating" not in df.columns:
                return jsonify({"error": "CSV file must contain 'date', 'review', and 'rating' columns"}), 400
            
            # Convert date column to datetime format and drop rows with invalid dates
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
            df = df.dropna(subset=["date"])

            # Perform sentiment analysis on each review
            df[["sentiment", "polarity"]] = df["review"].apply(lambda text: pd.Series(analyze_sentiment(text)))
            
            # Calculate average rating, most positive, and most negative reviews
            avg_rating = df["rating"].mean()
            most_positive_review = df.loc[df["polarity"].idxmax()]["review"]
            most_negative_review = df.loc[df["polarity"].idxmin()]["review"]
            
            # Count sentiments
            sentiment_counts = df["sentiment"].value_counts().to_dict()

            # Prepare review data for display
            reviews = df[["date", "review", "rating", "sentiment"]].to_dict(orient="records")

            # Send analysis results as JSON response
            return jsonify({
                "avg_rating": avg_rating,
                "most_positive_review": most_positive_review,
                "most_negative_review": most_negative_review,
                "sentiment_counts": sentiment_counts,
                "reviews": reviews
            })

        except Exception as e:
            print(f"Error processing file: {e}")
            return jsonify({"error": "An error occurred while processing the file"}), 500

    return jsonify({"error": "File upload failed"}), 400

# Route to handle review filtering based on date range and rating range
@app.route("/filter", methods=["GET"])
def filter_reviews():
    try:
        # Load the uploaded file or data source here
        # Assuming the file was uploaded and stored in the previous route for simplicity
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], "uploaded_reviews.csv")
        df = pd.read_csv(filepath)

        # Parse and filter by date range
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        # Filter by rating range
        min_rating = request.args.get("min_rating", type=int)
        max_rating = request.args.get("max_rating", type=int)
        if min_rating is not None and max_rating is not None:
            df = df[(df["rating"] >= min_rating) & (df["rating"] <= max_rating)]

        # Perform sentiment analysis on filtered data
        df[["sentiment", "polarity"]] = df["review"].apply(lambda text: pd.Series(analyze_sentiment(text)))

        # Calculate average rating, most positive, and most negative reviews for filtered data
        avg_rating = df["rating"].mean()
        most_positive_review = df.loc[df["polarity"].idxmax()]["review"]
        most_negative_review = df.loc[df["polarity"].idxmin()]["review"]
        
        # Count sentiments
        sentiment_counts = df["sentiment"].value_counts().to_dict()

        # Prepare review data for display
        reviews = df[["date", "review", "rating", "sentiment"]].to_dict(orient="records")

        # Send filtered analysis results as JSON response
        return jsonify({
            "avg_rating": avg_rating,
            "most_positive_review": most_positive_review,
            "most_negative_review": most_negative_review,
            "sentiment_counts": sentiment_counts,
            "reviews": reviews
        })

    except Exception as e:
        print(f"Error filtering data: {e}")
        return jsonify({"error": "An error occurred while filtering the data"}), 500

if __name__ == "__main__":
    app.run(debug=True)
