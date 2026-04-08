from flask import Flask, send_from_directory, request, jsonify
from assistant import VenueFlowAssistant, UserContext, VenueArea
import os

app = Flask(__name__, static_folder='static', static_url_path='')

# Initialize VenueFlow singleton
venue_assistant = VenueFlowAssistant()

# Default mocked user context for the demo
default_user = UserContext(
    user_id="WEB_USER_01",
    seat_section="Section 105, Row 12, Seat 8",
    current_location=VenueArea.ENTRANCE_GATE,
    preferences={"food_preference": "vegetarian"},
    accessibility_needs=[]
)

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    """Returns the venue heatmap for rendering UI cards."""
    heatmap = venue_assistant.get_venue_heatmap()
    return jsonify(heatmap)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handles natural language queries from the User."""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "Empty query"}), 400
        
    response = venue_assistant.handle_query(query, default_user)
    return jsonify(response)

@app.route('/api/recommendations', methods=['GET'])
def recommendations():
    """Returns smart recommendations based on user context."""
    recs = venue_assistant.get_smart_recommendations(default_user)
    return jsonify(recs)

if __name__ == '__main__':
    # Ensure static directory exists
    os.makedirs('static', exist_ok=True)
    # Cloud Run requires binding to 0.0.0.0 and picking up the PORT env variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
