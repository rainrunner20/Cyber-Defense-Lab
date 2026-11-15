"""Local demonstration accounts and explicitly synthetic security events."""
from datetime import datetime, timezone

from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    # Team is a training preference, never an authorization/admin role.
    team = db.Column(db.String(8), nullable=False, default="blue")


class SecurityEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    kind = db.Column(db.String(32), nullable=False)
    severity = db.Column(db.String(12), nullable=False)
    source = db.Column(db.String(20), nullable=False, default="synthetic")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
