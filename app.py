from flask import Flask, render_template, request, redirect, url_for, flash, g, session, abort
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import math
import re

app = Flask(__name__)
app.secret_key = 'esports_secret_key_2024'

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
ITEMS_PER_PAGE = 10

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'
_ADMIN_PREFIXES = ('/teams', '/players', '/gears', '/tournaments', '/results', '/dashboard')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            abort(404)
        return f(*args, **kwargs)
    return decorated


@app.before_request
def protect_admin_routes():
    if request.path.startswith('/static/'):
        return
    if request.path.startswith(_ADMIN_PREFIXES):
        if not session.get('admin_logged_in'):
            abort(404)


# ---------------------------------------------------------------------------
# Bootstrap: ensure users table exists at startup (idempotent)
# ---------------------------------------------------------------------------

def _bootstrap_users_table():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL UNIQUE,
            email      TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password   TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_bootstrap_users_table()

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def execute_db(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route('/dashboard')
def dashboard():
    db = get_db()

    total_teams       = db.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    total_players     = db.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    total_tournaments = db.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0]
    total_matches     = db.execute("SELECT COUNT(*) FROM match_results").fetchone()[0]

    wins   = db.execute("SELECT COUNT(*) FROM match_results WHERE result='WIN'").fetchone()[0]
    losses = db.execute("SELECT COUNT(*) FROM match_results WHERE result='LOSS'").fetchone()[0]
    draws  = db.execute("SELECT COUNT(*) FROM match_results WHERE result='DRAW'").fetchone()[0]

    win_rate = round((wins / total_matches * 100), 1) if total_matches > 0 else 0.0

    top_teams = db.execute("""
        SELECT t.id, t.name, t.game_title, t.country, t.ranking,
               COUNT(p.id) AS player_count,
               SUM(CASE WHEN mr.result='WIN'  THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN mr.result='LOSS' THEN 1 ELSE 0 END) AS losses
        FROM teams t
        LEFT JOIN players p      ON p.team_id = t.id
        LEFT JOIN match_results mr ON mr.team_id = t.id
        GROUP BY t.id
        ORDER BY t.ranking ASC
        LIMIT 5
    """).fetchall()

    recent_matches = db.execute("""
        SELECT mr.match_date, t.name AS team_name, mr.opponent,
               tn.name AS tournament_name, mr.result, mr.score, mr.mvp
        FROM match_results mr
        JOIN teams t       ON t.id  = mr.team_id
        JOIN tournaments tn ON tn.id = mr.tournament_id
        ORDER BY mr.match_date DESC, mr.id DESC
        LIMIT 5
    """).fetchall()

    return render_template('dashboard.html',
        total_teams=total_teams,
        total_players=total_players,
        total_tournaments=total_tournaments,
        total_matches=total_matches,
        wins=wins, losses=losses, draws=draws,
        win_rate=win_rate,
        top_teams=top_teams,
        recent_matches=recent_matches
    )


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

@app.route('/teams')
def teams_index():
    q    = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'ranking')
    page = int(request.args.get('page', 1))

    allowed_sorts = {'ranking': 't.ranking ASC', 'name': 't.name ASC'}
    order_clause  = allowed_sorts.get(sort, 't.ranking ASC')

    base_sql = """
        SELECT t.id, t.name, t.game_title, t.country, t.coach,
               t.ranking, t.sponsor, t.created_at,
               COUNT(p.id) AS player_count
        FROM teams t
        LEFT JOIN players p ON p.team_id = t.id
        {where}
        GROUP BY t.id
        ORDER BY {order}
    """
    where_clause = "WHERE t.name LIKE ?" if q else ""
    args = (f'%{q}%',) if q else ()

    sql        = base_sql.format(where=where_clause, order=order_clause)
    all_rows   = get_db().execute(sql, args).fetchall()
    total      = len(all_rows)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    page        = max(1, min(page, total_pages))
    offset      = (page - 1) * ITEMS_PER_PAGE

    paginated_sql = sql + " LIMIT ? OFFSET ?"
    teams = get_db().execute(paginated_sql, args + (ITEMS_PER_PAGE, offset)).fetchall()

    return render_template('teams/index.html',
        teams=teams, q=q, sort=sort,
        page=page, total_pages=total_pages, total=total
    )


@app.route('/teams/create', methods=['GET', 'POST'])
def teams_create():
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        game_title = request.form.get('game_title', '').strip()
        country    = request.form.get('country', '').strip()
        coach      = request.form.get('coach', '').strip()
        ranking    = request.form.get('ranking', '').strip()
        sponsor    = request.form.get('sponsor', '').strip()

        errors = []
        if not name:       errors.append("Team name is required.")
        if not game_title: errors.append("Game title is required.")
        if not country:    errors.append("Country is required.")
        if not coach:      errors.append("Coach is required.")
        if not ranking or not ranking.isdigit():
            errors.append("Ranking must be a positive integer.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('teams/create.html',
                form=request.form)

        try:
            execute_db(
                "INSERT INTO teams (name, game_title, country, coach, ranking, sponsor) VALUES (?,?,?,?,?,?)",
                (name, game_title, country, coach, int(ranking), sponsor)
            )
            flash(f'Team "{name}" created successfully!', 'success')
            return redirect(url_for('teams_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('teams/create.html', form=request.form)

    return render_template('teams/create.html', form={})


@app.route('/teams/<int:team_id>/edit', methods=['GET', 'POST'])
def teams_edit(team_id):
    team = query_db("SELECT * FROM teams WHERE id=?", (team_id,), one=True)
    if team is None:
        flash('Team not found.', 'error')
        return redirect(url_for('teams_index'))

    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        game_title = request.form.get('game_title', '').strip()
        country    = request.form.get('country', '').strip()
        coach      = request.form.get('coach', '').strip()
        ranking    = request.form.get('ranking', '').strip()
        sponsor    = request.form.get('sponsor', '').strip()

        errors = []
        if not name:       errors.append("Team name is required.")
        if not game_title: errors.append("Game title is required.")
        if not country:    errors.append("Country is required.")
        if not coach:      errors.append("Coach is required.")
        if not ranking or not ranking.isdigit():
            errors.append("Ranking must be a positive integer.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('teams/edit.html', team=team, form=request.form)

        try:
            execute_db(
                "UPDATE teams SET name=?, game_title=?, country=?, coach=?, ranking=?, sponsor=? WHERE id=?",
                (name, game_title, country, coach, int(ranking), sponsor, team_id)
            )
            flash(f'Team "{name}" updated successfully!', 'success')
            return redirect(url_for('teams_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('teams/edit.html', team=team, form=request.form)

    return render_template('teams/edit.html', team=team, form=team)


@app.route('/teams/<int:team_id>/delete', methods=['POST'])
def teams_delete(team_id):
    team = query_db("SELECT * FROM teams WHERE id=?", (team_id,), one=True)
    if team is None:
        flash('Team not found.', 'error')
    else:
        execute_db("DELETE FROM teams WHERE id=?", (team_id,))
        flash(f'Team "{team["name"]}" deleted.', 'success')
    return redirect(url_for('teams_index'))


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

@app.route('/players')
def players_index():
    q       = request.args.get('q', '').strip()
    team_id = request.args.get('team_id', '').strip()
    sort    = request.args.get('sort', 'name')
    page    = int(request.args.get('page', 1))

    allowed_sorts = {
        'name':   'p.name ASC',
        'kda':    'p.kda DESC',
        'salary': 'p.salary DESC',
    }
    order_clause = allowed_sorts.get(sort, 'p.name ASC')

    conditions = []
    args = []
    if q:
        conditions.append("p.name LIKE ?")
        args.append(f'%{q}%')
    if team_id:
        conditions.append("p.team_id = ?")
        args.append(team_id)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base_sql = f"""
        SELECT p.*, t.name AS team_name
        FROM players p
        LEFT JOIN teams t ON t.id = p.team_id
        {where_clause}
        ORDER BY {order_clause}
    """
    all_rows    = get_db().execute(base_sql, args).fetchall()
    total       = len(all_rows)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    page        = max(1, min(page, total_pages))
    offset      = (page - 1) * ITEMS_PER_PAGE

    players = get_db().execute(base_sql + " LIMIT ? OFFSET ?", args + [ITEMS_PER_PAGE, offset]).fetchall()
    all_teams = query_db("SELECT id, name FROM teams ORDER BY name")

    return render_template('players/index.html',
        players=players, all_teams=all_teams,
        q=q, team_id=team_id, sort=sort,
        page=page, total_pages=total_pages, total=total
    )


@app.route('/players/create', methods=['GET', 'POST'])
def players_create():
    all_teams = query_db("SELECT id, name FROM teams ORDER BY name")

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        age       = request.form.get('age', '').strip()
        role      = request.form.get('role', '').strip()
        team_id   = request.form.get('team_id', '').strip()
        kda       = request.form.get('kda', '').strip()
        salary    = request.form.get('salary', '').strip()
        join_date = request.form.get('join_date', '').strip()

        errors = []
        if not name:      errors.append("Player name is required.")
        if not age or not age.isdigit():
            errors.append("Age must be a positive integer.")
        if not role:      errors.append("Role is required.")
        if not team_id:   errors.append("Team is required.")
        if not join_date: errors.append("Join date is required.")
        try:
            float(kda)
        except (ValueError, TypeError):
            errors.append("KDA must be a decimal number.")
        try:
            float(salary)
        except (ValueError, TypeError):
            errors.append("Salary must be a decimal number.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('players/create.html',
                all_teams=all_teams, form=request.form)

        try:
            execute_db(
                "INSERT INTO players (name, age, role, team_id, kda, salary, join_date) VALUES (?,?,?,?,?,?,?)",
                (name, int(age), role, int(team_id), float(kda), float(salary), join_date)
            )
            flash(f'Player "{name}" created successfully!', 'success')
            return redirect(url_for('players_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('players/create.html',
                all_teams=all_teams, form=request.form)

    return render_template('players/create.html', all_teams=all_teams, form={})


@app.route('/players/<int:player_id>/edit', methods=['GET', 'POST'])
def players_edit(player_id):
    player = query_db("SELECT * FROM players WHERE id=?", (player_id,), one=True)
    if player is None:
        flash('Player not found.', 'error')
        return redirect(url_for('players_index'))

    all_teams = query_db("SELECT id, name FROM teams ORDER BY name")

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        age       = request.form.get('age', '').strip()
        role      = request.form.get('role', '').strip()
        team_id   = request.form.get('team_id', '').strip()
        kda       = request.form.get('kda', '').strip()
        salary    = request.form.get('salary', '').strip()
        join_date = request.form.get('join_date', '').strip()

        errors = []
        if not name:      errors.append("Player name is required.")
        if not age or not age.isdigit():
            errors.append("Age must be a positive integer.")
        if not role:      errors.append("Role is required.")
        if not team_id:   errors.append("Team is required.")
        if not join_date: errors.append("Join date is required.")
        try:
            float(kda)
        except (ValueError, TypeError):
            errors.append("KDA must be a decimal number.")
        try:
            float(salary)
        except (ValueError, TypeError):
            errors.append("Salary must be a decimal number.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('players/edit.html',
                player=player, all_teams=all_teams, form=request.form)

        try:
            execute_db(
                "UPDATE players SET name=?, age=?, role=?, team_id=?, kda=?, salary=?, join_date=? WHERE id=?",
                (name, int(age), role, int(team_id), float(kda), float(salary), join_date, player_id)
            )
            flash(f'Player "{name}" updated successfully!', 'success')
            return redirect(url_for('players_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('players/edit.html',
                player=player, all_teams=all_teams, form=request.form)

    return render_template('players/edit.html',
        player=player, all_teams=all_teams, form=player)


@app.route('/players/<int:player_id>/delete', methods=['POST'])
def players_delete(player_id):
    player = query_db("SELECT * FROM players WHERE id=?", (player_id,), one=True)
    if player is None:
        flash('Player not found.', 'error')
    else:
        execute_db("DELETE FROM players WHERE id=?", (player_id,))
        flash(f'Player "{player["name"]}" deleted.', 'success')
    return redirect(url_for('players_index'))


# ---------------------------------------------------------------------------
# Gears
# ---------------------------------------------------------------------------

@app.route('/gears')
def gears_index():
    q     = request.args.get('q', '').strip()
    brand = request.args.get('brand', '').strip()
    page  = int(request.args.get('page', 1))

    conditions = []
    args = []
    if q:
        conditions.append("(p.name LIKE ? OR g.mouse LIKE ? OR g.keyboard LIKE ?)")
        args += [f'%{q}%', f'%{q}%', f'%{q}%']
    if brand:
        conditions.append("g.brand LIKE ?")
        args.append(f'%{brand}%')

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base_sql = f"""
        SELECT g.*, p.name AS player_name
        FROM gears g
        LEFT JOIN players p ON p.id = g.player_id
        {where_clause}
        ORDER BY p.name ASC
    """
    all_rows    = get_db().execute(base_sql, args).fetchall()
    total       = len(all_rows)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    page        = max(1, min(page, total_pages))
    offset      = (page - 1) * ITEMS_PER_PAGE

    gears = get_db().execute(base_sql + " LIMIT ? OFFSET ?", args + [ITEMS_PER_PAGE, offset]).fetchall()
    all_brands = get_db().execute("SELECT DISTINCT brand FROM gears ORDER BY brand").fetchall()

    return render_template('gears/index.html',
        gears=gears, all_brands=all_brands,
        q=q, brand=brand,
        page=page, total_pages=total_pages, total=total
    )


@app.route('/gears/create', methods=['GET', 'POST'])
def gears_create():
    all_players = query_db("SELECT p.id, p.name, t.name AS team_name FROM players p LEFT JOIN teams t ON t.id=p.team_id ORDER BY p.name")

    if request.method == 'POST':
        player_id = request.form.get('player_id', '').strip()
        mouse     = request.form.get('mouse', '').strip()
        keyboard  = request.form.get('keyboard', '').strip()
        headset   = request.form.get('headset', '').strip()
        monitor   = request.form.get('monitor', '').strip()
        brand     = request.form.get('brand', '').strip()

        errors = []
        if not player_id: errors.append("Player is required.")
        if not mouse:     errors.append("Mouse is required.")
        if not keyboard:  errors.append("Keyboard is required.")
        if not headset:   errors.append("Headset is required.")
        if not monitor:   errors.append("Monitor is required.")
        if not brand:     errors.append("Brand is required.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('gears/create.html',
                all_players=all_players, form=request.form)

        try:
            execute_db(
                "INSERT INTO gears (mouse, keyboard, headset, monitor, brand, player_id) VALUES (?,?,?,?,?,?)",
                (mouse, keyboard, headset, monitor, brand, int(player_id))
            )
            flash('Gear entry created successfully!', 'success')
            return redirect(url_for('gears_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('gears/create.html',
                all_players=all_players, form=request.form)

    return render_template('gears/create.html', all_players=all_players, form={})


@app.route('/gears/<int:gear_id>/edit', methods=['GET', 'POST'])
def gears_edit(gear_id):
    gear = query_db("SELECT * FROM gears WHERE id=?", (gear_id,), one=True)
    if gear is None:
        flash('Gear entry not found.', 'error')
        return redirect(url_for('gears_index'))

    all_players = query_db("SELECT p.id, p.name, t.name AS team_name FROM players p LEFT JOIN teams t ON t.id=p.team_id ORDER BY p.name")

    if request.method == 'POST':
        player_id = request.form.get('player_id', '').strip()
        mouse     = request.form.get('mouse', '').strip()
        keyboard  = request.form.get('keyboard', '').strip()
        headset   = request.form.get('headset', '').strip()
        monitor   = request.form.get('monitor', '').strip()
        brand     = request.form.get('brand', '').strip()

        errors = []
        if not player_id: errors.append("Player is required.")
        if not mouse:     errors.append("Mouse is required.")
        if not keyboard:  errors.append("Keyboard is required.")
        if not headset:   errors.append("Headset is required.")
        if not monitor:   errors.append("Monitor is required.")
        if not brand:     errors.append("Brand is required.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('gears/edit.html',
                gear=gear, all_players=all_players, form=request.form)

        try:
            execute_db(
                "UPDATE gears SET mouse=?, keyboard=?, headset=?, monitor=?, brand=?, player_id=? WHERE id=?",
                (mouse, keyboard, headset, monitor, brand, int(player_id), gear_id)
            )
            flash('Gear entry updated successfully!', 'success')
            return redirect(url_for('gears_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('gears/edit.html',
                gear=gear, all_players=all_players, form=request.form)

    return render_template('gears/edit.html',
        gear=gear, all_players=all_players, form=gear)


@app.route('/gears/<int:gear_id>/delete', methods=['POST'])
def gears_delete(gear_id):
    gear = query_db("SELECT * FROM gears WHERE id=?", (gear_id,), one=True)
    if gear is None:
        flash('Gear entry not found.', 'error')
    else:
        execute_db("DELETE FROM gears WHERE id=?", (gear_id,))
        flash('Gear entry deleted.', 'success')
    return redirect(url_for('gears_index'))


# ---------------------------------------------------------------------------
# Tournaments
# ---------------------------------------------------------------------------

@app.route('/tournaments')
def tournaments_index():
    q    = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'start_date')
    page = int(request.args.get('page', 1))

    allowed_sorts = {
        'start_date': 't.start_date DESC',
        'prize_pool': 't.prize_pool DESC',
        'name':       't.name ASC',
    }
    order_clause = allowed_sorts.get(sort, 't.start_date DESC')

    where_clause = "WHERE t.name LIKE ?" if q else ""
    args = (f'%{q}%',) if q else ()

    base_sql = f"""
        SELECT t.*, COUNT(mr.id) AS match_count
        FROM tournaments t
        LEFT JOIN match_results mr ON mr.tournament_id = t.id
        {where_clause}
        GROUP BY t.id
        ORDER BY {order_clause}
    """
    all_rows    = get_db().execute(base_sql, args).fetchall()
    total       = len(all_rows)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    page        = max(1, min(page, total_pages))
    offset      = (page - 1) * ITEMS_PER_PAGE

    tournaments = get_db().execute(base_sql + " LIMIT ? OFFSET ?", args + (ITEMS_PER_PAGE, offset)).fetchall()

    return render_template('tournaments/index.html',
        tournaments=tournaments, q=q, sort=sort,
        page=page, total_pages=total_pages, total=total
    )


@app.route('/tournaments/create', methods=['GET', 'POST'])
def tournaments_create():
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        prize_pool = request.form.get('prize_pool', '').strip()
        location   = request.form.get('location', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date   = request.form.get('end_date', '').strip()
        organizer  = request.form.get('organizer', '').strip()

        errors = []
        if not name:       errors.append("Tournament name is required.")
        if not location:   errors.append("Location is required.")
        if not start_date: errors.append("Start date is required.")
        if not end_date:   errors.append("End date is required.")
        if not organizer:  errors.append("Organizer is required.")
        try:
            float(prize_pool)
        except (ValueError, TypeError):
            errors.append("Prize pool must be a number.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('tournaments/create.html', form=request.form)

        try:
            execute_db(
                "INSERT INTO tournaments (name, prize_pool, location, start_date, end_date, organizer) VALUES (?,?,?,?,?,?)",
                (name, float(prize_pool), location, start_date, end_date, organizer)
            )
            flash(f'Tournament "{name}" created successfully!', 'success')
            return redirect(url_for('tournaments_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('tournaments/create.html', form=request.form)

    return render_template('tournaments/create.html', form={})


@app.route('/tournaments/<int:tournament_id>/edit', methods=['GET', 'POST'])
def tournaments_edit(tournament_id):
    tournament = query_db("SELECT * FROM tournaments WHERE id=?", (tournament_id,), one=True)
    if tournament is None:
        flash('Tournament not found.', 'error')
        return redirect(url_for('tournaments_index'))

    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        prize_pool = request.form.get('prize_pool', '').strip()
        location   = request.form.get('location', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date   = request.form.get('end_date', '').strip()
        organizer  = request.form.get('organizer', '').strip()

        errors = []
        if not name:       errors.append("Tournament name is required.")
        if not location:   errors.append("Location is required.")
        if not start_date: errors.append("Start date is required.")
        if not end_date:   errors.append("End date is required.")
        if not organizer:  errors.append("Organizer is required.")
        try:
            float(prize_pool)
        except (ValueError, TypeError):
            errors.append("Prize pool must be a number.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('tournaments/edit.html',
                tournament=tournament, form=request.form)

        try:
            execute_db(
                "UPDATE tournaments SET name=?, prize_pool=?, location=?, start_date=?, end_date=?, organizer=? WHERE id=?",
                (name, float(prize_pool), location, start_date, end_date, organizer, tournament_id)
            )
            flash(f'Tournament "{name}" updated successfully!', 'success')
            return redirect(url_for('tournaments_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('tournaments/edit.html',
                tournament=tournament, form=request.form)

    return render_template('tournaments/edit.html',
        tournament=tournament, form=tournament)


@app.route('/tournaments/<int:tournament_id>/delete', methods=['POST'])
def tournaments_delete(tournament_id):
    tournament = query_db("SELECT * FROM tournaments WHERE id=?", (tournament_id,), one=True)
    if tournament is None:
        flash('Tournament not found.', 'error')
    else:
        execute_db("DELETE FROM tournaments WHERE id=?", (tournament_id,))
        flash(f'Tournament "{tournament["name"]}" deleted.', 'success')
    return redirect(url_for('tournaments_index'))


# ---------------------------------------------------------------------------
# Match Results
# ---------------------------------------------------------------------------

@app.route('/results')
def results_index():
    result_filter = request.args.get('result', '').strip()
    team_filter   = request.args.get('team_id', '').strip()
    page          = int(request.args.get('page', 1))

    conditions = []
    args = []
    if result_filter in ('WIN', 'LOSS', 'DRAW'):
        conditions.append("mr.result = ?")
        args.append(result_filter)
    if team_filter:
        conditions.append("mr.team_id = ?")
        args.append(team_filter)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base_sql = f"""
        SELECT mr.*, t.name AS team_name, tn.name AS tournament_name
        FROM match_results mr
        JOIN teams t        ON t.id  = mr.team_id
        JOIN tournaments tn ON tn.id = mr.tournament_id
        {where_clause}
        ORDER BY mr.match_date DESC, mr.id DESC
    """
    all_rows    = get_db().execute(base_sql, args).fetchall()
    total       = len(all_rows)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    page        = max(1, min(page, total_pages))
    offset      = (page - 1) * ITEMS_PER_PAGE

    results = get_db().execute(base_sql + " LIMIT ? OFFSET ?", args + [ITEMS_PER_PAGE, offset]).fetchall()
    all_teams = query_db("SELECT id, name FROM teams ORDER BY name")

    return render_template('results/index.html',
        results=results, all_teams=all_teams,
        result_filter=result_filter, team_filter=team_filter,
        page=page, total_pages=total_pages, total=total
    )


@app.route('/results/create', methods=['GET', 'POST'])
def results_create():
    all_teams       = query_db("SELECT id, name FROM teams ORDER BY name")
    all_tournaments = query_db("SELECT id, name FROM tournaments ORDER BY name")

    if request.method == 'POST':
        team_id       = request.form.get('team_id', '').strip()
        tournament_id = request.form.get('tournament_id', '').strip()
        opponent      = request.form.get('opponent', '').strip()
        result        = request.form.get('result', '').strip()
        score         = request.form.get('score', '').strip()
        mvp           = request.form.get('mvp', '').strip()
        match_date    = request.form.get('match_date', '').strip()

        errors = []
        if not team_id:       errors.append("Team is required.")
        if not tournament_id: errors.append("Tournament is required.")
        if not opponent:      errors.append("Opponent is required.")
        if result not in ('WIN', 'LOSS', 'DRAW'):
            errors.append("Result must be WIN, LOSS, or DRAW.")
        if not score:         errors.append("Score is required.")
        if not match_date:    errors.append("Match date is required.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('results/create.html',
                all_teams=all_teams, all_tournaments=all_tournaments,
                form=request.form)

        try:
            execute_db(
                "INSERT INTO match_results (team_id, tournament_id, opponent, result, score, mvp, match_date) VALUES (?,?,?,?,?,?,?)",
                (int(team_id), int(tournament_id), opponent, result, score, mvp, match_date)
            )
            flash('Match result recorded successfully!', 'success')
            return redirect(url_for('results_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('results/create.html',
                all_teams=all_teams, all_tournaments=all_tournaments,
                form=request.form)

    return render_template('results/create.html',
        all_teams=all_teams, all_tournaments=all_tournaments, form={})


@app.route('/results/<int:result_id>/edit', methods=['GET', 'POST'])
def results_edit(result_id):
    match = query_db("SELECT * FROM match_results WHERE id=?", (result_id,), one=True)
    if match is None:
        flash('Match result not found.', 'error')
        return redirect(url_for('results_index'))

    all_teams       = query_db("SELECT id, name FROM teams ORDER BY name")
    all_tournaments = query_db("SELECT id, name FROM tournaments ORDER BY name")

    if request.method == 'POST':
        team_id       = request.form.get('team_id', '').strip()
        tournament_id = request.form.get('tournament_id', '').strip()
        opponent      = request.form.get('opponent', '').strip()
        result        = request.form.get('result', '').strip()
        score         = request.form.get('score', '').strip()
        mvp           = request.form.get('mvp', '').strip()
        match_date    = request.form.get('match_date', '').strip()

        errors = []
        if not team_id:       errors.append("Team is required.")
        if not tournament_id: errors.append("Tournament is required.")
        if not opponent:      errors.append("Opponent is required.")
        if result not in ('WIN', 'LOSS', 'DRAW'):
            errors.append("Result must be WIN, LOSS, or DRAW.")
        if not score:         errors.append("Score is required.")
        if not match_date:    errors.append("Match date is required.")

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('results/edit.html',
                match=match, all_teams=all_teams,
                all_tournaments=all_tournaments, form=request.form)

        try:
            execute_db(
                "UPDATE match_results SET team_id=?, tournament_id=?, opponent=?, result=?, score=?, mvp=?, match_date=? WHERE id=?",
                (int(team_id), int(tournament_id), opponent, result, score, mvp, match_date, result_id)
            )
            flash('Match result updated successfully!', 'success')
            return redirect(url_for('results_index'))
        except sqlite3.IntegrityError as ex:
            flash(f'Database error: {ex}', 'error')
            return render_template('results/edit.html',
                match=match, all_teams=all_teams,
                all_tournaments=all_tournaments, form=request.form)

    return render_template('results/edit.html',
        match=match, all_teams=all_teams,
        all_tournaments=all_tournaments, form=match)


@app.route('/results/<int:result_id>/delete', methods=['POST'])
def results_delete(result_id):
    match = query_db("SELECT * FROM match_results WHERE id=?", (result_id,), one=True)
    if match is None:
        flash('Match result not found.', 'error')
    else:
        execute_db("DELETE FROM match_results WHERE id=?", (result_id,))
        flash('Match result deleted.', 'success')
    return redirect(url_for('results_index'))


# ---------------------------------------------------------------------------
# Admin Auth Routes
# ---------------------------------------------------------------------------

@app.route('/staff-access', methods=['GET', 'POST'])
def staff_access():
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('auth/login.html')


@app.route('/logout')
def logout_admin():
    session.pop('admin_logged_in', None)
    return redirect(url_for('public_home'))


# ---------------------------------------------------------------------------
# Public Routes
# ---------------------------------------------------------------------------

@app.route('/')
def public_home():
    db = get_db()
    total_teams       = db.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    total_players     = db.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    total_tournaments = db.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0]
    total_matches     = db.execute("SELECT COUNT(*) FROM match_results").fetchone()[0]

    featured_teams = db.execute("""
        SELECT t.id, t.name, t.game_title, t.country, t.ranking, t.sponsor,
               COUNT(DISTINCT p.id) AS player_count,
               SUM(CASE WHEN mr.result='WIN'  THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN mr.result='LOSS' THEN 1 ELSE 0 END) AS losses
        FROM teams t
        LEFT JOIN players p        ON p.team_id  = t.id
        LEFT JOIN match_results mr ON mr.team_id = t.id
        GROUP BY t.id
        ORDER BY t.ranking ASC
        LIMIT 6
    """).fetchall()

    top_players = db.execute("""
        SELECT p.id, p.name, p.role, p.kda, p.age,
               t.name AS team_name, t.id AS team_id
        FROM players p
        LEFT JOIN teams t ON t.id = p.team_id
        ORDER BY p.kda DESC
        LIMIT 5
    """).fetchall()

    recent_matches = db.execute("""
        SELECT mr.id, mr.match_date, t.name AS team_name, t.id AS team_id,
               mr.opponent, tn.name AS tournament_name, mr.result, mr.score, mr.mvp
        FROM match_results mr
        JOIN teams      t  ON t.id  = mr.team_id
        JOIN tournaments tn ON tn.id = mr.tournament_id
        ORDER BY mr.match_date DESC, mr.id DESC
        LIMIT 8
    """).fetchall()

    tournaments = db.execute("""
        SELECT t.id, t.name, t.prize_pool, t.location, t.start_date, t.end_date,
               COUNT(mr.id) AS match_count
        FROM tournaments t
        LEFT JOIN match_results mr ON mr.tournament_id = t.id
        GROUP BY t.id
        ORDER BY t.prize_pool DESC
        LIMIT 4
    """).fetchall()

    wins   = db.execute("SELECT COUNT(*) FROM match_results WHERE result='WIN'").fetchone()[0]
    losses = db.execute("SELECT COUNT(*) FROM match_results WHERE result='LOSS'").fetchone()[0]
    win_rate = round((wins / total_matches * 100), 1) if total_matches > 0 else 0.0

    return render_template('public/home.html',
        total_teams=total_teams, total_players=total_players,
        total_tournaments=total_tournaments, total_matches=total_matches,
        featured_teams=featured_teams, top_players=top_players,
        recent_matches=recent_matches, tournaments=tournaments,
        wins=wins, losses=losses, win_rate=win_rate
    )


@app.route('/pub/teams')
def pub_teams():
    teams = get_db().execute("""
        SELECT t.id, t.name, t.game_title, t.country, t.ranking, t.sponsor, t.coach,
               COUNT(DISTINCT p.id) AS player_count,
               SUM(CASE WHEN mr.result='WIN'  THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN mr.result='LOSS' THEN 1 ELSE 0 END) AS losses,
               SUM(CASE WHEN mr.result='DRAW' THEN 1 ELSE 0 END) AS draws
        FROM teams t
        LEFT JOIN players p        ON p.team_id  = t.id
        LEFT JOIN match_results mr ON mr.team_id = t.id
        GROUP BY t.id
        ORDER BY t.ranking ASC
    """).fetchall()
    return render_template('public/teams.html', teams=teams)


@app.route('/pub/teams/<int:team_id>')
def pub_team_detail(team_id):
    db = get_db()
    team = db.execute("""
        SELECT t.*,
               COUNT(DISTINCT p.id)  AS player_count,
               SUM(CASE WHEN mr.result='WIN'  THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN mr.result='LOSS' THEN 1 ELSE 0 END) AS losses,
               SUM(CASE WHEN mr.result='DRAW' THEN 1 ELSE 0 END) AS draws
        FROM teams t
        LEFT JOIN players p        ON p.team_id  = t.id
        LEFT JOIN match_results mr ON mr.team_id = t.id
        WHERE t.id = ?
        GROUP BY t.id
    """, (team_id,)).fetchone()

    if team is None:
        return redirect(url_for('pub_teams'))

    players = db.execute("""
        SELECT p.*, g.mouse, g.keyboard, g.headset, g.monitor, g.brand
        FROM players p
        LEFT JOIN gears g ON g.player_id = p.id
        WHERE p.team_id = ?
        ORDER BY p.kda DESC
    """, (team_id,)).fetchall()

    matches = db.execute("""
        SELECT mr.*, tn.name AS tournament_name
        FROM match_results mr
        JOIN tournaments tn ON tn.id = mr.tournament_id
        WHERE mr.team_id = ?
        ORDER BY mr.match_date DESC
        LIMIT 10
    """, (team_id,)).fetchall()

    total_match = (team['wins'] or 0) + (team['losses'] or 0) + (team['draws'] or 0)
    win_rate = round(((team['wins'] or 0) / total_match * 100), 1) if total_match > 0 else 0.0

    return render_template('public/team_detail.html',
        team=team, players=players, matches=matches, win_rate=win_rate
    )


@app.route('/pub/players')
def pub_players():
    q       = request.args.get('q', '').strip()
    team_id = request.args.get('team_id', '').strip()

    conditions, args = [], []
    if q:
        conditions.append("p.name LIKE ?")
        args.append(f'%{q}%')
    if team_id:
        conditions.append("p.team_id = ?")
        args.append(team_id)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    players = get_db().execute(f"""
        SELECT p.id, p.name, p.role, p.kda, p.age, p.join_date,
               t.name AS team_name, t.id AS team_id
        FROM players p
        LEFT JOIN teams t ON t.id = p.team_id
        {where}
        ORDER BY p.kda DESC
    """, args).fetchall()

    all_teams = query_db("SELECT id, name FROM teams ORDER BY name")
    return render_template('public/players.html',
        players=players, all_teams=all_teams, q=q, team_id=team_id
    )


@app.route('/pub/players/<int:player_id>')
def pub_player(player_id):
    db = get_db()
    player = db.execute("""
        SELECT p.*, t.name AS team_name, t.id AS team_id, t.game_title
        FROM players p
        LEFT JOIN teams t ON t.id = p.team_id
        WHERE p.id = ?
    """, (player_id,)).fetchone()

    if player is None:
        return redirect(url_for('pub_players'))

    gear = db.execute("SELECT * FROM gears WHERE player_id = ?", (player_id,)).fetchone()

    mvp_matches = db.execute("""
        SELECT mr.*, tn.name AS tournament_name, t.name AS team_name
        FROM match_results mr
        JOIN tournaments tn ON tn.id = mr.tournament_id
        JOIN teams       t  ON t.id  = mr.team_id
        WHERE mr.mvp = ? AND mr.team_id = ?
        ORDER BY mr.match_date DESC
        LIMIT 8
    """, (player['name'], player['team_id'] or 0)).fetchall()

    team_stats = db.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN result='WIN'  THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN result='LOSS' THEN 1 ELSE 0 END) AS losses
        FROM match_results WHERE team_id = ?
    """, (player['team_id'] or 0,)).fetchone()

    return render_template('public/player.html',
        player=player, gear=gear, mvp_matches=mvp_matches, team_stats=team_stats
    )


@app.route('/pub/tournaments')
def pub_tournaments():
    db = get_db()
    tournaments = db.execute("""
        SELECT t.*, COUNT(mr.id) AS match_count,
               SUM(CASE WHEN mr.result='WIN'  THEN 1 ELSE 0 END) AS total_wins
        FROM tournaments t
        LEFT JOIN match_results mr ON mr.tournament_id = t.id
        GROUP BY t.id
        ORDER BY t.prize_pool DESC
    """).fetchall()

    tournament_matches = {}
    for tn in tournaments:
        rows = db.execute("""
            SELECT mr.*, t.name AS team_name
            FROM match_results mr
            JOIN teams t ON t.id = mr.team_id
            WHERE mr.tournament_id = ?
            ORDER BY mr.match_date ASC
            LIMIT 6
        """, (tn['id'],)).fetchall()
        tournament_matches[tn['id']] = rows

    return render_template('public/tournaments.html',
        tournaments=tournaments, tournament_matches=tournament_matches
    )


@app.route('/pub/matches')
def pub_matches():
    result_filter = request.args.get('result', '').strip()
    team_filter   = request.args.get('team_id', '').strip()
    page          = int(request.args.get('page', 1))

    conditions, args = [], []
    if result_filter in ('WIN', 'LOSS', 'DRAW'):
        conditions.append("mr.result = ?")
        args.append(result_filter)
    if team_filter:
        conditions.append("mr.team_id = ?")
        args.append(team_filter)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    base_sql = f"""
        SELECT mr.*, t.name AS team_name, t.id AS team_id,
               tn.name AS tournament_name
        FROM match_results mr
        JOIN teams       t  ON t.id  = mr.team_id
        JOIN tournaments tn ON tn.id = mr.tournament_id
        {where}
        ORDER BY mr.match_date DESC, mr.id DESC
    """
    all_rows    = get_db().execute(base_sql, args).fetchall()
    total       = len(all_rows)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    page        = max(1, min(page, total_pages))
    offset      = (page - 1) * ITEMS_PER_PAGE

    matches   = get_db().execute(base_sql + " LIMIT ? OFFSET ?", args + [ITEMS_PER_PAGE, offset]).fetchall()
    all_teams = query_db("SELECT id, name FROM teams ORDER BY name")

    return render_template('public/matches.html',
        matches=matches, all_teams=all_teams,
        result_filter=result_filter, team_filter=team_filter,
        page=page, total_pages=total_pages, total=total
    )


@app.route('/pub/stats')
def pub_stats():
    db = get_db()

    top_teams_wins = db.execute("""
        SELECT t.id, t.name, t.game_title, t.country, t.ranking,
               COUNT(mr.id) AS total_matches,
               SUM(CASE WHEN mr.result='WIN'  THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN mr.result='LOSS' THEN 1 ELSE 0 END) AS losses,
               SUM(CASE WHEN mr.result='DRAW' THEN 1 ELSE 0 END) AS draws
        FROM teams t
        LEFT JOIN match_results mr ON mr.team_id = t.id
        GROUP BY t.id
        ORDER BY wins DESC, t.ranking ASC
        LIMIT 10
    """).fetchall()

    top_players_kda = db.execute("""
        SELECT p.id, p.name, p.role, p.kda, p.age,
               t.name AS team_name
        FROM players p
        LEFT JOIN teams t ON t.id = p.team_id
        ORDER BY p.kda DESC
        LIMIT 10
    """).fetchall()

    top_mvp = db.execute("""
        SELECT mr.mvp AS player_name,
               COUNT(*) AS mvp_count,
               t.name  AS team_name
        FROM match_results mr
        JOIN teams t ON t.id = mr.team_id
        WHERE mr.mvp IS NOT NULL AND mr.mvp != ''
        GROUP BY mr.mvp, mr.team_id
        ORDER BY mvp_count DESC
        LIMIT 10
    """).fetchall()

    total_teams       = db.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    total_players     = db.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    total_tournaments = db.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0]
    total_matches     = db.execute("SELECT COUNT(*) FROM match_results").fetchone()[0]
    wins   = db.execute("SELECT COUNT(*) FROM match_results WHERE result='WIN'").fetchone()[0]
    losses = db.execute("SELECT COUNT(*) FROM match_results WHERE result='LOSS'").fetchone()[0]
    draws  = db.execute("SELECT COUNT(*) FROM match_results WHERE result='DRAW'").fetchone()[0]

    return render_template('public/stats.html',
        top_teams_wins=top_teams_wins, top_players_kda=top_players_kda,
        top_mvp=top_mvp,
        total_teams=total_teams, total_players=total_players,
        total_tournaments=total_tournaments, total_matches=total_matches,
        wins=wins, losses=losses, draws=draws
    )


# ---------------------------------------------------------------------------
# Public User Authentication Routes
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def user_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to view that page.', 'info')
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if session.get('user_id'):
        return redirect(url_for('public_home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        errors = []
        if not email:    errors.append('Email is required.')
        if not password: errors.append('Password is required.')

        if not errors:
            user = query_db(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE",
                (email,), one=True
            )
            if user is None:
                errors.append('No account found with that email. Please register first.')
            elif not check_password_hash(user['password'], password):
                errors.append('Incorrect password.')
            else:
                session['user_id']    = user['id']
                session['user_name']  = user['username']
                session['user_email'] = user['email']
                flash(f"Welcome back, {user['username']}!", 'success')
                return redirect(url_for('public_home'))

        for e in errors:
            flash(e, 'error')

    return render_template('auth/user_login.html')


@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if session.get('user_id'):
        return redirect(url_for('public_home'))

    if request.method == 'POST':
        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        errors = []
        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        elif len(username) > 30:
            errors.append('Username must be 30 characters or fewer.')
        elif not re.match(r'^[A-Za-z0-9_]+$', username):
            errors.append('Username may only contain letters, numbers, and underscores.')

        if not email:
            errors.append('Email is required.')
        elif not _EMAIL_RE.match(email):
            errors.append('Please enter a valid email address.')

        if not password:
            errors.append('Password is required.')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters.')

        if password and confirm_password != password:
            errors.append('Passwords do not match.')

        if not errors:
            existing = query_db(
                "SELECT id FROM users WHERE email = ? COLLATE NOCASE OR username = ? COLLATE NOCASE",
                (email, username), one=True
            )
            if existing:
                by_email = query_db("SELECT id FROM users WHERE email = ? COLLATE NOCASE", (email,), one=True)
                if by_email:
                    errors.append('An account with that email already exists.')
                else:
                    errors.append('That username is already taken.')

        if not errors:
            hashed = generate_password_hash(password)
            try:
                execute_db(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, hashed)
                )
                flash('Account created! You can now log in.', 'success')
                return redirect(url_for('user_login'))
            except sqlite3.IntegrityError:
                errors.append('That username or email is already registered.')

        for e in errors:
            flash(e, 'error')

    return render_template('auth/user_register.html')


@app.route('/user-logout')
def user_logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('public_home'))


@app.route('/profile')
@user_login_required
def user_profile():
    db  = get_db()
    user = db.execute(
        "SELECT id, username, email, created_at FROM users WHERE id = ?",
        (session['user_id'],)
    ).fetchone()

    if user is None:
        session.clear()
        return redirect(url_for('user_login'))

    top_teams = db.execute("""
        SELECT t.id, t.name, t.game_title, t.ranking,
               SUM(CASE WHEN mr.result='WIN'  THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN mr.result='LOSS' THEN 1 ELSE 0 END) AS losses
        FROM teams t
        LEFT JOIN match_results mr ON mr.team_id = t.id
        GROUP BY t.id
        ORDER BY t.ranking ASC
        LIMIT 3
    """).fetchall()

    recent_matches = db.execute("""
        SELECT mr.match_date, t.name AS team_name, mr.opponent,
               mr.result, mr.score, mr.mvp
        FROM match_results mr
        JOIN teams t ON t.id = mr.team_id
        ORDER BY mr.match_date DESC, mr.id DESC
        LIMIT 5
    """).fetchall()

    total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    return render_template('public/profile.html',
        user=user,
        top_teams=top_teams,
        recent_matches=recent_matches,
        total_users=total_users
    )


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('public/404.html'), 404


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from init_db import init_db
    from seed import seed_if_empty

    init_db()
    seed_if_empty()

    app.run(debug=True, port=5000)
print(os.path.abspath(DATABASE))
