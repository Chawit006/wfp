"""
seed.py — Auto-seeding module for E-Sports Manager
CS104 Introduction to Database

Inserts realistic demo data into all tables on first run.
Completely safe: checks before inserting, never overwrites existing data,
rolls back on any error.
"""

import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _connect():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _is_empty(conn, table: str) -> bool:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


# ---------------------------------------------------------------------------
# Data insertion — one function per table
# ---------------------------------------------------------------------------

def _seed_teams(conn):
    """10 real-world pro esports organisations with accurate game titles."""
    rows = [
        # name             game_title   country         coach                   ranking  sponsor
        ('T1',             'Valorant',  'South Korea',  'Kim "Control" Minsuk',      1,  'Red Bull'),
        ('Gen.G',          'Valorant',  'South Korea',  'Park "Dexter" Sanghyun',    2,  'Samsung'),
        ('Fnatic',         'Valorant',  'United Kingdom','Louis "roeJ" Holm',         3,  'BMW'),
        ('Team Liquid',    'Valorant',  'Netherlands',  'Ben "mini" Harris',          4,  'Monster Energy'),
        ('Paper Rex',      'Valorant',  'Singapore',    'Alexandre "alecks" Sallé',  5,  'HP OMEN'),
        ('Sentinels',      'Valorant',  'United States','Adam "kaplan" Kaplan',       6,  'Red Bull'),
        ('DRX',            'Valorant',  'South Korea',  'Jung "termi" Yunsik',        7,  'Kia'),
        ('NAVI',           'CS2',       'Ukraine',      'Andrei "B1ad3" Gorodenskiy', 8,  'GG.BET'),
        ('G2 Esports',     'CS2',       'Germany',      'Ratan "ratz" Abzalov',       9,  'Logitech G'),
        ('LOUD',           'Valorant',  'Brazil',       'Nicholas "envy" Cannone',   10,  'Lenovo Legion'),
    ]
    conn.executemany(
        "INSERT INTO teams (name, game_title, country, coach, ranking, sponsor) "
        "VALUES (?,?,?,?,?,?)",
        rows,
    )


def _seed_players(conn):
    """30 players — 3 per team, covering all roles."""
    # Build name→id map after teams are committed inside the transaction
    tid = {r[0]: r[1] for r in conn.execute("SELECT name, id FROM teams").fetchall()}

    rows = [
        # name              age  role        team_id            kda     salary    join_date
        # ── T1 ────────────────────────────────────────────────────────────────────────
        ('stax',            24,  'IGL',      tid['T1'],         2.45,  18000.00, '2022-01-15'),
        ('GuardiaN',        23,  'Sniper',   tid['T1'],         2.88,  22000.00, '2022-01-15'),
        ('Meteor',          22,  'Support',  tid['T1'],         1.95,  15000.00, '2022-06-01'),
        # ── Gen.G ─────────────────────────────────────────────────────────────────────
        ('Rb',              23,  'Duelist',  tid['Gen.G'],      3.12,  24000.00, '2022-03-10'),
        ('Lakia',           25,  'IGL',      tid['Gen.G'],      2.30,  19000.00, '2022-03-10'),
        ('k1Ng',            22,  'Flex',     tid['Gen.G'],      2.10,  16000.00, '2022-08-01'),
        # ── Fnatic ────────────────────────────────────────────────────────────────────
        ('Boaster',         27,  'IGL',      tid['Fnatic'],     1.85,  17500.00, '2021-05-01'),
        ('Derke',           22,  'Duelist',  tid['Fnatic'],     3.45,  28000.00, '2021-05-01'),
        ('Magnum',          23,  'Support',  tid['Fnatic'],     1.70,  14000.00, '2022-01-20'),
        # ── Team Liquid ───────────────────────────────────────────────────────────────
        ('Jamppi',          24,  'Duelist',  tid['Team Liquid'],2.78,  20000.00, '2022-04-01'),
        ('ScreaM',          29,  'Flex',     tid['Team Liquid'],2.55,  22000.00, '2022-04-01'),
        ('L1NK',            23,  'IGL',      tid['Team Liquid'],1.92,  16500.00, '2022-09-01'),
        # ── Paper Rex ─────────────────────────────────────────────────────────────────
        ('f0rsakeN',        22,  'Duelist',  tid['Paper Rex'],  3.20,  21000.00, '2022-02-15'),
        ('Benkai',          24,  'IGL',      tid['Paper Rex'],  2.05,  17000.00, '2022-02-15'),
        ('Jinggg',          23,  'Duelist',  tid['Paper Rex'],  2.95,  23000.00, '2022-06-15'),
        # ── Sentinels ─────────────────────────────────────────────────────────────────
        ('TenZ',            23,  'Duelist',  tid['Sentinels'],  3.05,  30000.00, '2021-03-01'),
        ('Shahzam',         25,  'IGL',      tid['Sentinels'],  1.88,  18000.00, '2021-03-01'),
        ('SicK',            23,  'Support',  tid['Sentinels'],  1.75,  16000.00, '2021-07-01'),
        # ── DRX ───────────────────────────────────────────────────────────────────────
        ('BuZz',            21,  'Duelist',  tid['DRX'],        2.65,  17000.00, '2022-05-01'),
        ('MaKo',            23,  'Support',  tid['DRX'],        1.98,  15500.00, '2022-05-01'),
        ('Foxy9',           24,  'IGL',      tid['DRX'],        2.12,  16000.00, '2022-11-01'),
        # ── NAVI ──────────────────────────────────────────────────────────────────────
        ('s1mple',          26,  'Sniper',   tid['NAVI'],       3.78,  45000.00, '2016-08-01'),
        ('b1t',             20,  'Rifler',   tid['NAVI'],       2.55,  22000.00, '2021-01-01'),
        ('electroNic',      26,  'IGL',      tid['NAVI'],       2.15,  25000.00, '2018-05-01'),
        # ── G2 Esports ────────────────────────────────────────────────────────────────
        ('NiKo',            26,  'Rifler',   tid['G2 Esports'], 3.12,  38000.00, '2021-06-01'),
        ('m0NESY',          18,  'Sniper',   tid['G2 Esports'], 3.55,  32000.00, '2022-01-01'),
        ('Hooxi',           24,  'IGL',      tid['G2 Esports'], 1.82,  19000.00, '2022-06-01'),
        # ── LOUD ──────────────────────────────────────────────────────────────────────
        ('Less',            21,  'Duelist',  tid['LOUD'],       2.42,  16000.00, '2022-03-01'),
        ('Saadhak',         23,  'IGL',      tid['LOUD'],       2.18,  17500.00, '2022-03-01'),
        ('tuyz',            22,  'Support',  tid['LOUD'],       1.92,  14500.00, '2022-07-01'),
    ]
    conn.executemany(
        "INSERT INTO players (name, age, role, team_id, kda, salary, join_date) "
        "VALUES (?,?,?,?,?,?,?)",
        rows,
    )


def _seed_gears(conn):
    """30 gear entries — 1 realistic peripheral setup per player."""
    pid = {r[0]: r[1] for r in conn.execute("SELECT name, id FROM players").fetchall()}

    rows = [
        # mouse                              keyboard                     headset                        monitor                        brand         player_id
        # ── T1 — Razer ───────────────────────────────────────────────────────────────────────────────
        ('Razer Viper V3 Pro',             'Razer Huntsman V2 TKL',    'Razer BlackShark V2 Pro',     'BenQ XL2546K',                'Razer',      pid['stax']),
        ('Razer Viper V3 Pro',             'Razer Huntsman V3 Pro',    'Razer BlackShark V2 Pro',     'BenQ XL2546K',                'Razer',      pid['GuardiaN']),
        ('Razer DeathAdder V3 Pro',        'Razer Huntsman Mini',      'Razer Kraken V3 Pro',         'BenQ XL2546K',                'Razer',      pid['Meteor']),
        # ── Gen.G — Logitech ─────────────────────────────────────────────────────────────────────────
        ('Logitech G Pro X Superlight 2',  'Logitech G Pro X Keyboard','Logitech G Pro X Headset',    'Alienware AW2521HF',          'Logitech',   pid['Rb']),
        ('Logitech G Pro X Superlight 2',  'Logitech G Pro X Keyboard','Logitech G Pro X Headset',    'Alienware AW2521HF',          'Logitech',   pid['Lakia']),
        ('Logitech G Pro X Superlight',    'Logitech G815 TKL',        'Logitech G Pro X Headset',    'Alienware AW2521HF',          'Logitech',   pid['k1Ng']),
        # ── Fnatic — SteelSeries ─────────────────────────────────────────────────────────────────────
        ('SteelSeries Sensei Ten',         'SteelSeries Apex Pro',     'SteelSeries Arctis Nova Pro', 'BenQ XL2540K',                'SteelSeries',pid['Boaster']),
        ('SteelSeries Aerox 9 Wireless',   'SteelSeries Apex 9 Mini',  'SteelSeries Arctis Nova Pro', 'BenQ XL2540K',                'SteelSeries',pid['Derke']),
        ('SteelSeries Rival 5',            'SteelSeries Apex Pro',     'SteelSeries Arctis 9X',       'BenQ XL2540K',                'SteelSeries',pid['Magnum']),
        # ── Team Liquid — Zowie ──────────────────────────────────────────────────────────────────────
        ('Zowie EC2-CW',                   'Ducky One 3 SF',           'HyperX Cloud Alpha',          'AOC AG251FZ2E',               'Zowie',      pid['Jamppi']),
        ('Zowie EC3-CW',                   'Wooting 60HE',             'SteelSeries Arctis Nova Pro', 'AOC AG251FZ2E',               'Zowie',      pid['ScreaM']),
        ('Zowie S2-CW',                    'Ducky One 2 Mini',         'HyperX Cloud Stinger 2',      'AOC AG251FZ2E',               'Zowie',      pid['L1NK']),
        # ── Paper Rex — Finalmouse ───────────────────────────────────────────────────────────────────
        ('Finalmouse UltralightX',         'Wooting 60HE',             'SteelSeries Arctis Nova Pro', 'LG UltraGear 27GN750-B',      'Finalmouse', pid['f0rsakeN']),
        ('Logitech G Pro X Superlight 2',  'Logitech G Pro X Keyboard','Logitech G Pro X Headset',    'LG UltraGear 27GN750-B',      'Logitech',   pid['Benkai']),
        ('Finalmouse Starlight Pro',        'Wooting 60HE',             'HyperX Cloud Alpha',          'LG UltraGear 27GN750-B',      'Finalmouse', pid['Jinggg']),
        # ── Sentinels — HyperX ───────────────────────────────────────────────────────────────────────
        ('HyperX Pulsefire Haste 2',       'HyperX Alloy Origins 65',  'HyperX Cloud Alpha S',        'Asus ROG Swift PG259QN',      'HyperX',     pid['TenZ']),
        ('Logitech G Pro X Superlight 2',  'Corsair K65 Mini',         'HyperX Cloud II',             'Asus ROG Swift PG259QN',      'Logitech',   pid['Shahzam']),
        ('Razer Viper V2 Pro',             'Razer Huntsman V2',        'HyperX Cloud Stinger 2',      'Asus ROG Swift PG259QN',      'Razer',      pid['SicK']),
        # ── DRX — Logitech ───────────────────────────────────────────────────────────────────────────
        ('Logitech G Pro X Superlight 2',  'Logitech G Pro X Keyboard','Logitech G Pro X Headset',    'BenQ XL2540K',                'Logitech',   pid['BuZz']),
        ('Razer Viper V3 Pro',             'Razer Huntsman V2 TKL',    'Razer BlackShark V2 Pro',     'BenQ XL2540K',                'Razer',      pid['MaKo']),
        ('Logitech G303 Shroud Edition',   'Logitech G915 TKL',        'Logitech G Pro X Headset',    'BenQ XL2540K',                'Logitech',   pid['Foxy9']),
        # ── NAVI — Zowie ─────────────────────────────────────────────────────────────────────────────
        ('Zowie EC2-CW',                   'Ducky One 3 Mini',         'HyperX Cloud Alpha',          'BenQ XL2546K',                'Zowie',      pid['s1mple']),
        ('Logitech G Pro X Superlight 2',  'Logitech G Pro X Keyboard','Logitech G Pro X Headset',    'BenQ XL2546K',                'Logitech',   pid['b1t']),
        ('SteelSeries Rival 650',          'SteelSeries Apex Pro',     'SteelSeries Arctis Pro',      'BenQ XL2546K',                'SteelSeries',pid['electroNic']),
        # ── G2 Esports — Logitech ────────────────────────────────────────────────────────────────────
        ('Logitech G Pro X Superlight 2',  'Logitech G Pro X Keyboard','Logitech G Pro X Headset',    'BenQ XL2540K',                'Logitech',   pid['NiKo']),
        ('Logitech G Pro X Superlight 2',  'Logitech G Pro X Keyboard','Logitech G Pro X Headset',    'Alienware AW2521HF',          'Logitech',   pid['m0NESY']),
        ('SteelSeries Aerox 5 Wireless',   'SteelSeries Apex 9 Mini',  'SteelSeries Arctis Nova Pro', 'Alienware AW2521HF',          'SteelSeries',pid['Hooxi']),
        # ── LOUD — Razer ─────────────────────────────────────────────────────────────────────────────
        ('Razer Viper V3 HyperSpeed',      'Razer Huntsman V2',        'Razer BlackShark V2',         'Lenovo Legion Y25-25',        'Razer',      pid['Less']),
        ('Razer DeathAdder V3',            'Razer Huntsman Mini',      'Razer Kraken V3',             'Lenovo Legion Y25-25',        'Razer',      pid['Saadhak']),
        ('Razer Viper V2 Pro',             'Razer BlackWidow V4 75%',  'Razer BlackShark V2 Pro',     'Lenovo Legion Y25-25',        'Razer',      pid['tuyz']),
    ]
    conn.executemany(
        "INSERT INTO gears (mouse, keyboard, headset, monitor, brand, player_id) "
        "VALUES (?,?,?,?,?,?)",
        rows,
    )


def _seed_tournaments(conn):
    """5 major tier-1 esports tournaments."""
    rows = [
        # name                               prize_pool  location                start_date    end_date      organizer
        ('VCT 2024 Champions',              1_000_000,  'Seoul, South Korea',  '2024-08-01', '2024-08-25', 'Riot Games'),
        ('VCT 2024 Masters Shanghai',         500_000,  'Shanghai, China',     '2024-05-10', '2024-05-19', 'Riot Games'),
        ('VCT 2024 Americas Kickoff',         200_000,  'São Paulo, Brazil',   '2024-01-15', '2024-01-21', 'Riot Games'),
        ('BLAST Premier World Final 2024',  1_000_000,  'Abu Dhabi, UAE',      '2024-12-11', '2024-12-15', 'BLAST'),
        ('IEM Katowice 2025',               1_000_000,  'Katowice, Poland',    '2025-02-05', '2025-02-16', 'ESL'),
    ]
    conn.executemany(
        "INSERT INTO tournaments (name, prize_pool, location, start_date, end_date, organizer) "
        "VALUES (?,?,?,?,?,?)",
        rows,
    )


def _seed_match_results(conn):
    """62 realistic match results across all 5 tournaments and all 10 teams."""
    tid  = {r[0]: r[1] for r in conn.execute("SELECT name, id FROM teams").fetchall()}
    tnid = {r[0]: r[1] for r in conn.execute("SELECT name, id FROM tournaments").fetchall()}

    T1   = tid['T1']
    GENG = tid['Gen.G']
    FNC  = tid['Fnatic']
    TL   = tid['Team Liquid']
    PRX  = tid['Paper Rex']
    SEN  = tid['Sentinels']
    DRX  = tid['DRX']
    NAVI = tid['NAVI']
    G2   = tid['G2 Esports']
    LO   = tid['LOUD']

    CHAMP   = tnid['VCT 2024 Champions']
    MASTERS = tnid['VCT 2024 Masters Shanghai']
    AMKICK  = tnid['VCT 2024 Americas Kickoff']
    BLAST   = tnid['BLAST Premier World Final 2024']
    IEM     = tnid['IEM Katowice 2025']

    # (team_id, tournament_id, opponent, result, score, mvp, match_date)
    rows = [
        # ── VCT 2024 Champions — Group Stage ────────────────────────────────────────
        (T1,   CHAMP, 'Fnatic',        'WIN',  '2-0', 'stax',       '2024-08-05'),
        (T1,   CHAMP, 'Sentinels',     'WIN',  '2-1', 'GuardiaN',   '2024-08-07'),
        (T1,   CHAMP, 'LOUD',          'WIN',  '2-0', 'GuardiaN',   '2024-08-09'),
        (FNC,  CHAMP, 'T1',            'LOSS', '0-2', 'Derke',      '2024-08-05'),
        (FNC,  CHAMP, 'Paper Rex',     'WIN',  '2-1', 'Derke',      '2024-08-07'),
        (FNC,  CHAMP, 'DRX',           'WIN',  '2-0', 'Boaster',    '2024-08-09'),
        (GENG, CHAMP, 'DRX',           'WIN',  '2-0', 'Rb',         '2024-08-05'),
        (GENG, CHAMP, 'Sentinels',     'WIN',  '2-1', 'Rb',         '2024-08-07'),
        (GENG, CHAMP, 'Paper Rex',     'LOSS', '1-2', 'Lakia',      '2024-08-09'),
        (PRX,  CHAMP, 'Sentinels',     'WIN',  '2-0', 'f0rsakeN',   '2024-08-05'),
        (PRX,  CHAMP, 'Fnatic',        'LOSS', '1-2', 'Jinggg',     '2024-08-07'),
        (PRX,  CHAMP, 'Gen.G',         'WIN',  '2-1', 'f0rsakeN',   '2024-08-09'),
        (SEN,  CHAMP, 'Paper Rex',     'LOSS', '0-2', 'TenZ',       '2024-08-05'),
        (SEN,  CHAMP, 'Gen.G',         'LOSS', '1-2', 'Shahzam',    '2024-08-07'),
        (DRX,  CHAMP, 'Gen.G',         'LOSS', '0-2', 'BuZz',       '2024-08-05'),
        (DRX,  CHAMP, 'Fnatic',        'LOSS', '0-2', 'MaKo',       '2024-08-09'),
        (LO,   CHAMP, 'T1',            'LOSS', '0-2', 'Less',       '2024-08-09'),
        # ── VCT 2024 Champions — Playoffs ───────────────────────────────────────────
        (T1,   CHAMP, 'Gen.G',         'WIN',  '2-1', 'stax',       '2024-08-15'),
        (T1,   CHAMP, 'Paper Rex',     'WIN',  '2-0', 'GuardiaN',   '2024-08-20'),
        (T1,   CHAMP, 'Fnatic',        'WIN',  '2-1', 'stax',       '2024-08-25'),
        (FNC,  CHAMP, 'Paper Rex',     'LOSS', '0-2', 'Derke',      '2024-08-18'),
        (GENG, CHAMP, 'DRX',           'WIN',  '2-0', 'Rb',         '2024-08-14'),
        (GENG, CHAMP, 'T1',            'LOSS', '1-2', 'Lakia',      '2024-08-15'),
        (PRX,  CHAMP, 'Fnatic',        'WIN',  '2-0', 'f0rsakeN',   '2024-08-18'),
        (PRX,  CHAMP, 'T1',            'LOSS', '0-2', 'Jinggg',     '2024-08-20'),
        # ── VCT 2024 Masters Shanghai ────────────────────────────────────────────────
        (T1,   MASTERS, 'LOUD',        'WIN',  '2-1', 'GuardiaN',   '2024-05-11'),
        (T1,   MASTERS, 'Gen.G',       'WIN',  '2-0', 'stax',       '2024-05-13'),
        (T1,   MASTERS, 'Sentinels',   'DRAW', '1-1', 'stax',       '2024-05-15'),
        (T1,   MASTERS, 'Fnatic',      'WIN',  '2-1', 'GuardiaN',   '2024-05-17'),
        (GENG, MASTERS, 'T1',          'LOSS', '0-2', 'Rb',         '2024-05-13'),
        (GENG, MASTERS, 'Paper Rex',   'WIN',  '2-0', 'Lakia',      '2024-05-11'),
        (GENG, MASTERS, 'DRX',         'WIN',  '2-1', 'Rb',         '2024-05-15'),
        (FNC,  MASTERS, 'Sentinels',   'WIN',  '2-0', 'Derke',      '2024-05-11'),
        (FNC,  MASTERS, 'T1',          'LOSS', '1-2', 'Boaster',    '2024-05-17'),
        (PRX,  MASTERS, 'Gen.G',       'LOSS', '0-2', 'f0rsakeN',   '2024-05-11'),
        (PRX,  MASTERS, 'DRX',         'WIN',  '2-1', 'Jinggg',     '2024-05-13'),
        (SEN,  MASTERS, 'Fnatic',      'LOSS', '0-2', 'TenZ',       '2024-05-11'),
        (SEN,  MASTERS, 'T1',          'DRAW', '1-1', 'Shahzam',    '2024-05-15'),
        (DRX,  MASTERS, 'Gen.G',       'LOSS', '1-2', 'BuZz',       '2024-05-15'),
        (DRX,  MASTERS, 'Paper Rex',   'LOSS', '1-2', 'MaKo',       '2024-05-13'),
        (LO,   MASTERS, 'T1',          'LOSS', '1-2', 'Less',       '2024-05-11'),
        # ── VCT 2024 Americas Kickoff — TL, SEN, LOUD ───────────────────────────────
        (TL,   AMKICK, 'Sentinels',    'WIN',  '2-0', 'Jamppi',     '2024-01-16'),
        (TL,   AMKICK, 'LOUD',         'WIN',  '2-1', 'ScreaM',     '2024-01-18'),
        (TL,   AMKICK, 'Sentinels',    'WIN',  '2-1', 'Jamppi',     '2024-01-20'),
        (SEN,  AMKICK, 'Team Liquid',  'LOSS', '0-2', 'TenZ',       '2024-01-16'),
        (SEN,  AMKICK, 'LOUD',         'WIN',  '2-1', 'Shahzam',    '2024-01-18'),
        (SEN,  AMKICK, 'Team Liquid',  'LOSS', '1-2', 'TenZ',       '2024-01-20'),
        (LO,   AMKICK, 'Team Liquid',  'LOSS', '1-2', 'Saadhak',    '2024-01-18'),
        (LO,   AMKICK, 'Sentinels',    'LOSS', '1-2', 'Less',       '2024-01-19'),
        # ── BLAST Premier World Final 2024 — NAVI, G2 ───────────────────────────────
        (NAVI, BLAST, 'G2 Esports',    'WIN',  '16-10', 's1mple',   '2024-12-12'),
        (NAVI, BLAST, 'FaZe Clan',     'WIN',  '2-0',   's1mple',   '2024-12-13'),
        (NAVI, BLAST, 'G2 Esports',    'WIN',  '16-8',  'b1t',      '2024-12-15'),
        (G2,   BLAST, 'NAVI',          'LOSS', '10-16', 'NiKo',     '2024-12-12'),
        (G2,   BLAST, 'Cloud9',        'WIN',  '16-12', 'm0NESY',   '2024-12-13'),
        (G2,   BLAST, 'NAVI',          'LOSS', '8-16',  'NiKo',     '2024-12-15'),
        # ── IEM Katowice 2025 — NAVI, G2 ────────────────────────────────────────────
        (NAVI, IEM,   'G2 Esports',    'WIN',  '2-1',  's1mple',    '2025-02-07'),
        (NAVI, IEM,   'Heroic',        'WIN',  '16-9', 'b1t',       '2025-02-10'),
        (NAVI, IEM,   'Vitality',      'WIN',  '16-11','electroNic', '2025-02-12'),
        (NAVI, IEM,   'G2 Esports',    'LOSS', '0-2',  'electroNic','2025-02-14'),
        (G2,   IEM,   'NAVI',          'LOSS', '1-2',  'm0NESY',    '2025-02-07'),
        (G2,   IEM,   'Vitality',      'WIN',  '2-0',  'NiKo',      '2025-02-09'),
        (G2,   IEM,   'Heroic',        'WIN',  '16-7', 'm0NESY',    '2025-02-11'),
        (G2,   IEM,   'NAVI',          'WIN',  '2-0',  'm0NESY',    '2025-02-14'),
    ]
    conn.executemany(
        "INSERT INTO match_results "
        "(team_id, tournament_id, opponent, result, score, mvp, match_date) "
        "VALUES (?,?,?,?,?,?,?)",
        rows,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def seed_if_empty():
    conn = _connect()
    cursor = conn.cursor()

    print("SEED RUNNING")

    cursor.execute("SELECT COUNT(*) FROM teams")
    count = cursor.fetchone()[0]

    print("TEAM COUNT =", count)

    if count == 0:
        cursor.execute("""
            INSERT INTO teams
            (name, game_title, country, coach, ranking, sponsor)
            VALUES
            ('T1', 'Valorant', 'Korea', 'kkOma', 1, 'Red Bull')
        """)

        print("INSERT SUCCESS")

    conn.commit()
    conn.close()
    print(os.path.abspath(DATABASE))
