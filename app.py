import streamlit as st
import datetime
import os
import random

# ===================== CONFIG / CONSTANTS =====================

AGE_GUIDELINES = {
    "Child (4-8)": 1200,
    "Teen (9-13)": 1700,
    "Adult (14-64)": 2200,   # middle of 2000–2500
    "Senior (65+)": 1800     # middle of 1700–2000
}

HYDRATION_TIPS = [
    "Drink a glass of water after you wake up.",
    "Sip water regularly instead of chugging.",
    "Keep a water bottle near your study or work desk.",
    "Drink one glass of water with every meal.",
    "Thirst is a late sign — drink before you feel thirsty.",
    "Water helps with focus, mood, and energy.",
    "Add lemon or cucumber slices for taste.",
    "Eat water-rich foods like watermelon and cucumber."
]

DATA_FILE = "water_log.txt"   # simple text-file history


# ===================== STATE INIT / FILE I/O =====================

def init_state():
    if "age_group" not in st.session_state:
        st.session_state.age_group = "Adult (14-64)"
    if "goal_ml" not in st.session_state:
        st.session_state.goal_ml = AGE_GUIDELINES[st.session_state.age_group]
    if "total_ml" not in st.session_state:
        st.session_state.total_ml = 0
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False


def load_today_from_file():
    """Restore today's total + goal from DATA_FILE, if present."""
    today = datetime.date.today().isoformat()
    if not os.path.exists(DATA_FILE):
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) != 3:
                continue
            date_str, total_str, goal_str = parts
            if date_str == today:
                try:
                    total = int(total_str)
                    goal = int(goal_str)
                    st.session_state.total_ml = total
                    if goal > 0:
                        st.session_state.goal_ml = goal
                except ValueError:
                    pass


def save_today_to_file():
    """
    Store daily total + goal to DATA_FILE.
    Format per line: YYYY-MM-DD,total,goal
    """
    today = datetime.date.today().isoformat()
    history = {}

    # read existing
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 3:
                    continue
                d, total_str, goal_str = parts
                try:
                    history[d] = (int(total_str), int(goal_str))
                except ValueError:
                    continue

    # update today's
    history[today] = (st.session_state.total_ml, st.session_state.goal_ml)

    # write back
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for d, (t, g) in sorted(history.items()):
            f.write(f"{d},{t},{g}\n")


def load_history():
    """Return dict: date -> (total, goal)."""
    history = {}
    if not os.path.exists(DATA_FILE):
        return history
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) != 3:
                continue
            d, total_str, goal_str = parts
            try:
                history[d] = (int(total_str), int(goal_str))
            except ValueError:
                continue
    return history


# ===================== CORE LOGIC =====================

def recalc_goal_from_age():
    """Set goal from selected age group."""
    st.session_state.goal_ml = AGE_GUIDELINES.get(
        st.session_state.age_group,
        st.session_state.goal_ml
    )


def set_manual_goal(new_goal_str: str):
    """Set manual goal from text input."""
    try:
        val = int(new_goal_str)
        if val <= 0:
            raise ValueError
        st.session_state.goal_ml = val
        save_today_to_file()
        st.success(f"Daily goal set to {val} ml")
    except ValueError:
        st.error("Enter a positive integer for goal (ml).")


def add_water(amount: int):
    """Add water, update file."""
    if amount <= 0:
        return
    st.session_state.total_ml += amount
    save_today_to_file()


def reset_day():
    """Reset today’s progress but keep history file."""
    st.session_state.total_ml = 0
    save_today_to_file()


def compute_progress():
    goal = max(1, st.session_state.goal_ml)
    total = st.session_state.total_ml
    remaining = max(0, goal - total)
    percent = (total / goal) * 100
    return goal, total, remaining, percent


def motivational_message(percent: float) -> str:
    if percent <= 0:
        return "Start with one glass of water!"
    elif percent < 50:
        return "Good start! Keep sipping through the day."
    elif percent < 75:
        return "Nice! You're more than halfway there."
    elif percent < 100:
        return "Almost there! A few more sips to reach your goal."
    elif percent < 150:
        return "Goal completed! Great job staying hydrated!"
    else:
        return "Wow, you crossed your goal! Stay balanced."


def mascot_state(percent: float):
    """
    Replace Turtle mascot with simple emoji + description
    (Neutral / Smile / Wave / Celebrate).
    """
    if percent < 50:
        return "😐", "Mascot: Neutral (keep going!)"
    elif percent < 75:
        return "😊", "Mascot: Smiling (good progress!)"
    elif percent < 100:
        return "👋😄", "Mascot: Waving (almost there!)"
    else:
        return "🎉😄", "Mascot: Celebrating (goal reached!)"


# ===================== DARK MODE (CSS HACK) =====================

def apply_dark_mode():
    if st.session_state.dark_mode:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #111111;
                color: #f5f5f5;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #f5f5f5;
                color: #000000;
            }
            </style>
            """,
            unsafe_allow_html=True
        )


# ===================== MAIN APP =====================

def main():
    st.set_page_config(page_title="WaterBuddy", page_icon="💧", layout="centered")
    init_state()

    if not st.session_state.data_loaded:
        load_today_from_file()
        st.session_state.data_loaded = True

    apply_dark_mode()

    # ---------- SIDEBAR (GOAL SELECTION, TIP, RESET, DARK MODE) ----------
    with st.sidebar:
        st.header("⚙️ Settings")

        # Feature 1: Goal Selection (Age group + manual)
        st.subheader("Age Group")
        new_age = st.selectbox("Select Age Group", list(AGE_GUIDELINES.keys()),
                               index=list(AGE_GUIDELINES.keys()).index(st.session_state.age_group))
        if new_age != st.session_state.age_group:
            st.session_state.age_group = new_age
            recalc_goal_from_age()
            save_today_to_file()
            st.experimental_rerun()

        st.subheader("Daily Goal (ml)")
        goal_col1, goal_col2 = st.columns([2, 1])
        with goal_col1:
            goal_input = st.text_input("Manual goal (ml)", value=str(st.session_state.goal_ml))
        with goal_col2:
            if st.button("Set Goal"):
                set_manual_goal(goal_input)

        st.markdown("---")

        # Feature 5: Reset function (with confirmation)
        if st.button("🗓️ New Day / Reset"):
            # Simple confirmation pattern in Streamlit
            st.session_state._ask_reset = True

        if st.session_state.get("_ask_reset", False):
            st.warning("Are you sure you want to reset today's progress?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, reset"):
                    reset_day()
                    st.session_state._ask_reset = False
                    st.experimental_rerun()
            with c2:
                if st.button("❌ Cancel"):
                    st.session_state._ask_reset = False
                    st.experimental_rerun()

        st.markdown("---")

        # Hydration tip
        if st.button("💡 Hydration Tip"):
            st.info(random.choice(HYDRATION_TIPS))

        # Dark mode toggle
        st.markdown("---")
        st.session_state.dark_mode = st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode)
        # Apply immediately
        apply_dark_mode()

    # ---------- MAIN LAYOUT ----------
    st.title("💧 WaterBuddy – Daily Hydration Companion")

    # Progress calculations
    goal, total, remaining, percent = compute_progress()

    # Feature 3: Real-time feedback (labels + progress bar)
    c1, c2, c3 = st.columns(3)
    c1.metric("Daily Goal", f"{goal} ml")
    c2.metric("Total Drank", f"{total} ml")
    c3.metric("Remaining", f"{remaining} ml")

    st.progress(min(1.0, percent / 100.0))

    emoji, mascot_text = mascot_state(percent)
    st.markdown(f"### {emoji} {mascot_text}")
    st.caption(motivational_message(percent))

    # Feature 2: Logging water (+250 and custom)
    st.subheader("Log Water")

    log_col1, log_col2 = st.columns([1, 1])

    with log_col1:
        if st.button("+250 ml"):
            add_water(250)
            st.experimental_rerun()

    with log_col2:
        custom_amt = st.number_input("Custom amount (ml)", min_value=1, step=50, value=100)
        if st.button("Add Custom"):
            add_water(int(custom_amt))
            st.experimental_rerun()

    st.markdown("---")

    # Optional: history view
    with st.expander("📅 View Hydration History"):
        history = load_history()
        if not history:
            st.write("No history yet. Drink some water and it will be saved automatically.")
        else:
            for d, (t, g) in sorted(history.items(), reverse=True):
                status = "✅ Goal Met" if t >= g else "⚠️ Goal Not Met"
                st.write(f"**{d}** — {t} / {g} ml  {status}")
        st.caption(f"History is stored locally in `{DATA_FILE}` (no cloud login / no external DB).")


if __name__ == "__main__":
    main()
