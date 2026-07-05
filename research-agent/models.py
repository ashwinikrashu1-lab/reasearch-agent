"""
SQLAlchemy models for the Research Agent.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), default="New Session")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages    = db.relationship("ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat()}


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id          = db.Column(db.Integer, primary_key=True)
    session_id  = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False)
    role        = db.Column(db.String(20), nullable=False)   # user | assistant
    content     = db.Column(db.Text, nullable=False)
    msg_type    = db.Column(db.String(30), default="text")   # text | search | report | citation
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "session_id": self.session_id, "role": self.role,
                "content": self.content, "msg_type": self.msg_type, "created_at": self.created_at.isoformat()}


class UploadedDocument(db.Model):
    __tablename__ = "uploaded_documents"
    id           = db.Column(db.Integer, primary_key=True)
    filename     = db.Column(db.String(255), nullable=False)
    original_name= db.Column(db.String(255))
    file_size    = db.Column(db.Integer)
    summary      = db.Column(db.Text)
    insights     = db.Column(db.Text)
    word_count   = db.Column(db.Integer)
    uploaded_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "filename": self.filename, "original_name": self.original_name,
                "file_size": self.file_size, "summary": self.summary, "word_count": self.word_count,
                "uploaded_at": self.uploaded_at.isoformat()}


class SavedPaper(db.Model):
    __tablename__ = "saved_papers"
    id       = db.Column(db.Integer, primary_key=True)
    title    = db.Column(db.String(500))
    authors  = db.Column(db.Text)
    abstract = db.Column(db.Text)
    year     = db.Column(db.Integer)
    url      = db.Column(db.String(500))
    doi      = db.Column(db.String(200))
    source   = db.Column(db.String(100))
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "authors": self.authors,
                "abstract": self.abstract, "year": self.year, "url": self.url,
                "doi": self.doi, "source": self.source, "saved_at": self.saved_at.isoformat()}
