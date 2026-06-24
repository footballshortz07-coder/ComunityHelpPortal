from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import Config
from models import db, User, HelpRequest, Feedback, Volunteer


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please sign in to access that page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    @app.route("/signup", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not username or not email or not password:
                flash("Please fill in all fields.", "danger")
            elif password != confirm_password:
                flash("Passwords do not match.", "danger")
            elif User.query.filter((User.username == username) | (User.email == email)).first():
                flash("Username or email already exists.", "danger")
            else:
                user = User(username=username, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Registration successful. Please sign in.", "success")
                return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    @app.route("/signin", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            identifier = request.form.get("username_or_email", "").strip()
            password = request.form.get("password", "")

            user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Signed in successfully.", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid username or password.", "danger")

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been signed out.", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        requests = HelpRequest.query.filter_by(user_id=current_user.id).order_by(HelpRequest.created_at.desc()).all()
        feedbacks = Feedback.query.filter_by(user_id=current_user.id).order_by(Feedback.created_at.desc()).all()
        volunteers = Volunteer.query.filter_by(user_id=current_user.id).order_by(Volunteer.created_at.desc()).all()
        return render_template(
            "dashboard.html",
            request_count=len(requests),
            feedback_count=len(feedbacks),
            volunteer_count=len(volunteers),
            recent_requests=requests[:5],
            recent_feedback=feedbacks[:5],
            recent_volunteers=volunteers[:3],
        )

    @app.route("/requests", methods=["GET", "POST"])
    @login_required
    def requests():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            category = request.form.get("category", "").strip()

            if not title or not description or not category:
                flash("Please complete all fields.", "danger")
            else:
                new_request = HelpRequest(title=title, description=description, category=category, user_id=current_user.id)
                db.session.add(new_request)
                db.session.commit()
                flash("Help request submitted.", "success")
                return redirect(url_for("requests"))

        search_query = request.args.get("q", "").strip()
        category_filter = request.args.get("category", "").strip()
        status_filter = request.args.get("status", "").strip()

        query_obj = HelpRequest.query.filter_by(user_id=current_user.id)
        if search_query:
            query_obj = query_obj.filter(
                HelpRequest.title.ilike(f"%{search_query}%") |
                HelpRequest.description.ilike(f"%{search_query}%")
            )
        if category_filter:
            query_obj = query_obj.filter(HelpRequest.category == category_filter)
        if status_filter:
            query_obj = query_obj.filter(HelpRequest.status == status_filter)

        user_requests = query_obj.order_by(HelpRequest.created_at.desc()).all()
        return render_template(
            "requests.html",
            requests=user_requests,
            q=search_query,
            category=category_filter,
            status=status_filter,
        )

    @app.route("/volunteers", methods=["GET", "POST"])
    @login_required
    def volunteers():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            skills = request.form.get("skills", "").strip()
            availability = request.form.get("availability", "").strip()
            contact = request.form.get("contact", "").strip()

            if not name or not skills or not availability or not contact:
                flash("Please complete all volunteer fields.", "danger")
            else:
                volunteer = Volunteer(name=name, skills=skills, availability=availability, contact=contact, user_id=current_user.id)
                db.session.add(volunteer)
                db.session.commit()
                flash("Volunteer added.", "success")
                return redirect(url_for("volunteers"))

        volunteer_list = Volunteer.query.filter_by(user_id=current_user.id).order_by(Volunteer.created_at.desc()).all()
        return render_template("volunteers.html", volunteers=volunteer_list)

    @app.route("/volunteers/<int:volunteer_id>/delete", methods=["POST"])
    @login_required
    def delete_volunteer(volunteer_id):
        volunteer = Volunteer.query.filter_by(id=volunteer_id, user_id=current_user.id).first_or_404()
        db.session.delete(volunteer)
        db.session.commit()
        flash("Volunteer removed.", "info")
        return redirect(url_for("volunteers"))

    @app.route("/admin")
    @login_required
    def admin():
        if current_user.username != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))

        all_requests = HelpRequest.query.order_by(HelpRequest.created_at.desc()).all()
        all_feedback = Feedback.query.order_by(Feedback.created_at.desc()).all()
        all_volunteers = Volunteer.query.order_by(Volunteer.created_at.desc()).all()
        return render_template("admin.html", requests=all_requests, feedbacks=all_feedback, volunteers=all_volunteers)

    @app.route("/feedback", methods=["GET", "POST"])
    @login_required
    def feedback():
        if request.method == "POST":
            message = request.form.get("message", "").strip()
            rating = request.form.get("rating", "").strip()

            if not message or not rating:
                flash("Please add feedback and a rating.", "danger")
            else:
                new_feedback = Feedback(message=message, rating=int(rating), user_id=current_user.id)
                db.session.add(new_feedback)
                db.session.commit()
                flash("Feedback submitted.", "success")
                return redirect(url_for("feedback"))

        feedback_list = Feedback.query.filter_by(user_id=current_user.id).order_by(Feedback.created_at.desc()).all()
        return render_template("feedback.html", feedbacks=feedback_list)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
