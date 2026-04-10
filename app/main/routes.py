from flask import render_template
from flask import request, flash, redirect, url_for, session, make_response
from datetime import datetime
from . import main_bp

@main_bp.app_context_processor
def inject_globals():
    return {
        "year": datetime.now().year
    }

@main_bp.get("/")
def home():
    return render_template("main/home.html")

@main_bp.get("/about")
def about():
    return render_template("main/about.html")

@main_bp.get("/contact")
def contact():
    return render_template("main/contact.html")

@main_bp.route("/form-example", methods=["GET", "POST"])
def from_example():
    username = None
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        
        # Basic manual validation
        if not username:
            flash("Username is required!", "error")
            return redirect(url_for("main.form_example"))
        
        # Store in session
        session["username"] = username
        
        flash("Form submitted successfully!", "success")
        
    return render_template(
        "main/form_example.html", username=session.get("username")
        )
        

@main_bp.get("/set-cookie")
def set_cookie():
    response = make_response("Cookie has been set!")
    response.set_cookie("favorite_language", "python", max_age=60*60)
    
    return response

@main_bp.get("/get-cookie")
def get_cookie():
    lang = request.cookies.get("favorite_language")
    return f"Favorite language is: {lang}"