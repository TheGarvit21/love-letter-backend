from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Allow CORS for React running on localhost:8080
CORS(app, origins=["https://love-letter-iota-jade.vercel.app"])



# Use environment variable for API key, fallback to hardcoded for development
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCG-zNMdeWQQkb2m8TK9Mf1i1NHfuFFCzc")

@app.route("/generate-letter", methods=["POST"])
def generate_letter():
    try:
        # Get data from request
        data = request.json
        logger.debug(f"Received data: {data}")
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        your_name = data.get("yourName")
        crush_name = data.get("crushName")
        about_crush = data.get("aboutCrush")

        # Validate required fields
        if not your_name or not crush_name or not about_crush:
            return jsonify({"error": "Missing required fields"}), 400

        # Improved prompt for Gemini
        prompt = f"""Write a heartfelt and romantic love letter. Here are the details:

From: {your_name}
To: {crush_name}
About them: {about_crush}

Please write a sincere, romantic love letter that:
- Expresses genuine feelings
- Mentions specific qualities about {crush_name}
- Has a warm, personal tone
- Is approximately 200-300 words
- Starts with "My dearest {crush_name}," and ends with "With all my love, {your_name}"

Do not make it manipulative or overly dramatic. Keep it genuine and heartfelt."""

        logger.debug(f"Generated prompt: {prompt}")

        # Make API call to Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": 2048,
            }
        }

        logger.debug(f"Making API request to: {url}")
        
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"API response status: {response.status_code}")
        logger.debug(f"API response content: {response.text}")

        if response.status_code != 200:
            logger.error(f"API call failed with status {response.status_code}: {response.text}")
            return jsonify({"error": f"API call failed: {response.text}"}), 500

        result = response.json()
        
        # Extract the letter from the response
        if "candidates" in result and len(result["candidates"]) > 0:
            if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                letter = result["candidates"][0]["content"]["parts"][0]["text"]
                logger.debug(f"Generated letter: {letter}")
                return jsonify({"letter": letter})
            else:
                logger.error(f"Unexpected API response structure: {result}")
                return jsonify({"error": "Unexpected API response structure"}), 500
        else:
            logger.error(f"No candidates in API response: {result}")
            return jsonify({"error": "No content generated"}), 500

    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception: {str(e)}")
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except KeyError as e:
        logger.error(f"KeyError: {str(e)}")
        return jsonify({"error": f"Missing key in response: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Love Letter Generator API is running"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
