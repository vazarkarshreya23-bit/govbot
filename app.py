"""
app.py - Main Flask Application
This is the heart of the project. It handles all web requests.
Run this file to start the server: python app.py
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import db  # Our own db.py file

# -------------------------------------------------
# App Setup
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = "govbot_secret_2024"  # Needed for session (login memory)

# Create database tables when app starts
db.create_tables()


# =================================================
# CHATBOT LOGIC
# =================================================

def chatbot_response(user_message, session_data):
    """
    This is the brain of the chatbot.
    It reads the current 'step' from the session and decides what to say next.

    session_data: a dictionary stored in the user's browser session
    Returns: (bot_reply_text, updated_session_data)
    """
    step    = session_data.get("step", "start")
    service = session_data.get("service", "")
    answers = session_data.get("answers", {})

    msg = user_message.strip().lower()

    # ---- STEP: start ----
    if step == "start":
        if "apply" in msg or "hello" in msg or "hi" in msg or "start" in msg:
            session_data["step"] = "choose_service"
            return (
                "👋 Welcome to the <b>Government Services Portal</b>!<br><br>"
                "Please choose a service by typing the number:<br>"
                "1️⃣ <b>License</b> – Driving / Trade License<br>"
                "2️⃣ <b>Certificate</b> – Birth / Income / Caste Certificate<br>"
                "3️⃣ <b>Complaint</b> – File a Grievance<br><br>"
                "Type <b>1</b>, <b>2</b>, or <b>3</b>.",
                session_data
            )
        elif "status" in msg or "check" in msg:
            session_data["step"] = "check_status"
            return "🔍 Please enter your <b>Application ID</b> (e.g., LIC-AB12CD):", session_data
        else:
            return (
                "Hello! Type <b>apply</b> to start a new application, or <b>status</b> to check your application.",
                session_data
            )

    # ---- STEP: choose_service ----
    elif step == "choose_service":
        if msg in ["1", "license"]:
            session_data["service"] = "license"
            session_data["step"]    = "ask_name"
            return "🚗 <b>License Application</b> selected!<br><br>Let's begin. What is your <b>full name</b>?", session_data
        elif msg in ["2", "certificate"]:
            session_data["service"] = "certificate"
            session_data["step"]    = "ask_name"
            return "📄 <b>Certificate Application</b> selected!<br><br>Let's begin. What is your <b>full name</b>?", session_data
        elif msg in ["3", "complaint"]:
            session_data["service"] = "complaint"
            session_data["step"]    = "ask_name"
            return "📝 <b>Complaint</b> selected!<br><br>Let's begin. What is your <b>full name</b>?", session_data
        else:
            return "❗ Please type <b>1</b> for License, <b>2</b> for Certificate, or <b>3</b> for Complaint.", session_data

    # ---- STEP: ask_name ----
    elif step == "ask_name":
        if len(user_message.strip()) < 2:
            return "❗ Name seems too short. Please enter your <b>full name</b>.", session_data
        answers["name"]         = user_message.strip().title()
        session_data["answers"] = answers
        session_data["step"]    = "ask_age"
        return f"Nice to meet you, <b>{answers['name']}</b>! 😊<br><br>What is your <b>age</b>?", session_data

    # ---- STEP: ask_age ----
    elif step == "ask_age":
        if not user_message.strip().isdigit():
            return "❗ Please enter a valid <b>age</b> (numbers only, e.g., 25).", session_data
        answers["age"]          = user_message.strip()
        session_data["answers"] = answers
        session_data["step"]    = "ask_phone"
        return "📱 What is your <b>phone number</b>?", session_data

    # ---- STEP: ask_phone ----
    elif step == "ask_phone":
        phone = user_message.strip().replace(" ", "").replace("-", "")
        if len(phone) < 7:
            return "❗ Please enter a valid <b>phone number</b>.", session_data
        answers["phone"]        = user_message.strip()
        session_data["answers"] = answers
        session_data["step"]    = "ask_email"
        return "📧 What is your <b>email address</b>? (or type <b>skip</b>)", session_data

    # ---- STEP: ask_email ----
    elif step == "ask_email":
        answers["email"]        = "" if msg == "skip" else user_message.strip()
        session_data["answers"] = answers
        session_data["step"]    = "ask_address"
        return "🏠 What is your <b>home address</b>?", session_data

    # ---- STEP: ask_address ----
    elif step == "ask_address":
        if len(user_message.strip()) < 5:
            return "❗ Address seems too short. Please enter your <b>full address</b>.", session_data
        answers["address"]      = user_message.strip()
        session_data["answers"] = answers
        # Ask a service-specific question
        session_data["step"]    = "ask_details"
        if service == "license":
            return "🚘 What <b>type of license</b> are you applying for? (e.g., Driving, Trade, etc.)", session_data
        elif service == "certificate":
            return "📋 What <b>type of certificate</b> do you need? (e.g., Birth, Income, Caste)", session_data
        else:  # complaint
            return "🗣️ Please briefly <b>describe your complaint</b>.", session_data

    # ---- STEP: ask_details ----
    elif step == "ask_details":
        if len(user_message.strip()) < 2:
            return "❗ Please provide more <b>details</b>.", session_data
        answers["details"]      = user_message.strip()
        session_data["answers"] = answers
        session_data["step"]    = "confirm"

        # Build a summary
        summary = (
            f"📋 <b>Please confirm your details:</b><br><br>"
            f"▸ <b>Service:</b> {service.capitalize()}<br>"
            f"▸ <b>Name:</b> {answers.get('name')}<br>"
            f"▸ <b>Age:</b> {answers.get('age')}<br>"
            f"▸ <b>Phone:</b> {answers.get('phone')}<br>"
            f"▸ <b>Email:</b> {answers.get('email') or 'Not provided'}<br>"
            f"▸ <b>Address:</b> {answers.get('address')}<br>"
            f"▸ <b>Details:</b> {answers.get('details')}<br><br>"
            f"Type <b>yes</b> to submit or <b>no</b> to start over."
        )
        return summary, session_data

    # ---- STEP: confirm ----
    elif step == "confirm":
        if msg in ["yes", "y", "confirm", "submit"]:
            # Save to database
            app_id = db.save_application(service, answers)
            # Reset session
            session_data["step"]    = "start"
            session_data["service"] = ""
            session_data["answers"] = {}
            return (
                f"✅ <b>Application submitted successfully!</b><br><br>"
                f"🎫 Your Application ID is: <b style='font-size:1.2em;color:#00c853'>{app_id}</b><br><br>"
                f"📌 Save this ID to check your status later.<br>"
                f"Type <b>status</b> to check, or <b>apply</b> for a new application.",
                session_data
            )
        elif msg in ["no", "n", "restart"]:
            session_data["step"]    = "start"
            session_data["service"] = ""
            session_data["answers"] = {}
            return "🔄 Application cancelled. Type <b>apply</b> to start again.", session_data
        else:
            return "Please type <b>yes</b> to submit or <b>no</b> to cancel.", session_data

    # ---- STEP: check_status ----
    elif step == "check_status":
        app_id = user_message.strip().upper()
        result = db.get_application(app_id)
        session_data["step"] = "start"
        if result:
            status_icons = {
                "Pending":   "🕐",
                "In Review": "🔍",
                "Approved":  "✅",
                "Rejected":  "❌"
            }
            icon = status_icons.get(result["status"], "📌")
            return (
                f"📂 <b>Application Found!</b><br><br>"
                f"▸ <b>App ID:</b> {result['app_id']}<br>"
                f"▸ <b>Service:</b> {result['service'].capitalize()}<br>"
                f"▸ <b>Name:</b> {result['name']}<br>"
                f"▸ <b>Status:</b> {icon} <b>{result['status']}</b><br>"
                f"▸ <b>Submitted:</b> {result['created_at']}<br>"
                f"▸ <b>Last Updated:</b> {result['updated_at']}<br><br>"
                f"Type <b>apply</b> for a new application or <b>status</b> to check another.",
                session_data
            )
        else:
            return (
                f"❌ No application found with ID <b>{app_id}</b>.<br>"
                f"Please double-check the ID. Type <b>status</b> to try again.",
                session_data
            )

    # Fallback
    return "🤔 I didn't understand that. Type <b>apply</b> or <b>status</b>.", session_data


# =================================================
# ROUTES (Web Pages & API Endpoints)
# =================================================

@app.route("/")
def home():
    """Show the main chatbot page."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    API endpoint: receives a user message, returns a bot reply.
    The frontend JavaScript will call this via fetch().
    """
    data         = request.get_json()
    user_message = data.get("message", "")

    # Load session data (or start fresh)
    session_data = {
        "step":    session.get("step",    "start"),
        "service": session.get("service", ""),
        "answers": session.get("answers", {})
    }

    # Get bot reply
    reply, updated_session = chatbot_response(user_message, session_data)

    # Save updated session
    session["step"]    = updated_session["step"]
    session["service"] = updated_session["service"]
    session["answers"] = updated_session["answers"]

    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    """Clears the chat session so the user can start over."""
    session.clear()
    return jsonify({"reply": "🔄 Session reset. Type <b>apply</b> to begin!"})


# =================================================
# ADMIN PANEL ROUTES
# =================================================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if db.check_admin(username, password):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin_login.html", error="❌ Invalid credentials. Try admin / admin123")
    return render_template("admin_login.html", error=None)


@app.route("/admin/dashboard")
def admin_dashboard():
    """Admin dashboard - shows all applications."""
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    applications = db.get_all_applications()
    return render_template("admin_dashboard.html", applications=applications)


@app.route("/admin/update", methods=["POST"])
def admin_update():
    """Updates application status from the admin panel."""
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    app_id     = request.form.get("app_id")
    new_status = request.form.get("status")
    if app_id and new_status:
        db.update_status(app_id, new_status)
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout")
def admin_logout():
    """Logs out the admin."""
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


# =================================================
# Run the App
# =================================================
if __name__ == "__main__":
    print("\n🚀 Starting GovBot Server...")
    print("📌 Open your browser and go to: http://127.0.0.1:5000")
    print("🔑 Admin panel: http://127.0.0.1:5000/admin")
    print("   Username: admin | Password: admin123\n")
    app.run(debug=True)  # debug=True shows errors in browser during development
