"""
MTGA Tracker - Stats Viewer
Display match statistics from the database
"""

from mtga_database import MTGADatabase
from datetime import datetime


def display_stats():
    db = MTGADatabase()
    db.connect()
    
    print("=" * 70)
    print("MTGA TRACKER - MATCH STATISTICS")
    print("=" * 70)
    
    # Overall win rate
    stats = db.get_win_rate()
    if stats and stats['total_matches'] > 0:
        total = stats['total_matches']
        wins = stats['wins']
        losses = stats['losses']
        win_rate = (wins / total * 100) if total > 0 else 0
        
        print(f"\n📊 OVERALL RECORD")
        print(f"   Wins: {wins} | Losses: {losses} | Total: {total}")
        print(f"   Win Rate: {win_rate:.1f}%")
    else:
        print("\n📊 No match data yet")
    
    # Recent matches
    print(f"\n🎮 RECENT MATCHES")
    print("-" * 70)
    matches = db.get_match_stats(limit=10)
    
    if matches:
        for match in matches:
            result_emoji = "✅" if match['result'] == 'win' else "❌"
            duration_min = match['duration_seconds'] // 60 if match['duration_seconds'] else 0
            
            print(f"{result_emoji} {match['result'].upper():4} vs {match['opponent_name']:20} "
                  f"[{match['event_id']:25}] {duration_min}m")
    else:
        print("No matches recorded yet")
    
    # Event-specific stats
    print(f"\n📈 STATS BY EVENT")
    print("-" * 70)
    
    cursor = db.conn.cursor()
    cursor.execute('''
        SELECT 
            event_id,
            COUNT(*) as total,
            SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses
        FROM matches
        WHERE result IN ('win', 'loss') AND event_id IS NOT NULL
        GROUP BY event_id
        ORDER BY total DESC
    ''')
    
    event_stats = cursor.fetchall()
    if event_stats:
        for stat in event_stats:
            total = stat['total']
            wins = stat['wins']
            win_rate = (wins / total * 100) if total > 0 else 0
            print(f"   {stat['event_id']:30} {wins:2}W-{stat['losses']:2}L ({win_rate:.1f}%)")
    else:
        print("No event data yet")
    
    # Economy snapshot
    print(f"\n💰 LATEST ECONOMY")
    print("-" * 70)
    cursor.execute('''
        SELECT * FROM economy_snapshots 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''')
    economy = cursor.fetchone()
    
    if economy:
        print(f"   Gold: {economy['gold']:,}")
        print(f"   Gems: {economy['gems']:,}")
        print(f"   Vault: {economy['vault_progress']}/1000")
        print(f"   Wildcards: C:{economy['wc_common']} U:{economy['wc_uncommon']} "
              f"R:{economy['wc_rare']} M:{economy['wc_mythic']}")
        print(f"   Boosters: {economy['boosters_total']}")
    else:
        print("No economy data yet")
    
    print("\n" + "=" * 70)
    
    db.close()


if __name__ == '__main__':
    display_stats()
