import os
import torch
import torch.nn.functional as F
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
# ✅ ADDED: Missing security imports
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image

# --- CONFIGURATION & CONSTANTS ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'deepscan-secure-key-v1'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deepscan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Allowed image types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'tiff'}

# Initialize Core Systems
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image_path = db.Column(db.String(200))
    result_score = db.Column(db.String(50))
    verdict = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- INFERENCE ENGINE ---
class DeepFakeDetector:
    def __init__(self):
        print("[SYSTEM] Initializing Neural Network...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "dima806/ai_vs_real_image_detection"
        
        self.processor = AutoImageProcessor.from_pretrained(self.model_name)
        self.model = AutoModelForImageClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        print(f"[SYSTEM] Model loaded on {self.device.upper()}")

    def predict(self, image_path):
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            probabilities = F.softmax(outputs.logits, dim=1)
            predicted_label_id = probabilities.argmax().item()
            label = self.model.config.id2label[predicted_label_id]
            score = probabilities[0][predicted_label_id].item()
            
            return self._format_result(label, score)
        except Exception as e:
            print(f"[ERROR] Inference failed: {e}")
            return None

    def _format_result(self, label, score):
        percentage = round(score * 100, 2)
        if label.lower() in ['fake', 'ai', 'artificial']:
            return {"verdict": "Artificial", "confidence": percentage, "status": "warning", "color": "#ff4444"}
        else:
            return {"verdict": "Authentic", "confidence": percentage, "status": "safe", "color": "#00ffa3"}

detector = DeepFakeDetector()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', user=current_user)

@app.route('/analyze', methods=['POST'])
def analyze_photo():
    if 'file' not in request.files:
        return jsonify({"error": "No file payload"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        result = detector.predict(filepath)
        if not result:
            return jsonify({"error": "Analysis Engine Failed"}), 500

        display_score = f"{result['confidence']}% {result['verdict']}"
        
        if current_user.is_authenticated:
            log_entry = ScanHistory(user_id=current_user.id, image_path=filepath, verdict=result['verdict'], result_score=display_score)
            db.session.add(log_entry)
            db.session.commit()

        return jsonify({"success": True, "results": [{"provider": "Neural Engine (ViT)", "score": display_score, "status": result['status'], "color": result['color']}]})

@app.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"success": False, "message": "Email already exists"})
    
    # Hash the password before saving!
    hashed_pw = generate_password_hash(data['pass'], method='pbkdf2:sha256')
    new_user = User(name=data['name'], email=data['email'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Invalid credentials"})
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))  # Redirects to the function named 'index'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)