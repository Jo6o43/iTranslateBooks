import customtkinter as ctk
import os
import threading
import time

from src.config import AppConfig, APP_VERSION
from src.epub_core import process_epub
from src.paths_store import ensure_books_dirs

from ui.theme import *
from ui.explorer_view import ExplorerViewMixin
from ui.settings_view import SettingsViewMixin
from ui.prompt_view import PromptViewMixin
from ui.queue_panel import QueuePanelMixin
from ui.dashboard_view import DashboardViewMixin

class TranslatorApp(ctk.CTk, DashboardViewMixin, ExplorerViewMixin, SettingsViewMixin, PromptViewMixin, QueuePanelMixin):

    def __init__(self):
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

    def update_slider_label(self, value):
        self.slider_label.configure(text=f"Workers: {int(value)}")

    def update_temp_label(self, value):
        self.temp_label.configure(text=f"Temperature: {float(value):.2f}")

    def set_status(self, text: str):
        self.status_left.configure(text=text)

    def _safe_configure(self, widget, **kwargs):
        try:
            widget.configure(**kwargs)
        except Exception:
            pass

    def _make_accessible(self, widget, focus_style: dict, idle_style: dict | None = None):
        if idle_style is None:
            idle_style = {}
        self._safe_configure(widget, takefocus=True)
        widget.bind(
            "<FocusIn>",
            lambda _event, w=widget, style=focus_style: self._safe_configure(w, **style),
            add="+",
        )
        widget.bind(
            "<FocusOut>",
            lambda _event, w=widget, style=idle_style: self._safe_configure(w, **style),
            add="+",
        )

    def _register_keyboard_shortcuts(self):
        self.bind_all("<Alt-KeyPress-1>", lambda _event: self.set_view("explorer"), add="+")
        self.bind_all("<Alt-KeyPress-2>", lambda _event: self.set_view("lang_prompt"), add="+")
        self.bind_all("<Alt-KeyPress-3>", lambda _event: self.set_view("adv_prompt"), add="+")
        self.bind_all("<Alt-KeyPress-4>", lambda _event: self.set_view("settings"), add="+")
        self.bind_all("<Control-Return>", lambda _event: self.start_translation(), add="+")
        self.bind_all("<Escape>", lambda _event: self.stop_translation(), add="+")
        self.bind_all("<F5>", lambda _event: self.refresh_books() if self.active_view == "explorer" else None, add="+")
        self.bind_all("<Control-r>", lambda _event: self.refresh_books() if self.active_view == "explorer" else None, add="+")
        self.bind_all("<Control-s>", lambda _event: self.save_folder_paths(), add="+")

    def _focus_active_view(self):
        target = None
        if self.active_view == "explorer":
            target = self.checkboxes[0][0] if self.checkboxes else self.refresh_btn
        elif self.active_view == "lang_prompt":
            target = self.lang_prompt_dropdown
        elif self.active_view == "adv_prompt":
            target = self.adv_prompt_dropdown
        else:
            target = self.books_in_entry if hasattr(self, "books_in_entry") else None
        if target is not None:
            try:
                target.focus_set()
            except Exception:
                pass

    def _safe_startfile(self, path: str):
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            import platform
            import subprocess
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as e:
            self.log(f"[WARNING] Não foi possível abrir: {path} ({e})")

    def _resolve_path_from_entry(self, entry_widget):
        d = entry_widget.get().strip()
        if not d:
            from src.paths_store import PROJECT_ROOT
            return str(PROJECT_ROOT)
        if os.path.isabs(d):
            return d
        from src.paths_store import PROJECT_ROOT
        return os.path.normpath(os.path.join(str(PROJECT_ROOT), d))

    def open_books_in_folder(self):
        self._safe_startfile(self._resolve_path_from_entry(self.books_in_entry))

    def open_books_out_folder(self):
        self._safe_startfile(self._resolve_path_from_entry(self.books_out_entry))

    def clear_output(self):
        self.console.configure(state="normal")
        self.console.delete("0.0", "end")
        self.console.configure(state="disabled")

    def _all_sidebar_btns(self):
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
            
        self.after(0, self._focus_active_view)

    def log(self, msg):
        _MAX_LINES = 800
        _ARCHIVE_LINES = 250
        def append():
            self.console.configure(state="normal")
            self.console.insert("end", msg + "\n")
            # Summarize oldest lines instead of silently deleting them
            try:
                line_count = int(self.console.index("end-1c").split(".")[0])
                if line_count > _MAX_LINES:
                    self.console.delete("1.0", f"{_ARCHIVE_LINES + 1}.0")
                    self.console.insert(
                        "1.0",
                        f"[ … {_ARCHIVE_LINES} linhas anteriores arquivadas para libertar memória … ]\n"
                    )
            except Exception:
                pass
            self.console.see("end")
            self.console.configure(state="disabled")
        self.after(0, append)

    def update_progress(self, current, total, elapsed, eta, tps=None):
        def update():
            m, s = divmod(int(eta), 60)
            h, m = divmod(m, 60)
            time_str = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"
            pct = int(current / total * 100) if total > 0 else 0
            self.progress_bar.set(current / total if total > 0 else 0)
            tps_str = f" | Speed: {tps:.1f} t/s" if tps and tps > 0 else ""
            self.eta_label.configure(text=f"{pct}% | ETA: {time_str}{tps_str} | {current}/{total}")
            self.set_status(f"Em processamento: {current}/{total} ({pct}%)")
        self.after(0, update)

    def stop_translation(self):
        if self.is_running:
            self.cancel_event.set()
            self.log("[INFO] Pedido de cancelamento emitido. A aguardar o encerramento das tarefas ativas...")
            self.stop_btn.configure(state="disabled")
            self.set_status("A cancelar tradução")
            try:
                self.stop_btn.focus_set()
            except Exception:
                pass

    def start_translation(self):
        if self.is_running:
            return

        self.books_in_abs = self._resolve_path_from_entry(self.books_in_entry)
        self.books_out_abs = self._resolve_path_from_entry(self.books_out_entry)
        try:
            os.makedirs(self.books_in_abs, exist_ok=True)
            os.makedirs(self.books_out_abs, exist_ok=True)
        except OSError:
            pass

        selected_files = [item["input"] for item in self.queue_items if item.get("status") == "PENDING"]
        if not selected_files:
            self.log("[WARNING] Não há livros pendentes na fila para traduzir.")
            self.set_status("Nenhum livro pendente na fila")
            return

        self.is_running = True
        self.cancel_event.clear()
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.set_status(f"Tradução iniciada para {len(selected_files)} livro(s)")
        self.log("\n" + "="*40)
        self.log(f"[INFO] Tradução iniciada para {len(selected_files)} livro(s) pendente(s).")
        try:
            self.stop_btn.focus_set()
        except Exception:
            pass
        
        url = self.url_entry.get()
        model = self.model_entry.get()
        workers = int(self.worker_slider.get())
        temp = float(self.temp_slider.get())
        lang_prompt = self.lang_prompt_text.get("0.0", "end").strip()
        adv_prompt = self.adv_prompt_text.get("0.0", "end").strip()
        glossary = self.glossary_text.get("0.0", "end").strip()
        use_ctx = bool(self.context_checkbox.get())

        # Inject glossary into language prompt
        if glossary:
            glossary_block = f"TERMINOLOGY TO KEEP (DYNAMIC GLOSSARY):\n{glossary}"
        else:
            glossary_block = ""
        if "{GLOSSARY_SECTION}" in lang_prompt:
            lang_prompt = lang_prompt.replace("{GLOSSARY_SECTION}", glossary_block)
        else:
            lang_prompt += "\n" + glossary_block

        # Disparar numa worker thread para garantir que o UI não se congele.
        threading.Thread(target=self._worker_thread, args=(selected_files, url, model, workers, temp, lang_prompt, adv_prompt, use_ctx), daemon=True).start()

    def _worker_thread(self, files, url, model, workers, temp, lang_prompt, adv_prompt, use_ctx):
        self.log(f"[INFO] A verificar conexão ao servidor local ({url})...")
        import urllib.request
        try:
            req = urllib.request.Request(url.rstrip('/') + "/models", method='GET')
            with urllib.request.urlopen(req, timeout=3):
                pass
        except Exception:
            self.log(f"[ERROR] O servidor local falhou (LM Studio não está a correr em {url}). Tradução cancelada.")
            self.after(0, lambda: self.run_btn.configure(state="normal"))
            self.after(0, lambda: self.stop_btn.configure(state="disabled"))
            self.after(0, lambda: self.set_status("Falha na ligação ao servidor local"))
            self.is_running = False
            return

        succeeded = 0
        failed = 0
        cancelled = 0

        for file in files:
            self.log(f"\n--- Iniciando: {os.path.basename(file)} ---")

            output_file = next((item.get("output") for item in self.queue_items if item.get("input") == file), None)
            if not output_file:
                output_file = output_path_for_epub(file, self.books_out_abs)
            self._queue_set_status(file, "RUNNING")
            file_start = time.time()

            config = AppConfig(
                input_file=file,
                output_file=output_file,
                model_name=model,
                base_url=url,
                temperature=temp,
                language_prompt=lang_prompt,
                advanced_prompt=adv_prompt,
                max_workers=workers,
                use_context=use_ctx,
                save_translation_report=bool(self.report_checkbox.get()),
                cancel_event=self.cancel_event,
            )
            
            self.after(0, lambda: self.progress_bar.set(0))
            self.after(0, lambda: self.eta_label.configure(text="0% | ETA: Calculando... | 0/0"))
            
            success = process_epub(config, log_callback=self.log, progress_callback=self.update_progress)
            elapsed = time.time() - file_start

            if success:
                succeeded += 1
                self._queue_set_status(file, "DONE", elapsed)
            elif self.cancel_event.is_set():
                cancelled += 1
                self._queue_set_status(file, "CANCELLED", elapsed)
                for item in self.queue_items:
                    if item.get("status") == "PENDING":
                        item["status"] = "CANCELLED"
                self.after(0, self._render_queue)
                break
            else:
                failed += 1
                self._queue_set_status(file, "FAILED", elapsed)
            
        if self.cancel_event.is_set():
            final_status = f"Tradução cancelada após {succeeded} livro(s) concluído(s)"
        elif failed:
            final_status = f"Tradução concluída com {failed} falha(s)"
        else:
            final_status = f"Tradução concluída com {succeeded} livro(s)"

        self.log(f"\n[INFO] {final_status}.")
        self.after(0, lambda: self.run_btn.configure(state="normal"))
        self.after(0, lambda: self.stop_btn.configure(state="disabled"))
        self.after(0, lambda: self.set_status(final_status))
        self.after(0, lambda: self.run_btn.focus_set())
        self.is_running = False
