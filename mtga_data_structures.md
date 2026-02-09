# MTGA Log Parser - Data Structure Analysis

## Event Overview (2823 events captured)

### 1. Match Events - `matchGameRoomStateChangedEvent`

#### Match Start Event
```json
{
  "matchGameRoomStateChangedEvent": {
    "gameRoomInfo": {
      "gameRoomConfig": {
        "matchId": "bbd58bf5-40e7-4318-b786-e34621544ee3",
        "reservedPlayers": [
          {
            "userId": "XMIGUPBQHFEP5OXD4PI5WPDOAQ",
            "playerName": "hio",
            "systemSeatId": 1,
            "teamId": 1,
            "platformId": "AndroidPhone",
            "eventId": "Constructed_Event_2026"
          },
          {
            "userId": "HBSDKMZ3NZC5FF536MSLZF4TGA",
            "playerName": "apollyon",
            "systemSeatId": 2,
            "teamId": 2,
            "platformId": "SteamWindows",
            "eventId": "Constructed_Event_2026"
          }
        ]
      },
      "stateType": "MatchGameRoomStateType_Playing"
    }
  }
}
```

#### Match Completion Event
```json
{
  "matchGameRoomStateChangedEvent": {
    "gameRoomInfo": {
      "stateType": "MatchGameRoomStateType_MatchCompleted",
      "finalMatchResult": {
        "matchId": "bbd58bf5-40e7-4318-b786-e34621544ee3",
        "matchCompletedReason": "MatchCompletedReasonType_Success",
        "resultList": [
          {
            "scope": "MatchScope_Game",
            "result": "ResultType_WinLoss",
            "winningTeamId": 1,
            "reason": "ResultReason_Game"
          },
          {
            "scope": "MatchScope_Match",
            "result": "ResultType_WinLoss",
            "winningTeamId": 1,
            "reason": "ResultReason_Game"
          }
        ]
      }
    }
  }
}
```

**Key Fields for Database:**
- `matchId`: Unique identifier
- `timestamp`: Match start/end time
- `playerName`: Opponent name
- `eventId`: Event type (Constructed_Event_2026, etc.)
- `teamId`: Player's team (need to track which is user)
- `winningTeamId`: Winner determination
- `resultList`: Game-by-game results

### 2. Game State Events - `greToClientEvent`

Contains detailed game state information:
- Card plays
- Zone changes
- Turn progression
- Game objects

**Note:** Very verbose, may not need to store unless building detailed replay functionality.

### 3. Inventory/Economy Events - `InventoryInfo`

```json
{
  "InventoryInfo": {
    "SeqId": 1,
    "Gems": 1070,
    "Gold": 455,
    "TotalVaultProgress": 548,
    "wcTrackPosition": 20,
    "WildCardCommons": 204,
    "WildCardUnCommons": 205,
    "WildCardMythics": 4,
    "CustomTokens": {
      "BonusPackProgress": 1,
      "PlayInToken": 15,
      "Token_JumpIn": 2
    },
    "Boosters": [
      {
        "CollationId": 100058,
        "SetCode": "ECL",
        "Count": 1
      }
    ]
  }
}
```

**Key Fields for Database:**
- `Gems`, `Gold`: Currency
- `WildCard*`: Wildcard counts
- `Boosters`: Pack inventory
- `CustomTokens`: Event tokens
- Track changes over time for economy analysis

### 4. Draft Events - `DraftStatus`

```json
{
  "CurrentModule": "BotDraft",
  "Payload": {
    "EventName": "QuickDraft_OM1_20260209",
    "DraftStatus": "PickNext",
    "PackNumber": 0,
    "PickNumber": 0,
    "NumCardsToPick": 2,
    "DraftPack": ["97874", "97931", "97831", ...],
    "PickedCards": []
  }
}
```

**Key Fields for Database:**
- `EventName`: Draft event identifier
- `PackNumber`, `PickNumber`: Draft position
- `DraftPack`: Available cards (card IDs)
- `PickedCards`: User selections
- Track full draft for analysis

## Database Schema Design

### matches Table
```sql
CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT UNIQUE NOT NULL,
    event_id TEXT,
    opponent_name TEXT,
    opponent_user_id TEXT,
    player_team_id INTEGER,
    start_timestamp INTEGER,
    end_timestamp INTEGER,
    result TEXT, -- 'win', 'loss', 'draw'
    games_won INTEGER,
    games_lost INTEGER,
    duration_seconds INTEGER
);
```

### economy_snapshots Table
```sql
CREATE TABLE economy_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    gems INTEGER,
    gold INTEGER,
    vault_progress INTEGER,
    wc_common INTEGER,
    wc_uncommon INTEGER,
    wc_rare INTEGER,
    wc_mythic INTEGER,
    boosters_total INTEGER
);
```

### drafts Table
```sql
CREATE TABLE drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    draft_id TEXT UNIQUE,
    start_timestamp INTEGER,
    end_timestamp INTEGER,
    wins INTEGER,
    losses INTEGER,
    deck_cards TEXT -- JSON array of card IDs
);
```

### draft_picks Table
```sql
CREATE TABLE draft_picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id TEXT NOT NULL,
    pack_number INTEGER,
    pick_number INTEGER,
    card_id TEXT,
    available_cards TEXT, -- JSON array
    timestamp INTEGER,
    FOREIGN KEY (draft_id) REFERENCES drafts(draft_id)
);
```

## Implementation Priority

### Phase 2A: Core Match Tracking (NEXT)
1. Create SQLite database schema
2. Extract match start/completion events
3. Determine player's teamId (from userId comparison)
4. Store match results with win/loss
5. Calculate match duration

### Phase 2B: Economy Tracking
1. Parse InventoryInfo events
2. Store periodic snapshots
3. Calculate changes over time

### Phase 2C: Draft Tracking
1. Parse DraftStatus events
2. Track draft progression
3. Store pick-by-pick data

### Phase 2D: Advanced Features
1. Deck tracking (if available in logs)
2. Win rate by event type
3. Economy efficiency metrics
4. Draft pick analytics

## User Identification

**Critical:** Need to identify which teamId belongs to the user (apollyon in this case).
- Solution: Look for userId "HBSDKMZ3NZC5FF536MSLZF4TGA" in reservedPlayers
- User's playerName: "apollyon"
- Store user_id in config or detect on first match
