from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration - YOU MUST UPDATE THESE VALUES
db_config = {
    'host': 'localhost',
    'user': 'root',        # REPLACE WITH YOUR MYSQL USERNAME
    'password': 'NewPassword123',        # REPLACE WITH YOUR MYSQL PASSWORD
    'database': 'lookify_db'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Email already registered"}), 409

        # Insert new user
        sql = "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, email, password))
        conn.commit()
        
        user_id = cursor.lastrowid
        return jsonify({
            "success": True, 
            "message": "User registered successfully", 
            "user": {"id": user_id, "name": name, "email": email}
        }), 201

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"success": False, "error": "Missing email or password"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s AND password_hash = %s", (email, password))
        user = cursor.fetchone()
        
        if user:
            return jsonify({
                "success": True, 
                "user": {
                    "id": user['id'], 
                    "name": user['full_name'], 
                    "email": user['email']
                }
            })
        else:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print("Ensure your MySQL server is running and the 'lookify_db' database exists.")
    app.run(debug=True, port=5000)
