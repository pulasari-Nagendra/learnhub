from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from routes.users import users_bp
from database.db import get_db_connection
from routes.auth import auth_bp
from routes.subscriptions import subscriptions_bp
from routes.plans import plans_bp
from dotenv import load_dotenv
import os
from routes.ai import ai_bp

load_dotenv()



app = Flask(__name__)

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY",
    "learnhub_super_secret_key_2026"
)

jwt = JWTManager(app)


def initialize_database():
    connection = get_db_connection()

    if os.getenv("DATABASE_URL"):
        schema_file = "database/schema_postgres.sql"
    else:
        schema_file = "database/schema.sql"

    with open(schema_file, "r") as file:
        schema = file.read()

    connection.executescript(schema)
    connection.commit()
    connection.close()


# Register authentication routes
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(subscriptions_bp)
app.register_blueprint(plans_bp) 
app.register_blueprint(ai_bp)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/plans")
def plans_page():
    return render_template("plans.html")

@app.route("/courses/free")
def free_courses_page():
    return render_template("free_courses.html")

@app.route("/courses/basic")
def basic_courses_page():
    return render_template("basic_courses.html")

@app.route("/resources/study")
def study_resources_page():
    return render_template("study_resources.html")

@app.route("/ai-assistant")
def ai_assistant_page():
    return render_template("ai_assistant.html")

#initialize_database()
print(app.url_map)

if __name__ == "__main__":
    app.run(debug=True)