"""Small defensive training API: no real exploit execution or traffic capture."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import User, SecurityEvent

api = Blueprint("api", __name__)

DEMO_EVENTS = {
    "failed_login": "medium",
    "blocked_request": "low",
    "suspicious_volume": "high",
}


def json_object():
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else None


@api.post("/register")
def register():
    payload = json_object()
    if payload is None:
        return jsonify(error="Expected a JSON object."), 400
    username, password, team = (
        payload.get("username"), payload.get("password"), payload.get("team", "blue")
    )
    if not isinstance(username, str) or not (3 <= len(username) <= 50) or not username.isascii() or not all(x.isalnum() or x in "_-" for x in username):
        return jsonify(error="Username must be 3–50 ASCII letters, numbers, '_' or '-'."), 400
    if not isinstance(password, str) or not (12 <= len(password) <= 128):
        return jsonify(error="Password must contain 12–128 characters."), 400
    if team not in {"red", "blue"}:
        return jsonify(error="Choose red or blue as a training preference."), 400
    user = User(username=username, password_hash=generate_password_hash(password), team=team)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="That username is already registered."), 409
    return jsonify(message="Training account created. Sign in to continue."), 201


@api.post("/login")
def login():
    payload = json_object()
    if payload is None:
        return jsonify(error="Expected a JSON object."), 400
    username, password = payload.get("username"), payload.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify(error="Enter a username and password."), 400
    user = db.session.query(User).filter_by(username=username).first()
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify(error="Invalid credentials."), 401
    return jsonify(
        access_token=create_access_token(identity=str(user.id)),
        username=user.username,
        team=user.team,
    )


def current_user():
    try:
        uid = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    return db.session.get(User, uid)


@api.get("/api/me")
@jwt_required()
def me():
    user = current_user()
    if user is None:
        return jsonify(error="Account is no longer available."), 401
    return jsonify(username=user.username, team=user.team)


@api.get("/api/events")
@jwt_required()
def list_events():
    user = current_user()
    if user is None:
        return jsonify(error="Account is no longer available."), 401
    events = (
        db.session.query(SecurityEvent)
        .filter_by(owner_id=user.id)
        .order_by(SecurityEvent.id.desc())
        .limit(50).all()
    )
    return jsonify(events=[{
        "id": event.id,
        "kind": event.kind,
        "severity": event.severity,
        "source": event.source,
        "created_at": event.created_at.isoformat() + "Z",
    } for event in events])


@api.post("/api/events")
@jwt_required()
def simulate_event():
    user = current_user()
    if user is None:
        return jsonify(error="Account is no longer available."), 401
    payload = json_object()
    kind = payload.get("kind") if payload else None
    if kind not in DEMO_EVENTS:
        return jsonify(error="Choose a supported synthetic event type."), 400

    event = SecurityEvent(owner_id=user.id, kind=kind, severity=DEMO_EVENTS[kind])
    db.session.add(event)
    db.session.commit()
    return jsonify(
        id=event.id, kind=kind, severity=event.severity,
        source="synthetic", warning="Generated for an isolated demonstration only."
    ), 201
