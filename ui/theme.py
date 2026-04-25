import customtkinter as ctk

# Modern Premium Dark Theme
CURSOR_BG = "#0A0A0B"          # Very dark, almost black background
CURSOR_PANEL = "#121214"       # Slightly lighter for panels/cards
CURSOR_SIDEBAR = "#0A0A0B"     # Same as BG for seamless look, or #0F0F12
CURSOR_ACTIVITYBAR = "#0A0A0B" # Integrated sidebar
CURSOR_BORDER = "#1F1F22"      # Soft borders
CURSOR_TEXT = "#F9FAFB"        # Crisp white text
CURSOR_MUTED = "#8B8D98"       # Muted gray text
CURSOR_ACCENT = "#3B82F6"      # Primary Blue Accent
CURSOR_ACCENT_HOVER = "#60A5FA"
CURSOR_ACCENT_GRAD = "#8B5CF6" # Optional secondary accent (Violet)
CURSOR_SUCCESS = "#10B981"
CURSOR_SUCCESS_HOVER = "#059669"
CURSOR_DANGER = "#EF4444"
CURSOR_DANGER_HOVER = "#DC2626"
CURSOR_FOCUS = "#3B82F6"
CURSOR_WARNING = "#F59E0B"
CURSOR_CARD_BG = "#1A1A1E"     # For elevated cards

R0 = 0
R_SMALL = 6
R_MEDIUM = 12
R_LARGE = 16

def init_theme():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")
