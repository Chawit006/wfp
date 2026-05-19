import sqlite3
import os
from init_db import init_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')


def seed():
    # Initialize fresh DB
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        # Idempotent: clear all tables in reverse dependency order
        cur.execute("DELETE FROM match_results")
        cur.execute("DELETE FROM gears")
        cur.execute("DELETE FROM players")
        cur.execute("DELETE FROM tournaments")
        cur.execute("DELETE FROM teams")
        # Reset auto-increment counters
        cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('match_results','gears','players','tournaments','teams')")
        conn.commit()
        print("Cleared existing data.")
    except Exception as e:
        print(f"Warning during clear: {e}")

    # ------------------------------------------------------------------
    # TEAMS  (8 records)
    # ------------------------------------------------------------------
    teams = [
        ("Team Liquid",    "CS2",               "United States",  "Adren",       1,  "Monster Energy"),
        ("Cloud9",         "CS2",               "United States",  "Rejin",       3,  "HyperX"),
        ("FaZe Clan",      "CS2",               "International",  "NEO",         2,  "Nissan"),
        ("Natus Vincere",  "CS2",               "Ukraine",        "B1ad3",       4,  "GG.BET"),
        ("T1",             "League of Legends", "South Korea",    "Kkoma",       1,  "BMW"),
        ("Fnatic",         "Valorant",          "United Kingdom", "boaster",     5,  "Monster Energy"),
        ("G2 Esports",     "CS2",               "Spain",          "Kassad",      6,  "Red Bull"),
        ("100 Thieves",    "Valorant",          "United States",  "Hiko",        7,  "Cash App"),
    ]
    cur.executemany(
        "INSERT INTO teams (name, game_title, country, coach, ranking, sponsor) VALUES (?,?,?,?,?,?)",
        teams
    )
    conn.commit()
    print(f"Inserted {len(teams)} teams.")

    # ------------------------------------------------------------------
    # PLAYERS  (20 records)
    # ------------------------------------------------------------------
    players = [
        # Team Liquid (id=1)
        ("nitr0",       27, "IGL",           1, 1.42, 25000.00, "2019-01-15"),
        ("EliGE",       25, "Rifler",         1, 1.18, 22000.00, "2019-03-10"),
        ("NAF",         26, "Rifler",         1, 1.21, 21000.00, "2018-07-22"),
        # Cloud9 (id=2)
        ("HooXi",       28, "IGL",           2, 1.05, 18000.00, "2022-05-01"),
        ("NiKo",        27, "Rifler",         2, 1.35, 30000.00, "2023-01-10"),
        # FaZe Clan (id=3)
        ("karrigan",    34, "IGL",           3, 1.11, 20000.00, "2017-04-18"),
        ("broky",       23, "AWPer",         3, 1.28, 24000.00, "2020-09-30"),
        ("rain",        29, "Entry Fragger", 3, 1.19, 22500.00, "2016-02-14"),
        # Natus Vincere (id=4)
        ("s1mple",      27, "AWPer",         4, 1.89, 50000.00, "2016-08-10"),
        ("electronic",  27, "Rifler",         4, 1.25, 28000.00, "2017-11-05"),
        ("Perfecto",    25, "Support",        4, 1.08, 16000.00, "2020-03-22"),
        # T1 (id=5)
        ("Faker",       28, "Mid-laner",     5, 8.50, 80000.00, "2013-01-17"),
        ("Gumayusi",    21, "ADC",           5, 7.20, 35000.00, "2022-01-10"),
        ("Keria",       22, "Support",       5, 6.90, 32000.00, "2022-01-10"),
        # Fnatic (id=6)
        ("Boaster",     27, "IGL",           6, 1.02, 15000.00, "2021-06-01"),
        ("Derke",       23, "Duelist",       6, 1.55, 22000.00, "2021-03-15"),
        # G2 Esports (id=7)
        ("m0NESY",      19, "AWPer",         7, 1.45, 26000.00, "2022-12-01"),
        ("jks",         27, "Rifler",         7, 1.17, 19000.00, "2022-07-20"),
        # 100 Thieves (id=8)
        ("Asuna",       21, "Entry Fragger", 8, 1.38, 18000.00, "2020-11-01"),
        ("bang",        27, "Support",       8, 1.12, 16000.00, "2021-02-15"),
    ]
    cur.executemany(
        "INSERT INTO players (name, age, role, team_id, kda, salary, join_date) VALUES (?,?,?,?,?,?,?)",
        players
    )
    conn.commit()
    print(f"Inserted {len(players)} players.")

    # ------------------------------------------------------------------
    # GEARS  (15 records) — assign by player_id 1–15
    # ------------------------------------------------------------------
    gears = [
        ("Logitech G Pro X Superlight", "Logitech G Pro X",       "Logitech G Pro X",        "BenQ XL2546K",  "Logitech",   1),
        ("Zowie EC2-C",                 "Ducky One 2 Mini",        "HyperX Cloud II",          "ASUS ROG Swift", "Zowie",     2),
        ("Razer DeathAdder V3",         "Razer Huntsman V2",       "Razer BlackShark V2",      "Alienware AW2523HF", "Razer", 3),
        ("SteelSeries Rival 5",         "SteelSeries Apex Pro",    "SteelSeries Arctis Pro",   "MSI Optix MAG274QRF", "SteelSeries", 4),
        ("Logitech G502 X",             "Corsair K95 RGB",         "Corsair HS80 RGB",         "LG 27GN950-B",  "Logitech",   5),
        ("Finalmouse Starlight-12",     "Leopold FC900R",          "Beyerdynamic DT 990 Pro",  "BenQ ZOWIE XL2411P", "Finalmouse", 6),
        ("Zowie FK1+",                  "Filco Majestouch 2",      "Sennheiser HD 560S",       "AOC C24G1",     "Zowie",       7),
        ("Razer Viper V2 Pro",          "Razer Huntsman Elite",    "Razer Kraken V3 Pro",      "Razer Raptor 27", "Razer",    8),
        ("Logitech G Pro X Superlight 2","Logitech G915 TKL",      "Logitech G Pro X Headset", "BenQ XL2546K",  "Logitech",   9),
        ("Zowie S2",                    "Ducky Shine 7",           "HyperX Cloud Alpha S",     "ASUS TUF Gaming VG27AQ", "Zowie", 10),
        ("SteelSeries Prime+",          "SteelSeries Apex 7",     "SteelSeries Arctis 7P",    "ViewSonic XG2705", "SteelSeries", 11),
        ("Razer Basilisk V3 Pro",       "Razer BlackWidow V3",     "Razer BlackShark V2 Pro",  "LG 27GP950-B",  "Razer",      12),
        ("Logitech G703",               "Corsair K70 RGB MK.2",   "Corsair Virtuoso RGB",     "MSI MEG342C",   "Logitech",   13),
        ("Finalmouse Air58 Ninja",      "Topre Realforce R2",      "Audio-Technica ATH-M50x",  "Alienware AW3423DW", "Finalmouse", 14),
        ("HyperX Pulsefire Haste",      "HyperX Alloy Origins Core","HyperX Cloud Stinger 2",  "HyperX Armada 25", "HyperX",  15),
    ]
    cur.executemany(
        "INSERT INTO gears (mouse, keyboard, headset, monitor, brand, player_id) VALUES (?,?,?,?,?,?)",
        gears
    )
    conn.commit()
    print(f"Inserted {len(gears)} gear entries.")

    # ------------------------------------------------------------------
    # TOURNAMENTS  (6 records)
    # ------------------------------------------------------------------
    tournaments = [
        ("ESL Pro League Season 19",  1000000.0, "Malta",              "2024-03-20", "2024-04-07", "ESL Gaming"),
        ("IEM Katowice 2024",          1000000.0, "Katowice, Poland",   "2024-01-31", "2024-02-11", "ESL Gaming"),
        ("BLAST Premier Spring 2024",   425000.0, "Copenhagen, Denmark","2024-01-22", "2024-01-28", "BLAST"),
        ("PGL Major Copenhagen 2024",  1250000.0, "Copenhagen, Denmark","2024-03-17", "2024-03-31", "PGL"),
        ("Worlds 2024",               2250000.0, "London, UK",          "2024-09-25", "2024-11-02", "Riot Games"),
        ("VCT Champions 2024",         2250000.0, "Seoul, South Korea",  "2024-08-01", "2024-08-25", "Riot Games"),
    ]
    cur.executemany(
        "INSERT INTO tournaments (name, prize_pool, location, start_date, end_date, organizer) VALUES (?,?,?,?,?,?)",
        tournaments
    )
    conn.commit()
    print(f"Inserted {len(tournaments)} tournaments.")

    # ------------------------------------------------------------------
    # MATCH RESULTS  (18 records)
    # ------------------------------------------------------------------
    results = [
        # ESL Pro League (tournament_id=1)
        (1, 1, "Cloud9",          "WIN",  "16-10", "EliGE",    "2024-03-22"),
        (1, 1, "FaZe Clan",       "LOSS", "12-16", "NAF",      "2024-03-25"),
        (2, 1, "Team Liquid",     "WIN",  "16-12", "NiKo",     "2024-03-22"),
        (3, 1, "G2 Esports",      "WIN",  "16-8",  "broky",    "2024-03-24"),
        (4, 1, "Fnatic",          "WIN",  "16-14", "s1mple",   "2024-03-23"),
        # IEM Katowice (tournament_id=2)
        (1, 2, "Natus Vincere",   "DRAW", "15-15", "nitr0",    "2024-02-01"),
        (2, 2, "FaZe Clan",       "WIN",  "16-11", "NiKo",     "2024-02-03"),
        (3, 2, "Cloud9",          "WIN",  "16-9",  "karrigan",  "2024-02-02"),
        (4, 2, "G2 Esports",      "LOSS", "10-16", "electronic","2024-02-04"),
        # BLAST Premier (tournament_id=3)
        (1, 3, "G2 Esports",      "WIN",  "2-0",   "EliGE",    "2024-01-23"),
        (7, 3, "Cloud9",          "WIN",  "2-1",   "m0NESY",   "2024-01-24"),
        (4, 3, "FaZe Clan",       "WIN",  "2-0",   "s1mple",   "2024-01-25"),
        # PGL Major (tournament_id=4)
        (3, 4, "Natus Vincere",   "WIN",  "2-1",   "broky",    "2024-03-20"),
        (1, 4, "FaZe Clan",       "LOSS", "0-2",   "NAF",      "2024-03-22"),
        (4, 4, "Team Liquid",     "WIN",  "2-0",   "s1mple",   "2024-03-25"),
        # Worlds 2024 (tournament_id=5)
        (5, 5, "Gen.G",           "WIN",  "3-1",   "Faker",    "2024-10-15"),
        # VCT Champions (tournament_id=6)
        (6, 6, "Sentinels",       "WIN",  "2-0",   "Derke",    "2024-08-05"),
        (8, 6, "Team Liquid",     "LOSS", "1-2",   "Asuna",    "2024-08-07"),
    ]
    cur.executemany(
        "INSERT INTO match_results (team_id, tournament_id, opponent, result, score, mvp, match_date) VALUES (?,?,?,?,?,?,?)",
        results
    )
    conn.commit()
    print(f"Inserted {len(results)} match results.")

    conn.close()
    print("\nSeed data inserted successfully! Total records:")
    print(f"  Teams:          {len(teams)}")
    print(f"  Players:        {len(players)}")
    print(f"  Gear entries:   {len(gears)}")
    print(f"  Tournaments:    {len(tournaments)}")
    print(f"  Match results:  {len(results)}")
    print(f"  TOTAL:          {len(teams)+len(players)+len(gears)+len(tournaments)+len(results)}")


if __name__ == '__main__':
    seed()
