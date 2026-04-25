import customtkinter as ctk
from ui.theme import *

class DashboardViewMixin:
    def _build_dashboard_view(self, parent):
        self.dashboard_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.dashboard_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.dash_header = ctk.CTkLabel(
            self.dashboard_frame, 
            text="Visão Geral", 
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=CURSOR_TEXT
        )
        self.dash_header.pack(anchor="w", pady=(0, 20))
        
        # Stats Cards Container
        self.stats_container = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        self.stats_container.pack(fill="x", pady=(0, 20))
        self.stats_container.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Stat Card 1: Status
        self.stat_status = self._create_stat_card(self.stats_container, "Servidor LLM", "Pronto", 0)
        
        # Stat Card 2: Queue
        self.stat_queue = self._create_stat_card(self.stats_container, "Fila de Espera", "0", 1)
        
        # Stat Card 3: Books Translated
        self.stat_done = self._create_stat_card(self.stats_container, "Concluídos", "0", 2)
        
        # Drop Zone / Welcome Area
        self.drop_zone = ctk.CTkFrame(
            self.dashboard_frame, 
            fg_color=CURSOR_CARD_BG, 
            corner_radius=R_MEDIUM,
            border_width=2,
            border_color=CURSOR_BORDER
        )
        self.drop_zone.pack(fill="both", expand=True)
        
        self.drop_label = ctk.CTkLabel(
            self.drop_zone,
            text="Pronto para Traduzir",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CURSOR_TEXT
        )
        self.drop_label.pack(expand=True, pady=(40, 0))
        
        self.drop_sub = ctk.CTkLabel(
            self.drop_zone,
            text="Vá para o separador Ficheiros para adicionar livros à fila.",
            font=ctk.CTkFont(size=14),
            text_color=CURSOR_MUTED
        )
        self.drop_sub.pack(expand=True, pady=(0, 40))

    def _create_stat_card(self, parent, title, value, col):
        card = ctk.CTkFrame(parent, fg_color=CURSOR_CARD_BG, corner_radius=R_MEDIUM)
        card.grid(row=0, column=col, padx=10, sticky="ew")
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color=CURSOR_MUTED)
        lbl_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=CURSOR_TEXT)
        lbl_val.pack(anchor="w", padx=15, pady=(0, 15))
        
        return lbl_val
    
    def update_dashboard_stats(self, queue_count, done_count):
        if hasattr(self, 'stat_queue'):
            self.stat_queue.configure(text=str(queue_count))
            self.stat_done.configure(text=str(done_count))
