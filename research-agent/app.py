"""
Flask application — Research Agent backend.
"""
import os
import uuid
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

from models import db, ChatSession, ChatMessage, UploadedDocument, SavedPaper
from agent import research_tools as rt
from agent.instructions import AGENT_INSTRUCTIONS, get_citation_style

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__, instance_relative_config=True)
CORS(app)

# Load default config then instance/config.py overrides (silent if missing)
app.config["SECRET_KEY"]           = os.getenv("FLASK_SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///research_agent.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"]   = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
app.config["UPLOAD_FOLDER"]        = os.path.join("static", "uploads")
app.config.from_pyfile("config.py", silent=True)   # instance/config.py overrides

ALLOWED_EXTENSIONS = {"pdf"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    sessions = ChatSession.query.order_by(ChatSession.updated_at.desc()).limit(10).all()
    docs = UploadedDocument.query.order_by(UploadedDocument.uploaded_at.desc()).limit(10).all()
    return render_template("index.html", sessions=sessions, docs=docs, agent=AGENT_INSTRUCTIONS)


@app.route("/chat")
@app.route("/chat/<int:session_id>")
def chat(session_id=None):
    if session_id:
        session = db.session.get(ChatSession, session_id)
        if session is None:
            return "Session not found", 404
        messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).all()
    else:
        session = None
        messages = []
    sessions = ChatSession.query.order_by(ChatSession.updated_at.desc()).limit(20).all()
    return render_template("chat.html", session=session, messages=messages, sessions=sessions, agent=AGENT_INSTRUCTIONS)


# ── Chat API ──────────────────────────────────────────────────────────────────
@app.route("/api/sessions", methods=["POST"])
def new_session():
    s = ChatSession(title="New Research Session")
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict())


@app.route("/api/sessions/<int:sid>", methods=["DELETE"])
def delete_session(sid):
    s = db.session.get(ChatSession, sid)
    if s is None:
        return jsonify({"error": "Session not found"}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/chat", methods=["POST"])
def chat_message():
    data    = request.get_json()
    sid     = data.get("session_id")
    message = data.get("message", "").strip()
    mode    = data.get("mode", "chat")   # chat | search | report | gaps | cite

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Get or create session
    if sid:
        session = db.session.get(ChatSession, sid)
    else:
        session = ChatSession(title=message[:80])
        db.session.add(session)
        db.session.flush()

    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=message, msg_type=mode)
    db.session.add(user_msg)

    # ── Route to correct tool ──────────────────────────────────────────────
    try:
        if mode == "search":
            papers = rt.search_papers(message)
            result = _format_search_results(papers, message)
            msg_type = "search"
        elif mode == "report":
            papers = rt.search_papers(message, max_results=10)
            result = rt.generate_report(message, papers)
            msg_type = "report"
        elif mode == "gaps":
            papers = rt.search_papers(message, max_results=8)
            result = rt.suggest_gaps(papers, message)
            msg_type = "gaps"
        elif mode == "cite":
            papers = rt.search_papers(message, max_results=5)
            style  = data.get("citation_style") or get_citation_style()
            result = rt.generate_all_citations(papers, style)
            msg_type = "citation"
        else:
            result = rt.answer_research_question(message)
            msg_type = "text"
    except Exception as e:
        result = f"⚠️ Error: {str(e)}"
        msg_type = "text"

    # Save assistant message
    ai_msg = ChatMessage(session_id=session.id, role="assistant", content=result, msg_type=msg_type)
    db.session.add(ai_msg)

    # Update session title if first exchange
    if session.title in ("New Research Session", "") or not session.title:
        session.title = message[:80]

    db.session.commit()
    return jsonify({"session_id": session.id, "message": ai_msg.to_dict()})


def _format_search_results(papers, query):
    if not papers:
        return f"No papers found for **{query}**."
    lines = [f"## Search Results for: *{query}*\n", f"Found **{len(papers)}** papers:\n"]
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p["authors"][:2]) + (" et al." if len(p["authors"]) > 2 else "")
        lines.append(
            f"### {i}. {p['title']}\n"
            f"**Authors:** {authors} | **Year:** {p['year']} | **Source:** {p['source']}\n\n"
            f"{p['abstract']}\n\n"
            f"🔗 [View Paper]({p['url']})\n"
        )
    return "\n".join(lines)


# ── Search API ────────────────────────────────────────────────────────────────
@app.route("/api/search", methods=["POST"])
def search():
    q = request.get_json().get("query", "")
    papers = rt.search_papers(q)
    return jsonify(papers)


# ── Summarise API ─────────────────────────────────────────────────────────────
@app.route("/api/summarise", methods=["POST"])
def summarise():
    text = request.get_json().get("text", "")
    return jsonify({"summary": rt.summarise_text(text)})


# ── PDF Upload ────────────────────────────────────────────────────────────────
@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename or not allowed_file(f.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    safe = secure_filename(f.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    f.save(filepath)

    try:
        analysis = rt.analyse_pdf(filepath)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    doc = UploadedDocument(
        filename=unique_name,
        original_name=f.filename,
        file_size=os.path.getsize(filepath),
        summary=analysis.get("summary", ""),
        insights=analysis.get("insights", ""),
        word_count=analysis.get("word_count", 0),
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify(doc.to_dict() | {"preview": analysis.get("raw_preview", "")})


# ── Documents ─────────────────────────────────────────────────────────────────
@app.route("/api/documents", methods=["GET"])
def list_documents():
    docs = UploadedDocument.query.order_by(UploadedDocument.uploaded_at.desc()).all()
    return jsonify([d.to_dict() for d in docs])


@app.route("/api/documents/<int:did>", methods=["DELETE"])
def delete_document(did):
    doc = db.session.get(UploadedDocument, did)
    if doc is None:
        return jsonify({"error": "Document not found"}), 404
    try:
        path = os.path.join(app.config["UPLOAD_FOLDER"], doc.filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    db.session.delete(doc)
    db.session.commit()
    return jsonify({"ok": True})


# ── Save Paper ────────────────────────────────────────────────────────────────
@app.route("/api/papers/save", methods=["POST"])
def save_paper():
    data = request.get_json()
    p = SavedPaper(
        title=data.get("title"), authors=json.dumps(data.get("authors", [])),
        abstract=data.get("abstract"), year=data.get("year"),
        url=data.get("url"), doi=data.get("doi"), source=data.get("source"),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict())


@app.route("/api/papers", methods=["GET"])
def list_papers():
    papers = SavedPaper.query.order_by(SavedPaper.saved_at.desc()).all()
    return jsonify([p.to_dict() for p in papers])


# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "agent": AGENT_INSTRUCTIONS["name"], "version": AGENT_INSTRUCTIONS["version"]})


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", host="0.0.0.0", port=5000)
