import threading
import tkinter as tk
from tkinter import messagebox, ttk

from config import ASSISTANT_NAME
from database import (
    delete_long_term_memory,
    delete_user_preference,
    get_conversation_summaries,
    get_long_term_memories,
    get_recent_chat_history,
    get_user_preferences,
    init_database,
    load_user_profile,
    save_long_term_memory,
    save_user_preference,
    save_user_profile,
    update_long_term_memory,
)
from speech_service import listen, test_voice_output
from voice_chat import chat_once


class AssistantLauncher:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{ASSISTANT_NAME} Assistant Hub")
        self.root.geometry("1120x820")
        self.root.minsize(980, 700)
        self.root.configure(bg="#f3ede6")

        init_database()

        self.status_var = tk.StringVar(value=f"{ASSISTANT_NAME} is ready.")
        self.name_var = tk.StringVar()
        self.mood_var = tk.StringVar()
        self.goal_var = tk.StringVar()
        self.memory_category_var = tk.StringVar(value="personal")
        self.memory_importance_var = tk.StringVar(value="3")
        self.preference_key_var = tk.StringVar()
        self.preference_value_var = tk.StringVar()
        self.message_var = tk.StringVar()
        self.speak_replies_var = tk.BooleanVar(value=False)
        self.voice_conversation_active = False
        self.selected_memory_id = None
        self.selected_preference_key = None
        self.memory_records = []
        self.preference_records = []

        self._configure_styles()
        self._build_ui()
        self._load_saved_profile()
        self.refresh_context_views()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background="#f3ede6")
        style.configure("Card.TFrame", background="#fffaf4")
        style.configure("HeaderCard.TFrame", background="#1d3b36")
        style.configure("TabCard.TFrame", background="#fffaf4")
        style.configure("App.TLabel", background="#f3ede6", foreground="#2f2a26", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background="#f3ede6", foreground="#6f6a64", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#fffaf4", foreground="#2f2a26", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#fffaf4", foreground="#2a211b", font=("Georgia", 12, "bold"))
        style.configure("HeroTitle.TLabel", background="#1d3b36", foreground="#f8efe6", font=("Georgia", 24, "bold"))
        style.configure("HeroBody.TLabel", background="#1d3b36", foreground="#d8e6dc", font=("Segoe UI", 11))
        style.configure("Status.TLabel", background="#dce8df", foreground="#23433b", font=("Segoe UI Semibold", 10), padding=(12, 6))
        style.configure("Accent.TButton", background="#c96f4a", foreground="#fffaf4", borderwidth=0, focusthickness=0, font=("Segoe UI Semibold", 10), padding=(12, 8))
        style.map("Accent.TButton", background=[("active", "#b85f3b"), ("disabled", "#dbc1b7")])
        style.configure("Soft.TButton", background="#ece1d6", foreground="#3d312a", borderwidth=0, focusthickness=0, font=("Segoe UI", 10), padding=(12, 8))
        style.map("Soft.TButton", background=[("active", "#dfd0c1"), ("disabled", "#f2ebe3")])
        style.configure("App.TEntry", fieldbackground="#fffdf9", foreground="#2f2a26", bordercolor="#d7c7b9", lightcolor="#d7c7b9", darkcolor="#d7c7b9", padding=8)
        style.configure("App.TCheckbutton", background="#f3ede6", foreground="#4d463f", font=("Segoe UI", 10))
        style.configure("App.TNotebook", background="#f3ede6", borderwidth=0)
        style.configure("App.TNotebook.Tab", background="#eadfd3", foreground="#5b5149", padding=(16, 10), font=("Segoe UI Semibold", 10))
        style.map("App.TNotebook.Tab", background=[("selected", "#fffaf4")], foreground=[("selected", "#1f2c28")])
        style.configure("Section.TLabelframe", background="#fffaf4", bordercolor="#eadfd3", relief="solid")
        style.configure("Section.TLabelframe.Label", background="#fffaf4", foreground="#2f2a26", font=("Georgia", 11, "bold"))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, style="App.TFrame", padding=18)
        outer.pack(fill="both", expand=True)

        header_card = ttk.Frame(outer, style="HeaderCard.TFrame", padding=20)
        header_card.pack(fill="x", pady=(0, 14))

        title_row = ttk.Frame(header_card, style="HeaderCard.TFrame")
        title_row.pack(fill="x")

        left = ttk.Frame(title_row, style="HeaderCard.TFrame")
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text=f"{ASSISTANT_NAME}", style="HeroTitle.TLabel").pack(anchor="w")
        ttk.Label(
            left,
            text="A calmer, market-aware assistant space for conversation, memory, and voice.",
            style="HeroBody.TLabel",
            wraplength=640,
        ).pack(anchor="w", pady=(8, 0))

        status_shell = ttk.Frame(title_row, style="HeaderCard.TFrame")
        status_shell.pack(side="right", anchor="n")
        ttk.Label(status_shell, textvariable=self.status_var, style="Status.TLabel").pack(anchor="e")

        notebook = ttk.Notebook(outer, style="App.TNotebook")
        notebook.pack(fill="both", expand=True)

        chat_tab = ttk.Frame(notebook, style="App.TFrame", padding=8)
        profile_tab = ttk.Frame(notebook, style="App.TFrame", padding=8)
        memory_tab = ttk.Frame(notebook, style="App.TFrame", padding=8)

        notebook.add(chat_tab, text="Chat")
        notebook.add(profile_tab, text="Profile")
        notebook.add(memory_tab, text="Memory")

        self._build_chat_tab(chat_tab)
        self._build_profile_tab(profile_tab)
        self._build_memory_tab(memory_tab)

    def _build_chat_tab(self, parent: ttk.Frame) -> None:
        top_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
        top_card.pack(fill="both", expand=True)

        intro_row = ttk.Frame(top_card, style="Card.TFrame")
        intro_row.pack(fill="x", pady=(0, 12))
        ttk.Label(intro_row, text="Conversation", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            intro_row,
            text="Type, speak once, or keep a flowing voice conversation going.",
            style="Card.TLabel",
        ).pack(anchor="w", pady=(6, 0))

        self.chat_output = tk.Text(
            top_card,
            wrap="word",
            height=22,
            state="disabled",
            bg="#fffdf9",
            fg="#2d2722",
            relief="flat",
            bd=0,
            padx=18,
            pady=18,
            font=("Segoe UI", 11),
            insertbackground="#2d2722",
            spacing1=2,
            spacing2=2,
            spacing3=8,
        )
        self.chat_output.pack(fill="both", expand=True)
        self.chat_output.tag_configure("user_name", foreground="#8a4e33", font=("Segoe UI Semibold", 10))
        self.chat_output.tag_configure("assistant_name", foreground="#2d6256", font=("Segoe UI Semibold", 10))
        self.chat_output.tag_configure("system_name", foreground="#6f6a64", font=("Segoe UI Semibold", 10))
        self.chat_output.tag_configure("message", lmargin1=10, lmargin2=10, rmargin=12)
        self.chat_output.tag_configure("spacer", spacing1=10)

        controls_card = ttk.Frame(top_card, style="Card.TFrame")
        controls_card.pack(fill="x", pady=(14, 0))

        self.message_entry = ttk.Entry(controls_card, textvariable=self.message_var, style="App.TEntry", font=("Segoe UI", 11))
        self.message_entry.pack(side="left", fill="x", expand=True)
        self.message_entry.bind("<Return>", self._on_send_message)

        self.send_button = ttk.Button(controls_card, text="Send", style="Accent.TButton", command=self.send_message)
        self.send_button.pack(side="left", padx=(10, 0))

        self.voice_button = ttk.Button(controls_card, text="Mic Once", style="Soft.TButton", command=self.capture_voice_message)
        self.voice_button.pack(side="left", padx=(10, 0))

        self.voice_conversation_button = ttk.Button(
            controls_card,
            text="Start Voice Loop",
            style="Soft.TButton",
            command=self.toggle_voice_conversation,
        )
        self.voice_conversation_button.pack(side="left", padx=(10, 0))

        lower_row = ttk.Frame(top_card, style="Card.TFrame")
        lower_row.pack(fill="x", pady=(14, 0))
        ttk.Button(lower_row, text="Refresh Chat", style="Soft.TButton", command=self.load_recent_chat).pack(side="left")
        ttk.Button(lower_row, text="Test Voice", style="Soft.TButton", command=self.run_voice_test).pack(side="left", padx=(10, 0))
        ttk.Checkbutton(lower_row, text="Speak Replies", style="App.TCheckbutton", variable=self.speak_replies_var).pack(side="left", padx=(14, 0))
        ttk.Label(lower_row, text="Voice loop keeps listening after each reply.", style="Muted.TLabel").pack(side="left", padx=(14, 0))

        self.load_recent_chat()

    def _build_profile_tab(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Profile", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text="Set the details Ava should remember as your baseline context.", style="Card.TLabel").pack(anchor="w", pady=(6, 14))

        form = ttk.Frame(card, style="Card.TFrame")
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        self._build_form_row(form, 0, "Name", self.name_var)
        self._build_form_row(form, 1, "Current mood", self.mood_var)
        self._build_form_row(form, 2, "Trading goal", self.goal_var)

        ttk.Button(card, text="Save Profile", style="Accent.TButton", command=self.save_profile).pack(anchor="w", pady=(16, 14))

        self.profile_summary = tk.Text(
            card,
            wrap="word",
            height=12,
            state="disabled",
            bg="#fffdf9",
            fg="#2d2722",
            relief="flat",
            bd=0,
            padx=16,
            pady=16,
            font=("Segoe UI", 11),
        )
        self.profile_summary.pack(fill="both", expand=True)

    def _build_memory_tab(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent, style="App.TFrame")
        top.pack(fill="x")

        memory_box = ttk.LabelFrame(top, text="Memory Editor", style="Section.TLabelframe", padding=14)
        memory_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        memory_box.columnconfigure(1, weight=1)

        self._build_labeled_entry(memory_box, 0, "Category", self.memory_category_var)
        self._build_labeled_entry(memory_box, 1, "Importance 1-5", self.memory_importance_var)
        ttk.Label(memory_box, text="Memory content", style="Card.TLabel").grid(row=2, column=0, sticky="nw", pady=6)
        self.memory_content = tk.Text(memory_box, wrap="word", height=6, bg="#fffdf9", fg="#2d2722", relief="flat", bd=0, padx=12, pady=12, font=("Segoe UI", 10))
        self.memory_content.grid(row=2, column=1, sticky="ew", pady=6)

        memory_buttons = ttk.Frame(memory_box, style="Card.TFrame")
        memory_buttons.grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Button(memory_buttons, text="Save New", style="Accent.TButton", command=self.save_memory).pack(side="left")
        ttk.Button(memory_buttons, text="Update", style="Soft.TButton", command=self.update_selected_memory).pack(side="left", padx=(8, 0))
        ttk.Button(memory_buttons, text="Delete", style="Soft.TButton", command=self.delete_selected_memory).pack(side="left", padx=(8, 0))
        ttk.Button(memory_buttons, text="Clear", style="Soft.TButton", command=self.clear_memory_editor).pack(side="left", padx=(8, 0))

        preference_box = ttk.LabelFrame(top, text="Preference Editor", style="Section.TLabelframe", padding=14)
        preference_box.pack(side="left", fill="both", expand=True, padx=(8, 0))
        preference_box.columnconfigure(1, weight=1)

        self._build_labeled_entry(preference_box, 0, "Preference key", self.preference_key_var)
        self._build_labeled_entry(preference_box, 1, "Preference value", self.preference_value_var)

        preference_buttons = ttk.Frame(preference_box, style="Card.TFrame")
        preference_buttons.grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Button(preference_buttons, text="Save", style="Accent.TButton", command=self.save_preference).pack(side="left")
        ttk.Button(preference_buttons, text="Delete", style="Soft.TButton", command=self.delete_selected_preference).pack(side="left", padx=(8, 0))
        ttk.Button(preference_buttons, text="Clear", style="Soft.TButton", command=self.clear_preference_editor).pack(side="left", padx=(8, 0))

        lower = ttk.Frame(parent, style="App.TFrame")
        lower.pack(fill="both", expand=True, pady=(14, 0))

        viewer_notebook = ttk.Notebook(lower, style="App.TNotebook")
        viewer_notebook.pack(fill="both", expand=True)

        memories_tab = ttk.Frame(viewer_notebook, style="Card.TFrame", padding=10)
        preferences_tab = ttk.Frame(viewer_notebook, style="Card.TFrame", padding=10)
        summaries_tab = ttk.Frame(viewer_notebook, style="Card.TFrame", padding=10)

        viewer_notebook.add(memories_tab, text="Memories")
        viewer_notebook.add(preferences_tab, text="Preferences")
        viewer_notebook.add(summaries_tab, text="Summaries")

        self.memory_listbox = tk.Listbox(memories_tab, bg="#fffdf9", fg="#2d2722", relief="flat", bd=0, font=("Segoe UI", 10), selectbackground="#d7e6df", selectforeground="#1d3b36")
        self.memory_listbox.pack(fill="both", expand=True)
        self.memory_listbox.bind("<<ListboxSelect>>", self.on_memory_select)

        self.preference_listbox = tk.Listbox(preferences_tab, bg="#fffdf9", fg="#2d2722", relief="flat", bd=0, font=("Segoe UI", 10), selectbackground="#eddccf", selectforeground="#5a3423")
        self.preference_listbox.pack(fill="both", expand=True)
        self.preference_listbox.bind("<<ListboxSelect>>", self.on_preference_select)

        self.summary_view = tk.Text(
            summaries_tab,
            wrap="word",
            state="disabled",
            bg="#fffdf9",
            fg="#2d2722",
            relief="flat",
            bd=0,
            padx=14,
            pady=14,
            font=("Segoe UI", 10),
        )
        self.summary_view.pack(fill="both", expand=True)

    def _build_form_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=7, padx=(0, 12))
        ttk.Entry(parent, textvariable=variable, style="App.TEntry", font=("Segoe UI", 11)).grid(row=row, column=1, sticky="ew", pady=7)

    def _build_labeled_entry(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 12))
        ttk.Entry(parent, textvariable=variable, style="App.TEntry", font=("Segoe UI", 10)).grid(row=row, column=1, sticky="ew", pady=6)

    def _set_text(self, widget: tk.Text, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def _append_chat(self, speaker: str, message: str) -> None:
        self.chat_output.configure(state="normal")
        if speaker == "You":
            name_tag = "user_name"
        elif speaker == ASSISTANT_NAME:
            name_tag = "assistant_name"
        else:
            name_tag = "system_name"
        self.chat_output.insert("end", f"{speaker}\n", (name_tag,))
        self.chat_output.insert("end", f"{message}\n\n", ("message",))
        self.chat_output.see("end")
        self.chat_output.configure(state="disabled")

    def _load_saved_profile(self) -> None:
        profile = load_user_profile()
        if not profile:
            self._set_text(self.profile_summary, "No profile saved yet.")
            return
        self.name_var.set(profile.get("name", ""))
        self.mood_var.set(profile.get("mood", ""))
        self.goal_var.set(profile.get("trading_goal", ""))
        self.refresh_profile_summary()

    def refresh_profile_summary(self) -> None:
        profile = load_user_profile()
        if not profile:
            self._set_text(self.profile_summary, "No profile saved yet.")
            return
        content = (
            f"Name: {profile.get('name', '')}\n\n"
            f"Current mood: {profile.get('mood', '')}\n\n"
            f"Trading goal: {profile.get('trading_goal', '')}"
        )
        self._set_text(self.profile_summary, content)

    def refresh_context_views(self) -> None:
        self.memory_records = get_long_term_memories(limit=None)
        self.preference_records = get_user_preferences(limit=200)
        summaries = get_conversation_summaries(limit=20)

        self.memory_listbox.delete(0, "end")
        for item in self.memory_records:
            label = f"#{item['id']}  {item['category']}  imp {item['importance']}  {item['content'][:90]}"
            self.memory_listbox.insert("end", label)

        self.preference_listbox.delete(0, "end")
        for item in self.preference_records:
            label = f"{item['key']}  ->  {item['value']}"
            self.preference_listbox.insert("end", label)

        if summaries:
            summary_text = "\n\n".join(
                f"Summary #{item['id']}\n{item['summary']}\n\nChats: {', '.join(str(chat_id) for chat_id in item.get('chat_ids', []))}"
                for item in summaries
            )
        else:
            summary_text = "No conversation summaries yet."
        self._set_text(self.summary_view, summary_text)
        self.refresh_profile_summary()

    def load_recent_chat(self) -> None:
        history = get_recent_chat_history(limit=20)
        self.chat_output.configure(state="normal")
        self.chat_output.delete("1.0", "end")

        if not history:
            self.chat_output.insert("1.0", "No chat history yet.\n")
        else:
            for item in history:
                self._append_chat("You", str(item.get("user_input", "")))
                self._append_chat(ASSISTANT_NAME, str(item.get("ai_response", "")))

        self.chat_output.configure(state="disabled")

    def save_profile(self) -> None:
        save_user_profile(
            self.name_var.get().strip(),
            self.mood_var.get().strip(),
            self.goal_var.get().strip(),
        )
        self.status_var.set("Profile saved.")
        self.refresh_profile_summary()

    def save_memory(self) -> None:
        content = self.memory_content.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Missing memory", "Please enter memory content first.")
            return
        try:
            importance = int(self.memory_importance_var.get().strip() or "3")
        except ValueError:
            messagebox.showwarning("Invalid importance", "Importance should be a number from 1 to 5.")
            return

        save_long_term_memory(
            self.memory_category_var.get().strip() or "personal",
            content,
            importance=importance,
            source="launcher",
        )
        self.clear_memory_editor()
        self.status_var.set("Long-term memory saved.")
        self.refresh_context_views()

    def update_selected_memory(self) -> None:
        if self.selected_memory_id is None:
            messagebox.showinfo("No selection", "Select a memory first.")
            return
        content = self.memory_content.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Missing memory", "Please enter memory content first.")
            return
        try:
            importance = int(self.memory_importance_var.get().strip() or "3")
        except ValueError:
            messagebox.showwarning("Invalid importance", "Importance should be a number from 1 to 5.")
            return

        update_long_term_memory(
            self.selected_memory_id,
            category=self.memory_category_var.get().strip() or "personal",
            content=content,
            importance=importance,
        )
        self.status_var.set("Memory updated.")
        self.refresh_context_views()

    def delete_selected_memory(self) -> None:
        if self.selected_memory_id is None:
            messagebox.showinfo("No selection", "Select a memory first.")
            return
        delete_long_term_memory(self.selected_memory_id)
        self.clear_memory_editor()
        self.status_var.set("Memory deleted.")
        self.refresh_context_views()

    def clear_memory_editor(self) -> None:
        self.selected_memory_id = None
        self.memory_category_var.set("personal")
        self.memory_importance_var.set("3")
        self.memory_content.delete("1.0", "end")
        self.memory_listbox.selection_clear(0, "end")

    def save_preference(self) -> None:
        key = self.preference_key_var.get().strip()
        value = self.preference_value_var.get().strip()
        if not key or not value:
            messagebox.showwarning("Missing preference", "Please enter both a key and a value.")
            return
        save_user_preference(key, value, source="launcher")
        self.clear_preference_editor()
        self.status_var.set("Preference saved.")
        self.refresh_context_views()

    def delete_selected_preference(self) -> None:
        if not self.selected_preference_key:
            messagebox.showinfo("No selection", "Select a preference first.")
            return
        delete_user_preference(self.selected_preference_key)
        self.clear_preference_editor()
        self.status_var.set("Preference deleted.")
        self.refresh_context_views()

    def clear_preference_editor(self) -> None:
        self.selected_preference_key = None
        self.preference_key_var.set("")
        self.preference_value_var.set("")
        self.preference_listbox.selection_clear(0, "end")

    def on_memory_select(self, event: tk.Event) -> None:
        selection = self.memory_listbox.curselection()
        if not selection:
            return
        item = self.memory_records[selection[0]]
        self.selected_memory_id = int(item["id"])
        self.memory_category_var.set(str(item.get("category", "personal")))
        self.memory_importance_var.set(str(item.get("importance", 3)))
        self.memory_content.delete("1.0", "end")
        self.memory_content.insert("1.0", str(item.get("content", "")))

    def on_preference_select(self, event: tk.Event) -> None:
        selection = self.preference_listbox.curselection()
        if not selection:
            return
        item = self.preference_records[selection[0]]
        self.selected_preference_key = item["key"]
        self.preference_key_var.set(item["key"])
        self.preference_value_var.set(item["value"])

    def _on_send_message(self, event: tk.Event) -> None:
        self.send_message()

    def send_message(self) -> None:
        user_text = self.message_var.get().strip()
        if not user_text:
            return
        self.message_var.set("")
        self._submit_user_message(user_text)

    def capture_voice_message(self) -> None:
        self.status_var.set("Listening through the microphone...")
        self._set_chat_controls_enabled(False, keep_conversation_button=True)
        threading.Thread(target=self._run_voice_capture, daemon=True).start()

    def _submit_user_message(self, user_text: str) -> None:
        self._append_chat("You", user_text)
        self.status_var.set(f"{ASSISTANT_NAME} is thinking...")
        self._set_chat_controls_enabled(False, keep_conversation_button=True)
        threading.Thread(target=self._run_chat_request, args=(user_text,), daemon=True).start()

    def _run_voice_capture(self) -> None:
        try:
            user_text = listen(
                timeout=8,
                phrase_time_limit=25,
                pause_threshold=1.0,
                non_speaking_duration=0.8,
            ).strip()
            self.root.after(0, lambda captured_text=user_text: self._handle_voice_capture(captured_text))
        except Exception as exc:
            self.root.after(0, lambda error=exc: self._handle_chat_error(error))

    def _handle_voice_capture(self, user_text: str) -> None:
        if not user_text:
            self._set_chat_controls_enabled(True)
            self.status_var.set("No speech was captured.")
            return
        self._submit_user_message(user_text)

    def _run_chat_request(self, user_text: str) -> None:
        try:
            ai_response = chat_once(user_text, speak_response=self.speak_replies_var.get())
            self.root.after(0, lambda response=ai_response: self._handle_chat_success(response))
        except Exception as exc:
            self.root.after(0, lambda error=exc: self._handle_chat_error(error))

    def _handle_chat_success(self, ai_response: str) -> None:
        self._append_chat(ASSISTANT_NAME, ai_response)
        self._set_chat_controls_enabled(True)
        self.status_var.set(f"{ASSISTANT_NAME} is ready.")
        self.refresh_context_views()

    def _handle_chat_error(self, exc: Exception) -> None:
        self._append_chat("System", f"Something went wrong: {exc}")
        self._set_chat_controls_enabled(True)
        self.status_var.set("The last request failed.")

    def run_voice_test(self) -> None:
        self.status_var.set("Testing voice output...")
        self.send_button.configure(state="disabled")
        self.voice_button.configure(state="disabled")
        threading.Thread(target=self._run_voice_test, daemon=True).start()

    def _run_voice_test(self) -> None:
        try:
            spoken_text = test_voice_output()
            self.root.after(0, lambda sample=spoken_text: self._handle_voice_test_success(sample))
        except Exception as exc:
            self.root.after(0, lambda error=exc: self._handle_chat_error(error))

    def _handle_voice_test_success(self, spoken_text: str) -> None:
        self._set_chat_controls_enabled(True)
        self.status_var.set("Voice test completed.")
        self._append_chat("System", f"Voice test spoken: {spoken_text}")

    def toggle_voice_conversation(self) -> None:
        if self.voice_conversation_active:
            self.voice_conversation_active = False
            self.voice_conversation_button.configure(text="Start Voice Loop")
            self.status_var.set("Voice conversation stopped.")
            self._set_chat_controls_enabled(True)
            return

        self.voice_conversation_active = True
        self.voice_conversation_button.configure(text="Stop Voice Loop")
        self.status_var.set("Continuous voice conversation started. Speak after each reply.")
        self.send_button.configure(state="disabled")
        self.voice_button.configure(state="disabled")
        threading.Thread(target=self._run_voice_conversation_loop, daemon=True).start()

    def _run_voice_conversation_loop(self) -> None:
        while self.voice_conversation_active:
            try:
                user_text = listen(
                    timeout=10,
                    phrase_time_limit=40,
                    pause_threshold=1.1,
                    non_speaking_duration=0.9,
                ).strip()
            except Exception as exc:
                self.root.after(0, lambda error=exc: self._handle_chat_error(error))
                break

            if not self.voice_conversation_active:
                break

            if not user_text:
                self.root.after(0, lambda: self.status_var.set("Still listening. Speak when you're ready, or stop the conversation."))
                continue

            self.root.after(0, lambda captured_text=user_text: self._append_chat("You", captured_text))
            self.root.after(0, lambda: self.status_var.set(f"{ASSISTANT_NAME} is thinking..."))

            try:
                ai_response = chat_once(user_text, speak_response=self.speak_replies_var.get())
            except Exception as exc:
                self.root.after(0, lambda error=exc: self._handle_chat_error(error))
                break

            if not self.voice_conversation_active:
                break

            self.root.after(0, lambda response=ai_response: self._handle_voice_conversation_reply(response))

        self.root.after(0, self._finish_voice_conversation_loop)

    def _handle_voice_conversation_reply(self, ai_response: str) -> None:
        self._append_chat(ASSISTANT_NAME, ai_response)
        self.refresh_context_views()
        if self.voice_conversation_active:
            self.status_var.set("Listening for your next message...")

    def _finish_voice_conversation_loop(self) -> None:
        if not self.voice_conversation_active:
            self.voice_conversation_button.configure(text="Start Voice Loop")
            self._set_chat_controls_enabled(True)
            return

        self.voice_conversation_active = False
        self.voice_conversation_button.configure(text="Start Voice Loop")
        self._set_chat_controls_enabled(True)
        self.status_var.set("Voice conversation stopped.")

    def _set_chat_controls_enabled(self, enabled: bool, keep_conversation_button: bool = False) -> None:
        self.send_button.configure(state="normal" if enabled else "disabled")
        self.voice_button.configure(state="normal" if enabled else "disabled")
        if not keep_conversation_button:
            self.voice_conversation_button.configure(state="normal" if enabled else "disabled")


def main() -> None:
    root = tk.Tk()
    app = AssistantLauncher(root)
    app.message_entry.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
