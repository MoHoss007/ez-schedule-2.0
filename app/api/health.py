from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("", methods=["GET"], strict_slashes=False)
def health():
    return jsonify(status="ok")
