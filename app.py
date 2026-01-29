import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login")
def login():
    return render_template("login.html")

@app.route('/analyze', methods=['POST'])
def analyze_photo():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # This is where the "AI logic" happens.
        # In a real app, you would use 'requests' to send this file to 
        # APIs like Deepware, Sensity, etc.
        results = [
            {"provider": "Deepware", "score": "92% Authentic", "status": "safe"},
            {"provider": "Sensity AI", "score": "88% Authentic", "status": "safe"},
            {"provider": "Reality Check", "score": "42% Suspicious", "status": "warning"}
        ]
        
        return jsonify({
            "success": True,
            "image_url": filepath,
            "results": results
        })

if __name__ == '__main__':
    app.run(debug=True)