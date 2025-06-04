from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_login import current_user
import boto3
import uuid

app = Flask(__name__)
application = app
app.secret_key = "dspguardian_secret_2025"
login_manager = LoginManager(app)

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
users_table = dynamodb.Table("Users")
devices_table = dynamodb.Table("OBDDevices")
alerts_table = dynamodb.Table("Alerts")

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    response = users_table.get_item(Key={"username": username})
    if "Item" in response:
        return User(username)
    return None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        users_table.put_item(Item={"username": username, "password": password, "email": email})
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        response = users_table.get_item(Key={"username": username})
        if "Item" in response and response["Item"]["password"] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    # Scan OBDDevices table to get devices for the current user
    response = devices_table.scan(
        FilterExpression="owner_username = :u",
        ExpressionAttributeValues={":u": current_user.id}
    )
    devices = response.get("Items", [])
    response = alerts_table.scan()
    alerts = response.get("Items", [])
    return render_template("dashboard.html", devices=devices, alerts=alerts)

@app.route("/add_device", methods=["GET", "POST"])
@login_required
def add_device():
    if request.method == "POST":
        device_id = str(uuid.uuid4())
        vehicle_name = request.form["vehicle_name"]
        devices_table.put_item(Item={"device_id": device_id, "owner_username": current_user.id, "vehicle_name": vehicle_name})
        return redirect(url_for("dashboard"))
    return render_template("add_device.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)