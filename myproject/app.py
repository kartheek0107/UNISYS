from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from neo4j import GraphDatabase
import os
from datetime import datetime
import uuid
import base64
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a7fc783b214e40899208b4acf0e87561d92b33a7gd8d13eg'

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Rmkmrmkm0107"

# Initialize Neo4j driver
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
except Exception as e:
    logging.error(f"Failed to create the Neo4j driver: {e}")


# Neo4j helper functions
def get_db_session():
    return driver.session()


# Database setup functions
def setup_constraints():
    with get_db_session() as session:
        # Create constraints for unique username and email
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.username IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Canvas) REQUIRE c.id IS UNIQUE")


# User functions
def create_user(username, password_hash, name, email):
    with get_db_session() as session:
        user_id = str(uuid.uuid4())
        result = session.run(
            """
            CREATE (u:User {
                id: $id,
                username: $username,
                password_hash: $password_hash,
                name: $name,
                email: $email,
                created_at: datetime()
            })
            RETURN u
            """,
            id=user_id, username=username, password_hash=password_hash, name=name, email=email
        )
        return result.single()


def get_user_by_username(username):
    with get_db_session() as session:
        result = session.run(
            "MATCH (u:User) WHERE u.username = $username RETURN u",
            username=username
        )
        record = result.single()
        return record["u"] if record else None


def get_user_by_id(user_id):
    with get_db_session() as session:
        result = session.run(
            "MATCH (u:User) WHERE u.id = $id RETURN u",
            id=user_id
        )
        record = result.single()
        return record["u"] if record else None


def update_user(user_id, name, email):
    with get_db_session() as session:
        session.run(
            """
            MATCH (u:User) WHERE u.id = $id
            SET u.name = $name, u.email = $email
            """,
            id=user_id, name=name, email=email
        )


def update_user_password(user_id, password_hash):
    with get_db_session() as session:
        session.run(
            """
            MATCH (u:User) WHERE u.id = $id
            SET u.password_hash = $password_hash
            """,
            id=user_id, password_hash=password_hash
        )


# Canvas functions
def save_canvas(user_id, image_data):
    with get_db_session() as session:
        canvas_id = str(uuid.uuid4())
        result = session.run(
            """
            MATCH (u:User) WHERE u.id = $user_id
            CREATE (c:Canvas {
                id: $id,
                image_data: $image_data,
                created_at: datetime()
            })
            CREATE (u)-[:CREATED]->(c)
            RETURN c
            """,
            id=canvas_id, user_id=user_id, image_data=image_data
        )
        return result.single()


def get_user_canvases(user_id, limit=5):
    with get_db_session() as session:
        result = session.run(
            """
            MATCH (u:User)-[:CREATED]->(c:Canvas)
            WHERE u.id = $user_id
            RETURN c
            ORDER BY c.created_at DESC
            LIMIT $limit
            """,
            user_id=user_id, limit=limit
        )
        return [record["c"] for record in result]


def get_all_user_canvases(user_id):
    with get_db_session() as session:
        result = session.run(
            """
            MATCH (u:User)-[:CREATED]->(c:Canvas)
            WHERE u.id = $user_id
            RETURN c
            ORDER BY c.created_at DESC
            """,
            user_id=user_id
        )
        return [record["c"] for record in result]


# Login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('canvas'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user_by_username(username)

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('canvas'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')

        # Check if username exists
        existing_user = get_user_by_username(username)

        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        # Create the new user
        password_hash = generate_password_hash(password)
        try:
            create_user(username, password_hash, name, email)
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error during registration: {str(e)}', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/canvas', methods=['GET', 'POST'])
@login_required
def canvas():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'submit':
            image_data = request.form.get('image_data')
            if image_data:
                # Save canvas data to database
                save_canvas(session['user_id'], image_data)
                flash('Canvas saved successfully!', 'success')
            else:
                flash('No canvas data to save', 'warning')

        # Clear action is handled on the frontend

    # Get user's previous canvases
    user_canvases = get_user_canvases(session['user_id'], 5)

    return render_template('canvas.html', canvases=user_canvases)


@app.route('/canvas/submit', methods=['POST'])
@login_required
def submit_canvas():
    # API endpoint for AJAX submission
    data = request.json
    if data and 'image_data' in data:
        try:
            save_canvas(session['user_id'], data['image_data'])
            return jsonify({'success': True, 'message': 'Canvas saved successfully!'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error saving canvas: {str(e)}'})
    return jsonify({'success': False, 'message': 'No canvas data to save'})


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        # Update profile information
        name = request.form.get('name')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        # Update basic info
        update_user(user['id'], name, email)

        # Update password if provided
        if current_password and new_password:
            if check_password_hash(user['password_hash'], current_password):
                password_hash = generate_password_hash(new_password)
                update_user_password(user['id'], password_hash)
                flash('Password updated successfully', 'success')
            else:
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile'))

        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))

    # Get user's canvas history
    canvas_history = get_all_user_canvases(user['id'])

    return render_template('profile.html', user=user, canvas_history=canvas_history)


# Initialize database
@app.cli.command("init-db")
def init_db_command():
    """Initialize the Neo4j database with constraints."""
    try:
        setup_constraints()
        print("Initialized the Neo4j database.")
    except Exception as e:
        print(f"Error initializing database: {e}")


# Add a test user
@app.cli.command("add-test-user")
def add_test_user():
    """Add a test user to the database."""
    try:
        password_hash = generate_password_hash("password")
        create_user("test", password_hash, "Test User", "test@example.com")
        print("Added test user.")
    except Exception as e:
        print(f"Error adding test user: {e}")


@app.teardown_appcontext
def close_db(error):
    """Close the Neo4j driver at the end of the request."""
    # This function is left empty as the driver.session() is used within context managers
    pass


if __name__ == '__main__':
    # Ensure we have constraints set up
    with app.app_context():
        try:
            setup_constraints()
        except Exception as e:
            logging.error(f"Failed to set up constraints: {e}")

    app.run(debug=True)