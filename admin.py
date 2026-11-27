from flask import Blueprint, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import os
from functools import wraps

admin = Blueprint("admin", __name__, url_prefix="/admin")

DB_NAME = "tabariyan_admin.db"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CHANGE_THIS_PASSWORD")


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_admin_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opponent TEXT NOT NULL,
            match_date TEXT,
            match_time TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # دیتابیس مدیریت گل بازیکنان
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            goals INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_admin_db()


# =========================
# LOGIN
# =========================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.admin_login"))
        return f(*args, **kwargs)
    return decorated


# =========================
# STYLE
# =========================

STYLE = """
<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #101827;
    color: #fff;
}

header {
    background: linear-gradient(120deg,#123b83,#9b1732);
    padding: 25px;
    text-align: center;
}

header h1 {
    margin: 0;
}

nav {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    padding: 15px;
}

nav a {
    color: white;
    text-decoration: none;
    background: #26364c;
    padding: 12px 18px;
    border-radius: 10px;
}

nav a:hover {
    background: #405675;
}

.container {
    max-width: 1000px;
    margin: auto;
    padding: 20px;
}

.card {
    background: #1b2738;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
}

input, textarea {
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    border: 1px solid #475569;
    border-radius: 8px;
    background: #0f172a;
    color: white;
}

button {
    background: #e32645;
    color: white;
    border: 0;
    border-radius: 8px;
    padding: 12px 20px;
    cursor: pointer;
    margin: 4px;
}

button:hover {
    background: #b91c38;
}

.item {
    background: #253449;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}

.small {
    color: #aab8cc;
}

a.delete {
    color: #ff667e;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit,minmax(180px,1fr));
    gap: 15px;
}

.stat {
    font-size: 26px;
    font-weight: bold;
    color: #ff536f;
}

.goal-number {
    font-size: 32px;
    color: #ff536f;
    font-weight: bold;
    text-align: center;
    padding: 10px;
}

.actions {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    justify-content: center;
}

.green {
    background: #16803c;
}

.blue {
    background: #2563eb;
}

.gray {
    background: #475569;
}

.player-title {
    text-align: center;
    font-size: 20px;
}

@media(max-width:600px) {
    .container {
        padding: 10px;
    }

    nav a {
        padding: 10px;
        font-size: 14px;
    }
}
</style>
"""


# =========================
# NAVIGATION
# =========================

NAV_HTML = """
<nav>
    <a href="{{ url_for('admin.dashboard') }}">داشبورد</a>
    <a href="{{ url_for('admin.news_page') }}">اخبار</a>
    <a href="{{ url_for('admin.matches_page') }}">مسابقات</a>
    <a href="{{ url_for('admin.messages_page') }}">پیام‌ها</a>
    <a href="{{ url_for('admin.goals_page') }}">⚽ مدیریت گل‌ها</a>
    <a href="{{ url_for('admin.admin_logout') }}">خروج</a>
</nav>
"""


# =========================
# LOGIN PAGE
# =========================

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ورود مدیریت</title>
""" + STYLE + """
</head>
<body>

<header>
    <h1>💙 TABARIYAN CITY ❤️</h1>
    <p>ورود به پنل مدیریت</p>
</header>

<div class="container">
    <div class="card">
        <h2>ورود مدیر</h2>

        <form method="POST">
            <input name="password"
                   type="password"
                   placeholder="رمز مدیریت"
                   required>

            <button type="submit">ورود به پنل</button>
        </form>

        <p style="color:#ff667e">{{ error }}</p>
    </div>
</div>

</body>
</html>
"""


# =========================
# DASHBOARD
# =========================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>پنل مدیریت TABARIYAN CITY</title>
""" + STYLE + """
</head>
<body>

<header>
    <h1>💙 TABARIYAN CITY ❤️</h1>
    <p>پنل مدیریت سایت</p>
</header>

""" + NAV_HTML + """

<div class="container">

    <div class="grid">

        <div class="card">
            <h3>اخبار</h3>
            <div class="stat">{{ news_count }}</div>
        </div>

        <div class="card">
            <h3>مسابقات</h3>
            <div class="stat">{{ match_count }}</div>
        </div>

        <div class="card">
            <h3>پیام‌ها</h3>
            <div class="stat">{{ message_count }}</div>
        </div>

        <div class="card">
            <h3>بازیکنان گلزن</h3>
            <div class="stat">{{ goals_count }}</div>
        </div>

    </div>

    <div class="card">
        <h2>خوش آمدی مدیر 👋</h2>

        <p>
            از این پنل می‌تونی اخبار، مسابقات، پیام‌ها
            و تعداد گل بازیکنان رو مدیریت کنی.
        </p>

        <p class="small">
            TABARIYAN CITY | مدیریت سایت
        </p>
    </div>

</div>

</body>
</html>
"""


# =========================
# NEWS PAGE
# =========================

NEWS_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>مدیریت اخبار</title>
""" + STYLE + """
</head>
<body>

<header>
    <h1>مدیریت اخبار</h1>
</header>

""" + NAV_HTML + """

<div class="container">

    <div class="card">
        <h2>افزودن خبر جدید</h2>

        <form method="POST">
            <input name="title"
                   placeholder="عنوان خبر"
                   required>

            <textarea name="content"
                      rows="5"
                      placeholder="متن خبر..."
                      required></textarea>

            <button type="submit">ثبت خبر</button>
        </form>
    </div>

    <div class="card">
        <h2>خبرهای ثبت شده</h2>

        {% for n in news %}
        <div class="item">

            <h3>{{ n.title }}</h3>

            <p>{{ n.content }}</p>

            <p class="small">{{ n.created_at }}</p>

            <a class="delete"
               href="{{ url_for('admin.delete_news', news_id=n.id) }}">
               حذف خبر
            </a>

        </div>
        {% else %}
        <p>هنوز خبری ثبت نشده.</p>
        {% endfor %}

    </div>

</div>

</body>
</html>
"""


# =========================
# MATCHES PAGE
# =========================

MATCHES_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>مدیریت مسابقات</title>
""" + STYLE + """
</head>
<body>

<header>
    <h1>مدیریت مسابقات</h1>
</header>

""" + NAV_HTML + """

<div class="container">

    <div class="card">
        <h2>ثبت مسابقه</h2>

        <form method="POST">

            <input name="opponent"
                   placeholder="نام تیم مقابل"
                   required>

            <input name="match_date"
                   placeholder="تاریخ مسابقه">

            <input name="match_time"
                   placeholder="ساعت مسابقه">

            <input name="location"
                   placeholder="محل مسابقه">

            <button type="submit">ثبت مسابقه</button>

        </form>
    </div>

    <div class="card">
        <h2>مسابقات ثبت‌شده</h2>

        {% for m in matches %}
        <div class="item">

            <h3>TABARIYAN CITY VS {{ m.opponent }}</h3>

            <p>📅 {{ m.match_date }} | ⏰ {{ m.match_time }}</p>

            <p>📍 {{ m.location }}</p>

            <a class="delete"
               href="{{ url_for('admin.delete_match', match_id=m.id) }}">
               حذف مسابقه
            </a>

        </div>
        {% else %}
        <p>مسابقه‌ای ثبت نشده.</p>
        {% endfor %}

    </div>

</div>

</body>
</html>
"""


# =========================
# MESSAGES PAGE
# =========================

MESSAGES_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>پیام‌های مدیر</title>
""" + STYLE + """
</head>
<body>

<header>
    <h1>پیام‌های دریافتی</h1>
</header>

""" + NAV_HTML + """

<div class="container">

    <div class="card">
        <h2>پیام‌ها</h2>

        {% for m in messages %}
        <div class="item">

            <strong>{{ m.sender or 'ناشناس' }}</strong>

            <p>{{ m.message }}</p>

            <p class="small">{{ m.created_at }}</p>

            <a class="delete"
               href="{{ url_for('admin.delete_message', message_id=m.id) }}">
               حذف پیام
            </a>

        </div>
        {% else %}
        <p>پیامی موجود نیست.</p>
        {% endfor %}

    </div>

</div>

</body>
</html>
"""


# =========================
# GOALS MANAGEMENT PAGE
# =========================

GOALS_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>مدیریت گل بازیکنان</title>
""" + STYLE + """
</head>
<body>

<header>
    <h1>⚽ مدیریت گل بازیکنان</h1>
    <p>TABARIYAN CITY</p>
</header>

""" + NAV_HTML + """

<div class="container">

    <div class="card">
        <h2>➕ اضافه کردن بازیکن</h2>

        <form method="POST">

            <input type="hidden"
                   name="action"
                   value="add_player">

            <input name="player_name"
                   placeholder="نام بازیکن"
                   required>

            <input type="number"
                   name="goals"
                   placeholder="تعداد گل اولیه"
                   min="0"
                   value="0">

            <button type="submit">ثبت بازیکن</button>

        </form>
    </div>


    <div class="card">
        <h2>🏆 جدول گلزنان</h2>

        {% for p in players %}

        <div class="item">

            <h3 class="player-title">
                {{ p.player_name }}
            </h3>

            <div class="goal-number">
                ⚽ {{ p.goals }} گل
            </div>


            <!-- افزایش گل -->

            <div class="actions">

                <form method="POST">
                    <input type="hidden"
                           name="action"
                           value="change_goals">

                    <input type="hidden"
                           name="player_id"
                           value="{{ p.id }}">

                    <input type="hidden"
                           name="change"
                           value="1">

                    <button class="green">
                        ➕ یک گل
                    </button>
                </form>


                <!-- کاهش گل -->

                <form method="POST">
                    <input type="hidden"
                           name="action"
                           value="change_goals">

                    <input type="hidden"
                           name="player_id"
                           value="{{ p.id }}">

                    <input type="hidden"
                           name="change"
                           value="-1">

                    <button class="gray">
                        ➖ یک گل
                    </button>
                </form>

            </div>


            <!-- ثبت تعداد دلخواه -->

            <form method="POST">

                <input type="hidden"
                       name="action"
                       value="set_goals">

                <input type="hidden"
                       name="player_id"
                       value="{{ p.id }}">

                <label>تعداد گل دلخواه:</label>

                <input type="number"
                       name="goals"
                       min="0"
                       value="{{ p.goals }}"
                       required>

                <button class="blue">
                    💾 ذخیره تعداد گل
                </button>

            </form>


            <!-- تغییر نام بازیکن -->

            <form method="POST">

                <input type="hidden"
                       name="action"
                       value="rename_player">

                <input type="hidden"
                       name="player_id"
                       value="{{ p.id }}">

                <input name="player_name"
                       value="{{ p.player_name }}"
                       required>

                <button class="gray">
                    تغییر نام
                </button>

            </form>


            <!-- حذف بازیکن -->

            <form method="POST"
                  onsubmit="return confirm('بازیکن حذف شود؟');">

                <input type="hidden"
                       name="action"
                       value="delete_player">

                <input type="hidden"
                       name="player_id"
                       value="{{ p.id }}">

                <button>
                    🗑 حذف بازیکن
                </button>

            </form>

        </div>

        {% else %}

        <p>
            هنوز بازیکنی اضافه نشده.
            از فرم بالا بازیکن‌ها رو اضافه کن.
        </p>

        {% endfor %}

    </div>

</div>

</body>
</html>
"""


# =========================
# DASHBOARD ROUTE
# =========================

@admin.route("/", methods=["GET"])
@login_required
def dashboard():

    conn = get_db()

    news_count = conn.execute(
        "SELECT COUNT(*) FROM admin_news"
    ).fetchone()[0]

    match_count = conn.execute(
        "SELECT COUNT(*) FROM admin_matches"
    ).fetchone()[0]

    message_count = conn.execute(
        "SELECT COUNT(*) FROM admin_messages"
    ).fetchone()[0]

    goals_count = conn.execute(
        "SELECT COUNT(*) FROM admin_goals"
    ).fetchone()[0]

    conn.close()

    return render_template_string(
        DASHBOARD_HTML,
        news_count=news_count,
        match_count=match_count,
        message_count=message_count,
        goals_count=goals_count
    )


# =========================
# LOGIN ROUTE
# =========================

@admin.route("/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        password = request.form.get("password", "")

        if password == ADMIN_PASSWORD:

            session.clear()
            session["admin_logged_in"] = True

            return redirect(url_for("admin.dashboard"))

        return render_template_string(
            LOGIN_HTML,
            error="رمز اشتباه است!"
        )

    return render_template_string(
        LOGIN_HTML,
        error=""
    )


# =========================
# LOGOUT
# =========================

@admin.route("/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin.admin_login"))


# =========================
# NEWS ROUTE
# =========================

@admin.route("/news", methods=["GET", "POST"])
@login_required
def news_page():

    conn = get_db()

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if title and content:

            conn.execute(
                "INSERT INTO admin_news (title, content) VALUES (?, ?)",
                (title, content)
            )

            conn.commit()

    news = conn.execute(
        "SELECT * FROM admin_news ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template_string(
        NEWS_HTML,
        news=news
    )


# =========================
# MATCHES ROUTE
# =========================

@admin.route("/matches", methods=["GET", "POST"])
@login_required
def matches_page():

    conn = get_db()

    if request.method == "POST":

        opponent = request.form.get("opponent", "").strip()
        match_date = request.form.get("match_date", "").strip()
        match_time = request.form.get("match_time", "").strip()
        location = request.form.get("location", "").strip()

        if opponent:

            conn.execute("""
                INSERT INTO admin_matches
                (opponent, match_date, match_time, location)
                VALUES (?, ?, ?, ?)
            """, (
                opponent,
                match_date,
                match_time,
                location
            ))

            conn.commit()

    matches = conn.execute(
        "SELECT * FROM admin_matches ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template_string(
        MATCHES_HTML,
        matches=matches
    )


# =========================
# MESSAGES ROUTE
# =========================

@admin.route("/messages")
@login_required
def messages_page():

    conn = get_db()

    messages = conn.execute(
        "SELECT * FROM admin_messages ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template_string(
        MESSAGES_HTML,
        messages=messages
    )


# =========================
# GOALS ROUTE
# =========================

@admin.route("/goals", methods=["GET", "POST"])
@login_required
def goals_page():

    conn = get_db()

    if request.method == "POST":

        action = request.form.get("action", "")


        # اضافه کردن بازیکن

        if action == "add_player":

            player_name = request.form.get(
                "player_name", ""
            ).strip()

            try:
                goals = max(
                    0,
                    int(request.form.get("goals", 0))
                )
            except (ValueError, TypeError):
                goals = 0

            if player_name:

                conn.execute("""
                    INSERT INTO admin_goals
                    (player_name, goals)
                    VALUES (?, ?)
                """, (player_name, goals))

                conn.commit()


        # افزایش یا کاهش گل

        elif action == "change_goals":

            try:
                player_id = int(
                    request.form.get("player_id", 0)
                )

                change = int(
                    request.form.get("change", 0)
                )

                # محدود کردن تغییر به +1 یا -1
                if change in (-1, 1):

                    conn.execute("""
                        UPDATE admin_goals
                        SET goals = MAX(0, goals + ?)
                        WHERE id = ?
                    """, (change, player_id))

                    conn.commit()

            except (ValueError, TypeError):
                pass


        # ثبت تعداد گل دلخواه

        elif action == "set_goals":

            try:

                player_id = int(
                    request.form.get("player_id", 0)
                )

                goals = max(
                    0,
                    int(request.form.get("goals", 0))
                )

                conn.execute("""
                    UPDATE admin_goals
                    SET goals = ?
                    WHERE id = ?
                """, (goals, player_id))

                conn.commit()

            except (ValueError, TypeError):
                pass


        # تغییر نام بازیکن

        elif action == "rename_player":

            player_id = request.form.get(
                "player_id", ""
            )

            player_name = request.form.get(
                "player_name", ""
            ).strip()

            if player_name:

                conn.execute("""
                    UPDATE admin_goals
                    SET player_name = ?
                    WHERE id = ?
                """, (player_name, player_id))

                conn.commit()


        # حذف بازیکن

        elif action == "delete_player":

            try:

                player_id = int(
                    request.form.get("player_id", 0)
                )

                conn.execute("""
                    DELETE FROM admin_goals
                    WHERE id = ?
                """, (player_id,))

                conn.commit()

            except (ValueError, TypeError):
                pass


    # نمایش جدول گلزنان

    players = conn.execute("""
        SELECT *
        FROM admin_goals
        ORDER BY goals DESC, player_name ASC
    """).fetchall()

    conn.close()

    return render_template_string(
        GOALS_HTML,
        players=players
    )


# =========================
# DELETE NEWS
# =========================

@admin.route("/delete-news/<int:news_id>")
@login_required
def delete_news(news_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM admin_news WHERE id=?",
        (news_id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("admin.news_page")
    )


# =========================
# DELETE MATCH
# =========================

@admin.route("/delete-match/<int:match_id>")
@login_required
def delete_match(match_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM admin_matches WHERE id=?",
        (match_id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("admin.matches_page")
    )


# =========================
# DELETE MESSAGE
# =========================

@admin.route("/delete-message/<int:message_id>")
@login_required
def delete_message(message_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM admin_messages WHERE id=?",
        (message_id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("admin.messages_page")
    )
