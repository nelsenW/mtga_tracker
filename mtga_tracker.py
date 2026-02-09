import json
import time
import re
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
from mtga_database import MTGADatabase
from event_handlers import MTGAEventHandlers


class MTGALogParser(FileSystemEventHandler):
    def __init__(self, log_path, db):
        self.log_path = Path(log_path)
        self.db = db
        self.last_position = 0
        self.active_matches = {}
        self.user_id = self.db.get_user_id()
        self.handlers = MTGAEventHandlers()

        if self.log_path.exists():
            self.last_position = self.log_path.stat().st_size
            print(f"Starting from end of existing log (position: {self.last_position})")
    
    def on_modified(self, event):
        if event.src_path == str(self.log_path):
            self.parse_new_content()

    def parse_new_content(self):
        try:
            current_size = self.log_path.stat().st_size
            if current_size < self.last_position:
                print("Log file rotated, restarting from beginning")
                self.last_position = 0

            if current_size == self.last_position:
                return

            with open(self.log_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = current_size

            for line in new_content.split('\n'):
                if not line.strip():
                    continue
                self.process_log_line(line)

        except Exception as e:
            print(f"Error parsing log: {e}")

    def process_log_line(self, line):
        json_match = re.search(r'\{.*\}', line)
        if not json_match:
            return
        
        try:
            data = json.loads(json_match.group(0))
            self.handle_event(data)
        except json.JSONDecodeError:
            pass
    
    def handle_event(self, data):
        if 'matchGameRoomStateChangedEvent' in data:
            self.handle_match_event(data)
        elif 'InventoryInfo' in data:
            self.handle_inventory_event(data)
        elif 'DraftStatus' in data or 'CurrentModule' in data:
            self.handle_draft_event(data)
        elif 'greToClientEvent' in data:
            gre_event = data.get('greToClientEvent', {})
            if 'greToClientMessages' in gre_event:
                messages = gre_event['greToClientMessages']
                print(f'GRE Messages {len(messages)} messages')
                for msg in messages:
                    self.handlers.handle_gre_message(msg)
            else:
                print(f"GRE Event Keys: {list(gre_event.keys())}")
        elif 'transactionId' in data and 'authenticateResponse' in data:
            self.handlers.handle_authenticate_response_event(data)
        elif 'fdURI' in data and 'bundleManifests' in data:
            self.handlers.handle_bundle_manifest_event(data)
        elif 'creator' in data and len(data.keys()) == 1:
            self.handlers.handle_creator_event(data)
        elif 'RequestedType' in data and len(data.keys()) == 1:
            self.handlers.handle_requested_type_event(data)
        elif 'Formats' in data and 'FormatGroups' in data:
            self.handlers.handle_formats_event(data)
        elif 'MatchesV3' in data:
            self.handlers.handle_matches_event(data)
        elif 'CourseId' in data and 'InternalEventName' in data and 'CurrentModule' in data:
            self.handlers.handle_course_deck_event(data)
        elif 'CurrentModule' in data and ('Payload' in data or 'DTO_InventoryInfo' in data):
            self.handlers.handle_module_payload_event(data)
        elif 'status' in data and 'host' in data and 'port' in data:
            self.handlers.handle_connection_event(data)
        elif 'closeType' in data and 'reason' in data and 'tcpConn' in data:
            self.handlers.handle_connection_close_event(data)
        elif 'old' in data and 'new' in data:
            self.handlers.handle_state_change_event(data)
        elif 'id' in data and 'request' in data:
            self.handlers.handle_request_event(data)
        elif 'DeckSummariesV2' in data or 'Decks' in data:
            self.handlers.handle_inventory_update_event(data)
        elif 'constructedSeasonOrdinal' in data or 'limitedSeasonOrdinal' in data:
            self.handlers.handle_rank_event(data)
        elif 'currentSeason' in data and ('limitedRankInfo' in data or 'constructedRankInfo' in data):
            self.handlers.handle_season_rank_event(data)
        elif 'NodeStates' in data and 'MilestoneStates' in data:
            self.handlers.handle_mastery_event(data)
        elif 'Courses' in data:
            self.handlers.handle_courses_event(data)
        elif 'Course' in data and 'InventoryInfo' in data:
            self.handlers.handle_course_entry_event(data)
        elif 'fromSceneName' in data and 'toSceneName' in data:
            self.handlers.handle_scene_transition_event(data)
        elif '_dailyRewardSequenceId' in data and '_weeklyRewardSequenceId' in data:
            self.handlers.handle_periodic_rewards_event(data)
        elif 'canSwap' in data and 'quests' in data:
            self.handlers.handle_quest_event(data)
        elif 'Summaries' in data:
            self.handlers.handle_summaries_event(data)
        else:
            if data:
                print(f"Unhandled event type: {data.keys()}")
    
    def handle_match_event(self, data):
        event = data['matchGameRoomStateChangedEvent']
        game_room = event['gameRoomInfo']
        
        match_id = game_room['gameRoomConfig']['matchId']
        state_type = game_room.get('stateType', '')
        timestamp = int(data.get('timestamp', time.time() * 1000))

        if state_type == 'MatchGameRoomStateType_Playing':
            self.handle_match_start(match_id, game_room, timestamp)

        elif state_type == 'MatchGameRoomStateType_MatchCompleted':
            self.handle_match_completion(match_id, game_room, timestamp)

    def handle_match_start(self, match_id, game_room, timestamp):
        config = game_room['gameRoomConfig']
        players = config.get('reservedPlayers', [])

        if len(players) != 2:
            return

        player_data = None
        opponent_data = None

        for player in players:
            if self.user_id and player['userId'] == self.user_id:
                player_data = player
            else:
                if not self.user_id:
                    if player.get('teamId') == 2:
                        player_data = player
                        self.user_id = player['userId']
                        self.db.set_user_id(self.user_id)
                        print(f"Detected user: {player['playerName']} ({self.user_id})")
                    else:
                        opponent_data = player
                else:
                    opponent_data = player

        if not player_data:
            player_data = players[1] if players[0] == opponent_data else players[0]
        if not opponent_data:
            opponent_data = players[0] if players[1] == player_data else players[1]

        match_data = {
            'match_id': match_id,
            'event_id': player_data.get('eventId'),
            'opponent_name': opponent_data.get('playerName'),
            'opponent_user_id': opponent_data.get('userId'),
            'player_team_id': player_data.get('teamId'),
            'opponent_team_id': opponent_data.get('teamId'),
            'start_timestamp': timestamp
        }

        self.active_matches[match_id] = match_data
        self.db.insert_match_start(match_data)
        print(f"Match started: vs {match_data['opponent_name']} ({match_data['event_id']})")

    def handle_match_completion(self, match_id, game_room, timestamp):
        if match_id not in self.active_matches:
            print(f"Warning: Match completion for unknown match {match_id}")
            return

        match_start = self.active_matches[match_id]
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

        self.db.update_match_completion(match_data)
        print(f"Match completed: {result.upper()} vs {match_start['opponent_name']} ({games_won}-{games_lost}) [{duration}s]")

        del self.active_matches[match_id]

    def handle_inventory_event(self, data):
        inv = data['InventoryInfo']
        timestamp = int(time.time() * 1000)

        boosters_total = sum(b.get('Count', 0) for b in inv.get('Boosters', []))

        economy_data = {
            'timestamp': timestamp,
            'gems': inv.get('Gems'),
            'gold': inv.get('Gold'),
            'vault_progress': inv.get('TotalVaultProgress'),
            'wc_common': inv.get('WildCardCommons'),
            'wc_uncommon': inv.get('WildCardUnCommons'),
            'wc_rare': inv.get('WildCardRares'),
            'wc_mythic': inv.get('WildCardMythics'),
            'boosters_total': boosters_total
        }

        self.db.insert_economy_snapshot(economy_data)
        print(f"Economy update: {economy_data['gold']}g / {economy_data['gems']}gems")

    def handle_draft_event(self, data):
        if 'DraftStatus' in data.get('Payload', ''):
            print(f"Draft event detected (not yet tracked)")


def find_mtga_log():
    is_wsl = Path('/proc/version').exists() and 'microsoft' in Path('/proc/version').read_text().lower()

    if is_wsl:
        try:
            result = subprocess.run(
                ['cmd.exe', '/c', 'echo %USERNAME%'],
                capture_output=True,
                text=True,
                check=True
            )
            username = result.stdout.strip()
            log_path = Path(f'/mnt/c/Users/{username}/AppData/LocalLow/Wizards Of The Coast/MTGA/Player.log')
        except Exception as e:
            print(f"Error detecting Windows username: {e}")
            return None
    else:
        import os
        username = os.environ.get('USERNAME')
        log_path = Path(f'C:/Users/{username}/AppData/LocalLow/Wizards Of The Coast/MTGA/Player.log')

    return log_path if log_path.exists() else None


def main():
    print("MTGA Tracker - Enhanced Log Parser")
    print("=" * 50)

    log_path = find_mtga_log()
    if not log_path:
        print("ERROR: Could not find MTGA Player.log")
        print("Please ensure MTGA is installed and has been run at least once")
        return

    print(f"Found log file: {log_path}")

    db = MTGADatabase()
    db.connect()
    db.initialize_schema()

    user_id = db.get_user_id()
    if user_id:
        print(f"Tracking for user: {user_id}")
    else:
        print("User ID not set - will detect on first match")

    parser = MTGALogParser(log_path, db)

    observer = Observer()
    observer.schedule(parser, str(log_path.parent), recursive=False)
    observer.start()

    print("\nMonitoring log file for events...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(2)
            parser.parse_new_content()
    except KeyboardInterrupt:
        print("\nStopping log parser...")
        observer.stop()
        observer.join()
        db.close()
        print("Tracker stopped")


if __name__ == '__main__':
    main()
