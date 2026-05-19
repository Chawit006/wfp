# E-Sports Team Manager System

**CS104 Introduction to Database — University Mini Project**

A full-stack web application for managing e-sports teams, players, gear inventories, tournaments, and match results. Built with Python (Flask) and SQLite as a demonstration of relational database design and CRUD operations.

---

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Backend     | Python 3.10+, Flask 3.0           |
| Database    | SQLite 3 (via Python `sqlite3`)   |
| Frontend    | Jinja2 templates, Tailwind CSS CDN|
| Styling     | Custom CSS (dark gaming theme)    |
| JavaScript  | Vanilla JS (no frameworks)        |

---

## Installation & Running

### Prerequisites
- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Navigate to the project directory
cd D:\wqqeq

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize the database schema
python init_db.py

# 4. Seed the database with sample data
python seed_data.py

# 5. Start the Flask development server
python app.py
```

Then open your browser and navigate to: **http://127.0.0.1:5000**

---

## Features

- **Dashboard** — Overview statistics: total teams, players, tournaments, win rate; top 5 ranked teams table; recent 5 match results
- **Teams Management** — Full CRUD with search, sort by ranking/name, player count via JOIN, pagination
- **Players Management** — Full CRUD with search, filter by team, sort by KDA/salary, role badges
- **Gear Inventory** — Full CRUD tracking mouse, keyboard, headset, monitor per player; filter by brand
- **Tournaments** — Full CRUD with prize pool formatting, match count via JOIN, sort by date/prize/name
- **Match Results** — Full CRUD with WIN/LOSS/DRAW badges, filter by result type and team
- **Cascading Deletes** — Foreign key constraints with ON DELETE CASCADE (e.g., deleting a team removes all its players, gear, and results)
- **Validation** — Server-side field validation with flash messages for errors and success
- **Pagination** — All list pages paginate at 10 records per page
- **Dark Theme** — Full dark gaming UI using Tailwind CSS

---

## Database Design

### Table: `teams`
Stores e-sports organization data.

| Column     | Type    | Constraints                          |
|------------|---------|--------------------------------------|
| id         | INTEGER | PRIMARY KEY AUTOINCREMENT            |
| name       | TEXT    | NOT NULL UNIQUE                      |
| game_title | TEXT    | NOT NULL                             |
| country    | TEXT    | NOT NULL                             |
| coach      | TEXT    | NOT NULL                             |
| ranking    | INTEGER | NOT NULL DEFAULT 999                 |
| sponsor    | TEXT    | nullable                             |
| created_at | TEXT    | NOT NULL DEFAULT CURRENT_TIMESTAMP   |

### Table: `players`
Stores individual player profiles linked to a team.

| Column    | Type    | Constraints                          |
|-----------|---------|--------------------------------------|
| id        | INTEGER | PRIMARY KEY AUTOINCREMENT            |
| name      | TEXT    | NOT NULL                             |
| age       | INTEGER | NOT NULL                             |
| role      | TEXT    | NOT NULL                             |
| team_id   | INTEGER | NOT NULL, FK → teams(id) CASCADE     |
| kda       | REAL    | NOT NULL DEFAULT 1.0                 |
| salary    | REAL    | NOT NULL DEFAULT 0.0                 |
| join_date | TEXT    | NOT NULL                             |
| created_at| TEXT    | NOT NULL DEFAULT CURRENT_TIMESTAMP   |

### Table: `gears`
Tracks peripheral equipment assigned to each player.

| Column    | Type    | Constraints                          |
|-----------|---------|--------------------------------------|
| id        | INTEGER | PRIMARY KEY AUTOINCREMENT            |
| mouse     | TEXT    | NOT NULL                             |
| keyboard  | TEXT    | NOT NULL                             |
| headset   | TEXT    | NOT NULL                             |
| monitor   | TEXT    | NOT NULL                             |
| brand     | TEXT    | NOT NULL                             |
| player_id | INTEGER | NOT NULL, FK → players(id) CASCADE   |
| created_at| TEXT    | NOT NULL DEFAULT CURRENT_TIMESTAMP   |

### Table: `tournaments`
Stores competition events.

| Column     | Type    | Constraints                          |
|------------|---------|--------------------------------------|
| id         | INTEGER | PRIMARY KEY AUTOINCREMENT            |
| name       | TEXT    | NOT NULL                             |
| prize_pool | REAL    | NOT NULL DEFAULT 0.0                 |
| location   | TEXT    | NOT NULL                             |
| start_date | TEXT    | NOT NULL                             |
| end_date   | TEXT    | NOT NULL                             |
| organizer  | TEXT    | NOT NULL                             |
| created_at | TEXT    | NOT NULL DEFAULT CURRENT_TIMESTAMP   |

### Table: `match_results`
Records match outcomes linking teams and tournaments.

| Column        | Type    | Constraints                                        |
|---------------|---------|----------------------------------------------------|
| id            | INTEGER | PRIMARY KEY AUTOINCREMENT                          |
| team_id       | INTEGER | NOT NULL, FK → teams(id) CASCADE                   |
| tournament_id | INTEGER | NOT NULL, FK → tournaments(id) CASCADE             |
| opponent      | TEXT    | NOT NULL                                           |
| result        | TEXT    | NOT NULL CHECK(result IN ('WIN','LOSS','DRAW'))    |
| score         | TEXT    | NOT NULL                                           |
| mvp           | TEXT    | nullable                                           |
| match_date    | TEXT    | NOT NULL                                           |
| created_at    | TEXT    | NOT NULL DEFAULT CURRENT_TIMESTAMP                 |

---

## ER Diagram Description

```
teams (1) ──────── (N) players (1) ──── (N) gears
  │
  │ (N)
  │
match_results (N) ──── (1) tournaments
```

- **One Team** has **many Players** (1:N)
- **One Player** has **many Gear entries** (1:N)
- **One Team** participates in **many Match Results** (1:N)
- **One Tournament** has **many Match Results** (1:N)
- `match_results` is a bridge table connecting teams and tournaments with outcome data

---

## SQL Query Examples

### 1. Get all teams with player count
```sql
SELECT t.id, t.name, t.game_title, t.country, t.ranking,
       COUNT(p.id) AS player_count
FROM teams t
LEFT JOIN players p ON p.team_id = t.id
GROUP BY t.id
ORDER BY t.ranking ASC;
```

### 2. Win rate per team
```sql
SELECT t.name,
       COUNT(CASE WHEN mr.result = 'WIN' THEN 1 END) AS wins,
       COUNT(CASE WHEN mr.result = 'LOSS' THEN 1 END) AS losses,
       COUNT(mr.id) AS total_matches,
       ROUND(
           COUNT(CASE WHEN mr.result = 'WIN' THEN 1 END) * 100.0 / COUNT(mr.id), 1
       ) AS win_rate_pct
FROM teams t
LEFT JOIN match_results mr ON mr.team_id = t.id
GROUP BY t.id
HAVING total_matches > 0
ORDER BY win_rate_pct DESC;
```

### 3. Players with above-average KDA
```sql
SELECT p.name, p.role, t.name AS team, p.kda
FROM players p
JOIN teams t ON t.id = p.team_id
WHERE p.kda > (SELECT AVG(kda) FROM players)
ORDER BY p.kda DESC;
```

### 4. Tournaments sorted by prize pool with match count
```sql
SELECT tn.name, tn.prize_pool, tn.location, tn.organizer,
       COUNT(mr.id) AS matches_played
FROM tournaments tn
LEFT JOIN match_results mr ON mr.tournament_id = tn.id
GROUP BY tn.id
ORDER BY tn.prize_pool DESC;
```

### 5. Recent match results with full JOIN
```sql
SELECT mr.match_date, t.name AS team_name, mr.opponent,
       tn.name AS tournament_name, mr.result, mr.score, mr.mvp
FROM match_results mr
JOIN teams t        ON t.id  = mr.team_id
JOIN tournaments tn ON tn.id = mr.tournament_id
ORDER BY mr.match_date DESC, mr.id DESC
LIMIT 10;
```

### 6. Gear inventory by brand
```sql
SELECT g.brand, COUNT(*) AS gear_count,
       GROUP_CONCAT(p.name, ', ') AS players
FROM gears g
JOIN players p ON p.id = g.player_id
GROUP BY g.brand
ORDER BY gear_count DESC;
```

---

## Seed Data Summary

The `seed_data.py` script inserts the following records:

| Table          | Records | Details                                          |
|----------------|---------|--------------------------------------------------|
| teams          | 8       | Team Liquid, Cloud9, FaZe Clan, NaVi, T1, Fnatic, G2, 100T |
| players        | 20      | Roles: IGL, AWPer, Rifler, Support, Mid-laner, ADC, etc. |
| gears          | 15      | Brands: Logitech, Razer, SteelSeries, Zowie, Finalmouse, HyperX |
| tournaments    | 6       | ESL Pro League, IEM Katowice, BLAST Premier, PGL Major, Worlds, VCT Champions |
| match_results  | 18      | Spread across all 6 tournaments                  |
| **TOTAL**      | **67**  |                                                  |

---

## Project Report

### Objectives
This mini-project demonstrates:
1. Relational database schema design with proper normalization (3NF)
2. Implementation of PRIMARY KEY, FOREIGN KEY, CHECK, NOT NULL, and DEFAULT constraints
3. Multi-table JOIN queries (INNER JOIN, LEFT JOIN) for aggregated reporting
4. Full CRUD operations through a web interface using parameterized SQL queries
5. Referential integrity enforcement via ON DELETE CASCADE foreign keys

### Database Normalization
- **1NF**: All attributes are atomic; no repeating groups
- **2NF**: All non-key attributes depend on the whole primary key (no partial dependencies since all PKs are single-column surrogates)
- **3NF**: No transitive dependencies — e.g., team info is stored once in `teams`, referenced by FK in `players` and `match_results`

### Security Considerations
- All SQL queries use `?` parameterized placeholders — immune to SQL injection
- `sqlite3.IntegrityError` is caught and displayed as user-friendly flash messages
- No raw string formatting is used in any database query

### Relational Integrity
- `PRAGMA foreign_keys = ON` is set on every connection
- `ON DELETE CASCADE` ensures orphan records are never left behind
- `CHECK(result IN ('WIN','LOSS','DRAW'))` enforces domain constraints at the database level

### Flask Architecture
- Application context (`g`) manages a single DB connection per request
- `@app.teardown_appcontext` closes connections after each request
- `sqlite3.Row` factory allows dict-style column access in templates
- All routes follow RESTful conventions (GET for display, POST for mutation)

---

## File Structure

```
D:\wqqeq\
├── app.py              # Flask application with all routes
├── init_db.py          # Database initialization script
├── seed_data.py        # Sample data seeder
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── database.db         # SQLite database (auto-created)
├── sql/
│   └── schema.sql      # CREATE TABLE statements
├── static/
│   ├── css/custom.css  # Dark theme + custom styles
│   └── js/main.js      # Confirm dialogs, debounce search, UX
└── templates/
    ├── layout.html     # Base layout with sidebar
    ├── dashboard.html  # Stats overview page
    ├── teams/          # index, create, edit
    ├── players/        # index, create, edit
    ├── gears/          # index, create, edit
    ├── tournaments/    # index, create, edit
    └── results/        # index, create, edit
```
