from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from routes.users import users_bp
from database.db import get_db_connection
from routes.auth import auth_bp
from routes.subscriptions import subscriptions_bp
from routes.plans import plans_bp
import os

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

if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)