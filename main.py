import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import markdown
from jinja2 import DictLoader

# ============================================
# 1. НАЛАШТУВАННЯ ДОДАТКУ
# ============================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'green-library-full-no-shortcuts-final'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_text_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'txt'

# ============================================
# 2. МОДЕЛІ БАЗИ ДАНИХ
# ============================================
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), default="Невідомий автор")
    description = db.Column(db.Text, default="Опис відсутній")
    cover_image = db.Column(db.String(200), default="default_cover.jpg")
    slug = db.Column(db.String(200), unique=True, nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chapters = db.relationship('Chapter', backref='book', lazy=True, order_by="Chapter.chapter_number")

    def __repr__(self):
        return f'<Book {self.title}>'


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    chapter_number = db.Column(db.Integer, default=1)
    content = db.Column(db.Text, nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Chapter {self.chapter_number}: {self.title}>'

    def get_html(self):
        return markdown.markdown(self.content, extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists'])


with app.app_context():
    db.create_all()
# ============================================
# 3. CSS СТИЛІ (ПОВНИЙ, 500+ РЯДКІВ)
# ============================================
CSS_STYLE = """
<style>
    :root {
        --bg-dark: #050f0a;
        --bg-sidebar: #0a1912;
        --bg-card: #0f1f16;
        --bg-input: #050f0a;
        --text-main: #d1e7dd;
        --text-bright: #f0fdf4;
        --text-muted: #8ba89b;
        --accent: #4ade80;
        --accent-hover: #22c55e;
        --accent-glow: rgba(74, 222, 128, 0.3);
        --border: #1e3a2b;
        --border-hover: #4ade80;
        --danger: #ef4444;
        --danger-hover: #dc2626;
        --success: #22c55e;
        --warning: #f59e0b;
        --font-ui: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
        --font-read: 'Georgia', 'Times New Roman', serif;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.2);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.3);
        --shadow-lg: 0 10px 30px rgba(0,0,0,0.4);
        --radius-sm: 6px;
        --radius-md: 12px;
        --radius-lg: 20px;
        --transition: all 0.2s ease-in-out;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    html { scroll-behavior: smooth; }

    body { 
        background-color: var(--bg-dark); 
        color: var(--text-main); 
        font-family: var(--font-ui); 
        line-height: 1.6; 
        min-height: 100vh; 
        display: flex; 
        flex-direction: column;
    }

    a { text-decoration: none; color: inherit; transition: var(--transition); }
    a:hover { color: var(--accent); }

    .wrapper { display: flex; width: 100%; min-height: 100vh; }

    .sidebar {
        width: 260px;
        background: linear-gradient(180deg, var(--bg-sidebar) 0%, var(--bg-dark) 100%);
        border-right: 1px solid var(--border);
        padding: 25px 20px;
        display: flex;
        flex-direction: column;
        position: fixed;
        height: 100vh;
        top: 0;
        left: 0;
        z-index: 1000;
        overflow-y: auto;
    }

    .sidebar-logo { 
        font-size: 1.6rem; 
        font-weight: 700; 
        color: var(--accent); 
        margin-bottom: 40px; 
        padding-bottom: 20px;
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .sidebar-logo:hover { color: var(--accent); }

    .menu-section { margin-bottom: 10px; }

    .menu-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-muted);
        padding: 10px 15px;
        font-weight: 600;
    }

    .menu-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 15px;
        color: var(--text-muted);
        border-radius: var(--radius-sm);
        margin-bottom: 4px;
        font-weight: 500;
        transition: var(--transition);
    }

    .menu-item:hover { 
        background: rgba(74, 222, 128, 0.15); 
        color: var(--accent);
        transform: translateX(3px);
    }

    .menu-item.active { 
        background: rgba(74, 222, 128, 0.25); 
        color: var(--accent);
        border-left: 3px solid var(--accent);
        padding-left: 12px;
    }

    .menu-item.danger { color: var(--danger); }
    .menu-item.danger:hover { background: rgba(239, 68, 68, 0.15); }

    .menu-divider { 
        height: 1px; 
        background: var(--border); 
        margin: 20px 0; 
        border: none;
    }

    .user-info {
        margin-top: auto;
        padding-top: 20px;
        border-top: 1px solid var(--border);
        font-size: 0.85rem;
        color: var(--text-muted);
    }

    .main-content {
        margin-left: 260px;
        flex: 1;
        padding: 40px;
        width: calc(100% - 260px);
        min-height: 100vh;
    }

    header.public-header {
        width: 100%;
        padding: 1rem 2rem;
        background: var(--bg-card);
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 50;
        backdrop-filter: blur(10px);
    }

    .public-container { 
        margin-left: 0; 
        width: 100%; 
        padding: 40px; 
        max-width: 1400px; 
        margin: 0 auto; 
    }

    .books-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); 
        gap: 30px; 
    }

    .book-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        overflow: hidden;
        text-decoration: none;
        color: inherit;
        transition: var(--transition);
        display: flex;
        flex-direction: column;
        position: relative;
    }

    .book-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(180deg, transparent 60%, rgba(0,0,0,0.8) 100%);
        z-index: 1;
        opacity: 0;
        transition: var(--transition);
    }

    .book-card:hover { 
        transform: translateY(-8px); 
        box-shadow: var(--shadow-lg);
        border-color: var(--accent);
    }

    .book-card:hover::before { opacity: 1; }

    .book-cover-wrapper {
        position: relative;
        width: 100%;
        height: 340px;
        overflow: hidden;
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-sidebar) 100%);
    }

    .book-cover-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.4s ease;
    }

    .book-card:hover .book-cover-img { transform: scale(1.05); }

    .book-status {
        position: absolute;
        top: 12px;
        right: 12px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        z-index: 2;
    }

    .status-published { background: var(--success); color: #050f0a; }
    .status-draft { background: var(--warning); color: #050f0a; }

    .book-info { 
        padding: 20px; 
        flex: 1; 
        display: flex; 
        flex-direction: column;
        position: relative;
        z-index: 2;
    }

    .book-title { 
        font-weight: 700; 
        color: var(--text-bright); 
        margin-bottom: 8px; 
        font-size: 1.2rem;
        line-height: 1.3;
    }

    .book-author { 
        font-size: 0.9rem; 
        color: var(--accent); 
        margin-bottom: 12px;
        font-weight: 500;
    }

    .book-desc { 
        font-size: 0.85rem; 
        color: var(--text-muted); 
        line-height: 1.5; 
        display: -webkit-box; 
        -webkit-line-clamp: 3; 
        -webkit-box-orient: vertical; 
        overflow: hidden;
        flex: 1;
    }

    .book-meta {
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid var(--border);
        font-size: 0.8rem;
        color: var(--text-muted);
        display: flex;
        justify-content: space-between;
    }

    .chapter-list { list-style: none; margin-top: 20px; }

    .chapter-item {
        background: var(--bg-card);
        border: 1px solid var(--border);
        margin-bottom: 12px;
        border-radius: var(--radius-sm);
        transition: var(--transition);
        border-left: 3px solid transparent;
    }

    .chapter-item:hover { 
        border-color: var(--accent);
        border-left-color: var(--accent);
        transform: translateX(5px);
    }

    .chapter-link {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 18px 20px;
        color: var(--text-main);
        font-weight: 500;
    }

    .chapter-number {
        background: var(--accent);
        color: var(--bg-dark);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        min-width: 60px;
        text-align: center;
    }

    .chapter-link:hover { color: var(--text-bright); }
    .chapter-title { flex: 1; }
    .chapter-meta { font-size: 0.8rem; color: var(--text-muted); }

    .reader-container {
        background: var(--bg-card);
        padding: 60px;
        border-radius: var(--radius-lg);
        border: 1px solid var(--border);
        max-width: 850px;
        margin: 0 auto;
        box-shadow: var(--shadow-lg);
    }

    .reader-header {
        text-align: center;
        margin-bottom: 50px;
        padding-bottom: 30px;
        border-bottom: 2px solid var(--border);
    }

    .reader-chapter-num {
        color: var(--accent);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 3px;
        font-size: 0.9rem;
        margin-bottom: 15px;
    }

    .reader-title {
        font-family: var(--font-read);
        font-size: 2.8rem;
        color: var(--text-bright);
        line-height: 1.2;
        margin-bottom: 20px;
    }

    .reader-book-title {
        color: var(--text-muted);
        font-size: 1.1rem;
        font-style: italic;
    }

    .reader-content {
        font-family: var(--font-read);
        font-size: 1.3rem;
        color: var(--text-bright);
        line-height: 2;
        margin-top: 30px;
    }

    .reader-content p { margin-bottom: 1.8em; text-align: justify; }
    .reader-content h2 { color: var(--accent); margin: 2em 0 1em; font-size: 1.8rem; }
    .reader-content h3 { color: var(--text-main); margin: 1.5em 0 0.8em; font-size: 1.4rem; }
    .reader-content blockquote {
        border-left: 4px solid var(--accent);
        padding-left: 25px;
        margin: 2em 0;
        color: var(--text-muted);
        font-style: italic;
    }
    .reader-content code {
        background: var(--bg-sidebar);
        padding: 2px 6px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9em;
    }
    .reader-content pre {
        background: var(--bg-sidebar);
        padding: 20px;
        border-radius: var(--radius-sm);
        overflow-x: auto;
        margin: 1.5em 0;
    }
    .reader-content ul, .reader-content ol { margin: 1em 0 1em 2em; }
    .reader-content li { margin-bottom: 0.5em; }

    .form-card {
        background: var(--bg-card);
        padding: 30px;
        border-radius: var(--radius-md);
        border: 1px solid var(--border);
        margin-bottom: 30px;
    }

    .form-title {
        color: var(--accent);
        margin-bottom: 25px;
        font-size: 1.4rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .form-group { margin-bottom: 22px; }

    .form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    label { 
        display: block; 
        margin-bottom: 8px; 
        color: var(--text-muted); 
        font-weight: 500;
        font-size: 0.9rem;
    }

    label.required::after {
        content: ' *';
        color: var(--danger);
    }

    input[type="text"], 
    input[type="password"], 
    input[type="number"], 
    input[type="email"],
    textarea, 
    select {
        width: 100%;
        padding: 14px 16px;
        background: var(--bg-input);
        border: 1px solid var(--border);
        color: var(--text-main);
        border-radius: var(--radius-sm);
        font-family: inherit;
        font-size: 1rem;
        transition: var(--transition);
    }

    input[type="text"]:focus, 
    input[type="password"]:focus, 
    textarea:focus, 
    select:focus {
        outline: none; 
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-glow);
    }

    input[type="file"] { 
        padding: 12px; 
        background: var(--bg-input); 
        border: 2px dashed var(--border); 
        width: 100%; 
        color: var(--text-muted); 
        margin-bottom: 15px;
        border-radius: var(--radius-sm);
    }

    input[type="file"]:hover { border-color: var(--accent); }

    textarea { height: 180px; resize: vertical; line-height: 1.6; }
    textarea.full-height { height: 400px; }
    textarea.editor {
        height: 400px;
        resize: vertical;
        line-height: 1.6;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.95rem;
        background: #020604;
    }

    .form-hint {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-top: 5px;
        font-style: italic;
    }

    .form-actions {
        display: flex;
        gap: 15px;
        margin-top: 30px;
        justify-content: flex-end;
    }

    .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        background: var(--accent);
        color: var(--bg-dark);
        padding: 12px 28px;
        border-radius: var(--radius-sm);
        text-decoration: none;
        font-weight: 700;
        border: none;
        cursor: pointer;
        transition: var(--transition);
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .btn:hover { 
        background: var(--accent-hover); 
        transform: translateY(-2px);
        box-shadow: 0 5px 20px var(--accent-glow);
    }

    .btn:active { transform: translateY(0); }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    .btn-small { padding: 8px 16px; font-size: 0.85rem; }
    .btn-danger { background: var(--danger); color: white; }
    .btn-danger:hover { background: var(--danger-hover); box-shadow: 0 5px 20px rgba(239, 68, 68, 0.4); }
    .btn-outline { background: transparent; border: 2px solid var(--accent); color: var(--accent); }
    .btn-outline:hover { background: var(--accent); color: var(--bg-dark); }
    .btn-ghost { background: transparent; color: var(--text-muted); padding: 8px 12px; }
    .btn-ghost:hover { color: var(--accent); background: rgba(74, 222, 128, 0.1); }

    .flash { 
        padding: 16px 20px; 
        margin-bottom: 25px; 
        border-radius: var(--radius-sm); 
        background: var(--bg-card); 
        border-left: 4px solid var(--accent);
        display: flex;
        align-items: center;
        gap: 12px;
        animation: slideIn 0.3s ease;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .flash.success { border-left-color: var(--success); }
    .flash.error { border-left-color: var(--danger); }
    .flash.warning { border-left-color: var(--warning); }
    .flash.info { border-left-color: var(--accent); }

    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .badge-pub { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
    .badge-draft { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
    .badge-private { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

    .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; margin-bottom: 45px; }
    .stat-card { 
        background: var(--bg-card); 
        padding: 25px; 
        border-radius: var(--radius-md); 
        border: 1px solid var(--border); 
        text-align: center;
        transition: var(--transition);
    }
    .stat-card:hover { border-color: var(--accent); transform: translateY(-3px); }
    .stat-icon { font-size: 2.5rem; margin-bottom: 15px; display: block; }
    .stat-num { font-size: 3rem; color: var(--accent); font-weight: 800; margin-bottom: 5px; line-height: 1; }
    .stat-label { color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; }

    .modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        z-index: 2000;
        align-items: center;
        justify-content: center;
        padding: 20px;
        animation: fadeIn 0.2s ease;
    }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .modal.active { display: flex; }

    .modal-content {
        background: var(--bg-card);
        padding: 35px;
        border-radius: var(--radius-md);
        border: 1px solid var(--border);
        width: 100%;
        max-width: 550px;
        max-height: 90vh;
        overflow-y: auto;
        position: relative;
        animation: slideUp 0.3s ease;
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .modal-close {
        position: absolute;
        top: 15px;
        right: 20px;
        background: none;
        border: none;
        color: var(--text-muted);
        font-size: 1.5rem;
        cursor: pointer;
        padding: 5px;
    }
    .modal-close:hover { color: var(--danger); }

    .data-table {
        width: 100%;
        border-collapse: collapse;
        background: var(--bg-card);
        border-radius: var(--radius-sm);
        overflow: hidden;
        border: 1px solid var(--border);
    }
    .data-table th {
        background: var(--bg-sidebar);
        padding: 15px 20px;
        text-align: left;
        font-weight: 600;
        color: var(--accent);
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1px;
        border-bottom: 1px solid var(--border);
    }
    .data-table td {
        padding: 15px 20px;
        border-bottom: 1px solid var(--border);
        color: var(--text-main);
    }
    .data-table tr:last-child td { border-bottom: none; }
    .data-table tr:hover { background: rgba(74, 222, 128, 0.05); }

    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .mb-20 { margin-bottom: 20px; }
    .mb-30 { margin-bottom: 30px; }
    .mb-40 { margin-bottom: 40px; }
    .mt-20 { margin-top: 20px; }
    .mt-40 { margin-top: 40px; }
    .flex { display: flex; }
    .flex-center { display: flex; align-items: center; justify-content: center; }
    .flex-between { display: flex; align-items: center; justify-content: space-between; }
    .flex-wrap { flex-wrap: wrap; }
    .gap-10 { gap: 10px; }
    .gap-20 { gap: 20px; }
    .hidden { display: none !important; }
    .no-print { }

    @media print {
        header, .sidebar, .no-print, .modal { display: none !important; }
        body { background: white; color: black; display: block; font-size: 12pt; line-height: 1.6; }
        .main-content, .public-container { margin: 0; padding: 0; width: 100%; max-width: none; }
        .reader-container { box-shadow: none; border: none; padding: 0; background: white; max-width: none; }
        .reader-content { color: black; font-size: 12pt; font-family: Georgia, serif; }
        .reader-content p { text-align: justify; }
        h1, h2, h3 { color: black !important; }
        a { text-decoration: none; color: black; }
        .reader-header { border-bottom: 2px solid black; }
    }

    @media (max-width: 1024px) {
        .sidebar { width: 70px; padding: 20px 10px; }
        .sidebar-logo span, .menu-label, .menu-item span { display: none; }
        .menu-item { justify-content: center; padding: 15px; }
        .main-content { margin-left: 70px; width: calc(100% - 70px); }
        .stats-grid { grid-template-columns: 1fr; }
    }

    @media (max-width: 768px) {
        .sidebar { width: 100%; height: auto; position: relative; padding: 15px; flex-direction: row; flex-wrap: wrap; justify-content: center; }
        .sidebar-logo { margin: 0 20px 0 0; padding: 0; border: none; }
        .menu-item { padding: 10px 12px; margin: 2px; }
        .main-content { margin-left: 0; width: 100%; padding: 20px; }
        .books-grid { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
        .reader-container { padding: 30px 20px; }
        .reader-title { font-size: 2rem; }
        .reader-content { font-size: 1.1rem; }
        .form-row { grid-template-columns: 1fr; }
    }

    @media (max-width: 480px) {
        .books-grid { grid-template-columns: 1fr; }
        .book-cover-wrapper { height: 280px; }
        .form-actions { flex-direction: column; }
        .btn { width: 100%; }
    }
</style>
"""
# ============================================
# 4. HTML ШАБЛОНИ (ПОВНІ, БЕЗ СКОРОЧЕНЬ)
# ============================================

TEMPLATES = {
    'base_admin.html': """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Адмін-панель - GreenLib{% endblock %}</title>
""" + CSS_STYLE + """
</head>
<body>
    <div class="wrapper">
        <aside class="sidebar no-print">
            <a href="/admin" class="sidebar-logo">
                🌿 <span>GreenLib Admin</span>
            </a>
            <div class="menu-section">
                <div class="menu-label">Основне</div>
                <a href="/admin" class="menu-item {% if active == 'dashboard' %}active{% endif %}">
                    📊 <span>Огляд</span>
                </a>
                <a href="/admin?view=books" class="menu-item {% if active == 'books' %}active{% endif %}">
                    📚 <span>Мої Книги</span>
                </a>
            </div>
            <hr class="menu-divider">
            <div class="menu-section">
                <div class="menu-label">Навігація</div>
                <a href="/" target="_blank" class="menu-item">
                    🌍 <span>Перегляд сайту</span>
                </a>
                <a href="/admin?view=settings" class="menu-item">
                    ⚙️ <span>Налаштування</span>
                </a>
            </div>
            <hr class="menu-divider">
            <div class="menu-section">
                <a href="/logout" class="menu-item danger">
                    🚪 <span>Вийти</span>
                </a>
            </div>
            <div class="user-info">
                <p>Автор: <strong>Ви</strong></p>
                <p style="font-size: 0.75rem; margin-top: 5px; opacity: 0.7;">
                    v1.0 • Локальний режим
                </p>
            </div>
        </aside>
        <main class="main-content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">
                            {% if category == 'success' %}✅{% elif category == 'error' %}❌{% elif category == 'warning' %}⚠️{% else %}ℹ️{% endif %}
                            <span>{{ message }}</span>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            {% block content %}{% endblock %}
        </main>
    </div>
    <script>
        function openModal(id) { document.getElementById(id).classList.add('active'); }
        function closeModal(id) { document.getElementById(id).classList.remove('active'); }
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.classList.remove('active');
            });
        });
        function loadTextFromFile(input) {
            const file = input.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                const textarea = document.getElementById('chapter_content');
                if (textarea) {
                    textarea.value = e.target.result;
                }
            };
            reader.readAsText(file);
        }
    </script>
</body>
</html>
    """,

    'base_public.html': """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}GreenLib - Бібліотека{% endblock %}</title>
""" + CSS_STYLE + """
</head>
<body>
    <header class="public-header no-print">
        <a href="/" style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.8rem;">🌿</span>
            <span style="color:var(--accent); font-weight:700; font-size:1.4rem;">GreenLib</span>
        </a>
        <nav style="display: flex; align-items: center; gap: 20px;">
            <a href="/" style="color: var(--text-main); font-weight: 500;">Бібліотека</a>
            <a href="/admin" style="color: var(--text-muted);">Вхід для автора</a>
        </nav>
    </header>
    <div class="public-container">
        {% block content %}{% endblock %}
    </div>
    <footer style="text-align: center; padding: 40px 20px; color: var(--text-muted); border-top: 1px solid var(--border); margin-top: 60px;" class="no-print">
        <p style="margin-bottom: 10px;">&copy; 2026 GreenLib. Всі права захищені.</p>
        <p style="font-size: 0.85rem;">Створено з ❤️ для читачів</p>
    </footer>
</body>
</html>
    """,

    'dashboard.html': """
{% extends "base_admin.html" %}
{% block title %}Огляд - Адмін{% endblock %}
{% block content %}
    <div class="flex-between mb-40">
        <h1 style="color: var(--text-bright); font-size: 2rem;">📊 Панель керування</h1>
        <span class="badge badge-pub">Онлайн</span>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <span class="stat-icon">📚</span>
            <div class="stat-num">{{ books|length }}</div>
            <div class="stat-label">Всього книг</div>
        </div>
        <div class="stat-card">
            <span class="stat-icon">📖</span>
            <div class="stat-num">{{ chapters_count }}</div>
            <div class="stat-label">Всього глав</div>
        </div>
        <div class="stat-card">
            <span class="stat-icon">✨</span>
            <div class="stat-num" style="color: #6ee7b7;">✓</div>
            <div class="stat-label">Система активна</div>
        </div>
    </div>
    <div class="form-card">
        <h3 class="form-title">🚀 Швидкі дії</h3>
        <p style="margin-bottom: 25px; color: var(--text-muted); line-height: 1.7;">
            Керуйте своїми творами: створюйте нові книги, додавайте глави, 
            редагуйте контент та публікуйте історії для читачів.
        </p>
        <div style="display: flex; gap: 15px; flex-wrap: wrap;">
            <a href="/admin?view=books" class="btn">📚 Перейти до бібліотеки</a>
            <button onclick="openModal('addBookModal')" class="btn btn-outline">+ Нова книга</button>
            <a href="/" target="_blank" class="btn btn-ghost">👁️ Переглянути сайт</a>
        </div>
    </div>
    <div class="form-card mt-40">
        <h3 class="form-title">🕐 Останні зміни</h3>
        <p style="color: var(--text-muted);">
            Тут буде відображатися історія ваших дій: створення книг, 
            публікація глав, редагування контенту.
        </p>
        <div style="margin-top: 20px; padding: 15px; background: var(--bg-sidebar); border-radius: var(--radius-sm);">
            <p style="font-size: 0.9rem; color: var(--text-muted);">
                <em>Функціонал історії змін буде додано у наступних оновленнях.</em>
            </p>
        </div>
    </div>
{% endblock %}
    """,

    'books_list.html': """
{% extends "base_admin.html" %}
{% block title %}Книги - Адмін{% endblock %}
{% block content %}
    <div class="flex-between mb-40">
        <h1 style="color: var(--text-bright); font-size: 2rem;">📚 Управління книгами</h1>
        <button onclick="openModal('addBookModal')" class="btn">+ Створити книгу</button>
    </div>
    <div id="addBookModal" class="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('addBookModal')">&times;</button>
            <h2 class="form-title">✨ Нова книга</h2>
            <form method="POST" action="/add_book" enctype="multipart/form-data">
                <div class="form-group">
                    <label class="required">Назва книги</label>
                    <input type="text" name="title" required placeholder="Наприклад: Зелений Шлях" autocomplete="off">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Автор</label>
                        <input type="text" name="author" placeholder="Ваше ім'я або псевдонім">
                    </div>
                    <div class="form-group">
                        <label>Статус публікації</label>
                        <select name="status">
                            <option value="published">✅ Опубліковано відразу</option>
                            <option value="draft">📝 Чернетка (приховано)</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Обкладинка книги</label>
                    <input type="file" name="cover" accept="image/png, image/jpeg, image/gif, image/webp">
                    <p class="form-hint">Рекомендований розмір: 600×900px. Формати: JPG, PNG, GIF, WebP.</p>
                </div>
                <div class="form-group">
                    <label>Опис книги</label>
                    <textarea name="description" rows="4" placeholder="Короткий опис сюжету, жанр, для кого ця книга..."></textarea>
                </div>
                <div class="form-actions">
                    <button type="button" onclick="closeModal('addBookModal')" class="btn btn-outline">Скасувати</button>
                    <button type="submit" class="btn">💾 Створити книгу</button>
                </div>
            </form>
        </div>
    </div>
    <div style="display: grid; gap: 25px;">
        {% for book in books %}
        <div class="form-card" style="display: flex; gap: 25px; margin-bottom: 0; align-items: flex-start;">
            <div style="flex-shrink: 0;">
                <img src="{{ url_for('uploaded_file', filename=book.cover_image) }}" 
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22150%22 viewBox=%220 0 100 150%22%3E%3Crect fill=%22%230f1f16%22 width=%22100%22 height=%22150%22/%3E%3Ctext x=%2250%22 y=%2275%22 fill=%22%234ade80%22 font-size=%2210%22 text-anchor=%22middle%22%3ENo Image%3C/text%3E%3C/svg%3E'"
                     style="width: 110px; height: 165px; object-fit: cover; border-radius: var(--radius-sm); background: #000; border: 1px solid var(--border);">
                <span class="book-status {{ 'status-published' if book.is_published else 'status-draft' }}">
                    {{ 'Опубліковано' if book.is_published else 'Чернетка' }}
                </span>
            </div>
            <div style="flex: 1; min-width: 0;">
                <div class="flex-between" style="margin-bottom: 15px;">
                    <div>
                        <h3 style="color: var(--accent); font-size: 1.5rem; margin-bottom: 5px;">{{ book.title }}</h3>
                        <p style="color: var(--text-muted); font-size: 1rem;">{{ book.author }}</p>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <a href="/book/{{ book.slug }}" target="_blank" class="btn btn-small btn-outline">👁️ Перегляд</a>
                        <form action="/delete_book" method="POST" onsubmit="return confirm('⚠️ Ви впевнені, що хочете видалити книгу «{{ book.title }}» та всі її глави? Цю дію неможливо скасувати.');">
                            <input type="hidden" name="id" value="{{ book.id }}">
                            <button class="btn btn-small btn-danger">🗑️ Видалити</button>
                        </form>
                    </div>
                </div>
                <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 20px; line-height: 1.6;">
                    {{ book.description if book.description else 'Опис відсутній' }}
                </p>
                <div style="background: var(--bg-sidebar); padding: 20px; border-radius: var(--radius-sm); border: 1px solid var(--border);">
                    <h4 style="font-size: 1rem; margin-bottom: 15px; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
                        📖 Глави книги <span class="badge" style="margin-left: auto;">{{ book.chapters|length }}</span>
                    </h4>

                    <!-- ФОРМА ДОДАВАННЯ ГЛАВИ З ТЕКСТОМ (ВИПРАВЛЕНО - ТЕКСТ ВСЕРЕДИНІ ФОРМИ) -->
                    <form method="POST" action="/add_chapter" enctype="multipart/form-data">
                        <input type="hidden" name="book_id" value="{{ book.id }}">

                        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 10px; margin-bottom: 10px;">
                            <input type="text" name="title" placeholder="Назва нової глави" required style="margin: 0; padding: 10px 14px;">
                            <input type="number" name="number" placeholder="№" value="{{ book.chapters|length + 1 }}" min="1" style="margin: 0; padding: 10px 14px; text-align: center;">
                        </div>

                        <!-- 1. ПОЛЕ ДЛЯ РУЧНОГО ВВОДУ ТЕКСТУ (ВСЕРЕДИНІ ФОРМИ!) -->
                        <div class="form-group">
                            <label>Текст глави (можна вставити сюди)</label>
                            <textarea id="chapter_content" name="content" class="editor" placeholder="Вставте текст глави сюди або завантажте файл нижче..."></textarea>
                        </div>

                        <!-- 2. КНОПКА ЗАВАНТАЖЕННЯ ФАЙЛУ -->
                        <div class="form-group">
                            <label>Або завантажити з файлу (.txt)</label>
                            <input type="file" name="text_file" accept=".txt" onchange="loadTextFromFile(this)">
                            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 5px;">
                                При виборі файлу його вміст автоматично з'явиться у полі вище.
                            </p>
                        </div>

                        <button type="submit" class="btn btn-small" style="padding: 10px 20px; height: 42px;">💾 Зберегти главу</button>
                    </form>

                    <!-- СПИСОК ІСНУЮЧИХ ГЛАВ -->
                    <ul style="list-style: none; font-size: 0.9rem; color: var(--text-muted); max-height: 200px; overflow-y: auto; margin-top: 20px;">
                        {% for ch in book.chapters %}
                        <li style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border);">
                            <span style="display: flex; align-items: center; gap: 10px;">
                                <span style="color: var(--accent); font-weight: 600;">#{{ ch.chapter_number }}</span>
                                <span>{{ ch.title }}</span>
                                {% if not ch.is_published %}
                                    <span class="badge badge-draft" style="margin-left: 8px;">Чернетка</span>
                                {% endif %}
                            </span>
                            <div style="display: flex; gap: 8px;">
                                <a href="/read/{{ ch.id }}" target="_blank" style="color: var(--text-muted); font-size: 0.85rem;">👁️</a>
                                <form action="/delete_chapter" method="POST" style="display: inline;">
                                    <input type="hidden" name="id" value="{{ ch.id }}">
                                    <button type="submit" style="background:none; border:none; color: var(--danger); cursor:pointer; font-size: 0.85rem; padding: 2px 6px;">✕</button>
                                </form>
                            </div>
                        </li>
                        {% else %}
                        <li style="padding: 15px 0; text-align: center; font-style: italic; color: var(--text-muted);">
                            У цій книзі поки немає глав. Додайте першу главу вище.
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
        {% else %}
        <div class="form-card" style="text-align: center; padding: 60px 40px;">
            <div style="font-size: 4rem; margin-bottom: 20px;">📚</div>
            <h3 style="color: var(--text-main); margin-bottom: 15px; font-size: 1.5rem;">Бібліотека пуста</h3>
            <p style="color: var(--text-muted); margin-bottom: 30px; max-width: 500px; margin-left: auto; margin-right: auto;">
                Ви ще не створили жодної книги. Натисніть кнопку «+ Створити книгу» або використайте модальне вікно, щоб додати свій перший твір.
            </p>
            <button onclick="openModal('addBookModal')" class="btn">✨ Створити першу книгу</button>
        </div>
        {% endfor %}
    </div>
{% endblock %}
    """,

    'login.html': """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вхід - GreenLib Admin</title>
""" + CSS_STYLE + """
    <style>
        body { 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh;
            background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-sidebar) 100%);
        }
    </style>
</head>
<body>
    <div style="background: var(--bg-card); padding: 45px; border-radius: var(--radius-lg); border: 1px solid var(--border); width: 100%; max-width: 420px; box-shadow: var(--shadow-lg);">
        <div style="text-align: center; margin-bottom: 35px;">
            <span style="font-size: 3rem; display: block; margin-bottom: 15px;">🔐</span>
            <h2 style="color: var(--accent); margin-bottom: 10px; font-size: 1.8rem;">Вхід в адмінку</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem;">GreenLib Administration Panel</p>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}" style="margin-bottom: 25px;">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label for="password">Пароль доступу</label>
                <input type="password" id="password" name="password" placeholder="••••••••" required autofocus style="text-align: center; font-size: 1.1rem; letter-spacing: 3px;">
            </div>
            <button type="submit" class="btn" style="width: 100%; padding: 14px; font-size: 1.05rem; margin-top: 10px;">
                🔓 Увійти в систему
            </button>
        </form>
        <div style="margin-top: 30px; padding-top: 25px; border-top: 1px solid var(--border); text-align: center;">
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 15px;">
                Пароль за замовчуванням: <code style="background: var(--bg-sidebar); padding: 3px 8px; border-radius: 4px; color: var(--accent);">TrueAdmin</code>
            </p>
            <a href="/" style="color: var(--text-muted); font-size: 0.9rem; display: inline-flex; align-items: center; gap: 5px;">
                ← Повернутися на сайт
            </a>
        </div>
    </div>
    <script>
        document.getElementById('password').focus();
    </script>
</body>
</html>
    """,

    'public_index.html': """
{% extends "base_public.html" %}
{% block title %}Головна - GreenLib{% endblock %}
{% block content %}
    <div style="text-align: center; margin-bottom: 60px; padding: 40px 20px; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px solid var(--border);">
        <span style="font-size: 4rem; display: block; margin-bottom: 20px;">🌿</span>
        <h1 style="color: var(--accent); font-size: 3.5rem; margin-bottom: 15px; line-height: 1.1;">Бібліотека</h1>
        <p style="color: var(--text-muted); font-size: 1.3rem; max-width: 600px; margin: 0 auto 25px; line-height: 1.6;">
            Ласкаво просимо у світ історій. Читайте книги, відкривайте нові глави, занурюйтесь у захопливі світи.
        </p>
        <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
            <span class="badge badge-pub" style="padding: 8px 16px; font-size: 0.85rem;">{{ books|length }} книг доступно</span>
            <span class="badge" style="background: rgba(74,222,128,0.15); color: var(--accent); padding: 8px 16px; font-size: 0.85rem;">Оновлюється регулярно</span>
        </div>
    </div>
    <h2 style="color: var(--text-bright); margin-bottom: 30px; font-size: 1.8rem; display: flex; align-items: center; gap: 12px;">
        📚 Доступні книги
    </h2>
    <div class="books-grid">
        {% for book in books %}
        <a href="/book/{{ book.slug }}" class="book-card">
            <div class="book-cover-wrapper">
                <img src="{{ url_for('uploaded_file', filename=book.cover_image) }}" 
                     class="book-cover-img" 
                     alt="Обкладинка: {{ book.title }}"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22240%22 height=%22340%22 viewBox=%220 0 240 340%22%3E%3Crect fill=%22%230f1f16%22 width=%22240%22 height=%22340%22/%3E%3Ctext x=%22120%22 y=%22170%22 fill=%22%234ade80%22 font-size=%2214%22 text-anchor=%22middle%22%3ENo Cover%3C/text%3E%3C/svg%3E'">
                <span class="book-status status-published">Нове</span>
            </div>
            <div class="book-info">
                <div class="book-title">{{ book.title }}</div>
                <div class="book-author">{{ book.author }}</div>
                <div class="book-desc">{{ book.description if book.description else 'Опис відсутній. Натисніть, щоб дізнатися більше.' }}</div>
                <div class="book-meta">
                    <span>📖 {{ book.chapters|length }} глав</span>
                    <span>{{ book.created_at.strftime('%d.%m.%Y') }}</span>
                </div>
            </div>
        </a>
        {% else %}
        <div style="grid-column: 1 / -1; text-align: center; padding: 80px 40px; background: var(--bg-card); border-radius: var(--radius-md); border: 1px dashed var(--border);">
            <span style="font-size: 5rem; display: block; margin-bottom: 25px;">📭</span>
            <h3 style="color: var(--text-main); margin-bottom: 15px; font-size: 1.6rem;">Книг поки немає</h3>
            <p style="color: var(--text-muted); max-width: 500px; margin: 0 auto 30px; line-height: 1.6;">
                Автор ще не опублікував жодної книги. Загляньте пізніше — нові історії з'являться зовсім скоро!
            </p>
            <a href="/admin" class="btn btn-outline">Для автора: вхід в адмінку</a>
        </div>
        {% endfor %}
    </div>
{% endblock %}
    """,

    'public_book.html': """
{% extends "base_public.html" %}
{% block title %}{{ book.title }} - GreenLib{% endblock %}
{% block content %}
    <div style="margin-bottom: 30px;">
        <a href="/" style="display: inline-flex; align-items: center; gap: 8px; color: var(--accent); font-weight: 500; padding: 10px 15px; background: var(--bg-card); border-radius: var(--radius-sm); border: 1px solid var(--border); transition: var(--transition);">
            <span style="font-size: 1.2rem;">←</span>
            Повернутися до бібліотеки
        </a>
    </div>
    <div style="display: flex; gap: 50px; margin-bottom: 60px; align-items: flex-start; flex-wrap: wrap;">
        <div style="flex-shrink: 0;">
            <img src="{{ url_for('uploaded_file', filename=book.cover_image) }}" 
                 style="width: 280px; border-radius: var(--radius-md); box-shadow: var(--shadow-lg); border: 1px solid var(--border);"
                 alt="Обкладинка: {{ book.title }}"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22280%22 height=%22400%22 viewBox=%220 0 280 400%22%3E%3Crect fill=%22%230f1f16%22 width=%22280%22 height=%22400%22/%3E%3Ctext x=%22140%22 y=%22200%22 fill=%22%234ade80%22 font-size=%2216%22 text-anchor=%22middle%22%3ENo Cover%3C/text%3E%3C/svg%3E'">
        </div>
        <div style="flex: 1; min-width: 300px;">
            <h1 style="font-size: 3.2rem; margin-bottom: 15px; color: var(--text-bright); line-height: 1.1;">{{ book.title }}</h1>
            <h3 style="color: var(--accent); margin-bottom: 25px; font-size: 1.6rem; font-weight: 500;">{{ book.author }}</h3>
            <div style="background: var(--bg-card); padding: 25px; border-radius: var(--radius-md); border: 1px solid var(--border); margin-bottom: 30px;">
                <p style="color: var(--text-main); line-height: 1.8; font-size: 1.05rem;">
                    {{ book.description if book.description else 'Опис цієї книги відсутній.' }}
                </p>
            </div>
            <div style="display: flex; gap: 20px; flex-wrap: wrap; color: var(--text-muted); font-size: 0.95rem;">
                <span>📖 <strong>{{ book.chapters|length }}</strong> глав</span>
                <span>📅 Опубліковано: <strong>{{ book.created_at.strftime('%d %B %Y') }}</strong></span>
                {% if book.chapters %}
                <span>🔄 Останнє оновлення: <strong>{{ book.chapters[-1].created_at.strftime('%d.%m.%Y') }}</strong></span>
                {% endif %}
            </div>
        </div>
    </div>
    <h2 style="color: var(--text-bright); border-bottom: 2px solid var(--border); padding-bottom: 20px; margin-bottom: 30px; font-size: 2rem;">
        📑 Зміст книги
    </h2>
    <div class="chapter-list">
        {% for ch in book.chapters %}
            {% if ch.is_published %}
            <div class="chapter-item">
                <a href="/read/{{ ch.id }}" class="chapter-link">
                    <span class="chapter-number">{{ ch.chapter_number }}</span>
                    <span class="chapter-title">{{ ch.title }}</span>
                    <span class="chapter-meta">{{ ch.created_at.strftime('%d.%m') }}</span>
                </a>
            </div>
            {% endif %}
        {% else %}
            <div style="padding: 40px; background: var(--bg-card); border-radius: var(--radius-md); border: 1px dashed var(--border); text-align: center;">
                <span style="font-size: 3rem; display: block; margin-bottom: 15px;">🚧</span>
                <p style="color: var(--text-muted); font-size: 1.1rem;">
                    У цій книзі поки немає опублікованих глав.<br>
                    Автор працює над контентом — загляньте пізніше!
                </p>
            </div>
        {% endfor %}
    </div>
    <div class="no-print" style="margin-top: 50px; text-align: center; padding-top: 30px; border-top: 1px solid var(--border);">
        <button onclick="window.print()" class="btn btn-outline" style="display: inline-flex; align-items: center; gap: 8px;">
            🖨️ Зберегти книгу як PDF
        </button>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 12px;">
            Працює в будь-якому браузері • Форматування зберігається
        </p>
    </div>
{% endblock %}
    """,

    'public_read.html': """
{% extends "base_public.html" %}
{% block title %}Глава {{ chapter.chapter_number }}: {{ chapter.title }} - {{ chapter.book.title }}{% endblock %}
{% block content %}
    <div class="no-print" style="margin-bottom: 40px; display: flex; justify-content: center;">
        <a href="/book/{{ chapter.book.slug }}" style="display: inline-flex; align-items: center; gap: 8px; color: var(--accent); font-weight: 500; padding: 12px 20px; background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border); transition: var(--transition);">
            <span style="font-size: 1.3rem;">←</span>
            <span>Повернутися до змісту «{{ chapter.book.title }}»</span>
        </a>
    </div>
    <article class="reader-container">
        <header class="reader-header">
            <div class="reader-chapter-num">Глава {{ chapter.chapter_number }}</div>
            <h1 class="reader-title">{{ chapter.title }}</h1>
            <p class="reader-book-title">з книги «{{ chapter.book.title }}»</p>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-top: 15px;">
                {{ chapter.created_at.strftime('%d %B %Y') }}
            </p>
        </header>
        <div class="reader-content">
            {{ chapter.get_html() | safe }}
        </div>
        <div class="no-print" style="margin-top: 60px; padding-top: 40px; border-top: 2px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
            <div>
                <span style="color: var(--text-muted); font-size: 0.9rem;">Прочитано главу {{ chapter.chapter_number }}</span>
            </div>
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                <a href="/book/{{ chapter.book.slug }}" class="btn btn-outline">📑 До змісту</a>
                <button onclick="window.print()" class="btn">💾 Зберегти як PDF</button>
            </div>
        </div>
    </article>
    <script class="no-print">
        window.addEventListener('load', () => { window.scrollTo(0, 0); });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') { window.location.href = '/book/{{ chapter.book.slug }}'; }
        });
    </script>
{% endblock %}
"""
}

# ============================================
# 5. ІНІЦІАЛІЗАЦІЯ JINJA2 DICTLOADER
# ============================================
app.jinja_loader = DictLoader(TEMPLATES)


# ============================================
# 6. МАРШРУТИ (ПОВНІ)
# ============================================

@app.route('/')
def index():
    books = Book.query.filter_by(is_published=True).order_by(Book.created_at.desc()).all()
    from flask import render_template
    return render_template('public_index.html', books=books)


@app.route('/book/<slug>')
def show_book(slug):
    book = Book.query.filter_by(slug=slug).first_or_404()
    if not book.is_published and 'admin' not in session:
        from flask import abort
        abort(404)
    from flask import render_template
    return render_template('public_book.html', book=book)


@app.route('/read/<int:chapter_id>')
def read_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if not chapter.is_published and 'admin' not in session:
        from flask import abort
        abort(404)
    from flask import render_template
    return render_template('public_read.html', chapter=chapter)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'admin' not in session:
        if request.method == 'POST':
            password = request.form.get('password')
            if password == 'V9!kT2#Lm8@Q':
                session['admin'] = True
                flash('✅ Успішний вхід у систему!', 'success')
                return redirect(url_for('admin_panel'))
            else:
                flash('❌ Невірний пароль. Спробуйте ще раз.', 'error')
        from flask import render_template
        return render_template('login.html')

    view = request.args.get('view', 'dashboard')
    books = Book.query.order_by(Book.created_at.desc()).all()
    total_chapters = Chapter.query.count()

    from flask import render_template
    if view == 'books':
        return render_template('books_list.html', books=books, active='books')
    else:
        return render_template('dashboard.html', books=books, chapters_count=total_chapters, active='dashboard')


@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('👋 Ви вийшли з системи.', 'info')
    return redirect(url_for('index'))


@app.route('/add_book', methods=['POST'])
def add_book():
    if 'admin' not in session:
        return redirect(url_for('admin_panel'))

    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    description = request.form.get('description', '').strip()
    status = request.form.get('status', 'published')

    if not title:
        flash("❌ Назва книги є обов'язковою.", 'error')
        return redirect(url_for('admin_panel', view='books'))

    slug = title.lower().replace(' ', '-').replace('.', '').replace(',', '')
    slug = "".join(c for c in slug if c.isalnum() or c == '-')

    counter = 1
    original_slug = slug
    while Book.query.filter_by(slug=slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1

    filename = "default_cover.jpg"
    if 'cover' in request.files:
        file = request.files['cover']
        if file and file.filename != '' and allowed_image(file.filename):
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_book = Book(
        title=title,
        author=author or "Невідомий автор",
        description=description,
        slug=slug,
        cover_image=filename,
        is_published=(status == 'published')
    )

    db.session.add(new_book)
    db.session.commit()

    flash(f'✅ Книга «{title}» успішно створена!', 'success')
    return redirect(url_for('admin_panel', view='books'))


@app.route('/add_chapter', methods=['POST'])
def add_chapter():
    if 'admin' not in session:
        return redirect(url_for('admin_panel'))

    book_id = request.form.get('book_id')
    title = request.form.get('title', '').strip()
    chapter_number = request.form.get('number', 1)

    if not book_id or not title:
        flash("❌ Всі поля є обов'язковими.", 'error')
        return redirect(url_for('admin_panel', view='books'))

    # ОТРИМУЄМО ТЕКСТ З ПОЛЯ ВВОДУ
    content = request.form.get('content', '')

    # ЯКЩО ЗАВАНТАЖЕНО ФАЙЛ, ЧИТАЄМО ЙОГО
    if 'text_file' in request.files:
        file = request.files['text_file']
        if file and file.filename != '' and allowed_text_file(file.filename):
            try:
                file_content = file.read().decode('utf-8')
                if content.strip():
                    content += "\n\n" + file_content
                else:
                    content = file_content
            except Exception as e:
                flash(f'Помилка читання файлу: {e}', 'error')

    if not content:
        content = "Текст відсутній."

    new_chapter = Chapter(
        book_id=book_id,
        title=title,
        chapter_number=int(chapter_number),
        content=content,
        is_published=True
    )

    db.session.add(new_chapter)
    db.session.commit()

    flash(f'✅ Главу «{title}» додано!', 'success')
    return redirect(url_for('admin_panel', view='books'))


@app.route('/delete_book', methods=['POST'])
def delete_book():
    if 'admin' not in session:
        return redirect(url_for('admin_panel'))

    book_id = request.form.get('id')
    book = Book.query.get(book_id)

    if book:
        Chapter.query.filter_by(book_id=book_id).delete()
        db.session.delete(book)
        db.session.commit()
        flash(f'🗑️ Книга «{book.title}» та всі її глави видалені.', 'info')

    return redirect(url_for('admin_panel', view='books'))


@app.route('/delete_chapter', methods=['POST'])
def delete_chapter():
    if 'admin' not in session:
        return redirect(url_for('admin_panel'))

    chapter_id = request.form.get('id')
    chapter = Chapter.query.get(chapter_id)

    if chapter:
        chapter_title = chapter.title
        db.session.delete(chapter)
        db.session.commit()
        flash(f'🗑️ Главу «{chapter_title}» видалено.', 'info')

    return redirect(url_for('admin_panel', view='books'))


# ============================================
# 7. ЗАПУСК ДОДАТКУ
# ============================================
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🌿  GreenLib - Бібліотека для ваших книг  🌿")
    print("=" * 60)
    print(f"🌍 Сайт доступний за адресою: http://127.0.0.1:5000")
    print(f"🔑 Адмін-панель: http://127.0.0.1:5000/admin")
    print(f"📁 Папка для картинок: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
    print(f"🗄️ База даних: {os.path.abspath('instance/library.db')}")
    print("=" * 60)
    print("💡 Пароль адміністратора за замовчуванням: TrueAdmin")
    print("⚠️  Змініть пароль у коді перед використанням у продакшені!")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)