
import os
import sqlite3
from functools import wraps

from flask import (
    Flask, request, redirect, url_for,
    session, flash, render_template_string, g
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# ---------------- APP SETTINGS ----------------

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY", "tabariyan-local-secret-key"
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "tabariyan.db")

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME", "mehrsam_admin"
)

# ---------------- ADMIN BLUEPRINT ----------------

from admin import admin_bp
app.register_blueprint(admin_bp)


# ---------------- DATABASE ----------------

def db():
    if "database" not in g:
        g.database = sqlite3.connect(DATABASE)
        g.database.row_factory = sqlite3.Row
    return g.database


@app.teardown_appcontext
def close_db(error=None):
    database = g.pop("database", None)
    if database is not None:
        database.close()


def init_db():
    con = sqlite3.connect(DATABASE)

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            matches INTEGER DEFAULT 0,
            goals INTEGER DEFAULT 0,
            assists INTEGER DEFAULT 0,
            clean_sheets INTEGER DEFAULT 0,
            yellow_cards INTEGER DEFAULT 0,
            red_cards INTEGER DEFAULT 0,
            rating REAL DEFAULT 0,
            role TEXT DEFAULT 'player'
        )
    """)

    columns = [
        row[1] for row in con.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    ]

    if "role" not in columns:
        con.execute("""
            ALTER TABLE users
            ADD COLUMN role TEXT DEFAULT 'player'
        """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opponent TEXT NOT NULL,
            score TEXT NOT NULL,
            result TEXT NOT NULL,
            match_date TEXT
        )
    """)

    admin_password = os.environ.get("ADMIN_PASSWORD")

    admin = con.execute(
        "SELECT id FROM users WHERE username=?",
        (ADMIN_USERNAME,)
    ).fetchone()

    if admin:
        con.execute(
            "UPDATE users SET role='admin' WHERE username=?",
            (ADMIN_USERNAME,)
        )

        if admin_password:
            con.execute(
                "UPDATE users SET password=? WHERE username=?",
                (
                    generate_password_hash(admin_password),
                    ADMIN_USERNAME
                )
            )

    elif admin_password:
        con.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, 'admin')
        """, (
            ADMIN_USERNAME,
            generate_password_hash(admin_password)
        ))

    con.commit()
    con.close()


init_db()


# ---------------- LOGIN REQUIRED ----------------

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("ابتدا وارد حساب خود شوید.")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


# ---------------- DESIGN ----------------

BASE_STYLE = """
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    background: #071426;
    color: white;
    font-family: Tahoma, Arial, sans-serif;
    direction: rtl;
}

header {
    background: #102b4c;
    padding: 22px;
    text-align: center;
    border-bottom: 4px solid #e63946;
}

header h1 {
    margin: 0;
    color: white;
    font-size: 29px;
}

header p { color: #b9d8ff; }

nav {
    background: #0b1e35;
    padding: 15px;
    text-align: center;
}

nav a {
    color: white;
    text-decoration: none;
    margin: 8px;
    font-size: 14px;
}

nav a:hover { color: #ff4757; }

.container {
    width: 92%;
    max-width: 1000px;
    margin: 30px auto;
}

.card {
    background: #102b4c;
    border: 1px solid #24466c;
    border-radius: 13px;
    padding: 22px;
    margin-bottom: 20px;
}

h2 { color: #ff4757; }

input, button {
    width: 100%;
    padding: 13px;
    margin: 9px 0;
    border-radius: 8px;
    border: none;
    font-family: Tahoma;
}

input {
    background: #eaf2ff;
    color: #111;
}

button {
    background: #e63946;
    color: white;
    font-size: 16px;
    cursor: pointer;
}

button:hover { background: #b91c2a; }

a.btn {
    display: inline-block;
    background: #e63946;
    color: white;
    padding: 12px 20px;
    text-decoration: none;
    border-radius: 8px;
    margin: 5px;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 12px;
}

.stat {
    background: #071426;
    padding: 17px;
    border-radius: 10px;
    text-align: center;
}

.stat strong {
    display: block;
    font-size: 24px;
    color: #ff4757;
    margin-top: 8px;
}

.player {
    background: #071426;
    border-right: 4px solid #e63946;
    padding: 15px;
    margin: 12px 0;
    border-radius: 8px;
}

.message {
    background: #24466c;
    padding: 12px;
    border-radius: 8px;
    margin: 10px 0;
}

footer {
    text-align: center;
    padding: 25px;
    color: #9bb5d1;
}

@media(max-width:600px) {
    header h1 { font-size: 21px; }
    nav a { display: inline-block; }
}
</style>
"""


# ---------------- PAGE FUNCTION ----------------

def page(title, content):
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">
        <title>{{ title }} | TABARIYAN LEGENDS</title>
        """ + BASE_STYLE + """
    </head>
    <body>

    <header>
        <h1>💙 TABARIYAN LEGENDS ❤️</h1>
        <p>OFFICIAL FOOTBALL TEAM WEBSITE</p>
    </header>

    <nav>
        <a href="{{ url_for('home') }}">خانه</a>
        <a href="{{ url_for('players') }}">بازیکنان</a>
        <a href="{{ url_for('matches') }}">مسابقات</a>

        {% if session.get('user_id') %}
            <a href="{{ url_for('dashboard') }}">حساب من</a>

            {% if session.get('role') == 'admin' %}
                <a href="{{ url_for('admin_panel.dashboard') }}">
                    مدیریت
                </a>
            {% endif %}

            <a href="{{ url_for('logout') }}">خروج</a>
        {% else %}
            <a href="{{ url_for('login') }}">ورود</a>
            <a href="{{ url_for('register') }}">ثبت نام</a>
        {% endif %}
    </nav>

    <div class="container">

        {% with messages = get_flashed_messages() %}
            {% for message in messages %}
                <div class="message">{{ message }}</div>
            {% endfor %}
        {% endwith %}

        """ + content + """

    </div>

    <footer>
        TABARIYAN LEGENDS © 2026
        <br>
        OFFICIAL WEBSITE
    </footer>

    </body>
    </html>
    """, title=title)


# ---------------- HOME ----------------

@app.route("/")
def home():
    con = db()

    players = con.execute(
        "SELECT * FROM users WHERE role='player' ORDER BY goals DESC"
    ).fetchall()

    matches = con.execute(
        "SELECT * FROM matches ORDER BY id DESC LIMIT 3"
    ).fetchall()

    content = """
    <div class="card">
        <h2>به وب سایت رسمی تیم خوش آمدید</h2>
        <h3>💙 TABARIYAN LEGENDS ❤️</h3>

        <p>
            خانه رسمی تیم فوتبال طبریان لجندز.
            اخبار، بازیکنان، آمار و مسابقات تیم را دنبال کنید.
        </p>

        <a class="btn" href="{{ url_for('players') }}">
            مشاهده بازیکنان
        </a>

        <a class="btn" href="{{ url_for('matches') }}">
            مسابقات
        </a>
    </div>

    <div class="card">
        <h2>آمار تیم</h2>
        <div class="stat-grid">
            <div class="stat">
                تعداد بازیکنان
                <strong>{{ players|length }}</strong>
            </div>
            <div class="stat">
                تعداد مسابقات
                <strong>{{ matches|length }}</strong>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>بازیکنان برتر</h2>

        {% for p in players[:5] %}
        <div class="player">
            <b>{{ p.username }}</b>
            <p>گل: {{ p.goals }} | پاس گل: {{ p.assists }}</p>
            <a href="{{ url_for('player_profile', user_id=p.id) }}">
                مشاهده پروفایل
            </a>
        </div>
        {% else %}
        <p>هنوز بازیکنی ثبت نشده است.</p>
        {% endfor %}
    </div>

    <div class="card">
        <h2>آخرین مسابقات</h2>

        {% for m in matches %}
        <div class="player">
            مقابل: {{ m.opponent }}
            <h3>{{ m.score }}</h3>
            نتیجه: {{ m.result }}
        </div>
        {% else %}
        <p>هنوز مسابقه ای ثبت نشده است.</p>
        {% endfor %}
    </div>
    """

    return page(
        "خانه",
        render_template_string(
            content,
            players=players,
            matches=matches
        )
    )


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash("نام کاربری باید حداقل ۳ حرف باشد.")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("رمز عبور باید حداقل ۶ کاراکتر باشد.")
            return redirect(url_for("register"))

        try:
            db().execute("""
                INSERT INTO users (username, phone, password)
                VALUES (?, ?, ?)
            """, (
                username,
                phone,
                generate_password_hash(password)
            ))
            db().commit()

            flash("ثبت نام با موفقیت انجام شد.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("این نام کاربری قبلاً ثبت شده است.")
            return redirect(url_for("register"))

    content = """
    <div class="card">
        <h2>ثبت نام</h2>
        <form method="POST">
            <input name="username" placeholder="نام کاربری" required>
            <input name="phone" placeholder="شماره تماس" type="tel">
            <input name="password" placeholder="رمز عبور"
                   type="password" required>
            <button type="submit">ایجاد حساب</button>
        </form>
        <p>قبلاً ثبت نام کرده ای؟
        <a href="{{ url_for('login') }}">ورود</a></p>
    </div>
    """
    return page("ثبت نام", content)


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db().execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            flash("با موفقیت وارد شدی.")

            if user["role"] == "admin":
                return redirect(url_for("admin_panel.dashboard"))

            return redirect(url_for("dashboard"))

        flash("نام کاربری یا رمز عبور اشتباه است.")
        return redirect(url_for("login"))

    content = """
    <div class="card">
        <h2>ورود به حساب</h2>
        <form method="POST">
            <input name="username" placeholder="نام کاربری" required>
            <input name="password" type="password"
                   placeholder="رمز عبور" required>
            <button type="submit">ورود</button>
        </form>
        <p>حساب نداری؟
        <a href="{{ url_for('register') }}">ثبت نام</a></p>
    </div>
    """
    return page("ورود", content)


# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("از حساب خارج شدی.")
    return redirect(url_for("home"))


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    user = db().execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    content = """
    <div class="card">
        <h2>حساب کاربری</h2>
        <h3>خوش آمدی {{ user.username }}</h3>

        <div class="stat-grid">
            {% for label, value in [
                ('بازی', user.matches),
                ('گل', user.goals),
                ('پاس گل', user.assists),
                ('کلین شیت', user.clean_sheets),
                ('کارت زرد', user.yellow_cards),
                ('کارت قرمز', user.red_cards),
                ('امتیاز', user.rating)
            ] %}
            <div class="stat">
                {{ label }}
                <strong>{{ value }}</strong>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return page(
        "حساب من",
        render_template_string(content, user=user)
    )


# ---------------- PLAYERS ----------------

@app.route("/players")
def players():
    players_list = db().execute(
        "SELECT * FROM users WHERE role='player' ORDER BY goals DESC"
    ).fetchall()

    content = """
    <div class="card">
        <h2>بازیکنان تیم</h2>

        {% for p in players %}
        <div class="player">
            <h3>{{ p.username }}</h3>
            گل: {{ p.goals }} | پاس گل: {{ p.assists }}
            <br><br>
            <a href="{{ url_for('player_profile', user_id=p.id) }}">
                مشاهده پروفایل
            </a>
        </div>
        {% else %}
        <p>بازیکنی ثبت نشده است.</p>
        {% endfor %}
    </div>
    """
    return page(
        "بازیکنان",
        render_template_string(content, players=players_list)
    )


# ---------------- PLAYER PROFILE ----------------

@app.route("/player/<int:user_id>")
def player_profile(user_id):
    player = db().execute(
        "SELECT * FROM users WHERE id=? AND role='player'",
        (user_id,)
    ).fetchone()

    if player is None:
        return page(
            "یافت نشد",
            "<div class='card'><h2>بازیکن پیدا نشد.</h2></div>"
        ), 404

    content = """
    <div class="card">
        <h2>پروفایل بازیکن</h2>
        <h1>{{ player.username }}</h1>

        <div class="stat-grid">
            <div class="stat">بازی<strong>{{ player.matches }}</strong></div>
            <div class="stat">گل<strong>{{ player.goals }}</strong></div>
            <div class="stat">پاس گل<strong>{{ player.assists }}</strong></div>
            <div class="stat">کلین شیت<strong>{{ player.clean_sheets }}</strong></div>
            <div class="stat">امتیاز<strong>{{ player.rating }}</strong></div>
        </div>
    </div>
    """
    return page(
        "پروفایل",
        render_template_string(content, player=player)
    )


# ---------------- MATCHES ----------------

@app.route("/matches")
def matches():
    matches_list = db().execute(
        "SELECT * FROM matches ORDER BY id DESC"
    ).fetchall()

    content = """
    <div class="card">
        <h2>مسابقات تیم</h2>

        {% for m in matches %}
        <div class="player">
            <h3>TABARIYAN LEGENDS VS {{ m.opponent }}</h3>
            <h2>{{ m.score }}</h2>
            نتیجه: {{ m.result }}
            <p>تاریخ: {{ m.match_date or 'ثبت نشده' }}</p>
        </div>
        {% else %}
        <p>هنوز مسابقه ای ثبت نشده است.</p>
        {% endfor %}
    </div>
    """
    return page(
        "مسابقات",
        render_template_string(content, matches=matches_list)
    )


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )