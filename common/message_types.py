# common/message_types.py
# Message types for socket communication between server and clients

# Question related messages
QUESTION = "QUESTION"           # Server broadcasts a new question
QUESTION_CLOSED = "QUESTION_CLOSED"  # Server signals question time is up or answered
ANSWER = "ANSWER"               # Client sends an answer to server
WRONG_ANSWER = "WRONG_ANSWER"   # Server responds to wrong answers
CORRECT_ANSWER = "CORRECT_ANSWER"  # Server confirms correct answer

# Token related messages
REQUEST_TOKEN = "REQUEST_TOKEN"  # Client requests a token
RELEASE_TOKEN = "RELEASE_TOKEN"  # Client releases a token
TOKEN_GRANTED = "TOKEN_GRANTED"  # Server grants a token to client
TOKEN_DENIED = "TOKEN_DENIED"    # Server denies a token request
TOKEN_QUEUE = "TOKEN_QUEUE"      # Server sends token queue information

# Resource types
HINT_TOKEN = "hint"
SKIP_TOKEN = "skip"
LEADERBOARD_TOKEN = "leaderboard"
TIME_WARP_TOKEN = "time_warp"

# Hint and Skip related
HINT_REQUEST = "HINT_REQUEST"    # Client requests a hint
HINT_DATA = "HINT_DATA"          # Server sends hint information
SKIP_REQUEST = "SKIP_REQUEST"    # Client requests to skip a question

# Clock synchronization
CLOCK_SYNC = "CLOCK_SYNC"        # Clock synchronization message

# Game state
GAME_START = "GAME_START"        # Game is starting
GAME_END = "GAME_END"            # Game has ended
LEADERBOARD = "LEADERBOARD"      # Leaderboard data

# Error and status messages
ERROR = "ERROR"                  # Generic error message
DEADLOCK = "DEADLOCK"            # Deadlock detected message