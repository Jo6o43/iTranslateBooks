import os
import glob
import customtkinter as ctk
from src.config import DEFAULT_LANGUAGE_PROMPT, DEFAULT_ADVANCED_PROMPT
from src.paths_store import load_app_settings, save_app_settings, output_path_for_epub
from ui.theme import *
from tkinter import filedialog

class QueuePanelMixin:
    def _build_queue_panel(self):
        self.queue_panel = ctk.CTkFrame(self.editor_body, fg_color="transparent")
        self.queue_panel.pack(fill="both", expand=True, padx=20, pady=20)
        
        header = ctk.CTkFrame(self.queue_panel, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header, text="Fila de Espera", text_color=CURSOR_TEXT, font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, sticky="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")

        self.queue_clear_btn = ctk.CTkButton(
            actions,
            text="Limpar Fila",
            width=100,
            height=36,
            corner_radius=R_SMALL,
            fg_color=CURSOR_CARD_BG,
            hover_color=CURSOR_BORDER,
            command=self.clear_queue,
        )
        self.queue_clear_btn.pack(side="left", padx=(0, 10))

        self.queue_list = ctk.CTkScrollableFrame(self.queue_panel, fg_color="transparent", label_text="")
        self.queue_list.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(self.queue_panel, fg_color=CURSOR_CARD_BG, corner_radius=R_MEDIUM)
        footer.pack(fill="x", pady=(15, 0))
        footer.grid_columnconfigure(0, weight=1)

        self.queue_hint = ctk.CTkLabel(
            footer,
            text=" Vá ao separador Ficheiros para adicionar livros.",
            text_color=CURSOR_MUTED,
            font=ctk.CTkFont(size=13),
        )
        self.queue_hint.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        self.run_controls = ctk.CTkFrame(footer, fg_color="transparent")
        self.run_controls.grid(row=0, column=1, padx=15, pady=15, sticky="e")

        self.run_btn = ctk.CTkButton(
            self.run_controls,
            text="▶ INICIAR",
            width=120,
            height=36,
            corner_radius=R_SMALL,
            fg_color=CURSOR_ACCENT,
            hover_color=CURSOR_ACCENT_HOVER,
            font=ctk.CTkFont(weight="bold"),
            command=self.start_translation,
        )
        self.run_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            self.run_controls,
            text="⏹ Cancelar",
            width=100,
            height=36,
            corner_radius=R_SMALL,
            fg_color=CURSOR_DANGER,
            hover_color=CURSOR_DANGER_HOVER,
            command=self.stop_translation,
            state="disabled",
        )
        self.stop_btn.pack(side="left")

        self._render_queue()

    def clear_queue(self):
        if self.is_running:
            self.log("[WARNING] Não é possível limpar a fila durante a execução.")
            return
        self.queue_items = []
        self._render_queue()

    def remove_from_queue(self, input_file):
        if self.is_running:
            self.log("[WARNING] Não é possível remover da fila durante a execução.")
            return
        self.queue_items = [item for item in self.queue_items if item.get("input") != input_file]
        self._render_queue()
        self.log(f"[INFO] Removido da fila: {os.path.basename(input_file)}")

    def _queue_status_color(self, status: str) -> str:
        status = (status or "").upper()
        if status == "RUNNING":
            return CURSOR_ACCENT
        if status == "DONE":
            return CURSOR_SUCCESS
        if status in ("FAILED", "CANCELLED"):
            return CURSOR_DANGER
        return CURSOR_MUTED

    def _queue_status_label(self, status: str) -> str:
        status = (status or "").upper()
        if status == "RUNNING":
            return "Em Execução..."
        if status == "DONE":
            return "Concluído"
        if status == "FAILED":
            return "Falhou"
        if status == "CANCELLED":
            return "Cancelado"
        return "Pendente"

    def _render_queue(self):
        for child in self.queue_list.winfo_children():
            child.destroy()

        if not self.queue_items:
            empty = ctk.CTkLabel(self.queue_list, text="Nenhum livro na fila.", text_color=CURSOR_MUTED, font=ctk.CTkFont(size=14))
            empty.pack(pady=40)
            return

        for i, item in enumerate(self.queue_items):
            status = item.get("status", "PENDING")
            secs = item.get("seconds")
            dur = f"{int(secs)}s" if isinstance(secs, (int, float)) else ""
            base = os.path.basename(item.get("input", ""))
            out_path = item.get("output")

            row = ctk.CTkFrame(self.queue_list, fg_color=CURSOR_CARD_BG, corner_radius=R_MEDIUM)
            row.pack(fill="x", pady=6, padx=4)
            row.grid_columnconfigure(0, weight=1)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.grid(row=0, column=0, padx=15, pady=12, sticky="ew")
            left.grid_columnconfigure(0, weight=1)

            name_lbl = ctk.CTkLabel(left, text=base, text_color=CURSOR_TEXT, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
            name_lbl.grid(row=0, column=0, sticky="w")

            meta = f"{self._queue_status_label(status)}{(' • ' + dur) if dur else ''}"
            status_lbl = ctk.CTkLabel(left, text=meta, text_color=self._queue_status_color(status), font=ctk.CTkFont(size=12))
            status_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.grid(row=0, column=1, padx=15, sticky="e")

            open_btn = ctk.CTkButton(
                actions,
                text="Abrir",
                width=80,
                height=36,
                corner_radius=R_SMALL,
                fg_color=CURSOR_PANEL,
                hover_color=CURSOR_BORDER,
                command=(lambda p=out_path: self._safe_startfile(p)) if out_path else None,
                state=("normal" if (out_path and status.upper() == "DONE") else "disabled"),
            )
            open_btn.pack(side="left", padx=(0, 10))

            remove_btn = ctk.CTkButton(
                actions,
                text="✕",
                width=36,
                height=36,
                corner_radius=R_SMALL,
                fg_color="transparent",
                hover_color=CURSOR_DANGER_HOVER,
                text_color=CURSOR_DANGER,
                command=lambda f=item.get("input"): self.remove_from_queue(f),
                state="disabled" if self.is_running else "normal",
            )
            remove_btn.pack(side="left")

    def _queue_set_status(self, input_file: str, status: str, seconds: float | None = None):
        for item in self.queue_items:
            if item.get("input") == input_file:
                item["status"] = status
                if seconds is not None:
                    item["seconds"] = seconds
                break
        self.after(0, self._render_queue)

