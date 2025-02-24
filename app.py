from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)

# Replace with a secure key for production
app.secret_key = secrets.token_hex(16)  # Use a secure secret key here

# SQLite Configuration with SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stressless.db'  # SQLite URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Game Score Model
class GameScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('login'))

        new_user = User(name=name, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['name'] = user.name
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user_scores = GameScore.query.filter_by(user_id=user.id).all()
    cognitive_score = sum(score.score for score in user_scores) // max(len(user_scores), 1)

    return render_template('dashboard.html', user=user, cognitive_score=cognitive_score)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route("/mystery_expedition", methods=["GET", "POST"])
def mystery_expedition():
    # 10 Puzzles for the game
    puzzles = {
        1: ("What is the capital of France?", ["Berlin", "Madrid", "Paris", "Rome"], "Paris"),
        2: ("What comes next in the sequence: 1, 3, 6, 10, __ ?", ["12", "15", "14", "16"], "15"),
        3: ("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter", "Saturn"], "Mars"),
        4: ("How many continents are there?", ["5", "6", "7", "8"], "7"),
        5: ("Who wrote 'Romeo and Juliet'?", ["Shakespeare", "Hemingway", "Tolstoy", "Dickens"], "Shakespeare"),
        6: ("What is the square root of 64?", ["6", "7", "8", "9"], "8"),
        7: ("Which animal is known as the king of the jungle?", ["Tiger", "Elephant", "Lion", "Cheetah"], "Lion"),
        8: ("What is the boiling point of water in Celsius?", ["50", "100", "150", "200"], "100"),
        9: ("What is the chemical symbol for gold?", ["Ag", "Au", "Pb", "Fe"], "Au"),
        10: ("How many legs does a spider have?", ["6", "8", "10", "12"], "8"),
    }

    if "step" not in session:
        session["step"] = 1
        session["score"] = 0
        session["time_left"] = 15
        session["answered_correctly"] = None

    step = session["step"]
    
    # Check if game is finished
    if step > len(puzzles):
        final_score = session["score"]
        session.pop("step", None)
        session.pop("score", None)
        session.pop("time_left", None)
        session.pop("answered_correctly", None)
        return redirect(url_for("submit_score", game_name="Mystery Expedition", score=final_score))

    puzzle, options, correct_answer = puzzles[step]

    if request.method == "POST":
        user_answer = request.form.get("answer", "").strip().lower()
        
        if user_answer == correct_answer.lower():
            session["score"] += 10
            session["answered_correctly"] = True
            session["time_left"] = min(30, session["time_left"] + 5)  # Increase but cap at 30 seconds
        else:
            session["answered_correctly"] = False
            session["time_left"] -= 3

        # Prevent negative time
        session["time_left"] = max(0, session["time_left"])

        # Move to next question
        session["step"] += 1
        return redirect(url_for("mystery_expedition"))  

    return render_template("mystery_expedition.html", puzzle=puzzle, options=options, time_left=session["time_left"], score=session["score"], answered_correctly=session["answered_correctly"])

@app.route('/shapeshifter')
def shapeshifter():
    return render_template('shapeshifter.html')

@app.route('/submit_score', methods=['POST', 'GET'])
def submit_score():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

    if request.method == "POST":
        data = request.json
        game_name = data.get('game_name')
        score = data.get('score')

        new_score = GameScore(user_id=session['user_id'], game_name=game_name, score=score)
        db.session.add(new_score)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Score saved successfully'})

    return redirect(url_for("dashboard"))

@app.route('/memory_boost')
def memory_boost():
    return render_template('memory_boost.html')

@app.route('/zen_path')
def zen_path():
    return render_template('zen_path.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
