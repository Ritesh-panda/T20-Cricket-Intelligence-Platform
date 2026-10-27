"""Script to enrich player metadata in data/cricket_intel.db.

Extracts canonical full names, batting styles, and bowling styles from
the official 2024 ICC Men's T20 World Cup squads dataset and updates
the players table.
"""
import json
import re
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path("data/cricket_intel.db")
SQUADS_HTML = Path("data/raw/editorial/2024_Men's_T20_World_Cup_squads.html")

# Explicit overrides for unusual initials / nicknames
EXPLICIT_OVERRIDES = {
    "A Johnson": {"full_name": "Aaron Johnson", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "A Nortje": {"full_name": "Anrich Nortje", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "A Zampa": {"full_name": "Adam Zampa", "batting_style": "Right-handed", "bowling_style": "Right-arm leg break"},
    "AD Russell": {"full_name": "Andre Russell", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "AGS Gous": {"full_name": "Andries Gous", "batting_style": "Right-handed", "bowling_style": "None (Specialist Batter / Wicketkeeper)"},
    "AJ Hosein": {"full_name": "Akeal Hosein", "batting_style": "Left-handed", "bowling_style": "Slow left-arm orthodox"},
    "AK Markram": {"full_name": "Aiden Markram", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "AR Patel": {"full_name": "Axar Patel", "batting_style": "Left-handed", "bowling_style": "Slow left-arm orthodox"},
    "AS Joseph": {"full_name": "Alzarri Joseph", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "AU Rashid": {"full_name": "Adil Rashid", "batting_style": "Right-handed", "bowling_style": "Right-arm leg break"},
    "BA King": {"full_name": "Brandon King", "batting_style": "Right-handed", "bowling_style": "None (Specialist Batter)"},
    "KR Mayers": {"full_name": "Kyle Mayers", "batting_style": "Left-handed", "bowling_style": "Right-arm medium"},
    "OC McCoy": {"full_name": "Obed McCoy", "batting_style": "Left-handed", "bowling_style": "Left-arm fast medium"},
    "N Dutta": {"full_name": "Nikhil Dutta", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "Harmeet Singh": {"full_name": "Harmeet Singh", "batting_style": "Left-handed", "bowling_style": "Slow left-arm orthodox"},
    "RG Sharma": {"full_name": "Rohit Sharma", "batting_style": "Right-handed", "bowling_style": "Right-arm off spin"},
    "V Kohli": {"full_name": "Virat Kohli", "batting_style": "Right-handed", "bowling_style": "Right-arm medium"},
    "RR Pant": {"full_name": "Rishabh Pant", "batting_style": "Left-handed", "bowling_style": "None (Wicketkeeper)"},
    "SA Yadav": {"full_name": "Suryakumar Yadav", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "HH Pandya": {"full_name": "Hardik Pandya", "batting_style": "Right-handed", "bowling_style": "Right-arm medium fast"},
    "RA Jadeja": {"full_name": "Ravindra Jadeja", "batting_style": "Left-handed", "bowling_style": "Slow left-arm orthodox"},
    "S Dube": {"full_name": "Shivam Dube", "batting_style": "Left-handed", "bowling_style": "Right-arm medium"},
    "Kuldeep Yadav": {"full_name": "Kuldeep Yadav", "batting_style": "Left-handed", "bowling_style": "Left-arm wrist spin (Chinaman)"},
    "Arshdeep Singh": {"full_name": "Arshdeep Singh", "batting_style": "Left-handed", "bowling_style": "Left-arm medium fast"},
    "JJ Bumrah": {"full_name": "Jasprit Bumrah", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "Q de Kock": {"full_name": "Quinton de Kock", "batting_style": "Left-handed", "bowling_style": "None (Wicketkeeper)"},
    "H Klaasen": {"full_name": "Heinrich Klaasen", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "DA Miller": {"full_name": "David Miller", "batting_style": "Left-handed", "bowling_style": "Right-arm off break"},
    "M Jansen": {"full_name": "Marco Jansen", "batting_style": "Right-handed", "bowling_style": "Left-arm fast"},
    "KA Maharaj": {"full_name": "Keshav Maharaj", "batting_style": "Right-handed", "bowling_style": "Slow left-arm orthodox"},
    "K Rabada": {"full_name": "Kagiso Rabada", "batting_style": "Left-handed", "bowling_style": "Right-arm fast"},
    "T Shamsi": {"full_name": "Tabraiz Shamsi", "batting_style": "Right-handed", "bowling_style": "Left-arm wrist spin (Chinaman)"},
    "JC Buttler": {"full_name": "Jos Buttler", "batting_style": "Right-handed", "bowling_style": "None (Wicketkeeper)"},
    "PD Salt": {"full_name": "Phil Salt", "batting_style": "Right-handed", "bowling_style": "None (Wicketkeeper)"},
    "JM Bairstow": {"full_name": "Jonny Bairstow", "batting_style": "Right-handed", "bowling_style": "None (Wicketkeeper / Batter)"},
    "HC Brook": {"full_name": "Harry Brook", "batting_style": "Right-handed", "bowling_style": "Right-arm medium"},
    "MM Ali": {"full_name": "Moeen Ali", "batting_style": "Left-handed", "bowling_style": "Right-arm off break"},
    "SM Curran": {"full_name": "Sam Curran", "batting_style": "Left-handed", "bowling_style": "Left-arm medium fast"},
    "CJ Jordan": {"full_name": "Chris Jordan", "batting_style": "Right-handed", "bowling_style": "Right-arm fast medium"},
    "Jofra Archer": {"full_name": "Jofra Archer", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "RA Topley": {"full_name": "Reece Topley", "batting_style": "Right-handed", "bowling_style": "Left-arm fast medium"},
    "Babar Azam": {"full_name": "Babar Azam", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "Mohammad Rizwan": {"full_name": "Mohammad Rizwan", "batting_style": "Right-handed", "bowling_style": "None (Wicketkeeper)"},
    "Fakhar Zaman": {"full_name": "Fakhar Zaman", "batting_style": "Left-handed", "bowling_style": "Slow left-arm orthodox"},
    "Shadab Khan": {"full_name": "Shadab Khan", "batting_style": "Right-handed", "bowling_style": "Right-arm leg break"},
    "Iftikhar Ahmed": {"full_name": "Iftikhar Ahmed", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "Shaheen Shah Afridi": {"full_name": "Shaheen Shah Afridi", "batting_style": "Left-handed", "bowling_style": "Left-arm fast"},
    "Naseem Shah": {"full_name": "Naseem Shah", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "Haris Rauf": {"full_name": "Haris Rauf", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "Mohammad Amir": {"full_name": "Mohammad Amir", "batting_style": "Left-handed", "bowling_style": "Left-arm fast"},
    "TM Head": {"full_name": "Travis Head", "batting_style": "Left-handed", "bowling_style": "Right-arm off break"},
    "DA Warner": {"full_name": "David Warner", "batting_style": "Left-handed", "bowling_style": "Right-arm leg break"},
    "MR Marsh": {"full_name": "Mitchell Marsh", "batting_style": "Right-handed", "bowling_style": "Right-arm medium"},
    "GJ Maxwell": {"full_name": "Glenn Maxwell", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "MP Stoinis": {"full_name": "Marcus Stoinis", "batting_style": "Right-handed", "bowling_style": "Right-arm medium"},
    "TH David": {"full_name": "Tim David", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "MS Wade": {"full_name": "Matthew Wade", "batting_style": "Left-handed", "bowling_style": "None (Wicketkeeper)"},
    "PJ Cummins": {"full_name": "Pat Cummins", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "MA Starc": {"full_name": "Mitchell Starc", "batting_style": "Left-handed", "bowling_style": "Left-arm fast"},
    "JR Hazlewood": {"full_name": "Josh Hazlewood", "batting_style": "Left-handed", "bowling_style": "Right-arm fast medium"},
    "Shakib Al Hasan": {"full_name": "Shakib Al Hasan", "batting_style": "Left-handed", "bowling_style": "Slow left-arm orthodox"},
    "Mustafizur Rahman": {"full_name": "Mustafizur Rahman", "batting_style": "Left-handed", "bowling_style": "Left-arm fast medium"},
    "Taskin Ahmed": {"full_name": "Taskin Ahmed", "batting_style": "Left-handed", "bowling_style": "Right-arm fast"},
    "Tanzid Hasan": {"full_name": "Tanzid Hasan", "batting_style": "Left-handed", "bowling_style": "None (Specialist Batter)"},
    "Towhid Hridoy": {"full_name": "Towhid Hridoy", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "Mahmudullah": {"full_name": "Mahmudullah", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "Litton Das": {"full_name": "Litton Das", "batting_style": "Right-handed", "bowling_style": "None (Wicketkeeper)"},
    "Rishad Hossain": {"full_name": "Rishad Hossain", "batting_style": "Right-handed", "bowling_style": "Right-arm leg break"},
    "Tanzim Hasan Sakib": {"full_name": "Tanzim Hasan Sakib", "batting_style": "Right-handed", "bowling_style": "Right-arm fast medium"},
    "Monank Patel": {"full_name": "Monank Patel", "batting_style": "Right-handed", "bowling_style": "None (Wicketkeeper / Captain)"},
    "Aaron Jones": {"full_name": "Aaron Jones", "batting_style": "Right-handed", "bowling_style": "Right-arm leg break"},
    "Steven Taylor": {"full_name": "Steven Taylor", "batting_style": "Left-handed", "bowling_style": "Right-arm off break"},
    "Corey Anderson": {"full_name": "Corey Anderson", "batting_style": "Left-handed", "bowling_style": "Left-arm medium fast"},
    "Saurabh Netravalkar": {"full_name": "Saurabh Netravalkar", "batting_style": "Right-handed", "bowling_style": "Left-arm fast medium"},
    "Ali Khan": {"full_name": "Ali Khan", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"},
    "Jasdeep Singh": {"full_name": "Jasdeep Singh", "batting_style": "Right-handed", "bowling_style": "Right-arm medium"},
    "Nosthush Kenjige": {"full_name": "Nosthush Kenjige", "batting_style": "Right-handed", "bowling_style": "Slow left-arm orthodox"},
    "Shayan Jahangir": {"full_name": "Shayan Jahangir", "batting_style": "Right-handed", "bowling_style": "None (Wicketkeeper)"},
    "Nitish Kumar": {"full_name": "Nitish Kumar", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
    "Milind Kumar": {"full_name": "Milind Kumar", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
}

def clean_style(text: str) -> str:
    text = text.strip()
    if text in ['—', '-', '–', 'N/a', 'N/A', '', 'None']:
        return 'None (Specialist Batter)'
    text = text.replace('Right-armfast', 'Right-arm fast')
    text = text.replace('Right-armmedium', 'Right-arm medium')
    text = text.replace('Left-armfast', 'Left-arm fast')
    text = text.replace('Left-armmedium', 'Left-arm medium')
    text = text.replace('Right-armoff', 'Right-arm off')
    text = text.replace('Right-armleg', 'Right-arm leg')
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    return text

def parse_squads() -> list:
    if not SQUADS_HTML.exists():
        return []
    with open(SQUADS_HTML, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    squads_players = []
    for t in soup.find_all('table', class_='wikitable'):
        for tr in t.find_all('tr')[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if len(cells) >= 5:
                raw_name = cells[1]
                name_clean = re.sub(r'\s*\([^)]*\)', '', raw_name).strip()
                bat = clean_style(cells[3])
                bowl = clean_style(cells[4])
                squads_players.append({
                    'full_name': name_clean,
                    'batting_style': bat,
                    'bowling_style': bowl
                })
    return squads_players

def enrich_all_players():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    squads_players = parse_squads()
    c.execute("SELECT player_id, full_name, primary_team_id, aliases_json FROM players")
    players = c.fetchall()

    updated = 0
    for p in players:
        p_id = p["player_id"]
        current_name = p["full_name"]
        aliases = json.loads(p["aliases_json"]) if p["aliases_json"] else []

        # Check explicit overrides first
        if current_name in EXPLICIT_OVERRIDES:
            info = EXPLICIT_OVERRIDES[current_name]
        else:
            # Fuzzy match surname and initial against Wikipedia squads
            parts = current_name.split()
            surname = parts[-1].lower()
            initial = parts[0][0].lower() if parts else ""
            info = None
            for sp in squads_players:
                sp_parts = sp["full_name"].split()
                sp_surname = sp_parts[-1].lower()
                sp_initial = sp_parts[0][0].lower() if sp_parts else ""
                if surname == sp_surname and (initial == sp_initial or len(parts) == 1):
                    info = sp
                    break

        if info:
            new_full_name = info["full_name"]
            bat_style = info["batting_style"]
            bowl_style = info["bowling_style"]

            # Add abbreviated current name to aliases if not present
            if current_name not in aliases:
                aliases.append(current_name)
            if new_full_name not in aliases:
                aliases.append(new_full_name)

            if not bowl_style or "n/a" in bowl_style.lower() or "\ufffd" in bowl_style:
                bowl_style = "None (Specialist Batter)"

            c.execute("""
                UPDATE players
                SET full_name = ?, batting_style = ?, bowling_style = ?, aliases_json = ?
                WHERE player_id = ?
            """, (new_full_name, bat_style, bowl_style, json.dumps(list(set(aliases))), p_id))
            updated += 1
        else:
            # Fallback formatting if somehow not in squads
            formatted_name = current_name
            bat_style = "Right-handed"
            bowl_style = "Right-arm medium"
            c.execute("""
                UPDATE players
                SET full_name = ?, batting_style = ?, bowling_style = ?
                WHERE player_id = ?
            """, (formatted_name, bat_style, bowl_style, p_id))

    conn.commit()
    print(f"Enrichment Complete: Successfully enriched {updated} of {len(players)} players in database!")

    # Verify a few
    c.execute("SELECT full_name, batting_style, bowling_style, aliases_json FROM players ORDER BY full_name LIMIT 10")
    for r in c.fetchall():
        print(f"  {r['full_name']:<25} | Bat: {r['batting_style']:<15} | Bowl: {r['bowling_style']:<30}")

    conn.close()

if __name__ == "__main__":
    enrich_all_players()
