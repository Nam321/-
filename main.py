import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.environ['DATABASE_USER']}:{os.environ['DATABASE_PASSWORD']}@{os.environ['DATABASE_HOST']}/{os.environ['DATABASE_NAME']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    tasks = db.relationship('Task', backref='author', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="изчакваща")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@jwt.user_loader_callback
def user_loader_callback(identity):
    return User.query.get(identity)


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(email=data['email'], password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token)
    else:
        return jsonify({"message": "Invalid email or password"}), 401


@app.route("/profile/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_profile(user_id):
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({"message": "Unauthorized"}), 401

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'email' in data:
        user.email = data['email']

    if 'password' in data:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user.password = hashed_password

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"})

# Task Management


@app.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()
    tasks = Task.query.filter_by(user_id=user_id).all()
    task_list = []
    for task in tasks:
        task_data = {
            'id': task.id,
            'description': task.description,
            'status': task.status,
            'user_id': task.user_id
        }
        task_list.append(task_data)
    return jsonify({"tasks": task_list})


@app.route("/tasks", methods=["POST"])
@jwt_required()
def create_task():
    data = request.get_json()
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    new_task = Task(description=data['description'], status=data['status'], author=user)

    db.session.add(new_task)
    db.session.commit()

    return jsonify({"message": "Task created successfully"})


@app.route("/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)

    # Check if the task belongs to the current user
    if task.user_id != user_id:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        task.status = data['status']

    db.session.commit()

    return jsonify({"message": "Task updated successfully"})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    task = Task.query.get_or_404(task_id)

    # Check if the task belongs to the current user
    if task.user_id != user_id:
        return jsonify({"message": "Unauthorized"}), 401

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted successfully"})


@app.route("/task-statistics", methods=["GET"])
@jwt_required()
def task_statistics():
    user_id = get_jwt_identity()
    total_tasks = Task.query.filter_by(user_id=user_id).count()
    waiting_tasks = Task.query.filter_by(user_id=user_id, status='изчакваща').count()
    in_progress_tasks = Task.query.filter_by(user_id=user_id, status='в процес').count()
    completed_tasks = Task.query.filter_by(user_id=user_id, status='завършена').count()

    statistics = {
        'total_tasks': total_tasks,
        'waiting_tasks': waiting_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks
    }

    return jsonify(statistics)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
