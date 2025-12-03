import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import turtle
import random
import datetime
import os

# ===================== CONFIGURATION / RESEARCH DATA =====================
# (Processing: fixed reference data used by the app)

AGE_GUIDELINES = {
    "Child (4-8)": 1200,      # ml
    "Teen (9-13)": 1700,      # ml
    "Adult (14-64)": 2200,    # mid-value between 2000-2500
    "Senior (65+)": 1800      # mid-value between 1700-2000
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

DATA_FILE = "water_log.txt"   # Simple text file for history (privacy-friendly)


class WaterBuddyApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # ===================== MAIN WINDOW SETUP =====================
        self.title("WaterBuddy - Daily Hydration Companion")
        self.geometry("900x550")
        self.resizable(False, False)

        # STATE VARIABLES (Processing: in-memory data)
        self.age_group = tk.StringVar(value="Adult (14-64)")
        self.goal_ml = tk.IntVar(value=AGE_GUIDELINES[self.age_group.get()])
        self.total_ml = tk.IntVar(value=0)
        self.remaining_ml = tk.IntVar(value=self.goal_ml.get())
        self.progress_percent = tk.DoubleVar(value=0.0)
        self.dark_mode = tk.BooleanVar(value=False)

        # For theme handling
        self.frames = []
        self.labels = []
        self.buttons = []
        self.entries = []
        self.checkbuttons = []

        # BUILD UI
        self.create_layout()
        self.create_turtle_canvas()
        self.apply_theme()  # initial theme

        # Load today's history (if any)
        self.load_today_from_file()
        self.update_all_output()

        # Handle graceful closing (save history once more)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ===================== UI CONSTRUCTION =====================

    def create_layout(self):
        # Main layout: Left controls + Right visual/meter + Mascot below
        left_frame = tk.Frame(self)
        right_frame = tk.Frame(self)
        mascot_frame = tk.Frame(self, height=260)

        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        right_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=10)
        mascot_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=10, pady=10)

        self.frames.extend([left_frame, right_frame, mascot_frame])
        self.mascot_frame = mascot_frame

        # ----- LEFT PANEL: INPUT (Goal & Logging Controls) -----
        # SECTION: Age / Goal Selection
        lbl_profile = tk.Label(left_frame, text="Goal Selection", font=("Arial", 12, "bold"))
        lbl_profile.pack(anchor="w", pady=(0, 5))
        self.labels.append(lbl_profile)

        age_row = tk.Frame(left_frame)
        age_row.pack(fill=tk.X, pady=2)
        self.frames.append(age_row)

        lbl_age = tk.Label(age_row, text="Age Group:")
        lbl_age.pack(side=tk.LEFT)
        self.labels.append(lbl_age)

        age_menu = tk.OptionMenu(
            age_row,
            self.age_group,
            *AGE_GUIDELINES.keys(),
            command=self.on_age_change  # INPUT handler
        )
        age_menu.pack(side=tk.LEFT, padx=5)
        self.buttons.append(age_menu)

        # Manual goal adjustment
        goal_row = tk.Frame(left_frame)
        goal_row.pack(fill=tk.X, pady=5)
        self.frames.append(goal_row)

        lbl_goal = tk.Label(goal_row, text="Daily Goal (ml):")
        lbl_goal.pack(side=tk.LEFT)
        self.labels.append(lbl_goal)

        self.goal_entry = tk.Entry(goal_row, width=8)
        self.goal_entry.insert(0, str(self.goal_ml.get()))
        self.goal_entry.pack(side=tk.LEFT, padx=5)
        self.entries.append(self.goal_entry)

        btn_set_goal = tk.Button(goal_row, text="Set Goal", command=self.on_set_goal)
        btn_set_goal.pack(side=tk.LEFT)
        self.buttons.append(btn_set_goal)

        # SECTION: Logging Water
        sep1 = tk.Label(left_frame, text="------------------------------")
        sep1.pack(fill=tk.X, pady=5)
        self.labels.append(sep1)

        lbl_log = tk.Label(left_frame, text="Log Water", font=("Arial", 12, "bold"))
        lbl_log.pack(anchor="w", pady=(0, 5))
        self.labels.append(lbl_log)

        # Quick +250 ml button (INPUT)
        btn_250 = tk.Button(left_frame, text="+250 ml", font=("Arial", 11, "bold"),
                            command=lambda: self.add_water(250))
        btn_250.pack(fill=tk.X, pady=5)
        self.buttons.append(btn_250)

        # Custom amount input (INPUT)
        custom_row = tk.Frame(left_frame)
        custom_row.pack(fill=tk.X, pady=5)
        self.frames.append(custom_row)

        lbl_custom = tk.Label(custom_row, text="Custom amount (ml):")
        lbl_custom.pack(side=tk.LEFT)
        self.labels.append(lbl_custom)

        self.custom_entry = tk.Entry(custom_row, width=8)
        self.custom_entry.pack(side=tk.LEFT, padx=5)
        self.entries.append(self.custom_entry)

        btn_add_custom = tk.Button(custom_row, text="Add",
                                   command=self.on_add_custom)
        btn_add_custom.pack(side=tk.LEFT)
        self.buttons.append(btn_add_custom)

        # SECTION: Utility buttons
        sep2 = tk.Label(left_frame, text="------------------------------")
        sep2.pack(fill=tk.X, pady=5)
        self.labels.append(sep2)

        # Reset / New Day (INPUT)
        btn_reset = tk.Button(left_frame, text="New Day / Reset",
                              command=self.on_reset_clicked)
        btn_reset.pack(fill=tk.X, pady=5)
        self.buttons.append(btn_reset)

        # Hydration Tip (INPUT)
        btn_tip = tk.Button(left_frame, text="Hydration Tip",
                            command=self.show_tip)
        btn_tip.pack(fill=tk.X, pady=5)
        self.buttons.append(btn_tip)

        # Dark Mode Toggle (INPUT)
        chk_dark = tk.Checkbutton(left_frame, text="Dark Mode",
                                  variable=self.dark_mode,
                                  command=self.apply_theme)
        chk_dark.pack(anchor="w", pady=5)
        self.checkbuttons.append(chk_dark)

        # ----- RIGHT PANEL: OUTPUT (Progress / Labels) -----
        lbl_status = tk.Label(right_frame, text="Today's Hydration", font=("Arial", 14, "bold"))
        lbl_status.pack(anchor="w", pady=(0, 10))
        self.labels.append(lbl_status)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            right_frame,
            orient="horizontal",
            length=300,
            mode="determinate",
            maximum=100
        )
        self.progress_bar.pack(pady=5)

        # Numeric labels
        self.lbl_total = tk.Label(right_frame, text="Total Drank: 0 ml", font=("Arial", 11))
        self.lbl_remaining = tk.Label(right_frame, text="Remaining Goal: 0 ml", font=("Arial", 11))
        self.lbl_percent = tk.Label(right_frame, text="Progress: 0%", font=("Arial", 11))
        self.lbl_message = tk.Label(right_frame, text="", font=("Arial", 11, "italic"))

        for lbl in (self.lbl_total, self.lbl_remaining, self.lbl_percent, self.lbl_message):
            lbl.pack(anchor="w", pady=2)
            self.labels.append(lbl)

        # History note (simple read-only text info)
        self.lbl_history_info = tk.Label(right_frame, text="", font=("Arial", 9))
        self.lbl_history_info.pack(anchor="w", pady=(10, 0))
        self.labels.append(self.lbl_history_info)

    def create_turtle_canvas(self):
        # Canvas for Turtle mascot
        canvas = tk.Canvas(self.mascot_frame, width=400, height=260)
        canvas.pack()
        self.frames.append(canvas)

        # Embed Turtle into Tkinter Canvas
        self.turtle_screen = turtle.TurtleScreen(canvas)
        self.turtle_screen.bgcolor("white")
        self.turtle_screen.tracer(0)

        self.mascot = turtle.RawTurtle(self.turtle_screen)
        self.mascot.hideturtle()
        self.mascot.speed(0)

        # Draw initial neutral mascot
        self.draw_mascot_neutral()
        self.turtle_screen.update()

    # ===================== INPUT HANDLERS =====================

    def on_age_change(self, _event=None):
        """Input: Age group dropdown change."""
        # Processing: update goal based on standard data
        new_goal = AGE_GUIDELINES.get(self.age_group.get(), 2000)
        self.goal_ml.set(new_goal)
        self.goal_entry.delete(0, tk.END)
        self.goal_entry.insert(0, str(new_goal))

        # Output: re-calc remaining & progress, update UI
        self.update_all_output()

    def on_set_goal(self):
        """Input: manual goal entered by user."""
        text = self.goal_entry.get().strip()
        try:
            value = int(text)
            if value <= 0:
                raise ValueError
            self.goal_ml.set(value)
        except ValueError:
            messagebox.showerror("Invalid Goal", "Please enter a positive integer for the goal (ml).")
            return

        self.update_all_output()

    def add_water(self, amount):
        """
        INPUT: water amount from +250 button or custom entry.
        PROCESSING: total += amount; recalc remaining & percent; save to file.
        OUTPUT: update progress bar, labels, mascot.
        """
        if amount <= 0:
            return

        self.total_ml.set(self.total_ml.get() + amount)
        self.update_all_output()
        self.save_today_to_file()

    def on_add_custom(self):
        """Input: Add button for custom water amount."""
        text = self.custom_entry.get().strip()
        if not text:
            messagebox.showwarning("No Amount", "Enter an amount in ml.")
            return
        try:
            amount = int(text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a positive integer for the amount (ml).")
            return

        self.add_water(amount)
        self.custom_entry.delete(0, tk.END)

    def on_reset_clicked(self):
        """Input: user clicks Reset / New Day."""
        answer = messagebox.askyesno("New Day / Reset", "Are you sure you want to reset today's progress?")
        if not answer:
            return

        # PROCESSING: reset counters
        self.total_ml.set(0)
        self.update_all_output()
        self.save_today_to_file()  # save reset state

        # OUTPUT: mascot returns to neutral state
        self.draw_mascot_neutral()
        self.turtle_screen.update()

    def show_tip(self):
        """Input: user clicks Hydration Tip."""
        tip = random.choice(HYDRATION_TIPS)
        messagebox.showinfo("Hydration Tip", tip)

    def on_close(self):
        """Called when window is closed."""
        self.save_today_to_file()
        self.destroy()

    # ===================== PROCESSING & OUTPUT UPDATES =====================

    def update_all_output(self):
        """
        PROCESSING:
          - remaining = goal - total
          - progress_percent = (total / goal) * 100
        OUTPUT:
          - update labels, progress bar, mascot facial expression.
        """
        goal = max(1, self.goal_ml.get())  # avoid division by zero
        total = self.total_ml.get()
        remaining = max(0, goal - total)
        self.remaining_ml.set(remaining)

        percent = (total / goal) * 100
        if percent > 200:
            percent = 200  # cap UI progress
        self.progress_percent.set(percent)

        # Update numeric labels
        self.lbl_total.config(text=f"Total Drank: {total} ml")
        self.lbl_remaining.config(text=f"Remaining Goal: {remaining} ml")
        self.lbl_percent.config(text=f"Progress: {self.progress_percent.get():.1f}%")

        # Progress bar
        self.progress_bar["value"] = min(100, self.progress_percent.get())

        # Motivational message (OUTPUT)
        msg = self.get_motivational_message(self.progress_percent.get())
        self.lbl_message.config(text=msg)

        # Update mascot
        self.update_mascot(self.progress_percent.get())

        # History info text (simple output)
        self.lbl_history_info.config(
            text=f"History is saved locally in '{DATA_FILE}' for privacy."
        )

    def get_motivational_message(self, percent):
        """PROCESSING: choose message based on progress. OUTPUT: returns text."""
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

    # ===================== MASCOT (TURTLE) STATE MACHINE =====================

    def clear_mascot(self):
        self.mascot.clear()
        self.mascot.penup()
        self.mascot.home()

    def draw_face_base(self):
        """Draws the basic round face outline."""
        self.mascot.penup()
        self.mascot.goto(0, -40)
        self.mascot.pendown()
        self.mascot.circle(60)

    def draw_eyes_neutral(self):
        # Left eye
        self.mascot.penup()
        self.mascot.goto(-25, 10)
        self.mascot.dot(10)
        # Right eye
        self.mascot.goto(25, 10)
        self.mascot.dot(10)

    def draw_mouth_neutral(self):
        self.mascot.penup()
        self.mascot.goto(-20, -20)
        self.mascot.pendown()
        self.mascot.forward(40)

    def draw_mouth_smile(self):
        self.mascot.penup()
        self.mascot.goto(-25, -15)
        self.mascot.setheading(-60)
        self.mascot.pendown()
        self.mascot.circle(30, 120)

    def draw_mascot_neutral(self):
        """Mascot state: Neutral (<50%)."""
        self.clear_mascot()
        self.mascot.pensize(3)
        self.draw_face_base()
        self.draw_eyes_neutral()
        self.draw_mouth_neutral()

    def draw_mascot_happy(self):
        """Mascot state: Smile (>=50%)."""
        self.clear_mascot()
        self.mascot.pensize(3)
        self.draw_face_base()
        self.draw_eyes_neutral()
        self.draw_mouth_smile()

    def draw_mascot_wave(self):
        """Mascot state: Wave (>=75%)."""
        self.clear_mascot()
        self.mascot.pensize(3)
        self.draw_face_base()
        self.draw_eyes_neutral()
        self.draw_mouth_smile()

        # Simple waving arm on the right side
        self.mascot.penup()
        self.mascot.goto(40, -10)
        self.mascot.setheading(-30)
        self.mascot.pendown()
        self.mascot.forward(40)
        self.mascot.left(30)
        self.mascot.forward(20)

    def celebrate_animation(self, steps=10):
        """
        Mascot state: Celebrate (>=100%).
        Small looped animation; non-blocking using ontimer.
        """
        self.mascot.clear()
        self.mascot.penup()
        self.mascot.goto(0, 0)
        self.mascot.pendown()
        self.mascot.pensize(3)

        # Draw happy face
        self.draw_face_base()
        self.draw_eyes_neutral()
        self.draw_mouth_smile()

        # Confetti arcs
        for angle in range(0, 360, 60):
            self.mascot.penup()
            self.mascot.goto(0, 0)
            self.mascot.setheading(angle)
            self.mascot.forward(80)
            self.mascot.pendown()
            self.mascot.circle(10)

        self.turtle_screen.update()

        # Optionally loop a few times
        if steps > 0:
            self.mascot_screen_after = self.turtle_screen.ontimer(
                lambda: self.celebrate_animation(steps - 1),
                200
            )

    def update_mascot(self, percent):
        """STATE MACHINE: choose mascot expression based on progress%."""
        if percent < 50:
            self.draw_mascot_neutral()
            self.turtle_screen.update()
        elif percent < 75:
            self.draw_mascot_happy()
            self.turtle_screen.update()
        elif percent < 100:
            self.draw_mascot_wave()
            self.turtle_screen.update()
        else:
            # >= 100%: celebration animation
            self.celebrate_animation(steps=1)  # 1 short loop to avoid overdoing it

    # ===================== DARK MODE THEME =====================

    def apply_theme(self):
        """INPUT: dark mode checkbox. PROCESSING + OUTPUT: change widget colors."""
        if self.dark_mode.get():
            bg = "#121212"
            fg = "#f5f5f5"
            button_bg = "#1f1f1f"
            entry_bg = "#222222"
        else:
            bg = "#f0f0f0"
            fg = "#000000"
            button_bg = "#e0e0e0"
            entry_bg = "#ffffff"

        # Window background
        self.configure(bg=bg)

        # Frames
        for f in self.frames:
            try:
                f.configure(bg=bg)
            except tk.TclError:
                pass  # some (like Canvas) may not support

        # Labels
        for lbl in self.labels:
            try:
                lbl.configure(bg=bg, fg=fg)
            except tk.TclError:
                pass

        # Buttons
        for btn in self.buttons:
            try:
                btn.configure(bg=button_bg, fg=fg, activebackground=button_bg)
            except tk.TclError:
                pass

        # Checkbuttons
        for chk in self.checkbuttons:
            try:
                chk.configure(bg=bg, fg=fg, activebackground=bg, selectcolor=bg)
            except tk.TclError:
                pass

        # Entries
        for ent in self.entries:
            try:
                ent.configure(bg=entry_bg, fg=fg, insertbackground=fg)
            except tk.TclError:
                pass

        # Turtle background
        if hasattr(self, "turtle_screen"):
            self.turtle_screen.bgcolor(bg if not self.dark_mode.get() else "#202020")
            self.turtle_screen.update()

    # ===================== SIMPLE TEXT-FILE HISTORY =====================

    def save_today_to_file(self):
        """
        PROCESSING: store daily total + goal to a simple text file.
        Format per line: YYYY-MM-DD,total,goal
        """
        today = datetime.date.today().isoformat()
        history = {}

        # Load existing data
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(",")
                    if len(parts) == 3:
                        date_str, total_str, goal_str = parts
                        try:
                            history[date_str] = (int(total_str), int(goal_str))
                        except ValueError:
                            continue

        # Update today's record
        history[today] = (self.total_ml.get(), self.goal_ml.get())

        # Write back
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            for date_str, (total, goal) in sorted(history.items()):
                f.write(f"{date_str},{total},{goal}\n")

    def load_today_from_file(self):
        """
        PROCESSING: read history and restore today's data.
        """
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
                        self.total_ml.set(int(total_str))
                        # If goal in file differs from current, prefer stored goal
                        stored_goal = int(goal_str)
                        if stored_goal > 0:
                            self.goal_ml.set(stored_goal)
                            self.goal_entry.delete(0, tk.END)
                            self.goal_entry.insert(0, str(stored_goal))
                    except ValueError:
                        pass


if __name__ == "__main__":
    app = WaterBuddyApp()
    app.mainloop()
