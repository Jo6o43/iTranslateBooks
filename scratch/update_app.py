import sys

with open('ui/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add DashboardViewMixin import
if 'from ui.dashboard_view import DashboardViewMixin' not in content:
    content = content.replace('from ui.queue_panel import QueuePanelMixin', 'from ui.queue_panel import QueuePanelMixin\nfrom ui.dashboard_view import DashboardViewMixin')

# Replace the class signature and init
class_sig = "class TranslatorApp(ctk.CTk, ExplorerViewMixin, SettingsViewMixin, PromptViewMixin, QueuePanelMixin):"
new_class_sig = "class TranslatorApp(ctk.CTk, DashboardViewMixin, ExplorerViewMixin, SettingsViewMixin, PromptViewMixin, QueuePanelMixin):"

content = content.replace(class_sig, new_class_sig)

# We need to replace everything from `def __init__(self):` up to `def update_slider_label`
import re
pattern_init = re.compile(r'    def __init__\(self\):.*?    def update_slider_label', re.DOTALL)

new_init = '''    def __init__(self):
        super().__init__()
        self.title("iTranslateBooks")
        self.geometry("1180x760")
        self.minsize(980, 640)

        # Suporte para Ícone da Aplicação
        try:
            self.iconbitmap(os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico"))
        except Exception:
            pass

        self.books_in_abs, self.books_out_abs = ensure_books_dirs()
        self.configure(fg_color=CURSOR_BG)

        # Layout grid: Modern Dashboard Layout
        # col 0: Sidebar
        # col 1: Main Content
        self.grid_columnconfigure(0, minsize=220, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.cancel_event = threading.Event()
        self.is_running = False
        self.active_view = "dashboard"
        self.custom_lang_prompts = {}
        self.custom_adv_prompts = {}
        self.queue_items = []
        
        # Sidebar (Navigation)
        self.sidebar = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=CURSOR_SIDEBAR,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo / Title area
        self.sidebar_header = ctk.CTkLabel(
            self.sidebar,
            text="iTranslateBooks",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CURSOR_ACCENT
        )
        self.sidebar_header.grid(row=0, column=0, padx=20, pady=(30, 30), sticky="w")

        # Sidebar Buttons
        def create_nav_btn(row, text, view_name):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                height=40,
                corner_radius=R_SMALL,
                fg_color="transparent",
                text_color=CURSOR_MUTED,
                hover_color=CURSOR_PANEL,
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda v=view_name: self.set_view(v),
            )
            btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
            self._make_accessible(
                btn,
                {"border_width": 2, "border_color": CURSOR_FOCUS},
                {"border_width": 0, "border_color": "transparent"},
            )
            return btn

        self.btn_dashboard = create_nav_btn(1, "Visão Geral", "dashboard")
        self.btn_explorer = create_nav_btn(2, "Ficheiros", "explorer")
        self.btn_queue = create_nav_btn(3, "Fila de Espera", "queue")
        self.btn_lang_prompt = create_nav_btn(4, "Prompt de Idioma", "lang_prompt")
        self.btn_adv_prompt = create_nav_btn(5, "Prompt Avançado", "adv_prompt")
        
        self.sidebar.grid_rowconfigure(10, weight=1) # Spacer
        self.btn_settings = create_nav_btn(11, "Definições", "settings")

        # Main Content Area
        self.main_area = ctk.CTkFrame(self, fg_color=CURSOR_BG, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, minsize=200) # Bottom Panel

        # View Container (Top part of Main Content)
        self.view_container = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.view_container.grid(row=0, column=0, sticky="nsew")
        self.view_container.grid_columnconfigure(0, weight=1)
        self.view_container.grid_rowconfigure(0, weight=1)

        # Views
        self.view_dashboard = ctk.CTkFrame(self.view_container, fg_color="transparent")
        self.view_explorer = ctk.CTkFrame(self.view_container, fg_color="transparent")
        self.view_queue = ctk.CTkFrame(self.view_container, fg_color="transparent")
        self.view_lang_prompt = ctk.CTkFrame(self.view_container, fg_color="transparent")
        self.view_adv_prompt = ctk.CTkFrame(self.view_container, fg_color="transparent")
        self.view_settings = ctk.CTkFrame(self.view_container, fg_color="transparent")

        for v in (self.view_dashboard, self.view_explorer, self.view_queue, self.view_lang_prompt, self.view_adv_prompt, self.view_settings):
            v.grid(row=0, column=0, sticky="nsew")

        # Bottom panel (Output + progress) inside main area
        self.bottom_panel = ctk.CTkFrame(
            self.main_area,
            corner_radius=R_MEDIUM,
            fg_color=CURSOR_PANEL,
            border_width=1,
            border_color=CURSOR_BORDER,
        )
        self.bottom_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.bottom_panel.grid_columnconfigure(0, weight=1)
        self.bottom_panel.grid_rowconfigure(1, weight=1)

        self.bottom_header = ctk.CTkFrame(self.bottom_panel, fg_color="transparent")
        self.bottom_header.grid(row=0, column=0, padx=12, pady=8, sticky="ew")
        self.bottom_header.grid_columnconfigure(0, weight=1)

        self.status_left = ctk.CTkLabel(self.bottom_header, text="Pronto", text_color=CURSOR_TEXT, font=ctk.CTkFont(size=12, weight="bold"))
        self.status_left.grid(row=0, column=0, sticky="w")

        self.progress_wrap = ctk.CTkFrame(self.bottom_header, fg_color="transparent")
        self.progress_wrap.grid(row=0, column=1, sticky="e")

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_wrap,
            width=220,
            height=8,
            corner_radius=R_SMALL,
            progress_color=CURSOR_ACCENT,
        )
        self.progress_bar.pack(side="left", padx=(0, 10))
        self.progress_bar.set(0)

        self.eta_label = ctk.CTkLabel(self.progress_wrap, text="-- | ETA: -- | 0/0", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=11))
        self.eta_label.pack(side="left")

        self.console = ctk.CTkTextbox(
            self.bottom_panel,
            fg_color=CURSOR_CARD_BG,
            text_color=CURSOR_MUTED,
            border_width=0,
            corner_radius=R_SMALL,
        )
        self.console.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.console.configure(state="disabled")

        # Build view contents
        self._build_dashboard_view(self.view_dashboard)
        self._build_explorer_view(self.view_explorer)
        
        # queue_panel.py expects self.editor_body to exist and inserts itself there
        self.editor_body = self.view_queue
        self.editor_header = ctk.CTkFrame(self.view_queue, height=0) # dummy to prevent errors
        self._build_queue_panel() 
        
        self._build_settings_view(self.view_settings)
        self._build_prompt_view(self.view_lang_prompt, mode="lang")
        self._build_prompt_view(self.view_adv_prompt, mode="adv")
        
        self.checkboxes = []
        self._sync_books_paths_ui()
        self.refresh_books()
        self._register_keyboard_shortcuts()
        self.set_view("dashboard")

    def update_slider_label'''

content = pattern_init.sub(new_init, content)

# Now replace `set_view` and `_all_sidebar_btns`
pattern_view = re.compile(r'    def _all_sidebar_btns\(self\):.*?        self\.after\(0, self\._focus_active_view\)', re.DOTALL)

new_view = '''    def _all_sidebar_btns(self):
        return [self.btn_dashboard, self.btn_explorer, self.btn_queue, self.btn_lang_prompt, self.btn_adv_prompt, self.btn_settings]

    def set_view(self, view: str):
        self.active_view = view
        for b in self._all_sidebar_btns():
            b.configure(fg_color="transparent", text_color=CURSOR_MUTED)
        
        btn_map = {
            "dashboard": (self.btn_dashboard, self.view_dashboard),
            "explorer": (self.btn_explorer, self.view_explorer),
            "queue": (self.btn_queue, self.view_queue),
            "lang_prompt": (self.btn_lang_prompt, self.view_lang_prompt),
            "adv_prompt": (self.btn_adv_prompt, self.view_adv_prompt),
            "settings": (self.btn_settings, self.view_settings),
        }
        
        if view in btn_map:
            btn, view_frame = btn_map[view]
            btn.configure(fg_color=CURSOR_PANEL, text_color=CURSOR_TEXT)
            view_frame.tkraise()
            
        self.after(0, self._focus_active_view)'''

content = pattern_view.sub(new_view, content)

# Remove self.status_version usage from where it was
# Actually, it might be safer to just ensure no errors if it's missing, but I didn't include it in new init.
# And also remove any self.sidebar_title references if they exist elsewhere (e.g. set_view used to have it).
# I already replaced set_view.

with open('ui/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated app.py successfully")
