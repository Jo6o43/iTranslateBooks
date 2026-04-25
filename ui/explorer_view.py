import os
import glob
import customtkinter as ctk
from src.config import DEFAULT_LANGUAGE_PROMPT, DEFAULT_ADVANCED_PROMPT
from src.paths_store import load_app_settings, save_app_settings, output_path_for_epub
from ui.theme import *
from tkinter import filedialog

class ExplorerViewMixin:
    def _build_explorer_view(self, parent):
        self.explorer_view = ctk.CTkFrame(parent, fg_color="transparent")
        self.explorer_view.pack(fill="both", expand=True, padx=20, pady=20)
        
        header = ctk.CTkFrame(self.explorer_view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        header.grid_columnconfigure(0, weight=1)

        self.books_path = ctk.CTkLabel(header, text="Ficheiros", text_color=CURSOR_TEXT, font=ctk.CTkFont(size=24, weight="bold"))
        self.books_path.grid(row=0, column=0, sticky="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")

        self.refresh_btn = ctk.CTkButton(
            actions,
            text="Atualizar",
            width=100,
            height=36,
            corner_radius=R_SMALL,
            fg_color=CURSOR_CARD_BG,
            hover_color=CURSOR_BORDER,
            command=self.refresh_books,
        )
        self.refresh_btn.pack(side="left")

        self.books_frame = ctk.CTkScrollableFrame(self.explorer_view, fg_color="transparent", label_text="")
        self.books_frame.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(self.explorer_view, fg_color=CURSOR_CARD_BG, corner_radius=R_MEDIUM)
        footer.pack(fill="x", pady=(15, 0))
        footer.grid_columnconfigure(0, weight=1)

        sel_frame = ctk.CTkFrame(footer, fg_color="transparent")
        sel_frame.grid(row=0, column=0, sticky="w", padx=15, pady=15)

        self.select_all_btn = ctk.CTkButton(
            sel_frame,
            text="Selecionar Todos",
            width=120,
            height=36,
            corner_radius=R_SMALL,
            fg_color=CURSOR_PANEL,
            border_width=1,
            border_color=CURSOR_BORDER,
            hover_color=CURSOR_BORDER,
            command=lambda: self._set_all_books(True),
        )
        self.select_all_btn.pack(side="left", padx=(0, 10))

        self.clear_all_btn = ctk.CTkButton(
            sel_frame,
            text="Limpar Seleção",
            width=120,
            height=36,
            corner_radius=R_SMALL,
            fg_color=CURSOR_PANEL,
            border_width=1,
            border_color=CURSOR_BORDER,
            hover_color=CURSOR_BORDER,
            command=lambda: self._set_all_books(False),
        )
        self.clear_all_btn.pack(side="left")

        self.add_to_queue_btn = ctk.CTkButton(
            footer,
            text="📥 Adicionar à Fila",
            width=150,
            height=36,
            corner_radius=R_SMALL,
            fg_color=CURSOR_ACCENT,
            hover_color=CURSOR_ACCENT_HOVER,
            font=ctk.CTkFont(weight="bold"),
            command=self.add_selected_to_queue,
        )
        self.add_to_queue_btn.grid(row=0, column=1, sticky="e", padx=15, pady=15)

    def add_selected_to_queue(self):
        selected_files = [file for cb, file in self.checkboxes if cb.get()]
        if not selected_files:
            self.log("[WARNING] Nenhum livro selecionado para adicionar!")
            return
        
        self.books_out_abs = self._resolve_path_from_entry(self.books_out_entry)
        added = 0
        existing = {item["input"] for item in self.queue_items}
        for f in selected_files:
            if f not in existing:
                out = output_path_for_epub(f, self.books_out_abs)
                self.queue_items.append({"input": f, "output": out, "status": "PENDING", "seconds": None})
                added += 1
                existing.add(f)
        
        self._set_all_books(False)
        if added > 0:
            self.log(f"[INFO] Adicionados {added} livros à fila.")
            self._render_queue()
            # Update dashboard stats
            done_count = sum(1 for i in self.queue_items if i.get("status") == "DONE")
            self.update_dashboard_stats(len(self.queue_items), done_count)
        else:
            self.log("[INFO] Os livros selecionados já estavam na fila.")

    def _set_all_books(self, checked: bool):
        for cb, _ in self.checkboxes:
            if checked:
                cb.select()
            else:
                cb.deselect()

    def refresh_books(self):
        for cb, _ in self.checkboxes:
            cb.destroy()
        self.checkboxes.clear()
        
        self.books_in_abs = self._resolve_path_from_entry(self.books_in_entry)
        self.books_out_abs = self._resolve_path_from_entry(self.books_out_entry)

        try:
            os.makedirs(self.books_in_abs, exist_ok=True)
        except OSError:
            pass

        pattern = os.path.join(self.books_in_abs, "*.epub")
        files = glob.glob(pattern)
        
        for child in self.books_frame.winfo_children():
            child.destroy()
            
        if not files:
            empty = ctk.CTkLabel(self.books_frame, text="Nenhum EPUB encontrado.", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=14))
            empty.pack(pady=40)
            
        for i, file in enumerate(files):
            filename = os.path.basename(file)
            row = ctk.CTkFrame(self.books_frame, fg_color=CURSOR_CARD_BG, corner_radius=R_SMALL)
            row.pack(fill="x", pady=4, padx=4)
            
            cb = ctk.CTkCheckBox(
                row,
                text=filename,
                corner_radius=R_SMALL,
                font=ctk.CTkFont(size=13),
                checkbox_height=20,
                checkbox_width=20,
            )
            cb.pack(side="left", padx=15, pady=12)
            self._make_accessible(
                cb,
                {"border_color": CURSOR_FOCUS},
                {"border_color": CURSOR_BORDER},
            )
            self.checkboxes.append((cb, file))
        self.set_status(f"{len(files)} EPUB(s) encontrados")
        self._focus_active_view()
