import os
import glob
import customtkinter as ctk
from src.config import DEFAULT_LANGUAGE_PROMPT, DEFAULT_ADVANCED_PROMPT
from src.paths_store import load_app_settings, save_app_settings, output_path_for_epub
from ui.theme import *
from tkinter import filedialog

class PromptViewMixin:
    def _build_prompt_view(self, parent, mode: str):
        """mode='lang' for Language Prompt, mode='adv' for Advanced Prompt."""
        is_lang = (mode == "lang")
        default_text = DEFAULT_LANGUAGE_PROMPT if is_lang else DEFAULT_ADVANCED_PROMPT
        hint_text = (
            "Regras de linguagem, estilo e concordância. Suporta {GLOSSARY_SECTION}."
            if is_lang else
            "Regras técnicas de formatação XML/HTML e Drop Caps."
        )
        title_text = "Prompt de Idioma" if is_lang else "Prompt Avançado"

        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=20, pady=20)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(wrap, fg_color="transparent")
        header.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header, text=title_text, text_color=CURSOR_TEXT, font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, sticky="w")
        
        hint = ctk.CTkLabel(header, text=hint_text, text_color=CURSOR_MUTED, font=ctk.CTkFont(size=13))
        hint.grid(row=1, column=0, sticky="w", pady=(4, 0))

        card = ctk.CTkFrame(wrap, fg_color=CURSOR_CARD_BG, corner_radius=R_MEDIUM)
        card.grid(row=2, column=0, sticky="nsew", ipady=10)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="ew")
        controls.grid_columnconfigure(1, weight=1) # Spacer

        # Preset Dropdown
        preset_frame = ctk.CTkFrame(controls, fg_color="transparent")
        preset_frame.pack(side="left", fill="y")
        
        ctk.CTkLabel(preset_frame, text="Preset Atual", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 2))
        dropdown = ctk.CTkOptionMenu(
            preset_frame, values=["Default"],
            command=lambda c, m=mode: self._on_prompt_selected(c, m),
            corner_radius=R_SMALL,
            height=36,
            fg_color=CURSOR_PANEL,
            button_color=CURSOR_BORDER,
            button_hover_color=CURSOR_ACCENT
        )
        dropdown.pack(fill="x")

        # New Preset Input
        new_frame = ctk.CTkFrame(controls, fg_color="transparent")
        new_frame.pack(side="left", fill="y", padx=(20, 0))
        
        ctk.CTkLabel(new_frame, text="Criar / Atualizar", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 2))
        input_wrap = ctk.CTkFrame(new_frame, fg_color="transparent")
        input_wrap.pack(fill="x")
        
        name_entry = ctk.CTkEntry(input_wrap, placeholder_text="Nome do preset...", corner_radius=R_SMALL, height=36, width=150)
        name_entry.pack(side="left")
        
        add_prompt_btn = ctk.CTkButton(
            input_wrap, text="+ Salvar", width=80, height=36, corner_radius=R_SMALL,
            fg_color=CURSOR_ACCENT, hover_color=CURSOR_ACCENT_HOVER,
            command=lambda m=mode: self._add_custom_prompt(m),
        )
        add_prompt_btn.pack(side="left", padx=(10, 0))

        # Delete Button
        del_frame = ctk.CTkFrame(controls, fg_color="transparent")
        del_frame.pack(side="right", fill="y")
        
        ctk.CTkLabel(del_frame, text="", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 2)) # Spacer
        del_btn = ctk.CTkButton(
            del_frame, text="Apagar", width=80, height=36, corner_radius=R_SMALL,
            fg_color="transparent", border_width=1, border_color=CURSOR_DANGER,
            hover_color=CURSOR_DANGER_HOVER, text_color=CURSOR_DANGER,
            command=lambda m=mode: self._del_custom_prompt(m),
        )
        del_btn.pack(side="right")
        del_btn.configure(state="disabled")

        textbox = ctk.CTkTextbox(
            card, fg_color=CURSOR_BG, text_color=CURSOR_TEXT,
            border_width=1, border_color=CURSOR_BORDER, corner_radius=R_SMALL,
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        textbox.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nsew")
        textbox.insert("0.0", default_text)

        if is_lang:
            self.lang_prompt_dropdown = dropdown
            self.lang_prompt_name_entry = name_entry
            self.lang_prompt_text = textbox
            self.lang_del_btn = del_btn
        else:
            self.adv_prompt_dropdown = dropdown
            self.adv_prompt_name_entry = name_entry
            self.adv_prompt_text = textbox
            self.adv_del_btn = del_btn

    def _on_prompt_selected(self, choice, mode):
        is_lang = (mode == "lang")
        textbox = self.lang_prompt_text if is_lang else self.adv_prompt_text
        del_btn = self.lang_del_btn if is_lang else self.adv_del_btn
        presets = self.custom_lang_prompts if is_lang else self.custom_adv_prompts
        default = DEFAULT_LANGUAGE_PROMPT if is_lang else DEFAULT_ADVANCED_PROMPT
        textbox.delete("0.0", "end")
        textbox.insert("0.0", presets.get(choice, default))
        # Only allow delete for non-default presets
        del_btn.configure(state=("normal" if choice != "Default" else "disabled"))

    def _add_custom_prompt(self, mode):
        is_lang = (mode == "lang")
        name_entry = self.lang_prompt_name_entry if is_lang else self.adv_prompt_name_entry
        textbox = self.lang_prompt_text if is_lang else self.adv_prompt_text
        dropdown = self.lang_prompt_dropdown if is_lang else self.adv_prompt_dropdown
        presets = self.custom_lang_prompts if is_lang else self.custom_adv_prompts
        name = name_entry.get().strip()
        if not name or name.lower() == "default":
            self.log("[WARNING] Nome de preset inválido.")
            return
        presets[name] = textbox.get("0.0", "end").strip()
        name_entry.delete(0, "end")
        opts = ["Default"] + list(presets.keys())
        dropdown.configure(values=opts)
        dropdown.set(name)
        self.save_folder_paths()

    def _del_custom_prompt(self, mode):
        is_lang = (mode == "lang")
        dropdown = self.lang_prompt_dropdown if is_lang else self.adv_prompt_dropdown
        del_btn = self.lang_del_btn if is_lang else self.adv_del_btn
        presets = self.custom_lang_prompts if is_lang else self.custom_adv_prompts
        choice = dropdown.get()
        if choice == "Default":
            return
        if choice in presets:
            del presets[choice]
            opts = ["Default"] + list(presets.keys())
            dropdown.configure(values=opts)
            dropdown.set("Default")
            del_btn.configure(state="disabled")
            self._on_prompt_selected("Default", mode)
            self.save_folder_paths()

    def reset_system_prompt(self):
        if hasattr(self, "lang_prompt_text"):
            self.lang_prompt_text.delete("0.0", "end")
            self.lang_prompt_text.insert("0.0", DEFAULT_LANGUAGE_PROMPT)
            self.lang_prompt_dropdown.set("Default")
            self.lang_del_btn.configure(state="disabled")
            self.set_view("lang_prompt")
