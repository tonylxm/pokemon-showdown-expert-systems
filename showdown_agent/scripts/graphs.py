import os
import re
from collections import Counter, defaultdict
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

# --- CONFIG ---
FOLDER = r'C:\Users\HP\Documents\2025_University\COMPSYS_726\showdown_agent\showdown_agent\scripts\replays'
PLAYER_TAG = 'p1a:'  # Your agent's moves start with this in the logs

TEAM_MOVES = {
    'Spikes': 'hazard',
    'Thunder Wave': 'status',
    'Taunt': 'anti-setup',
    'Psycho Boost': 'attack',
    'Swords Dance': 'setup',
    'Kowtow Cleave': 'attack',
    'Iron Head': 'attack',
    'Sucker Punch': 'attack',
    'Calm Mind': 'setup',
    'Judgment': 'attack',
    'Recover': 'healing',
    'Dynamax Cannon': 'attack',
    'Sludge Bomb': 'attack',
    'Fire Blast': 'attack',
    'Meteor Beam': 'attack',
    'Scale Shot': 'attack',
    'Close Combat': 'attack',
    'Flame Charge': 'attack',
    'U-turn': 'pivot',
    'Brave Bird': 'attack',
    'Sacred Fire': 'attack',
    'Earthquake': 'attack'
}

def classify_move(move):
    if move in TEAM_MOVES:
        return TEAM_MOVES[move]
    if move == 'switch':
        return 'switching'
    return 'other'

def is_super_effective(line):
    return "supereffective|p2" in line

def is_ko(line):
    # KO lines: |faint|p2a: ... (opponent fainted)
    return re.match(r'\|faint\|p2a:', line)

def is_hazard(move):
    return TEAM_MOVES.get(move, '') == 'hazard'

def extract_moves_from_html(filepath):
    with open(filepath, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    script = soup.find('script', {'class': 'battle-log-data'})
    if not script:
        return []
    log = script.string
    moves = []
    for line in log.split('\n'):
        # Look for lines like: |move|p1a: Kingambit|Sucker Punch|p2a: Bronzong
        m = re.match(r'\|move\|'+re.escape(PLAYER_TAG)+r'[^|]*\|([^|]+)', line)
        if m:
            move = m.group(1)
            moves.append(move)
        # Look for switches: |switch|p1a: Eternatus|Eternatus|452/452
        elif re.match(r'\|switch\|'+re.escape(PLAYER_TAG), line):
            moves.append('switch')
    return moves

def main():
    move_counter = Counter()
    type_counter = Counter()
    total_turns = 0
    total_battles = 0
    total_super_effective = 0
    total_kos = 0
    total_hazards = 0
    total_switches = 0

    for root, dirs, files in os.walk(FOLDER):
        for fname in files:
            if fname.endswith('.html'):
                fpath = os.path.join(root, fname)
                moves = extract_moves_from_html(fpath)
                move_counter.update(moves)
                for move in moves:
                    move_type = classify_move(move)
                    type_counter[move_type] += 1

                # Parse the log for stats
                with open(fpath, encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                script = soup.find('script', {'class': 'battle-log-data'})
                if not script:
                    continue
                log = script.string
                lines = log.split('\n')

                turns = sum(1 for line in lines if line.startswith('|turn|'))
                super_effective = sum(1 for line in lines if is_super_effective(line))
                kos = sum(1 for line in lines if is_ko(line))
                hazards = sum(1 for move in moves if is_hazard(move))
                switches = sum(1 for move in moves if move == 'switch')

                total_turns += turns
                total_super_effective += super_effective
                total_kos += kos
                total_hazards += hazards
                total_switches += switches
                total_battles += 1

    # Print statistics
    if total_battles > 0:
        print(f"Avg turns per battle: {total_turns / total_battles:.2f}")
        print(f"Super-effective moves per battle: {total_super_effective / total_battles:.2f}")
        print(f"KO moves per battle: {total_kos / total_battles:.2f}")
        print(f"Hazards set per battle: {total_hazards / total_battles:.2f}")
        print(f"Switches per battle: {total_switches / total_battles:.2f}")
    else:
        print("No battles found.")

    # Plot move frequency (excluding "switch")
    filtered_moves = [(move, count) for move, count in move_counter.items() if move != 'switch']
    if filtered_moves:
        moves, freqs = zip(*sorted(filtered_moves, key=lambda x: -x[1]))
        plt.figure(figsize=(12, 6))
        plt.bar(moves, freqs)
        plt.title('Move Frequency')
        plt.xlabel('Move')
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    # Plot move type frequency (keep "switching"), ordered descending
    plt.figure(figsize=(8, 5))
    sorted_types = sorted(type_counter.items(), key=lambda x: -x[1])
    types, freqs = zip(*sorted_types)
    plt.bar(types, freqs, color='orange')
    plt.title('Move Type Frequency')
    plt.xlabel('Move Type')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()