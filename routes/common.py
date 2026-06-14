from flask import Blueprint, render_template, jsonify
from state import app_stats, email_task_state

common_bp = Blueprint('common', __name__)

@common_bp.route("/")
def index():
    return render_template("index.html")

@common_bp.route("/stats", methods=["GET"])
def get_stats():
    return jsonify({
        "app_stats": app_stats,
        "email_sheet_stats": email_task_state.get("sheet_stats", {})
    })
