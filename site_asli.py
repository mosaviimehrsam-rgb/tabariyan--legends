import os
import sqlite3
import secrets
from functools import wraps
from datetime import datetime
from flask import session, redirect, url_for, render_template_string
from admin import admin

from flask import (
    Flask, request, redirect, url_for, session,
    flash, render_template_string, send_from_directory
)
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# ==================================================
# SETTINGS
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tabariyan.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.register_blueprint(admin)

@app.route("/admin")
def admin_panel():
    if not session.get("is_admin"):
        return redirect("/login")

    return render_template_string("""
    <html>
    <head>
        <title>Tabariyan City Admin</title>
        <style>
            body {
                background: #101827;
                color: white;
                font-family: Arial;
                text-align: center;
                padding: 40px;
            }
            .box {
                background: #1e293b;
                padding: 25px;
                border-radius: 15px;
                max-width: 500px;
                margin: auto;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>🏙️ TABARIYAN CITY</h1>
            <h2>Admin Panel</h2>
            <p>خوش آمدی به پنل مدیریت</p>
        </div>
    </body>
    </html>
    """)


app.secret_key = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

socketio = SocketIO(app, cors_allowed_origins=[])

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME", "mehrsam_admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD", "ChangeMe123!"
)

online_users = {}


# ==================================================
# DATABASE
# ==================================================

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def add_missing_columns(con, table, columns):
    existing = {
        row["name"]
        for row in con.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }

    for name, definition in columns.items():
        if name not in existing:
            con.execute(
                f"ALTER TABLE {table} ADD COLUMN {name} {definition}"
            )


def init_db():
    con = get_db()

    con.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        fullname TEXT DEFAULT '',
        position TEXT DEFAULT '',
        number INTEGER DEFAULT 0,
        goals INTEGER DEFAULT 0,
        assists INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT DEFAULT '',
        poster TEXT DEFAULT '',
        author TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # فقط ستون‌هایی که در دیتابیس قدیمی وجود ندارند اضافه می‌شوند.
    # مقدارهای DEFAULT در این بخش باید ثابت باشند.

    add_missing_columns(con, "users", {
        "username": "TEXT DEFAULT ''",
        "password": "TEXT DEFAULT ''",
        "fullname": "TEXT DEFAULT ''",
        "position": "TEXT DEFAULT ''",
        "number": "INTEGER DEFAULT 0",
        "goals": "INTEGER DEFAULT 0",
        "assists": "INTEGER DEFAULT 0",
        "is_admin": "INTEGER DEFAULT 0",
        "created_at": "TEXT DEFAULT ''"
    })

    add_missing_columns(con, "messages", {
        "sender": "TEXT DEFAULT ''",
        "receiver": "TEXT DEFAULT 'TEAM'",
        "message": "TEXT DEFAULT ''",
        "created_at": "TEXT DEFAULT ''"
    })

    add_missing_columns(con, "news", {
        "title": "TEXT DEFAULT ''",
        "content": "TEXT DEFAULT ''",
        "poster": "TEXT DEFAULT ''",
        "author": "TEXT DEFAULT ''",
        "created_at": "TEXT DEFAULT ''"
    })

    # ایجاد مدیر اولیه، فقط اگر وجود نداشته باشد.
    admin = con.execute(
        "SELECT id FROM users WHERE username=?",
        (ADMIN_USERNAME,)
    ).fetchone()

    if admin:
        con.execute(
            "UPDATE users SET is_admin=1 WHERE username=?",
            (ADMIN_USERNAME,)
        )
    else:
        con.execute("""
            INSERT INTO users
            (username, password, fullname, is_admin)
            VALUES (?, ?, ?, 1)
        """, (
            ADMIN_USERNAME,
            generate_password_hash(ADMIN_PASSWORD),
            "مدیریت TABARIYAN LEGENDS"
        ))

    con.commit()
    con.close()


init_db()


# ==================================================
# DESIGN
# ==================================================

STYLE = """
<style>
* { box-sizing:border-box; }

body {
    margin:0;
    direction:rtl;
    font-family:Tahoma,Arial,sans-serif;
    background:#071629;
    color:white;
}

nav {
    background:#0d2745;
    padding:15px;
    display:flex;
    flex-wrap:wrap;
    justify-content:center;
    gap:12px;
    border-bottom:2px solid #e63950;
}

nav a {
    color:white;
    text-decoration:none;
    padding:8px;
}

nav a:hover { color:#ff5367; }

.container {
    max-width:1050px;
    margin:25px auto;
    padding:15px;
}

.hero {
    background:linear-gradient(135deg,#123d69,#a51f39);
    padding:35px 20px;
    text-align:center;
    border-radius:18px;
    margin-bottom:20px;
}

.hero h1 { font-size:30px; }

.card {
    background:#102b49;
    border:1px solid #25496c;
    border-radius:14px;
    padding:20px;
    margin-bottom:18px;
}

h2 { color:#ff5367; }

input,textarea,select {
    width:100%;
    padding:13px;
    margin:8px 0;
    border:1px solid #31577e;
    border-radius:8px;
    background:#071629;
    color:white;
    font-family:inherit;
}

textarea {
    min-height:110px;
    resize:vertical;
}

button,.btn {
    display:inline-block;
    padding:12px 18px;
    border:0;
    border-radius:8px;
    background:#e63950;
    color:white;
    cursor:pointer;
    text-decoration:none;
    font-family:inherit;
    margin:5px 0;
}

button:hover,.btn:hover { background:#bd263d; }

.grid {
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
    gap:15px;
}

.player {
    background:#0b2038;
    border:1px solid #294b6d;
    padding:18px;
    border-radius:12px;
    margin-bottom:10px;
}

.player a {
    color:white;
    text-decoration:none;
}

.poster {
    width:100%;
    max-height:400px;
    object-fit:contain;
    border-radius:10px;
    margin-top:10px;
}

.message {
    background:#163858;
    padding:12px;
    margin:9px 0;
    border-radius:10px;
    overflow-wrap:anywhere;
}

.message small { color:#a9c2d8; }

#messages {
    height:350px;
    overflow-y:auto;
    background:#081a2d;
    padding:12px;
    border-radius:10px;
}

video {
    width:100%;
    background:black;
    border-radius:10px;
    margin:5px 0;
}

.flash {
    background:#7c2535;
    padding:12px;
    border-radius:8px;
    margin:10px 0;
}

footer {
    text-align:center;
    padding:25px;
    color:#9db3c9;
}

@media(max-width:600px) {
    .hero h1 { font-size:22px; }
    nav { gap:5px; }
    nav a { font-size:12px; }
}
</style>
"""

NAV = """
<nav>
    <a href="/">خانه</a>
    <a href="/players">بازیکنان</a>
    <a href="/news">اخبار</a>
    <a href="/chat">پیام‌رسان</a>
    <a href="/call">تماس</a>

    {% if session.get('user') %}
        <a href="/profile">پروفایل</a>
        <a href="/logout">خروج</a>
    {% else %}
        <a href="/login">ورود</a>
        <a href="/register">ثبت‌نام</a>
    {% endif %}

    {% if session.get('admin') %}
        <a href="/admin">مدیریت</a>
    {% endif %}
</nav>
"""


def page(content, **context):
    body = render_template_string(content, **context)

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>TABARIYAN LEGENDS</title>
        """ + STYLE + """
    </head>
    <body>
        """ + NAV + """
        <div class="container">
            {% with items=get_flashed_messages() %}
                {% for item in items %}
                    <div class="flash">{{item}}</div>
                {% endfor %}
            {% endwith %}
            {{body|safe}}
        </div>
        <footer>TABARIYAN LEGENDS</footer>
    </body>
    </html>
    """, body=body)


# ==================================================
# AUTH
# ==================================================

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            flash("ابتدا وارد حساب شوید.")
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            flash("دسترسی مدیر لازم است.")
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        fullname = request.form.get("fullname", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(password) < 6:
            flash("نام کاربری حداقل ۳ و رمز حداقل ۶ حرف باشد.")
            return redirect("/register")

        con = get_db()
        try:
            con.execute("""
                INSERT INTO users(username,password,fullname)
                VALUES(?,?,?)
            """, (
                username,
                generate_password_hash(password),
                fullname
            ))
            con.commit()
            flash("ثبت‌نام موفق بود.")
            return redirect("/login")

        except sqlite3.IntegrityError:
            flash("این نام کاربری قبلاً استفاده شده است.")

        finally:
            con.close()

    return page("""
    <div class="card">
        <h2>ثبت‌نام</h2>
        <form method="POST">
            <input name="fullname" placeholder="نام کامل" required>
            <input name="username" placeholder="نام کاربری" required>
            <input name="password" type="password"
                   placeholder="رمز عبور" required>
            <button>ثبت‌نام</button>
        </form>
    </div>
    """)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        con = get_db()
        user = con.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        con.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user"] = user["username"]
            session["admin"] = bool(user["is_admin"])
            flash("با موفقیت وارد شدید.")
            return redirect("/")

        flash("نام کاربری یا رمز اشتباه است.")

    return page("""
    <div class="card">
        <h2>ورود</h2>
        <form method="POST">
            <input name="username" placeholder="نام کاربری" required>
            <input name="password" type="password"
                   placeholder="رمز عبور" required>
            <button>ورود</button>
        </form>
    </div>
    """)


@app.route("/logout")
def logout():
    session.clear()
    flash("از حساب خارج شدید.")
    return redirect("/")


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():
    con = get_db()

    players = con.execute("""
        SELECT * FROM users
        WHERE is_admin=0
        ORDER BY goals DESC
        LIMIT 6
    """).fetchall()

    news = con.execute("""
        SELECT * FROM news
        ORDER BY id DESC
        LIMIT 3
    """).fetchall()

    con.close()

    return page("""
    <div class="hero">
        <h1>💙 TABARIYAN CITY ❤️</h1>
        <h3>وب‌سایت رسمی تیم</h3>
        <p>قدرت، اتحاد و افتخار</p>
        <a class="btn" href="/players">بازیکنان</a>
        <a class="btn" href="/news">اخبار</a>
    </div>

    <h2>بازیکنان برتر</h2>
    <div class="grid">
    {% for p in players %}
        <div class="player">
            <h3>{{p.fullname or p.username}}</h3>
            <p>شماره: {{p.number}}</p>
            <p>پست: {{p.position}}</p>
            <p>گل: {{p.goals}} | پاس گل: {{p.assists}}</p>
            <a href="/profile?username={{p.username}}">پروفایل</a>
        </div>
    {% else %}
        <div class="card">بازیکنی ثبت نشده است.</div>
    {% endfor %}
    </div>

    <h2>آخرین اخبار</h2>
    {% for n in news %}
        <div class="card">
            <h3>{{n.title}}</h3>
            <p>{{n.content}}</p>
            {% if n.poster %}
                <img class="poster" src="/uploads/{{n.poster}}">
            {% endif %}
        </div>
    {% else %}
        <div class="card">خبری منتشر نشده است.</div>
    {% endfor %}
    """, players=players, news=news)


# ==================================================
# PLAYERS
# ==================================================

@app.route("/players")
def players():
    con = get_db()
    data = con.execute("""
        SELECT * FROM users
        WHERE is_admin=0
        ORDER BY goals DESC, assists DESC
    """).fetchall()
    con.close()

    return page("""
    <h2>بازیکنان تیم</h2>
    <div class="grid">
    {% for p in players %}
        <div class="player">
            <h3>{{p.fullname or p.username}}</h3>
            <p>شماره: {{p.number}}</p>
            <p>پست: {{p.position}}</p>
            <p>گل: {{p.goals}}</p>
            <p>پاس گل: {{p.assists}}</p>
            <a href="/profile?username={{p.username}}">مشاهده پروفایل</a>
        </div>
    {% else %}
        <div class="card">بازیکنی وجود ندارد.</div>
    {% endfor %}
    </div>
    """, players=data)


# ==================================================
# PROFILE
# ==================================================

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    username = request.args.get("username", session["user"])

    can_edit = (
        username == session["user"] or session.get("admin")
    )

    if request.method == "POST":
        if not can_edit:
            flash("اجازه ویرایش ندارید.")
            return redirect("/profile")

        fullname = request.form.get("fullname", "").strip()
        position = request.form.get("position", "").strip()

        try:
            number = max(0, int(request.form.get("number", 0)))
        except ValueError:
            number = 0

        con = get_db()
        con.execute("""
            UPDATE users
            SET fullname=?, position=?, number=?
            WHERE username=?
        """, (fullname, position, number, username))
        con.commit()
        con.close()

        flash("پروفایل ذخیره شد.")
        return redirect(url_for("profile", username=username))

    con = get_db()
    user = con.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()
    con.close()

    if not user:
        flash("کاربر پیدا نشد.")
        return redirect("/players")

    return page("""
    <div class="card">
        <h2>پروفایل {{user.fullname or user.username}}</h2>
        <p>نام کاربری: {{user.username}}</p>
        <p>شماره: {{user.number}}</p>
        <p>پست: {{user.position}}</p>
        <p>گل: {{user.goals}}</p>
        <p>پاس گل: {{user.assists}}</p>

        {% if can_edit %}
        <hr>
        <h3>ویرایش پروفایل</h3>
        <form method="POST">
            <input name="fullname" value="{{user.fullname}}"
                   placeholder="نام کامل">
            <input name="position" value="{{user.position}}"
                   placeholder="پست بازی">
            <input name="number" type="number"
                   value="{{user.number}}" placeholder="شماره">
            <button>ذخیره</button>
        </form>
        {% endif %}
    </div>
    """, user=user, can_edit=can_edit)


# ==================================================
# NEWS
# ==================================================

@app.route("/news")
def news():
    con = get_db()
    items = con.execute(
        "SELECT * FROM news ORDER BY id DESC"
    ).fetchall()
    con.close()

    return page("""
    <h2>اخبار تیم</h2>
    {% for n in news %}
        <div class="card">
            <h3>{{n.title}}</h3>
            <p>{{n.content}}</p>
            {% if n.poster %}
                <img class="poster" src="/uploads/{{n.poster}}">
            {% endif %}
            <small>نویسنده: {{n.author}}</small>
        </div>
    {% else %}
        <div class="card">هنوز خبری منتشر نشده است.</div>
    {% endfor %}
    """, news=items)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ==================================================
# ADMIN
# ==================================================

@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    con = get_db()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_player":
            username = request.form.get("username", "").strip()
            fullname = request.form.get("fullname", "").strip()
            password = request.form.get("password", "")

            if len(username) < 3 or len(password) < 6:
                flash("نام کاربری یا رمز معتبر نیست.")
            else:
                try:
                    con.execute("""
                        INSERT INTO users(username,password,fullname)
                        VALUES(?,?,?)
                    """, (
                        username,
                        generate_password_hash(password),
                        fullname
                    ))
                    con.commit()
                    flash("بازیکن اضافه شد.")
                except sqlite3.IntegrityError:
                    flash("نام کاربری تکراری است.")

        elif action == "update_stats":
            username = request.form.get("username", "")

            try:
                goals = max(0, int(request.form.get("goals", 0)))
                assists = max(0, int(request.form.get("assists", 0)))
            except ValueError:
                goals = assists = 0

            con.execute("""
                UPDATE users SET goals=?, assists=?
                WHERE username=? AND is_admin=0
            """, (goals, assists, username))
            con.commit()
            flash("آمار ذخیره شد.")

        elif action == "delete_player":
            username = request.form.get("username", "")

            if username != ADMIN_USERNAME:
                con.execute("""
                    DELETE FROM users
                    WHERE username=? AND is_admin=0
                """, (username,))
                con.commit()
                flash("بازیکن حذف شد.")

        elif action == "add_news":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            poster = request.files.get("poster")
            filename = ""

            if poster and poster.filename:
                safe_name = secure_filename(poster.filename)
                extension = os.path.splitext(safe_name)[1].lower()

                if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
                    flash("فرمت پوستر نامعتبر است.")
                    con.close()
                    return redirect("/admin")

                filename = secrets.token_hex(12) + extension
                poster.save(os.path.join(UPLOAD_DIR, filename))

            if title:
                con.execute("""
                    INSERT INTO news(title,content,poster,author)
                    VALUES(?,?,?,?)
                """, (
                    title, content, filename, session["user"]
                ))
                con.commit()
                flash("خبر منتشر شد.")

        elif action == "delete_news":
            try:
                news_id = int(request.form.get("news_id", 0))
            except ValueError:
                news_id = 0

            item = con.execute(
                "SELECT poster FROM news WHERE id=?",
                (news_id,)
            ).fetchone()

            if item:
                con.execute(
                    "DELETE FROM news WHERE id=?",
                    (news_id,)
                )
                con.commit()

                if item["poster"]:
                    path = os.path.join(UPLOAD_DIR, item["poster"])
                    if os.path.isfile(path):
                        os.remove(path)

                flash("خبر حذف شد.")

    players_data = con.execute("""
        SELECT * FROM users
        WHERE is_admin=0
        ORDER BY username
    """).fetchall()

    news_data = con.execute(
        "SELECT * FROM news ORDER BY id DESC"
    ).fetchall()

    con.close()

    return page("""
    <div class="card">
        <h2>پنل مدیریت</h2>
        <p>مدیریت TABARIYAN LEGENDS</p>
    </div>

    <div class="card">
        <h2>افزودن بازیکن</h2>
        <form method="POST">
            <input type="hidden" name="action" value="add_player">
            <input name="fullname" placeholder="نام کامل" required>
            <input name="username" placeholder="نام کاربری" required>
            <input name="password" type="password"
                   placeholder="رمز عبور" required>
            <button>افزودن</button>
        </form>
    </div>

    <div class="card">
        <h2>مدیریت آمار</h2>
        {% for p in players %}
        <form method="POST" class="player">
            <input type="hidden" name="action" value="update_stats">
            <input type="hidden" name="username" value="{{p.username}}">
            <b>{{p.fullname or p.username}}</b>
            <input type="number" name="goals"
                   value="{{p.goals}}" min="0">
            <input type="number" name="assists"
                   value="{{p.assists}}" min="0">
            <button>ذخیره آمار</button>
        </form>
        {% endfor %}
    </div>

    <div class="card">
        <h2>حذف بازیکن</h2>
        {% for p in players %}
        <form method="POST">
            <input type="hidden" name="action" value="delete_player">
            <input type="hidden" name="username" value="{{p.username}}">
            <button>حذف {{p.fullname or p.username}}</button>
        </form>
        {% endfor %}
    </div>

    <div class="card">
        <h2>انتشار خبر و پوستر</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="add_news">
            <input name="title" placeholder="عنوان خبر" required>
            <textarea name="content" placeholder="متن خبر"></textarea>
            <input type="file" name="poster"
                   accept=".jpg,.jpeg,.png,.webp">
            <button>انتشار خبر</button>
        </form>
    </div>

    <div class="card">
        <h2>حذف اخبار</h2>
        {% for n in news %}
        <form method="POST">
            <input type="hidden" name="action" value="delete_news">
            <input type="hidden" name="news_id" value="{{n.id}}">
            <b>{{n.title}}</b>
            <button>حذف خبر</button>
        </form>
        {% endfor %}
    </div>
    """, players=players_data, news=news_data)


# ==================================================
# CHAT
# ==================================================

def private_room(user1, user2):
    return "private_" + "_".join(sorted([user1, user2]))


def get_chat_messages(username, target):
    con = get_db()

    if target == "TEAM":
        data = con.execute("""
            SELECT * FROM messages
            WHERE receiver='TEAM'
            ORDER BY id DESC LIMIT 100
        """).fetchall()
    else:
        data = con.execute("""
            SELECT * FROM messages
            WHERE
            (sender=? AND receiver=?)
            OR
            (sender=? AND receiver=?)
            ORDER BY id DESC LIMIT 100
        """, (
            username, target,
            target, username
        )).fetchall()

    con.close()
    return list(reversed(data))


@app.route("/chat")
@login_required
def chat():
    username = session["user"]
    target = request.args.get("user", "TEAM")

    con = get_db()

    if target != "TEAM":
        user = con.execute(
            "SELECT id FROM users WHERE username=?",
            (target,)
        ).fetchone()

        if not user or target == username:
            con.close()
            flash("کاربر معتبر نیست.")
            return redirect("/chat")

    users = con.execute("""
        SELECT username,fullname FROM users
        WHERE username != ?
        ORDER BY username
    """, (username,)).fetchall()

    con.close()

    messages = get_chat_messages(username, target)

    return page("""
    <div class="card">
        <h2>پیام‌رسان TABARIYAN LEGENDS</h2>

        <p>کاربر: {{username}}</p>

        <a class="btn" href="/chat">گروه تیم</a>

        {% for u in users %}
            <a class="btn" href="/chat?user={{u.username}}">
                {{u.fullname or u.username}}
            </a>
        {% endfor %}

        <hr>
        <h3>
            {% if target == "TEAM" %}
                گفت‌وگوی گروهی تیم
            {% else %}
                گفت‌وگوی خصوصی با {{target}}
            {% endif %}
        </h3>

        <div id="messages">
            {% for m in messages %}
            <div class="message">
                <b>{{m.sender}}</b>
                <p>{{m.message}}</p>
                <small>{{m.created_at}}</small>
            </div>
            {% endfor %}
        </div>

        <input id="msg" placeholder="پیام خود را بنویسید">
        <button onclick="sendMessage()">ارسال پیام</button>
        <p id="status"></p>
    </div>

    <script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>
    <script>
    const socket = io();
    const target = {{target|tojson}};

    socket.on("connect", () => {
        socket.emit("join_chat", {target: target});
        document.getElementById("status").textContent = "متصل شدی";
    });

    socket.on("connect_error", () => {
        document.getElementById("status").textContent =
            "ارتباط با سرور برقرار نشد.";
    });

    socket.on("new_message", m => {
        const box = document.getElementById("messages");
        const div = document.createElement("div");
        div.className = "message";

        const name = document.createElement("b");
        name.textContent = m.sender;

        const text = document.createElement("p");
        text.textContent = m.message;

        const time = document.createElement("small");
        time.textContent = m.created_at;

        div.append(name, text, time);
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    });

    function sendMessage() {
        const input = document.getElementById("msg");
        const message = input.value.trim();

        if (!message) return;

        socket.emit("send_message", {
            target: target,
            message: message
        });

        input.value = "";
    }

    document.getElementById("msg").addEventListener("keydown", e => {
        if (e.key === "Enter") sendMessage();
    });
    </script>
    """, username=username, target=target,
         users=users, messages=messages)


# ==================================================
# CHAT SOCKET EVENTS
# ==================================================

@socketio.on("connect")
def socket_connect(auth=None):
    username = session.get("user")

    if not username:
        return False

    online_users[username] = request.sid


@socketio.on("disconnect")
def socket_disconnect(reason=None):
    sid = request.sid

    for username, user_sid in list(online_users.items()):
        if user_sid == sid:
            del online_users[username]


@socketio.on("join_chat")
def join_chat(data):
    username = session.get("user")

    if not username:
        return

    target = str(data.get("target", "TEAM"))

    if target == "TEAM":
        join_room("TEAM")
        return

    con = get_db()
    user = con.execute(
        "SELECT id FROM users WHERE username=?",
        (target,)
    ).fetchone()
    con.close()

    if user and target != username:
        join_room(private_room(username, target))


@socketio.on("send_message")
def send_message(data):
    username = session.get("user")

    if not username:
        return

    target = str(data.get("target", "TEAM"))
    message = str(data.get("message", "")).strip()

    if not message or len(message) > 2000:
        return

    if target != "TEAM":
        con = get_db()
        user = con.execute(
            "SELECT id FROM users WHERE username=?",
            (target,)
        ).fetchone()
        con.close()

        if not user or target == username:
            return

    con = get_db()

    con.execute("""
        INSERT INTO messages(sender,receiver,message)
        VALUES(?,?,?)
    """, (username, target, message))

    con.commit()

    row = con.execute("""
        SELECT * FROM messages ORDER BY id DESC LIMIT 1
    """).fetchone()

    con.close()

    payload = {
        "sender": row["sender"],
        "message": row["message"],
        "created_at": row["created_at"]
    }

    if target == "TEAM":
        socketio.emit("new_message", payload, room="TEAM")
    else:
        socketio.emit(
            "new_message",
            payload,
            room=private_room(username, target)
        )


# ==================================================
# CALL PAGE
# ==================================================

@app.route("/call")
@login_required
def call():
    username = session["user"]

    con = get_db()
    users = con.execute("""
        SELECT username,fullname FROM users
        WHERE username != ?
        ORDER BY username
    """, (username,)).fetchall()
    con.close()

    return page("""
    <div class="card">
        <h2>تماس صوتی و تصویری</h2>

        <select id="target">
            <option value="">انتخاب بازیکن</option>
            {% for u in users %}
            <option value="{{u.username}}">
                {{u.fullname or u.username}}
            </option>
            {% endfor %}
        </select>

        <button onclick="startCall(false)">تماس صوتی</button>
        <button onclick="startCall(true)">تماس تصویری</button>
        <button onclick="endCall()">پایان تماس</button>

        <h3 id="callStatus">آماده تماس</h3>

        <div id="incoming" style="display:none">
            <p id="caller"></p>
            <button onclick="answerCall()">پاسخ</button>
            <button onclick="rejectCall()">رد تماس</button>
        </div>

        <h3>تصویر شما</h3>
        <video id="localVideo" autoplay muted playsinline></video>

        <h3>تصویر طرف مقابل</h3>
        <video id="remoteVideo" autoplay playsinline></video>
    </div>

    <script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>
    <script>
    const socket = io();

    let pc = null;
    let localStream = null;
    let incomingOffer = null;
    let currentPeer = null;
    let pendingCandidates = [];

    const localVideo = document.getElementById("localVideo");
    const remoteVideo = document.getElementById("remoteVideo");
    const callStatus = document.getElementById("callStatus");

    function setStatus(text) {
        callStatus.textContent = text;
    }

    function createPeer() {
        pc = new RTCPeerConnection({
            iceServers: [
                {urls:"stun:stun.l.google.com:19302"}
            ]
        });

        pc.onicecandidate = event => {
            if (event.candidate && currentPeer) {
                socket.emit("call_ice", {
                    target: currentPeer,
                    candidate: event.candidate
                });
            }
        };

        pc.ontrack = event => {
            remoteVideo.srcObject = event.streams[0];
        };

        pc.onconnectionstatechange = () => {
            if (!pc) return;

            if (pc.connectionState === "connected") {
                setStatus("تماس برقرار شد");
            } else if (pc.connectionState === "failed") {
                setStatus("ارتباط ناموفق بود؛ ممکن است TURN لازم باشد.");
            }
        };
    }

    async function getMedia(video) {
        localStream = await navigator.mediaDevices.getUserMedia({
            audio:true,
            video:video
        });

        localVideo.srcObject = localStream;
    }

    async function startCall(video) {
        const target = document.getElementById("target").value;

        if (!target) {
            alert("ابتدا بازیکن را انتخاب کن.");
            return;
        }

        if (!navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia) {
            alert("برای تماس از HTTPS یا localhost استفاده کن.");
            return;
        }

        try {
            currentPeer = target;
            pendingCandidates = [];

            await getMedia(video);
            createPeer();

            localStream.getTracks().forEach(track => {
                pc.addTrack(track, localStream);
            });

            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            socket.emit("call_offer", {
                target:target,
                offer:offer,
                video:video
            });

            setStatus("در انتظار پاسخ...");
        } catch (error) {
            console.error(error);
            setStatus("دسترسی به دوربین یا میکروفون ممکن نشد.");
            cleanupMedia();
        }
    }

    socket.on("incoming_call", data => {
        if (pc || localStream) {
            socket.emit("call_reject", {target:data.from});
            return;
        }

        incomingOffer = data;
        currentPeer = data.from;

        document.getElementById("caller").textContent =
            "تماس از طرف " + data.from;

        document.getElementById("incoming").style.display = "block";
        setStatus("تماس ورودی");
    });

    async function answerCall() {
        if (!incomingOffer) return;

        try {
            await getMedia(!!incomingOffer.video);
            createPeer();

            localStream.getTracks().forEach(track => {
                pc.addTrack(track, localStream);
            });

            await pc.setRemoteDescription(
                new RTCSessionDescription(incomingOffer.offer)
            );

            for (const candidate of pendingCandidates) {
                await pc.addIceCandidate(
                    new RTCIceCandidate(candidate)
                );
            }
            pendingCandidates = [];

            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);

            socket.emit("call_answer", {
                target:currentPeer,
                answer:answer
            });

            document.getElementById("incoming").style.display = "none";
            incomingOffer = null;
            setStatus("در حال برقراری تماس...");
        } catch (error) {
            console.error(error);
            setStatus("پاسخ به تماس ناموفق بود.");
            cleanupMedia();
        }
    }

    function rejectCall() {
        if (currentPeer) {
            socket.emit("call_reject", {target:currentPeer});
        }

        cleanupMedia();
        document.getElementById("incoming").style.display = "none";
        setStatus("تماس رد شد");
    }

    socket.on("call_answer_received", async data => {
        if (!pc) return;

        try {
            await pc.setRemoteDescription(
                new RTCSessionDescription(data.answer)
            );

            for (const candidate of pendingCandidates) {
                await pc.addIceCandidate(
                    new RTCIceCandidate(candidate)
                );
            }
            pendingCandidates = [];
        } catch (error) {
            console.error(error);
        }
    });

    socket.on("call_ice_received", async data => {
        if (!pc || !pc.remoteDescription) {
            pendingCandidates.push(data.candidate);
            return;
        }

        try {
            await pc.addIceCandidate(
                new RTCIceCandidate(data.candidate)
            );
        } catch (error) {
            console.error(error);
        }
    });

    socket.on("call_ended", () => {
        cleanupMedia();
        setStatus("تماس پایان یافت");
    });

    socket.on("call_unavailable", () => {
        cleanupMedia();
        setStatus("کاربر در دسترس نیست.");
    });

    function cleanupMedia() {
        if (pc) {
            pc.close();
            pc = null;
        }

        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }

        localVideo.srcObject = null;
        remoteVideo.srcObject = null;
        incomingOffer = null;
        currentPeer = null;
        pendingCandidates = [];
    }

    function endCall() {
        if (currentPeer) {
            socket.emit("call_end", {target:currentPeer});
        }

        cleanupMedia();
        document.getElementById("incoming").style.display = "none";
        setStatus("تماس پایان یافت");
    }
    </script>
    """, username=username)


# ==================================================
# CALL SIGNALING
# ==================================================

def send_to_user(username, event, data):
    sid = online_users.get(username)

    if sid:
        socketio.emit(event, data, to=sid)
        return True

    return False


@socketio.on("call_offer")
def call_offer(data):
    sender = session.get("user")

    if not sender:
        return

    target = str(data.get("target", ""))

    if not target or target == sender:
        return

    con = get_db()
    exists = con.execute(
        "SELECT id FROM users WHERE username=?",
        (target,)
    ).fetchone()
    con.close()

    if not exists:
        return

    payload = {
        "from":sender,
        "offer":data.get("offer"),
        "video":bool(data.get("video"))
    }

    if not send_to_user(target, "incoming_call", payload):
        emit("call_unavailable")


@socketio.on("call_answer")
def call_answer(data):
    sender = session.get("user")

    if not sender:
        return

    target = str(data.get("target", ""))

    send_to_user(target, "call_answer_received", {
        "from":sender,
        "answer":data.get("answer")
    })


@socketio.on("call_ice")
def call_ice(data):
    sender = session.get("user")

    if not sender:
        return

    target = str(data.get("target", ""))

    send_to_user(target, "call_ice_received", {
        "from":sender,
        "candidate":data.get("candidate")
    })


@socketio.on("call_reject")
def call_reject(data):
    sender = session.get("user")

    if not sender:
        return

    target = str(data.get("target", ""))

    send_to_user(target, "call_ended", {"from":sender})


@socketio.on("call_end")
def call_end(data):
    sender = session.get("user")

    if not sender:
        return

    target = str(data.get("target", ""))

    send_to_user(target, "call_ended", {"from":sender})


# ==================================================
# ERROR HANDLERS
# ==================================================

@app.errorhandler(404)
def not_found(error):
    return page("""
    <div class="card">
        <h2>صفحه پیدا نشد</h2>
        <a class="btn" href="/">بازگشت به خانه</a>
    </div>
    """), 404


@app.errorhandler(413)
def too_large(error):
    return page("""
    <div class="card">
        <h2>حجم فایل زیاد است</h2>
        <p>حداکثر حجم فایل ۵ مگابایت است.</p>
    </div>
    """), 413


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    print("================================")
    print("TABARIYAN LEGENDS")
    print("http://127.0.0.1:5000")
    print("================================")

    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
