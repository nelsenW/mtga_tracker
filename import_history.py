import json
from mtga_database import MTGADatabase


def import_historical_data(jsonl_file):
    db = MTGADatabase()
    db.connect()

    print("Importing historical data...")
    print(f"Source: {jsonl_file}")
    print()

    matches_imported = 0
    economy_imported = 0
    active_matches = {}
    user_id = None

    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                if 'matchGameRoomStateChangedEvent' in data:
                    event = data['matchGameRoomStateChangedEvent']
                    game_room = event['gameRoomInfo']
                    match_id = game_room['gameRoomConfig']['matchId']
                    state_type = game_room.get('stateType', '')
                    timestamp = int(data.get('timestamp', 0))

                    if state_type == 'MatchGameRoomStateType_Playing':
                        config = game_room['gameRoomConfig']
                        players = config.get('reservedPlayers', [])
                        
                        if len(players) == 2:
                            player_data = None
                            opponent_data = None
                            
                            for player in players:
                                if player.get('playerName') == 'apollyon' or player.get('teamId') == 2:
                                    player_data = player
                                    if not user_id:
                                        user_id = player['userId']
                                        db.set_user_id(user_id)
                                        print(f" User detected: {player['playerName']} ({user_id})")
                                else:
                                    opponent_data = player
                            
                            if not player_data:
                                player_data = players[1] if opponent_data == players[0] else players[0]
                            if not opponent_data:
                                opponent_data = players[0] if player_data == players[1] else players[1]
                            
                            match_data = {
                                'match_id': match_id,
                                'event_id': player_data.get('eventId'),
                                'opponent_name': opponent_data.get('playerName'),
                                'opponent_user_id': opponent_data.get('userId'),
                                'player_team_id': player_data.get('teamId'),
                                'opponent_team_id': opponent_data.get('teamId'),
                                'start_timestamp': timestamp
                            }
                            
                            active_matches[match_id] = match_data
                            db.insert_match_start(match_data)
                    
                    elif state_type == 'MatchGameRoomStateType_MatchCompleted':
                        if match_id in active_matches:
                            match_start = active_matches[match_id]
                            final_result = game_room.get('finalMatchResult', {})
                            result_list = final_result.get('resultList', [])
                            
                            match_result = None
                            games_won = 0
                            games_lost = 0
                            
                            for result in result_list:
                                if result['scope'] == 'MatchScope_Match':
                                    match_result = result
                                elif result['scope'] == 'MatchScope_Game':
                                    if result['winningTeamId'] == match_start['player_team_id']:
                                        games_won += 1
                                    else:
                                        games_lost += 1
                            
                            if match_result:
                                if match_result['winningTeamId'] == match_start['player_team_id']:
                                    result = 'win'
                                else:
                                    result = 'loss'
                            else:
                                result = 'unknown'
                            
                            duration = (timestamp - match_start['start_timestamp']) // 1000
                            
                            match_data = {
                                'match_id': match_id,
                                'end_timestamp': timestamp,
                                'result': result,
                                'games_won': games_won,
                                'games_lost': games_lost,
                                'duration_seconds': duration
                            }
                            
                            db.update_match_completion(match_data)
                            matches_imported += 1
                            
                            result_emoji = "" if result == 'win' else ""
                            print(f"{result_emoji} Match {matches_imported}: {result.upper()} vs "
                                  f"{match_start['opponent_name']} ({games_won}-{games_lost})")
                            
                            del active_matches[match_id]
                
                elif 'InventoryInfo' in data:
                    inv = data['InventoryInfo']
                    
                    if economy_imported == 0:
                        boosters_total = sum(b.get('Count', 0) for b in inv.get('Boosters', []))
                        
                        economy_data = {
                            'timestamp': int(data.get('timestamp', 0)) if 'timestamp' in data else 0,
                            'gems': inv.get('Gems'),
                            'gold': inv.get('Gold'),
                            'vault_progress': inv.get('TotalVaultProgress'),
                            'wc_common': inv.get('WildCardCommons'),
                            'wc_uncommon': inv.get('WildCardUnCommons'),
                            'wc_rare': inv.get('WildCardRares'),
                            'wc_mythic': inv.get('WildCardMythics'),
                            'boosters_total': boosters_total
                        }
                        
                        db.insert_economy_snapshot(economy_data)
                        economy_imported += 1
                        print(f" Economy snapshot: {economy_data['gold']}g / {economy_data['gems']}")
            
            except json.JSONDecodeError:
                print(f" Skipping invalid JSON at line {line_num}")
            except Exception as e:
                print(f" Error processing line {line_num}: {e}")
    
    print()
    print("=" * 60)
    print(f"Import complete!")
    print(f"  Matches imported: {matches_imported}")
    print(f"  Economy snapshots: {economy_imported}")
    print(f"  Active matches (incomplete): {len(active_matches)}")
    print("=" * 60)
    
    db.close()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
    else:
        jsonl_file = '/mnt/user-data/uploads/match_events.jsonl'
    
    import_historical_data(jsonl_file)
