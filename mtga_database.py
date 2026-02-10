import sqlite3
from pathlib import Path


class MTGADatabase:
    def __init__(self, db_path='mtga_tracker.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def initialize_schema(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT UNIQUE NOT NULL,
                event_id TEXT,
                opponent_name TEXT,
                opponent_user_id TEXT,
                player_team_id INTEGER,
                opponent_team_id INTEGER,
                start_timestamp INTEGER,
                end_timestamp INTEGER,
                result TEXT CHECK(result IN ('win', 'loss', 'draw', 'unknown')),
                games_won INTEGER DEFAULT 0,
                games_lost INTEGER DEFAULT 0,
                duration_seconds INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS economy_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                gems INTEGER,
                gold INTEGER,
                vault_progress INTEGER,
                wc_common INTEGER,
                wc_uncommon INTEGER,
                wc_rare INTEGER,
                wc_mythic INTEGER,
                boosters_total INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draft_id TEXT UNIQUE NOT NULL,
                event_name TEXT NOT NULL,
                start_timestamp INTEGER,
                end_timestamp INTEGER,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                deck_cards TEXT,
                status TEXT DEFAULT 'in_progress',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS draft_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draft_id TEXT NOT NULL,
                pack_number INTEGER,
                pick_number INTEGER,
                card_id TEXT,
                available_cards TEXT,
                timestamp INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (draft_id) REFERENCES drafts(draft_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_timestamp ON matches(start_timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_event ON matches(event_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_economy_timestamp ON economy_snapshots(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_draft_picks_draft_id ON draft_picks(draft_id)')
        
        self.conn.commit()
        print("Database schema initialized successfully")
    
    def get_user_id(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM config WHERE key = ?', ('user_id',))
        row = cursor.fetchone()
        return row['value'] if row else None
    
    def set_user_id(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('user_id', user_id))
        self.conn.commit()
    
    def insert_match_start(self, match_data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO matches (
                match_id, event_id, opponent_name, opponent_user_id,
                player_team_id, opponent_team_id, start_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_data['match_id'],
            match_data.get('event_id'),
            match_data.get('opponent_name'),
            match_data.get('opponent_user_id'),
            match_data.get('player_team_id'),
            match_data.get('opponent_team_id'),
            match_data.get('start_timestamp')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_match_completion(self, match_data):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE matches
            SET end_timestamp = ?,
                result = ?,
                games_won = ?,
                games_lost = ?,
                duration_seconds = ?
            WHERE match_id = ?
        ''', (
            match_data.get('end_timestamp'),
            match_data.get('result'),
            match_data.get('games_won', 0),
            match_data.get('games_lost', 0),
            match_data.get('duration_seconds'),
            match_data['match_id']
        ))
        self.conn.commit()
    
    def insert_economy_snapshot(self, economy_data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO economy_snapshots (
                timestamp, gems, gold, vault_progress,
                wc_common, wc_uncommon, wc_rare, wc_mythic, boosters_total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            economy_data.get('timestamp'),
            economy_data.get('gems'),
            economy_data.get('gold'),
            economy_data.get('vault_progress'),
            economy_data.get('wc_common'),
            economy_data.get('wc_uncommon'),
            economy_data.get('wc_rare'),
            economy_data.get('wc_mythic'),
            economy_data.get('boosters_total')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_match_stats(self, limit=20):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                match_id,
                event_id,
                opponent_name,
                result,
                datetime(start_timestamp/1000, 'unixepoch') as match_date,
                duration_seconds
            FROM matches
            WHERE end_timestamp IS NOT NULL
            ORDER BY start_timestamp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_win_rate(self, event_id=None):
        cursor = self.conn.cursor()
        if event_id:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_matches,
                    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses
                FROM matches
                WHERE event_id = ? AND result IN ('win', 'loss')
            ''', (event_id,))
        else:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_matches,
                    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses
                FROM matches
                WHERE result IN ('win', 'loss')
            ''')
        return cursor.fetchone()


if __name__ == '__main__':
    db = MTGADatabase()
    db.connect()
    db.initialize_schema()
    
    print("\nDatabase tables created:")
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for table in cursor.fetchall():
        print(f"  - {table['name']}")
    
    db.close()
    print("\nDatabase ready at: mtga_tracker.db")
