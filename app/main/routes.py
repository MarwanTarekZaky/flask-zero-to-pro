from flask import render_template
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