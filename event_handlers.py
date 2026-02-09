import json


class MTGAEventHandlers:

    def handle_match_event(self, data):
        print(f"Match event: {json.dumps(data, indent=2)}")

    def handle_draft_event(self, data):
        print(f"Draft event: {json.dumps(data, indent=2)}")

    def handle_collection_event(self, data):
        print(f"Collection event: {json.dumps(data, indent=2)}")

    def handle_gre_message(self, msg):
        msg_type = msg.get('type', 'unknown')

        if msg_type == 'GREMessageType_GameStateMessage':
            print(f"[Game State Update], {msg}")
        elif msg_type == 'GREMessageType_QueuedGameStateMessage':
            print(f"[Queued State]")
        elif msg_type == 'GREMessageType_UIMessage':
            print(f"[UI Message]")
        else:
            print(f"[GRE Message] Type: {msg_type}")

    def handle_connection_event(self, data):
        status = data.get('status', 'unknown')
        host = data.get('host', 'unknown')
        port = data.get('port', 'unknown')
        print(f"[Connection] Status: {status}, Host: {host}:{port}")

    def handle_connection_close_event(self, data):
        close_type = data.get('closeType', 'unknown')
        reason = data.get('reason', 'unknown')
        print(f"[Connection Close] Type: {close_type}, Reason: {reason}")

    def handle_state_change_event(self, data):
        old_state = data.get('old', 'unknown')
        new_state = data.get('new', 'unknown')
        print(f"[State Change] {old_state} -> {new_state}")

    def handle_request_event(self, data):
        request_id = data.get('id', 'unknown')
        request_type = data.get('request', 'unknown')
        print(f"[Request] ID: {request_id}, Type: {request_type}")

    def handle_inventory_update_event(self, data):
        updates = []
        if 'InventoryInfo' in data:
            updates.append('Inventory')
        if 'DeckSummariesV2' in data or 'Decks' in data:
            updates.append('Decks')
        if 'SystemMessages' in data:
            updates.append('Messages')
        print(f"[Inventory Update] {', '.join(updates)}")

    def handle_rank_event(self, data):
        if 'constructedSeasonOrdinal' in data:
            print(f"[Rank] Constructed: Class {data.get('constructedClass', '?')}, "
                  f"Level {data.get('constructedLevel', '?')}, "
                  f"Step {data.get('constructedStep', '?')}")
        if 'limitedSeasonOrdinal' in data:
            print(f"[Rank] Limited: Class {data.get('limitedClass', '?')}, "
                  f"Level {data.get('limitedLevel', '?')}")

    def handle_season_rank_event(self, data):
        season = data.get('currentSeason', 'unknown')
        print(f"[Season Rank] Season: {season}")

    def handle_mastery_event(self, data):
        node_count = len(data.get('NodeStates', []))
        milestone_count = len(data.get('MilestoneStates', []))
        print(f"[Mastery] Nodes: {node_count}, Milestones: {milestone_count}")

    def handle_courses_event(self, data):
        courses = data.get('Courses', [])
        print(f"[Courses] Available: {len(courses)}")

    def handle_course_entry_event(self, data):
        course = data.get('Course', {})
        course_id = course.get('InternalEventName', 'unknown') if isinstance(course, dict) else 'unknown'
        print(f"[Course Entry] Entered: {course_id}")

    def handle_scene_transition_event(self, data):
        from_scene = data.get('fromSceneName', 'unknown')
        to_scene = data.get('toSceneName', 'unknown')
        print(f"[Scene] {from_scene} -> {to_scene}")

    def handle_periodic_rewards_event(self, data):
        daily_seq = data.get('_dailyRewardSequenceId', 'unknown')
        weekly_seq = data.get('_weeklyRewardSequenceId', 'unknown')
        print(f"[Periodic Rewards] Daily: {daily_seq}, Weekly: {weekly_seq}")

    def handle_quest_event(self, data):
        quests = data.get('quests', [])
        can_swap = data.get('canSwap', False)
        print(f"[Quests] Active: {len(quests)}, Can Swap: {can_swap}")

    def handle_summaries_event(self, data):
        summaries = data.get('Summaries', [])
        print(f"[Event Summaries] Count: {len(summaries)}")

    def handle_module_payload_event(self, data):
        module = data.get('CurrentModule', 'unknown')
        has_payload = 'Payload' in data
        has_inventory = 'DTO_InventoryInfo' in data
        components = []
        if has_payload:
            components.append('Payload')
        if has_inventory:
            components.append('Inventory')
        print(f"[Module] {module} - {', '.join(components) if components else 'No data'}")

    def handle_course_deck_event(self, data):
        course_id = data.get('CourseId', 'unknown')
        event_name = data.get('InternalEventName', 'unknown')
        module = data.get('CurrentModule', 'unknown')

        has_deck = 'CourseDeck' in data
        has_card_pool = 'CardPool' in data

        deck_info = []
        if has_deck:
            deck = data.get('CourseDeck', {})
            if isinstance(deck, dict):
                main_deck = deck.get('MainDeck', [])
                sideboard = deck.get('Sideboard', [])
                deck_info.append(f"Main: {len(main_deck)}, Side: {len(sideboard)}")

        if has_card_pool:
            card_pool = data.get('CardPool', [])
            deck_info.append(f"Pool: {len(card_pool)}")

        deck_details = f" - {', '.join(deck_info)}" if deck_info else ""
        print(f"[Course Deck] {event_name} (Module: {module}){deck_details}")

    def handle_bundle_manifest_event(self, data):
        uri = data.get('fdURI', 'unknown')
        manifests = data.get('bundleManifests', [])
        print(f"[Bundle] URI: {uri}, Manifests: {len(manifests)}")

    def handle_creator_event(self, data):
        creator = data.get('creator', 'unknown')
        print(f"[Creator] {creator}")

    def handle_requested_type_event(self, data):
        requested_type = data.get('RequestedType', 'unknown')
        print(f"[Requested Type] {requested_type}")

    def handle_formats_event(self, data):
        formats = data.get('Formats', [])
        format_groups = data.get('FormatGroups', [])
        print(f"[Formats] Formats: {len(formats)}, Groups: {len(format_groups)}")

    def handle_matches_event(self, data):
        matches = data.get('MatchesV3', [])
        print(f"[Matches] Count: {len(matches)}")

    def handle_authenticate_response_event(self, data):
        transaction_id = data.get('transactionId', 'unknown')
        has_auth = 'authenticateResponse' in data
        print(f"[Auth Response] Transaction: {transaction_id[:8]}...")
