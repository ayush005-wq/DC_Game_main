"""
Trivia Game Client implementation.
Handles communication with the server and game logic.
"""
import socket
import threading
import json
import time
import xmlrpc.client


class TriviaGameClient:
    def __init__(self, player_id, server_host="localhost", socket_port=9997, rpc_port=8000):
        self.player_id = player_id
        self.server_host = server_host
        self.socket_port = socket_port
        self.rpc_port = rpc_port
        self.socket = None
        self.rpc_client = None

        # Game state
        self.current_question = None
        self.scores = {}
        self.token_status = {}
        self.time_warp_active = False
        self.time_warp_end = 0
        self.question_end_time = 0
        self.dark_mode = False

        # Callbacks for UI updates
        self.callbacks = {
            "on_question": None,
            "on_question_closed": None,
            "on_correct_answer": None,
            "on_wrong_answer": None,
            "on_scores_update": None,
            "on_hint": None,
            "on_token_status": None,
            "on_message": None,
            "on_time_warp_update": None
        }

        # Connect to the server
        self.connect()

    def connect(self):
        """Connect to the game server"""
        self.connect_socket()
        self.connect_rpc()

        # Start background threads
        threading.Thread(target=self.socket_listener, daemon=True).start()
        threading.Thread(target=self.update_scores_loop, daemon=True).start()
        threading.Thread(target=self.update_token_status_loop, daemon=True).start()
        threading.Thread(target=self.sync_clock_loop, daemon=True).start()

    def connect_socket(self):
        """Connect to the socket server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.socket_port))
            # Send player ID as first message
            self.socket.sendall(self.player_id.encode('utf-8'))
            print(f"Connected to socket server at {self.server_host}:{self.socket_port}")
            return True
        except Exception as e:
            print(f"Socket connection failed: {e}")
            return False

    def connect_rpc(self):
        """Connect to the XML-RPC server"""
        try:
            self.rpc_client = xmlrpc.client.ServerProxy(f"http://{self.server_host}:{self.rpc_port}")
            # Test connection
            self.scores = self.rpc_client.get_scores()
            print(f"Connected to RPC server at {self.server_host}:{self.rpc_port}")
            return True
        except Exception as e:
            print(f"RPC connection failed: {e}")
            return False

    def socket_listener(self):
        """Listen for messages from the socket server"""
        while True:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    print("Connection lost")
                    break

                # Process message
                self.process_message(data)
            except Exception as e:
                print(f"Error in socket listener: {e}")
                # Try to reconnect
                time.sleep(2)
                self.connect_socket()

    def process_message(self, data):
        """Process a message from the server"""
        if ":" not in data:
            return

        msg_type, content = data.split(":", 1)

        if msg_type == "WELCOME":
            print(f"Server: {content}")
            self.notify("on_message", f"Welcome to the Trivia Game!")

        elif msg_type == "QUESTION":
            # Parse question JSON
            try:
                question_data = json.loads(content)
                self.current_question = question_data
                self.question_end_time = time.time() + 15  # 15 seconds per question
                self.notify("on_question", question_data)
            except json.JSONDecodeError:
                print(f"Invalid question data: {content}")

        elif msg_type == "QUESTION_CLOSED":
            self.notify("on_question_closed", content)
            self.current_question = None

        elif msg_type == "CORRECT":
            self.notify("on_correct_answer", content)

        elif msg_type == "WRONG_ANSWER":
            self.notify("on_wrong_answer", content)

        elif msg_type == "HINT":
            self.notify("on_hint", content)

        elif msg_type == "ALREADY_ANSWERED":
            self.notify("on_message", content)

        elif msg_type == "TOKEN_REQUEST":
            self.notify("on_message", content)

        elif msg_type == "LEADERBOARD_CONFLICT":
            self.notify("on_message", content)

        elif msg_type == "DEADLOCK":
            self.notify("on_message", content)

        elif msg_type == "FINAL_SCORES":
            try:
                final_scores = json.loads(content)
                self.scores = final_scores
                self.notify("on_scores_update", final_scores)
                self.notify("on_message", "Game Over! Final scores displayed.")
            except json.JSONDecodeError:
                print(f"Invalid scores data: {content}")

        elif msg_type == "PONG":
            # Process clock synchronization response
            try:
                t1, t2 = map(float, content.split(":"))
                t4 = time.time()
                offset = ((t2 - t1) + (time.time() - t4)) / 2
                # Could adjust local time calculations with this offset
            except:
                pass

    def update_scores_loop(self):
        """Periodically update scores from the server"""
        while True:
            try:
                self.scores = self.rpc_client.get_scores()
                self.notify("on_scores_update", self.scores)
            except Exception as e:
                print(f"Error updating scores: {e}")
            time.sleep(3)  # Update every 3 seconds

    def update_token_status_loop(self):
        """Periodically update token status from the server"""
        while True:
            try:
                self.token_status = self.rpc_client.get_token_status()
                self.notify("on_token_status", self.token_status)

                # Check time warp status
                if self.player_id in self.token_status.get("time_warp", {}).get("active", {}):
                    self.time_warp_active = True
                    self.time_warp_end = time.time() + self.token_status["time_warp"]["active"][self.player_id]
                    self.notify("on_time_warp_update", True, self.time_warp_end)
                elif self.time_warp_active:
                    self.time_warp_active = False
                    self.notify("on_time_warp_update", False, 0)
            except Exception as e:
                print(f"Error updating token status: {e}")
            time.sleep(1)  # Update every second

    def sync_clock_loop(self):
        """Periodically synchronize clock with server"""
        while True:
            try:
                t1 = time.time()
                self.socket.sendall(f"PING:{t1}".encode('utf-8'))
            except Exception as e:
                print(f"Error in clock sync: {e}")
            time.sleep(10)  # Sync every 10 seconds

    # Game actions
    def submit_answer(self, answer):
        """Submit an answer to the current question"""
        if not self.current_question:
            self.notify("on_message", "No active question")
            return False

        multiplier = 2 if self.time_warp_active else 1
        try:
            self.socket.sendall(f"ANSWER:{answer}:{multiplier}".encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error submitting answer: {e}")
            return False

    def request_hint_token(self):
        """Request the hint token"""
        try:
            # Generate random number as per your logic
            import random
            random_number = random.randint(0, 10)
            success, message = self.rpc_client.request_hint_token(self.player_id, random_number)
            self.notify("on_message", message)
            return success
        except Exception as e:
            print(f"Error requesting hint token: {e}")
            self.notify("on_message", f"Error: {str(e)}")
            return False

    def request_skip_token(self):
        """Request the skip token"""
        try:
            success, message = self.rpc_client.request_skip_token(self.player_id)
            self.notify("on_message", message)
            return success
        except Exception as e:
            print(f"Error requesting skip token: {e}")
            self.notify("on_message", f"Error: {str(e)}")
            return False

    def request_leaderboard_token(self):
        """Request the leaderboard token"""
        try:
            success, message = self.rpc_client.request_leaderboard_token(self.player_id)
            self.notify("on_message", message)
            return success
        except Exception as e:
            print(f"Error requesting leaderboard token: {e}")
            self.notify("on_message", f"Error: {str(e)}")
            return False

    def request_time_warp(self):
        """Request time warp activation"""
        try:
            success, message, remaining = self.rpc_client.request_time_warp(self.player_id)
            self.notify("on_message", message)

            if success:
                self.time_warp_active = True
                self.time_warp_end = time.time() + remaining
                self.notify("on_time_warp_update", True, self.time_warp_end)

            return success
        except Exception as e:
            print(f"Error requesting time warp: {e}")
            self.notify("on_message", f"Error: {str(e)}")
            return False

    def use_hint(self):
        """Use the hint token to get a hint"""
        try:
            success, message = self.rpc_client.use_hint(self.player_id)
            if not success:
                self.notify("on_message", message)
            return success
        except Exception as e:
            print(f"Error using hint: {e}")
            self.notify("on_message", f"Error: {str(e)}")
            return False

    def use_skip(self):
        """Use the skip token to skip the current question"""
        try:
            success, message = self.rpc_client.use_skip(self.player_id)
            self.notify("on_message", message)
            return success
        except Exception as e:
            print(f"Error using skip: {e}")
            self.notify("on_message", f"Error: {str(e)}")
            return False

    def release_hint_token(self):
        """Release the hint token"""
        try:
            success, message = self.rpc_client.release_hint_token(self.player_id)
            self.notify("on_message", message)
            return success
        except Exception as e:
            print(f"Error releasing hint token: {e}")
            return False

    def release_skip_token(self):
        """Release the skip token"""
        try:
            success, message = self.rpc_client.release_skip_token(self.player_id)
            self.notify("on_message", message)
            return success
        except Exception as e:
            print(f"Error releasing skip token: {e}")
            return False

    def release_leaderboard_token(self):
        """Release the leaderboard token"""
        try:
            success, message = self.rpc_client.release_leaderboard_token(self.player_id)
            self.notify("on_message", message)
            return success
        except Exception as e:
            print(f"Error releasing leaderboard token: {e}")
            return False

    def toggle_dark_mode(self):
        """Toggle dark mode setting"""
        self.dark_mode = not self.dark_mode
        return self.dark_mode

    def set_callback(self, event_name, callback_function):
        """Set a callback function for a specific event"""
        if event_name in self.callbacks:
            self.callbacks[event_name] = callback_function

    def notify(self, event_name, *args):
        """Notify the registered callback for an event"""
        if event_name in self.callbacks and self.callbacks[event_name]:
            self.callbacks[event_name](*args)