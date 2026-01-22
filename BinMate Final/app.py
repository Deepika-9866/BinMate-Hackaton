import os
import requests
from flask import Flask, jsonify, request, send_from_directory, render_template
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Initialize the Flask app, telling it where to find the templates folder
app = Flask(__name__, template_folder='templates')


# --- In-memory "Database" ---
# In a real app, this would come from a database query. We are simulating it for now.
user_data = {
    "name": "User",
    "points": 1250
}

# In-memory "database" of marketplace items for price lookup on the backend
marketplace_items_db = {
    'Cloth Tote Bag': 500,
    'Seed Paper Pack': 350,
    'Bamboo Coffee Cup': 750,
    'Compost Bin': 1500
}


# --- API Endpoints ---

# NEW: Endpoint to get the current user's data (points)
@app.route('/api/user')
def get_user():
    """Provides current user's data."""
    return jsonify(user_data)

@app.route('/api/leaderboard')
def get_leaderboard():
    """Provides leaderboard data."""
    leaderboard_data = [
        {'rank': 1, 'name': 'K Keerthana', 'points': 5430},
        {'rank': 2, 'name': 'Deepika', 'points': 5120},
        {'rank': 3, 'name': 'Aravind', 'points': 4980},
        {'rank': 4, 'name': 'Sai Charan', 'points': 3200},
        {'rank': 5, 'name': 'Priya', 'points': 2150},
        {'rank': 6, 'name': 'Ramesh', 'points': 1500},
        {'rank': 7, 'name': 'You', 'points': user_data['points']} # Dynamically show user's current points
    ]
    return jsonify(leaderboard_data)

@app.route('/api/marketplace')
def get_marketplace_items():
    """Provides marketplace item data."""
    # This data could also come from a database
    marketplace_items = [
        {'icon': 'fa-shopping-bag', 'name': 'Cloth Tote Bag', 'points': 500},
        {'icon': 'fa-seedling', 'name': 'Seed Paper Pack', 'points': 350},
        {'icon': 'fa-mug-hot', 'name': 'Bamboo Coffee Cup', 'points': 750},
        {'icon': 'fa-recycle', 'name': 'Compost Bin', 'points': 1500}
    ]
    return jsonify(marketplace_items)

# NEW: Endpoint to handle redeeming an item and deducting points
@app.route('/api/marketplace/redeem', methods=['POST'])
def redeem_item():
    """Handles the logic for a user redeeming an item with points."""
    global user_data # Use the global variable to modify it
    item_name = request.json.get('name')

    if not item_name or item_name not in marketplace_items_db:
        return jsonify({'success': False, 'message': 'Item not found.'}), 404

    item_cost = marketplace_items_db[item_name]

    if user_data['points'] >= item_cost:
        user_data['points'] -= item_cost
        message = f"Successfully redeemed {item_name}!"
        return jsonify({
            'success': True,
            'message': message,
            'new_points': user_data['points']
        })
    else:
        message = f"Not enough points to redeem {item_name}."
        return jsonify({
            'success': False,
            'message': message,
            'new_points': user_data['points']
        }), 400

# NEW: AI-powered endpoint for eco-friendly recommendations
@app.route('/api/recommend', methods=['POST'])
def get_recommendation():
    """Generates eco-friendly recommendations using the Gemini API."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'API key not configured on the server.'}), 500

    try:
        item_to_replace = request.json['item']
        if not item_to_replace:
            return jsonify({'error': 'Item field cannot be empty.'}), 400
            
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"

        # A detailed prompt for better, more creative results
        prompt = (f"I want to replace '{item_to_replace}'. "
                  f"In a friendly and encouraging tone, suggest 1-3 common, eco-friendly alternatives. "
                  f"Keep the total response under 40 words. Start directly with the suggestion, for example: 'Instead of {item_to_replace}, you could try...'.")

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        
        ai_response = response.json()
        recommendation_text = ai_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'Sorry, I could not think of a recommendation right now.')

        return jsonify({'recommendation': recommendation_text})

    except requests.exceptions.RequestException:
        return jsonify({'error': 'Could not reach the AI service.'}), 500
    except (KeyError, IndexError):
        return jsonify({'error': 'Received an invalid response from the AI service.'}), 500
    except Exception as e:
        print(f"An unexpected error occurred in recommendation: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

@app.route('/api/news')
def get_news():
    """Provides news update data."""
    news_data = [{'title': 'Community Clean-Up Drive This Sunday!', 'date': 'October 8, 2025', 'content': "Join us this Sunday at 8 AM near the Ramagundam Municipal Park for our monthly clean-up drive. Let's make our city shine together! Gloves and bags will be provided."}, {'title': 'BinMate Reaches 1,000 Users!', 'date': 'September 28, 2025', 'content': 'We are thrilled to announce that over 1,000 residents are now using BinMate to make a difference.'}, {'title': 'New Smart Bins Deployed in Sector 5', 'date': 'September 15, 2025', 'content': 'As part of the Smart City initiative, 20 new IoT-enabled smart bins have been installed across Sector 5.'}]
    return jsonify(news_data)

@app.route('/api/scan/image', methods=['POST'])
def scan_image():
    """Securely handles the AI image scanning by proxying the request to the Google Gemini API."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'API key not configured on the server.'}), 500

    try:
        image_data = request.json['imageData']
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "Analyze this image and identify the main waste item. Classify it into one of these three categories: Biodegradable, Recyclable, or Hazardous. Respond with only one of these three words, followed by a colon and the name of the item. For example: 'Recyclable: Plastic Bottle'."}, {"inlineData": {"mimeType": "image/jpeg", "data": image_data}}]}]}
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Could not reach Google API. Status: {e.response.status_code}'}), 500
    except KeyError:
        return jsonify({'error': 'Invalid request: "imageData" field missing.'}), 400
    except Exception as e:
        print(f"An unexpected error occurred in scan_image: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500


# --- Serve Frontend ---
@app.route('/')
def serve_index():
    """Serves the main index.html file from the templates folder."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=3000, debug=True)

