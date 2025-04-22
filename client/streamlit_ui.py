"""
Streamlit UI for the Trivia Game client.
"""
import streamlit as st
import time
import threading
import json
import random
from client import TriviaGameClient

# Page configuration
st.set_page_config(
    page_title="Distributed Trivia Game",
    page_icon="🎮",
    layout="wide"
)

# Session state initialization
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.client = None
    st.session_state.player_id = None
    st.session_state.current_question = None
    st.session_state.scores = {}
    st.session_state.token_status = {}
    st.session_state.messages = []
    st.session_state.time_warp_active = False
    st.session_state.time_warp_end = 0
    st.session_state.dark_mode = False
    st.session_state.question_end_time = 0
    st.session_state.selected_answer = None
    st.session_state.correct_answer = None
    st.session_state.question_answered = False
    st.session_state.leaderboard_visible = False


# UI Colors
def get_colors():
    if st.session_state.dark_mode:
        return {
            "bg": "#121212",
            "panel": "#1E1E1E",
            "text": "#FFFFFF",
            "accent": "#BB86FC",
            "button": "#3700B3",
            "success": "#03DAC6",
            "error": "#CF6679",
            "warning": "#FFB900"
        }
    else:
        return {
            "bg": "#F5F5F5",
            "panel": "#FFFFFF",
            "text": "#121212",
            "accent": "#6200EE",
            "button": "#3700B3",
            "success": "#03DAC5",
            "error": "#B00020",
            "warning": "#FF6D00"
        }


# Apply theme
def apply_theme():
    colors = get_colors()

    # Custom CSS
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {colors["bg"]};
            color: {colors["text"]};
        }}
        .stButton button {{
            background-color: {colors["button"]};
            color: white;
        }}
        .success {{
            color: {colors["success"]};
        }}
        .error {{
            color: {colors["error"]};
        }}
        .warning {{
            color: {colors["warning"]};
        }}
        .token-holder {{
            font-weight: bold;
            color: {colors["accent"]};
        }}
        .token-queue {{
            font-style: italic;
        }}
        .message-box {{
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            background-color: {colors["panel"]};
        }}
        .question-timer {{
            height: 10px;
            background-color: {colors["accent"]};
            margin-bottom: 20px;
        }}
    </style>
    """, unsafe_allow_html=True)


# Callback functions for client events
def on_question(question_data):
    st.session_state.current_question = question_data
    st.session_state.question_end_time = time.time() + 15  # 15 seconds per question
    st.session_state.selected_answer = None
    st.session_state.question_answered = False
    st.session_state.correct_answer = None
    st.experimental_rerun()


def on_question_closed(message):
    st.session_state.current_question = None
    add_message(f"Question closed: {message}", "warning")
    st.experimental_rerun()


def on_correct_answer(message):
    st.session_state.correct_answer = st.session_state.selected_answer
    st.session_state.question_answered = True
    add_message(f"Correct! {message}", "success")
    st.experimental_rerun()


def on_wrong_answer(message):
    add_message(f"Wrong answer. {message}", "error")
    st.experimental_rerun()


def on_scores_update(scores):
    st.session_state.scores = scores
    if st.session_state.leaderboard_visible:
        st.experimental_rerun()


def on_hint(hint_text):
    add_message(f"Hint: {hint_text}", "accent")
    st.experimental_rerun()


def on_token_status(token_status):
    st.session_state.token_status = token_status
    st.experimental_rerun()


def on_message(message):
    add_message(message)
    st.experimental_rerun()


def on_time_warp_update(active, end_time):
    st.session_state.time_warp_active = active
    st.session_state.time_warp_end = end_time
    if active:
        add_message(f"Time Warp activated! 2x points for {int(end_time - time.time())} seconds", "accent")
    else:
        add_message("Time Warp deactivated", "warning")
    st.experimental_rerun()


def add_message(message, level="info"):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.messages.append({
        "text": message,
        "time": timestamp,
        "level": level
    })
    # Keep only last 10 messages
    if len(st.session_state.messages) > 10:
        st.session_state.messages.pop(0)


# Action functions
def submit_answer():
    if not st.session_state.selected_answer:
        add_message("Please select an answer first", "warning")
        return

    st.session_state.question_answered = True
    st.session_state.client.submit_answer(st.session_state.selected_answer)


def request_hint_token():
    st.session_state.client.request_hint_token()


def request_skip_token():
    st.session_state.client.request_skip_token()


def request_leaderboard_token():
    st.session_state.client.request_leaderboard_token()
    st.session_state.leaderboard_visible = True


def request_time_warp():
    st.session_state.client.request_time_warp()


def use_hint():
    st.session_state.client.use_hint()


def use_skip():
    st.session_state.client.use_skip()


def toggle_dark_mode():
    st.session_state.dark_mode = st.session_state.client.toggle_dark_mode()
    st.experimental_rerun()


# Login screen
def show_login():
    st.title("Distributed Trivia Game")
    st.markdown("Enter your player ID and server information to join the game.")

    col1, col2 = st.columns(2)

    with col1:
        player_id = st.text_input("Player ID", value=f"Player_{random.randint(1000, 9999)}")

    with col2:
        server_host = st.text_input("Server Host", value="localhost")

    col3, col4 = st.columns(2)

    with col3:
        socket_port = st.number_input("Socket Port", value=9997, min_value=1024, max_value=65535)

    with col4:
        rpc_port = st.number_input("RPC Port", value=8000, min_value=1024, max_value=65535)

    if st.button("Join Game"):
        st.session_state.player_id = player_id

        # Initialize client
        try:
            client = TriviaGameClient(player_id, server_host, socket_port, rpc_port)

            # Set callbacks
            client.set_callback("on_question", on_question)
            client.set_callback("on_question_closed", on_question_closed)
            client.set_callback("on_correct_answer", on_correct_answer)
            client.set_callback("on_wrong_answer", on_wrong_answer)
            client.set_callback("on_scores_update", on_scores_update)
            client.set_callback("on_hint", on_hint)
            client.set_callback("on_token_status", on_token_status)
            client.set_callback("on_message", on_message)
            client.set_callback("on_time_warp_update", on_time_warp_update)

            st.session_state.client = client
            st.session_state.initialized = True
            add_message(f"Connected to game server as {player_id}")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to connect: {str(e)}")


# Game UI
def show_game_ui():
    apply_theme()

    # Header with control buttons
    col1, col2, col3 = st.columns([2, 8, 2])

    with col1:
        st.button("🌓 Theme", on_click=toggle_dark_mode)

    with col2:
        st.title("Distributed Trivia Game")

    with col3:
        player_score = st.session_state.scores.get(st.session_state.player_id, 0)
        st.metric("Your Score", player_score)

    # Game area
    left_col, right_col = st.columns([7, 3])

    with left_col:
        show_question_area()

    with right_col:
        show_control_panel()

    # Messages area
    st.divider()
    st.subheader("Game Messages")

    for msg in reversed(st.session_state.messages):
        st.markdown(f"""
        <div class="message-box">
            <span style="color: gray;">[{msg['time']}]</span> 
            <span class="{msg['level']}">{msg['text']}</span>
        </div>
        """, unsafe_allow_html=True)


def show_question_area():
    if st.session_state.current_question:
        # Question timer
        remaining = max(0, st.session_state.question_end_time - time.time())
        progress = remaining / 15  # 15 seconds total

        st.progress(progress, "⏱️ Time remaining")

        # Question display
        question = st.session_state.current_question
        st.subheader(f"Category: {question.get('category', 'General')}")
        st.write(f"## {question.get('question', 'Loading question...')}")

        # Answer options
        if not st.session_state.question_answered:
            options = question.get('options', [])
            cols = st.columns(len(options))

            for i, option in enumerate(options):
                with cols[i]:
                    if st.button(option, use_container_width=True, key=f"option_{i}"):
                        st.session_state.selected_answer = option
                        submit_answer()
        else:
            if st.session_state.correct_answer:
                st.success(f"✅ Correct answer: {st.session_state.correct_answer}")
            else:
                st.info("Waiting for next question...")
    else:
        st.info("Waiting for a new question...")


def show_control_panel():
    st.subheader("Game Controls")

    # Time Warp status
    if st.session_state.time_warp_active:
        remaining = max(0, st.session_state.time_warp_end - time.time())
        st.warning(f"⏰ Time Warp Active: {int(remaining)}s remaining")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        st.button("⏱️ Time Warp", on_click=request_time_warp)
        st.button("🔍 Request Hint", on_click=request_hint_token)

        # Use hint if token available
        hint_token = st.session_state.token_status.get('hint', {})
        can_use_hint = hint_token.get('current_holder') == st.session_state.player_id
        st.button("💡 Use Hint", on_click=use_hint, disabled=not can_use_hint)

    with col2:
        st.button("🏆 Leaderboard", on_click=request_leaderboard_token)
        st.button("⏭️ Request Skip", on_click=request_skip_token)

        # Use skip if token available
        skip_token = st.session_state.token_status.get('skip', {})
        can_use_skip = skip_token.get('current_holder') == st.session_state.player_id
        st.button("⏩ Use Skip", on_click=use_skip, disabled=not can_use_skip)

    # Token status display
    st.divider()
    display_token_status()

    # Leaderboard display
    if st.session_state.leaderboard_visible:
        show_leaderboard()


def display_token_status():
    st.subheader("Resource Tokens")

    # Hint token
    hint_token = st.session_state.token_status.get('hint', {})
    holder = hint_token.get('current_holder', 'None')
    queue = hint_token.get('queue', [])

    st.markdown(f"""
    **Hint Token**: 
    - Holder: <span class="token-holder">{holder}</span>
    - Queue: <span class="token-queue">{', '.join(queue) if queue else 'Empty'}</span>
    """, unsafe_allow_html=True)

    # Skip token
    skip_token = st.session_state.token_status.get('skip', {})
    holder = skip_token.get('current_holder', 'None')
    queue = skip_token.get('queue', [])

    st.markdown(f"""
    **Skip Token**: 
    - Holder: <span class="token-holder">{holder}</span>
    - Queue: <span class="token-queue">{', '.join(queue) if queue else 'Empty'}</span>
    """, unsafe_allow_html=True)

    # Leaderboard token
    leaderboard_token = st.session_state.token_status.get('leaderboard', {})
    holder = leaderboard_token.get('current_holder', 'None')
    queue = leaderboard_token.get('queue', [])

    st.markdown(f"""
    **Leaderboard Token**: 
    - Holder: <span class="token-holder">{holder}</span>
    - Queue: <span class="token-queue">{', '.join(queue) if queue else 'Empty'}</span>
    """, unsafe_allow_html=True)


def show_leaderboard():
    st.divider()
    st.subheader("🏆 Leaderboard")

    # Check if player has leaderboard token
    leaderboard_token = st.session_state.token_status.get('leaderboard', {})
    has_token = leaderboard_token.get('current_holder') == st.session_state.player_id

    if has_token:
        # Sort scores
        sorted_scores = sorted(
            st.session_state.scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Display as table
        data = []
        for rank, (player, score) in enumerate(sorted_scores, 1):
            data.append({
                "Rank": rank,
                "Player": player,
                "Score": score
            })

        st.table(data)

        if st.button("Release Leaderboard"):
            st.session_state.client.release_leaderboard_token()
            st.session_state.leaderboard_visible = False
    else:
        st.info("You need the leaderboard token to view scores")
        st.session_state.leaderboard_visible = False


# Main app flow
def main():
    if not st.session_state.initialized:
        show_login()
    else:
        show_game_ui()


if __name__ == "__main__":
    main()