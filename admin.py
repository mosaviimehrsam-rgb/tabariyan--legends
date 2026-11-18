
import os
import sqlite3
from functools import wraps

from flask import (
    Blueprint, render_template_string, request,
    redirect, url_for, session, flash, abort
)

# ---------------- SETTINGS ----------------

admin_bp = Blueprint(
    "admin_panel",
    __name__,
    url_prefix="/admin"
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "tabariyan.db")


# ---------------- DATABASE ----------------

def get_db():
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con


# ---------------- ADMIN CHECK ----------------

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("ابتدا وارد حساب خود شوید.")
            return redirect(url_for("login"))

        con = get_db()

        user = con.execute(
            "SELECT role FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()

        con.close()

        if user is None or user["role"] != "admin":
            abort(403)

        return func(*args, **kwargs)

    return wrapper


# ---------------- ADMIN DESIGN ----------------

STYLE = """
<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #071426;
    color: white;
    font-family: Tahoma, Arial, sans-serif;
    direction: rtl;
}

header {
    background: #102b4c;
    padding: 25px;
    text-align: center;
    border-bottom: 4px solid #e63946;
}

header h1 {
    margin: 0;
    color: white;
}

nav {
    background: #0b1e35;
    padding: 16px;
    text-align: center;
}

nav a {
    color: white;
    text-decoration: none;
    margin: 10px;
}

nav a:hover {
    color: #ff4757;
}

.container {
    width: 94%;
    max-width: 1100px;
    margin: 30px auto;
}

.card {
    background: #102b4c;
    border: 1px solid #24466c;
    border-radius: 13px;
    padding: 22px;
    margin-bottom: 20px;
}

h2 {
    color: #ff4757;
}

input, select {
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    border: none;
    border-radius: 7px;
    font-family: Tahoma;
}

button, .btn {
    display: inline-block;
    background: #e63946;
    color: white;
    border: none;
    padding: 11px 17px;
    border-radius: 7px;
    cursor: pointer;
    text-decoration: none;
    font-family: Tahoma;
    margin: 5px 0;
}

button:hover, .btn:hover {
    background: #b91c2a;
}

.player {
    background: #071426;
    padding: 16px;
    border-right: 4px solid #e63946;
    border-radius: 8px;
    margin: 12px 0;
}

.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
}

.stat {
    background: #071426;
    padding: 20px;
    text-align: center;
    border-radius: 9px;
}

.stat strong {
    display: block;
    color: #ff4757;
    font-size: 25px;
    margin-top: 10px;
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
    nav a {
        display: inline-block;
        margin: 7px;
    }
}
</style>
"""


# ---------------- PAGE ----------------

def admin_page(title, content):

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">
        <title>{{ title }} | مدیریت</title>
        """ + STYLE + """
    </head>

    <body>

    <header>
        <h1>💙 TABARIYAN LEGENDS ❤️</h1>
        <p>ADMIN CONTROL PANEL</p>
    </header>

    <nav>
        <a href="{{ url_for('admin_panel.dashboard') }}">داشبورد</a>
        <a href="{{ url_for('admin_panel.players_admin') }}">بازیکنان</a>
        <a href="{{ url_for('admin_panel.add_match') }}">ثبت مسابقه</a>
        <a href="{{ url_for('home') }}">سایت اصلی</a>
        <a href="{{ url_for('logout') }}">خروج</a>
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
        TABARIYAN LEGENDS ADMIN PANEL
    </footer>

    </body>
    </html>
    """, title=title)


# ---------------- DASHBOARD ----------------

@admin_bp.route("/")
@admin_required
def dashboard():

    con = get_db()

    players = con.execute(
        "SELECT * FROM users WHERE role='player' ORDER BY goals DESC"
    ).fetchall()

    matches = con.execute(
        "SELECT * FROM matches ORDER BY id DESC"
    ).fetchall()

    player_count = con.execute(
        "SELECT COUNT(*) FROM users WHERE role='player'"
    ).fetchone()[0]

    match_count = con.execute(
        "SELECT COUNT(*) FROM matches"
    ).fetchone()[0]

    con.close()

    content = """
    <div class="card">
        <h2>داشبورد مدیریت</h2>
        <h3>خوش آمدی {{ username }}</h3>

        <div class="stats">

            <div class="stat">
                تعداد بازیکنان
                <strong>{{ player_count }}</strong>
            </div>

            <div class="stat">
                تعداد مسابقات
                <strong>{{ match_count }}</strong>
            </div>

        </div>
    </div>

    <div class="card">
        <h2>دسترسی سریع</h2>

        <a class="btn"
           href="{{ url_for('admin_panel.players_admin') }}">
            مدیریت بازیکنان
        </a>

        <a class="btn"
           href="{{ url_for('admin_panel.add_match') }}">
            ثبت مسابقه جدید
        </a>
    </div>

    <div class="card">
        <h2>آخرین بازیکنان</h2>

        {% for p in players[:5] %}
        <div class="player">
            <h3>{{ p.username }}</h3>
            گل: {{ p.goals }} |
            پاس گل: {{ p.assists }}

            <br><br>

            <a class="btn"
               href="{{ url_for('admin_panel.edit_player', player_id=p.id) }}">
                ویرایش بازیکن
            </a>
        </div>
        {% else %}
        <p>هنوز بازیکنی ثبت نشده است.</p>
        {% endfor %}
    </div>

    <div class="card">
        <h2>آخرین مسابقات</h2>

        {% for m in matches[:5] %}
        <div class="player">
            مقابل {{ m.opponent }}
            <h3>{{ m.score }}</h3>
            نتیجه: {{ m.result }}
        </div>
        {% else %}
        <p>مسابقه ای ثبت نشده است.</p>
        {% endfor %}
    </div>
    """

    return admin_page(
        "داشبورد",
        render_template_string(
            content,
            username=session.get("username"),
            players=players,
            matches=matches,
            player_count=player_count,
            match_count=match_count
        )
    )


# ---------------- PLAYERS ----------------

@admin_bp.route("/players")
@admin_required
def players_admin():

    con = get_db()

    players = con.execute(
        "SELECT * FROM users WHERE role='player' ORDER BY username"
    ).fetchall()

    con.close()

    content = """
    <div class="card">
        <h2>مدیریت بازیکنان</h2>

        {% for p in players %}

        <div class="player">

            <h3>{{ p.username }}</h3>

            بازی: {{ p.matches }} |
            گل: {{ p.goals }} |
            پاس گل: {{ p.assists }}

            <br><br>

            <a class="btn"
               href="{{ url_for('admin_panel.edit_player', player_id=p.id) }}">
                ویرایش آمار
            </a>

        </div>

        {% else %}

        <p>بازیکنی وجود ندارد.</p>

        {% endfor %}
    </div>
    """

    return admin_page(
        "بازیکنان",
        render_template_string(content, players=players)
    )


# ---------------- EDIT PLAYER ----------------

@admin_bp.route("/player/<int:player_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_player(player_id):

    con = get_db()

    player = con.execute(
        "SELECT * FROM users WHERE id=? AND role='player'",
        (player_id,)
    ).fetchone()

    if player is None:
        con.close()
        flash("بازیکن پیدا نشد.")
        return redirect(url_for("admin_panel.players_admin"))

    if request.method == "POST":

        try:
            matches = int(request.form.get("matches", 0))
            goals = int(request.form.get("goals", 0))
            assists = int(request.form.get("assists", 0))
            clean_sheets = int(request.form.get("clean_sheets", 0))
            yellow_cards = int(request.form.get("yellow_cards", 0))
            red_cards = int(request.form.get("red_cards", 0))
            rating = float(request.form.get("rating", 0))

            numbers = [
                matches, goals, assists, clean_sheets,
                yellow_cards, red_cards
            ]

            if any(number < 0 for number in numbers) or rating < 0:
                raise ValueError

        except ValueError:
            con.close()
            flash("لطفاً آمار معتبر و غیرمنفی وارد کن.")
            return redirect(
                url_for("admin_panel.edit_player", player_id=player_id)
            )

        con.execute("""
            UPDATE users
            SET matches=?,
                goals=?,
                assists=?,
                clean_sheets=?,
                yellow_cards=?,
                red_cards=?,
                rating=?
            WHERE id=? AND role='player'
        """, (
            matches,
            goals,
            assists,
            clean_sheets,
            yellow_cards,
            red_cards,
            rating,
            player_id
        ))

        con.commit()
        con.close()

        flash("آمار بازیکن با موفقیت ویرایش شد.")

        return redirect(url_for("admin_panel.players_admin"))

    con.close()

    content = """
    <div class="card">

        <h2>ویرایش آمار {{ player.username }}</h2>

        <form method="POST">

            <label>تعداد بازی</label>
            <input type="number" min="0" name="matches"
                   value="{{ player.matches }}" required>

            <label>گل</label>
            <input type="number" min="0" name="goals"
                   value="{{ player.goals }}" required>

            <label>پاس گل</label>
            <input type="number" min="0" name="assists"
                   value="{{ player.assists }}" required>

            <label>کلین شیت</label>
            <input type="number" min="0" name="clean_sheets"
                   value="{{ player.clean_sheets }}" required>

            <label>کارت زرد</label>
            <input type="number" min="0" name="yellow_cards"
                   value="{{ player.yellow_cards }}" required>

            <label>کارت قرمز</label>
            <input type="number" min="0" name="red_cards"
                   value="{{ player.red_cards }}" required>

            <label>امتیاز</label>
            <input type="number" min="0" step="0.1" name="rating"
                   value="{{ player.rating }}" required>

            <button type="submit">ذخیره تغییرات</button>

        </form>

    </div>
    """

    return admin_page(
        "ویرایش بازیکن",
        render_template_string(content, player=player)
    )


# ---------------- ADD MATCH ----------------

@admin_bp.route("/match/add", methods=["GET", "POST"])
@admin_required
def add_match():

    if request.method == "POST":

        opponent = request.form.get("opponent", "").strip()
        score = request.form.get("score", "").strip()
        result = request.form.get("result", "").strip()
        match_date = request.form.get("match_date", "").strip()

        if not opponent or not score or result not in [
            "برد", "باخت", "مساوی"
        ]:
            flash("لطفاً اطلاعات مسابقه را کامل و درست وارد کن.")
            return redirect(url_for("admin_panel.add_match"))

        con = get_db()

        con.execute("""
            INSERT INTO matches (
                opponent, score, result, match_date
            )
            VALUES (?, ?, ?, ?)
        """, (
            opponent,
            score,
            result,
            match_date
        ))

        con.commit()
        con.close()

        flash("مسابقه با موفقیت ثبت شد.")

        return redirect(url_for("admin_panel.dashboard"))

    content = """
    <div class="card">

        <h2>ثبت مسابقه جدید</h2>

        <form method="POST">

            <label>نام تیم حریف</label>
            <input name="opponent" placeholder="نام تیم حریف" required>

            <label>نتیجه بازی</label>
            <input name="score" placeholder="مثلاً 3 - 0" required>

            <label>نتیجه مسابقه</label>
            <select name="result" required>
                <option value="">انتخاب کن</option>
                <option value="برد">برد</option>
                <option value="باخت">باخت</option>
                <option value="مساوی">مساوی</option>
            </select>

            <label>تاریخ مسابقه</label>
            <input name="match_date"
                   placeholder="مثلاً 1405/08/26">

            <button type="submit">ثبت مسابقه</button>

        </form>

    </div>
    """

    return admin_page("ثبت مسابقه", content)


# ---------------- DELETE MATCH ----------------

@admin_bp.route("/match/<int:match_id>/delete", methods=["POST"])
@admin_required
def delete_match(match_id):

    con = get_db()

    con.execute(
        "DELETE FROM matches WHERE id=?",
        (match_id,)
    )

    con.commit()
    con.close()

    flash("مسابقه حذف شد.")

    return redirect(url_for("admin_panel.dashboard"))

