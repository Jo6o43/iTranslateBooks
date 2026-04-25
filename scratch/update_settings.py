import sys

new_settings_view = """import os
import glob
import customtkinter as ctk
from src.config import DEFAULT_LANGUAGE_PROMPT, DEFAULT_ADVANCED_PROMPT
from src.paths_store import load_app_settings, save_app_settings, output_path_for_epub, ensure_books_dirs
from ui.theme import *
from tkinter import filedialog

class SettingsViewMixin:
    def _build_settings_view(self, parent):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=20, pady=20)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(wrap, fg_color="transparent")
        top_bar.grid(row=0, column=0, pady=(0, 15), sticky="ew")

        title = ctk.CTkLabel(top_bar, text="Definições", text_color=CURSOR_TEXT, font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")

        save_btn = ctk.CTkButton(
            top_bar,
            text="Guardar Definições",
            corner_radius=R_SMALL,
            fg_color=CURSOR_ACCENT,
            hover_color=CURSOR_ACCENT_HOVER,
            command=self.save_folder_paths,
        )
        save_btn.pack(side="right")

        form = ctk.CTkScrollableFrame(wrap, fg_color="transparent", label_text="")
        form.grid(row=1, column=0, sticky="nsew")
        form.grid_columnconfigure(0, weight=1)

        s0 = load_app_settings()

        # CARD 1: Folders
        c1 = ctk.CTkFrame(form, fg_color=CURSOR_CARD_BG, corner_radius=R_MEDIUM)
        c1.grid(row=0, column=0, pady=(0, 20), sticky="ew", ipady=10)
        c1.grid_columnconfigure(0, weight=1)
        
        c1_title = ctk.CTkLabel(c1, text="Diretórios", text_color=CURSOR_TEXT, font=ctk.CTkFont(size=16, weight="bold"))
        c1_title.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")

        self.books_in_label = ctk.CTkLabel(c1, text="Pasta de entrada (EPUBs a processar)", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=13))
        self.books_in_label.grid(row=1, column=0, padx=20, pady=(0, 4), sticky="w")

        in_row = ctk.CTkFrame(c1, fg_color="transparent")
        in_row.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")
        in_row.grid_columnconfigure(0, weight=1)

        self.books_in_entry = ctk.CTkEntry(in_row, placeholder_text="books_IN", corner_radius=R_SMALL, height=36)
        self.books_in_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        browse_in_btn = ctk.CTkButton(in_row, text="Procurar", width=80, height=36, corner_radius=R_SMALL, fg_color=CURSOR_PANEL, hover_color=CURSOR_BORDER, command=self.browse_books_in)
        browse_in_btn.grid(row=0, column=1, sticky="e")

        self.books_out_label = ctk.CTkLabel(c1, text="Pasta de saída (EPUBs traduzidos)", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=13))
        self.books_out_label.grid(row=3, column=0, padx=20, pady=(0, 4), sticky="w")

        out_row = ctk.CTkFrame(c1, fg_color="transparent")
        out_row.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        out_row.grid_columnconfigure(0, weight=1)

        self.books_out_entry = ctk.CTkEntry(out_row, placeholder_text="books_OUT", corner_radius=R_SMALL, height=36)
        self.books_out_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        browse_out_btn = ctk.CTkButton(out_row, text="Procurar", width=80, height=36, corner_radius=R_SMALL, fg_color=CURSOR_PANEL, hover_color=CURSOR_BORDER, command=self.browse_books_out)
        browse_out_btn.grid(row=0, column=1, sticky="e")


        # CARD 2: API
        c2 = ctk.CTkFrame(form, fg_color=CURSOR_CARD_BG, corner_radius=R_MEDIUM)
        c2.grid(row=1, column=0, pady=(0, 20), sticky="ew", ipady=10)
        c2.grid_columnconfigure(0, weight=1)
        
        c2_title = ctk.CTkLabel(c2, text="Servidor LLM", text_color=CURSOR_TEXT, font=ctk.CTkFont(size=16, weight="bold"))
        c2_title.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")

        self.url_label = ctk.CTkLabel(c2, text="Base URL da API local", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=13))
        self.url_label.grid(row=1, column=0, padx=20, pady=(0, 4), sticky="w")
        self.url_entry = ctk.CTkEntry(c2, placeholder_text="http://127.0.0.1:1234/v1", corner_radius=R_SMALL, height=36)
        self.url_entry.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.model_label = ctk.CTkLabel(c2, text="Modelo exposto pela API", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=13))
        self.model_label.grid(row=3, column=0, padx=20, pady=(0, 4), sticky="w")
        self.model_entry = ctk.CTkEntry(c2, placeholder_text="qwen3-v1-8b-instruct", corner_radius=R_SMALL, height=36)
        self.model_entry.grid(row=4, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.slider_label = ctk.CTkLabel(c2, text="Workers: 3", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=13))
        self.slider_label.grid(row=5, column=0, padx=20, pady=(0, 2), sticky="w")
        self.worker_slider = ctk.CTkSlider(c2, from_=1, to=8, number_of_steps=7, command=self.update_slider_label, corner_radius=R_SMALL, button_corner_radius=R_SMALL)
        self.worker_slider.set(3)
        self.worker_slider.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.temp_label = ctk.CTkLabel(c2, text="Temperature: 0.40", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=13))
        self.temp_label.grid(row=7, column=0, padx=20, pady=(0, 2), sticky="w")
        self.temp_slider = ctk.CTkSlider(c2, from_=0.0, to=1.0, number_of_steps=20, command=self.update_temp_label, corner_radius=R_SMALL, button_corner_radius=R_SMALL)
        self.temp_slider.set(0.4)
        self.temp_slider.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")


        # CARD 3: Options
        c3 = ctk.CTkFrame(form, fg_color=CURSOR_CARD_BG, corner_radius=R_MEDIUM)
        c3.grid(row=2, column=0, pady=(0, 20), sticky="ew", ipady=10)
        c3.grid_columnconfigure(0, weight=1)
        
        c3_title = ctk.CTkLabel(c3, text="Opções de Tradução", text_color=CURSOR_TEXT, font=ctk.CTkFont(size=16, weight="bold"))
        c3_title.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")

        self.glossary_label = ctk.CTkLabel(c3, text="Glossário Dinâmico (Ex: 'Mage: Mago')", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=13))
        self.glossary_label.grid(row=1, column=0, padx=20, pady=(0, 4), sticky="w")
        self.glossary_text = ctk.CTkTextbox(c3, height=60, corner_radius=R_SMALL, fg_color=CURSOR_BG, text_color=CURSOR_TEXT)
        self.glossary_text.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.context_checkbox = ctk.CTkCheckBox(c3, text="Usar Contexto Anterior (Reduz alucinações, ligeiramente mais lento)", corner_radius=R_SMALL)
        self.context_checkbox.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="w")

        self.report_checkbox = ctk.CTkCheckBox(c3, text="Guardar relatório TXT após tradução (Tempos, ficheiros e config)", corner_radius=R_SMALL)
        self.report_checkbox.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="w")


    def save_folder_paths(self):
        lang_text = self.lang_prompt_text.get("0.0", "end").strip() if hasattr(self, "lang_prompt_text") else DEFAULT_LANGUAGE_PROMPT
        adv_text = self.adv_prompt_text.get("0.0", "end").strip() if hasattr(self, "adv_prompt_text") else DEFAULT_ADVANCED_PROMPT
        save_app_settings(
            self.books_in_entry.get(),
            self.books_out_entry.get(),
            self.glossary_text.get("0.0", "end").strip(),
            bool(self.context_checkbox.get()),
            bool(self.report_checkbox.get()),
            self.url_entry.get().strip(),
            self.model_entry.get().strip(),
            int(self.worker_slider.get()),
            float(self.temp_slider.get()) if hasattr(self, "temp_slider") else 0.4,
            lang_text,
            self.custom_lang_prompts,
            adv_text,
            self.custom_adv_prompts,
            [i for i in self.queue_items if i.get("status") == "PENDING"] if hasattr(self, "queue_items") else [],
        )
        self._sync_books_paths_ui()
        self.refresh_books()
        self.log("[INFO] Definições guardadas com sucesso.")

    def browse_books_in(self):
        d = filedialog.askdirectory(initialdir=self.books_in_abs or os.getcwd())
        if d:
            self.books_in_entry.delete(0, "end")
            self.books_in_entry.insert(0, d)

    def browse_books_out(self):
        d = filedialog.askdirectory(initialdir=self.books_out_abs or os.getcwd())
        if d:
            self.books_out_entry.delete(0, "end")
            self.books_out_entry.insert(0, d)

    def _sync_books_paths_ui(self):
        self.books_in_abs, self.books_out_abs = ensure_books_dirs()
        s = load_app_settings()
        if hasattr(self, "books_in_entry"):
            self.books_in_entry.delete(0, "end")
            self.books_in_entry.insert(0, s["books_in_dir"])
            self.books_out_entry.delete(0, "end")
            self.books_out_entry.insert(0, s["books_out_dir"])
            self.glossary_text.delete("0.0", "end")
            self.glossary_text.insert("0.0", s.get("glossary", ""))
            if s.get("use_context", True):
                self.context_checkbox.select()
            else:
                self.context_checkbox.deselect()
            if s.get("save_translation_report", False):
                self.report_checkbox.select()
            else:
                self.report_checkbox.deselect()
                
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, s.get("base_url", "http://127.0.0.1:1234/v1"))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, s.get("model_name", "qwen3-v1-8b-instruct"))
            self.worker_slider.set(s.get("max_workers", 3))
            self.slider_label.configure(text=f"Workers: {int(s.get('max_workers', 3))}")
            if hasattr(self, "temp_slider"):
                t = float(s.get("temperature", 0.4))
                self.temp_slider.set(t)
                self.temp_label.configure(text=f"Temperature: {t:.2f}")

        self.custom_lang_prompts = s.get("custom_lang_prompts", {})
        self.custom_adv_prompts = s.get("custom_adv_prompts", {})
        if hasattr(self, "lang_prompt_text"):
            self.lang_prompt_text.delete("0.0", "end")
            self.lang_prompt_text.insert("0.0", s.get("language_prompt", DEFAULT_LANGUAGE_PROMPT))
            opts = ["Default"] + list(self.custom_lang_prompts.keys())
            self.lang_prompt_dropdown.configure(values=opts)
        if hasattr(self, "adv_prompt_text"):
            self.adv_prompt_text.delete("0.0", "end")
            self.adv_prompt_text.insert("0.0", s.get("advanced_prompt", DEFAULT_ADVANCED_PROMPT))
            opts = ["Default"] + list(self.custom_adv_prompts.keys())
            self.adv_prompt_dropdown.configure(values=opts)

        if hasattr(self, "books_path"):
            self.books_path.configure(text=f"{s['books_in_dir'].rstrip(os.sep).rstrip('/')}/")
        
        self.queue_items = s.get("pending_queue", [])
        if hasattr(self, "queue_list"):
            self.after(0, self._render_queue)
"""

with open('ui/settings_view.py', 'w', encoding='utf-8') as f:
    f.write(new_settings_view)

print("settings_view.py updated!")
