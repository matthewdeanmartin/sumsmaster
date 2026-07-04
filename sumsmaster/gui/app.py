"""Tkinter application: screens, navigation and event wiring.

One ``Tk`` root hosts a stack of ``ttk.Frame`` screens swapped in place:

* ProfileScreen   — pick/create/delete an unauthenticated local profile
* DashboardScreen — plan, mastery summary, per-trick progress, actions
* PracticeScreen  — the answer loop, with resume support
* TricksScreen    — the trick taxonomy, grouped by operation
* CoverageScreen  — the phase-0 coverage report (computed off-thread)

All learning logic lives in :mod:`sumsmaster.gui.practice` and
:mod:`sumsmaster.gui.store`; this module is presentation only.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Literal

from sumsmaster import coverage as coverage_mod
from sumsmaster.__about__ import __version__
from sumsmaster.gui.plans import ALL_PLANS, DEFAULT_PLAN_ID, get_plan
from sumsmaster.gui.practice import PracticeSession
from sumsmaster.gui.store import DEFAULT_PROFILE_NAME, MASTERY_STREAK, Profile, ProfileStore, slugify
from sumsmaster.tricks import ALL_TRICKS, Operation

PAD = 12


class App(tk.Tk):
    """Application root: owns the store, the active profile, and the router."""

    def __init__(self, store: ProfileStore | None = None) -> None:
        super().__init__()
        self.title(f"Sumsmaster {__version__} — free edition")
        self.geometry("760x560")
        self.minsize(620, 460)

        style = ttk.Style(self)
        for theme in ("vista", "aqua", "clam"):  # best native fit per platform
            if theme in style.theme_names():
                style.theme_use(theme)
                break
        style.configure("Mastery.Horizontal.TProgressbar", thickness=14)

        self.store = store or ProfileStore()
        self.store.ensure_default()
        self.profile: Profile | None = None
        self.session: PracticeSession | None = None

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.screens: dict[str, Screen] = {}
        for cls in (ProfileScreen, DashboardScreen, PracticeScreen, TricksScreen, CoverageScreen):
            screen = cls(container, self)
            self.screens[cls.__name__] = screen
            screen.grid(row=0, column=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show("ProfileScreen")

    # -- navigation -----------------------------------------------------------

    def show(self, name: str) -> None:
        screen = self.screens[name]
        screen.refresh()
        screen.tkraise()

    def select_profile(self, profile: Profile) -> None:
        self.profile = profile
        self.store.remember_profile(profile.slug)
        self.show("DashboardScreen")

    def save_profile(self) -> None:
        if self.profile is not None:
            self.store.save(self.profile)

    def _on_close(self) -> None:
        # Mid-session state is already synced into the profile after every
        # answer; a final save makes close-mid-session resumable.
        self.save_profile()
        self.destroy()


class Screen(ttk.Frame):
    """Base class: subclasses override refresh() to rebuild from state."""

    def __init__(self, parent: ttk.Frame, app: App) -> None:
        super().__init__(parent, padding=PAD)
        self.app = app

    def refresh(self) -> None:  # pragma: no cover - trivial default
        pass


# ---------------------------------------------------------------------------
# Profile picker
# ---------------------------------------------------------------------------


class ProfileScreen(Screen):
    def __init__(self, parent: ttk.Frame, app: App) -> None:
        super().__init__(parent, app)
        self.profiles: list[Profile] = []
        ttk.Label(self, text="Who is practicing?", font=("", 16, "bold")).pack(anchor="w", pady=(0, PAD))

        self.listbox = tk.Listbox(self, height=8, exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda _e: self._open_selected())

        row = ttk.Frame(self)
        row.pack(fill="x", pady=(PAD, 0))
        ttk.Button(row, text="Use selected profile", command=self._open_selected).pack(side="left")
        ttk.Button(row, text="Delete", command=self._delete_selected).pack(side="left", padx=(8, 0))

        # -- create-new form --------------------------------------------------
        form = ttk.Labelframe(self, text="Create a profile", padding=PAD)
        form.pack(fill="x", pady=(PAD, 0))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        entry = ttk.Entry(form, textvariable=self.name_var)
        entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        entry.bind("<Return>", lambda _e: self._create())

        ttk.Label(form, text="Plan:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.plan_var = tk.StringVar(value=DEFAULT_PLAN_ID)
        plan_box = ttk.Combobox(
            form,
            textvariable=self.plan_var,
            state="readonly",
            values=[p.id for p in ALL_PLANS],
        )
        plan_box.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        plan_box.bind("<<ComboboxSelected>>", lambda _e: self._describe_plan())

        self.plan_desc = ttk.Label(form, text="", wraplength=480, foreground="gray")
        self.plan_desc.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self._describe_plan()

        ttk.Button(form, text="Create and start", command=self._create).grid(
            row=3, column=0, columnspan=2, sticky="e", pady=(8, 0)
        )

    def refresh(self) -> None:
        self.profiles = self.app.store.list_profiles()
        self.listbox.delete(0, "end")
        last = self.app.store.last_profile_slug()
        select_index = 0
        for i, profile in enumerate(self.profiles):
            plan = get_plan(profile.plan)
            mastered = sum(1 for p in profile.progress.values() if p.mastered)
            self.listbox.insert("end", f"{profile.name}   —   {plan.name}, {mastered} tricks mastered")
            if profile.slug == last:
                select_index = i
        if self.profiles:
            self.listbox.selection_set(select_index)

    def _describe_plan(self) -> None:
        plan = get_plan(self.plan_var.get())
        self.plan_desc.config(text=f"{plan.name}: {plan.description}")

    def _selected(self) -> Profile | None:
        sel = self.listbox.curselection()  # type: ignore[no-untyped-call]  # tkinter stub gap
        return self.profiles[sel[0]] if sel else None

    def _open_selected(self) -> None:
        profile = self._selected()
        if profile is None:
            messagebox.showinfo("Sumsmaster", "Select a profile first.")
            return
        self.app.select_profile(profile)

    def _delete_selected(self) -> None:
        profile = self._selected()
        if profile is None:
            return
        if profile.slug == slugify(DEFAULT_PROFILE_NAME):
            messagebox.showinfo("Sumsmaster", "The default profile can't be deleted.")
            return
        if messagebox.askyesno(
            "Delete profile",
            f"Delete '{profile.name}' and all of its progress? This can't be undone.",
        ):
            self.app.store.delete(profile.slug)
            self.refresh()

    def _create(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showinfo("Sumsmaster", "Enter a name for the profile.")
            return
        if self.app.store.exists(name):
            messagebox.showinfo("Sumsmaster", f"A profile named '{name}' already exists.")
            return
        profile = Profile(name=name, plan=self.plan_var.get())
        self.app.store.save(profile)
        self.name_var.set("")
        self.app.select_profile(profile)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class DashboardScreen(Screen):
    def __init__(self, parent: ttk.Frame, app: App) -> None:
        super().__init__(parent, app)
        self.header = ttk.Label(self, text="", font=("", 16, "bold"))
        self.header.pack(anchor="w")
        self.summary = ttk.Label(self, text="")
        self.summary.pack(anchor="w", pady=(4, 4))
        self.mastery_bar = ttk.Progressbar(self, style="Mastery.Horizontal.TProgressbar", maximum=1, value=0)
        self.mastery_bar.pack(fill="x", pady=(0, PAD))

        table = ttk.Frame(self)
        table.pack(side="top", fill="both", expand=True)
        columns = ("trick", "attempts", "accuracy", "streak", "mastered")
        self.tree = ttk.Treeview(table, columns=columns, show="headings", height=12)
        headings: dict[str, tuple[str, int, Literal["w", "center"]]] = {
            "trick": ("Trick", 280, "w"),
            "attempts": ("Attempts", 80, "center"),
            "accuracy": ("Accuracy", 80, "center"),
            "streak": ("Streak", 70, "center"),
            "mastered": ("Mastered", 80, "center"),
        }
        for col, (text, width, anchor) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(PAD, 0))
        ttk.Button(buttons, text="Start practice", command=self._start).pack(side="left")
        self.resume_btn = ttk.Button(buttons, text="Resume session", command=self._resume)
        self.resume_btn.pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Browse tricks", command=lambda: self.app.show("TricksScreen")).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(
            buttons,
            text="Coverage report",
            command=lambda: self.app.show("CoverageScreen"),
        ).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Change plan", command=self._change_plan).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Switch profile", command=self._switch).pack(side="right")

    def refresh(self) -> None:
        profile = self.app.profile
        if profile is None:
            return
        plan = get_plan(profile.plan)
        self.header.config(text=f"Hi {profile.name}!")

        mastered = sum(1 for name in plan.trick_names if name in profile.progress and profile.progress[name].mastered)
        self.summary.config(
            text=(
                f"Plan: {plan.name} — {mastered} of {len(plan.trick_names)} tricks "
                f"mastered (a trick is mastered at a streak of {MASTERY_STREAK})."
            )
        )
        self.mastery_bar.config(maximum=max(len(plan.trick_names), 1), value=mastered)

        self.tree.delete(*self.tree.get_children())
        for name in plan.trick_names:
            prog = profile.progress.get(name)
            if prog is None:
                self.tree.insert("", "end", values=(name, 0, "—", 0, ""))
            else:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        name,
                        prog.attempts,
                        f"{prog.accuracy:.0%}",
                        prog.streak,
                        "✓" if prog.mastered else "",
                    ),
                )

        state = profile.session
        if state is not None and state.queue:
            self.resume_btn.config(
                text=f"Resume session ({state.answered} of {state.total} done)",
                state="normal",
            )
        else:
            self.resume_btn.config(text="Resume session", state="disabled")

    def _start(self) -> None:
        profile = self.app.profile
        if not profile:
            raise TypeError("profile must be truthy")

        session_ok = profile.session is not None and profile.session.queue
        if session_ok and not messagebox.askyesno(
            "Sumsmaster",
            "Starting a new session discards the paused one. Continue?",
        ):
            return
        self.app.session = PracticeSession.start(profile, get_plan(profile.plan))
        self.app.save_profile()
        self.app.show("PracticeScreen")

    def _resume(self) -> None:
        profile = self.app.profile
        if not profile:
            raise TypeError("profile must be truthy")
        session = PracticeSession.resume(profile)
        if session is None:
            messagebox.showinfo("Sumsmaster", "That session can't be resumed.")
            self.app.save_profile()
            self.refresh()
            return
        self.app.session = session
        self.app.show("PracticeScreen")

    def _change_plan(self) -> None:
        profile = self.app.profile
        if not profile:
            raise TypeError("profile must be truthy")
        dialog = PlanDialog(self, current=profile.plan)
        self.wait_window(dialog)
        if dialog.result and dialog.result != profile.plan:
            profile.plan = dialog.result
            profile.session = None  # queue was built from the old plan
            self.app.save_profile()
            self.refresh()

    def _switch(self) -> None:
        self.app.save_profile()
        self.app.profile = None
        self.app.show("ProfileScreen")


class PlanDialog(tk.Toplevel):
    """Modal plan picker used by 'Change plan'."""

    def __init__(self, parent: tk.Widget, current: str) -> None:
        super().__init__(parent)
        self.title("Choose a plan")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.result: str | None = None

        body = ttk.Frame(self, padding=PAD)
        body.pack(fill="both", expand=True)
        self.var = tk.StringVar(value=current)
        for plan in ALL_PLANS:
            ttk.Radiobutton(
                body,
                text=f"{plan.name} — {plan.description}",
                variable=self.var,
                value=plan.id,
            ).pack(anchor="w", pady=2)
        row = ttk.Frame(body)
        row.pack(fill="x", pady=(PAD, 0))
        ttk.Button(row, text="OK", command=self._ok).pack(side="right")
        ttk.Button(row, text="Cancel", command=self.destroy).pack(side="right", padx=(0, 8))

    def _ok(self) -> None:
        self.result = self.var.get()
        self.destroy()


# ---------------------------------------------------------------------------
# Practice
# ---------------------------------------------------------------------------


class PracticeScreen(Screen):
    def __init__(self, parent: ttk.Frame, app: App) -> None:
        super().__init__(parent, app)
        self.progress_label = ttk.Label(self, text="")
        self.progress_label.pack(anchor="e")

        center = ttk.Frame(self)
        center.pack(expand=True)
        self.problem_label = ttk.Label(center, text="", font=("", 28, "bold"))
        self.problem_label.pack(pady=(0, PAD))

        self.answer_var = tk.StringVar()
        self.entry = ttk.Entry(
            center,
            textvariable=self.answer_var,
            font=("", 20),
            width=10,
            justify="center",
        )
        self.entry.pack()
        self.entry.bind("<Return>", lambda _e: self._submit())

        self.submit_btn = ttk.Button(center, text="Check", command=self._submit)
        self.submit_btn.pack(pady=(8, 0))

        self.feedback = ttk.Label(center, text="", wraplength=520, justify="center")
        self.feedback.pack(pady=(PAD, 0))

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", side="bottom")
        ttk.Button(bottom, text="Pause (save for later)", command=self._pause).pack(side="left")
        ttk.Button(bottom, text="End session", command=self._end).pack(side="right")

    def refresh(self) -> None:
        self.feedback.config(text="")
        self._show_current()

    def _show_current(self) -> None:
        session = self.app.session
        if session is None:
            return
        if session.finished:
            self._finish()
            return
        item = session.current
        if not item:
            raise TypeError("item must be truthy")
        self.problem_label.config(text=f"{item.problem} = ?")
        self.progress_label.config(
            text=f"Problem {session.answered + 1} of {session.total}" f"   •   {session.correct} correct"
        )
        self.answer_var.set("")
        self.entry.state(["!disabled"])
        self.entry.focus_set()

    def _submit(self) -> None:
        session = self.app.session
        if session is None or session.finished:
            return
        raw = self.answer_var.get().strip()
        try:
            answer = int(raw)
        except ValueError:
            self.feedback.config(text="Enter a whole number.", foreground="")
            return
        item = session.current
        if not item:
            raise TypeError("item must be truthy")
        correct = session.submit(answer)
        self.app.save_profile()
        if correct:
            self.feedback.config(
                foreground="dark green",
                text=f"Correct!  Trick: {item.trick.name} — {item.trick.explanation}",
            )
        else:
            self.feedback.config(
                foreground="dark red",
                text=(
                    f"Not quite: {item.problem} = {item.problem.answer}.\n"
                    f"Trick: {item.trick.name} — {item.trick.explanation}"
                ),
            )
        self._show_current()

    def _finish(self) -> None:
        session = self.app.session
        if not session:
            raise TypeError("session must be truthy")
        self.problem_label.config(text="Session complete!")
        self.progress_label.config(text="")
        self.entry.state(["disabled"])
        pct = 100.0 * session.correct / session.total if session.total else 0.0
        self.feedback.config(
            foreground="",
            text=f"You got {session.correct} of {session.total} ({pct:.0f}%).",
        )
        self.app.session = None
        self.app.save_profile()

    def _pause(self) -> None:
        # Session state is already synced after every answer; just persist.
        self.app.session = None
        self.app.save_profile()
        self.app.show("DashboardScreen")

    def _end(self) -> None:
        session = self.app.session
        if session is not None and not session.finished:
            session.abandon()
        self.app.session = None
        self.app.save_profile()
        self.app.show("DashboardScreen")


# ---------------------------------------------------------------------------
# Trick browser and coverage report
# ---------------------------------------------------------------------------


class TricksScreen(Screen):
    def __init__(self, parent: ttk.Frame, app: App) -> None:
        super().__init__(parent, app)
        ttk.Label(self, text="Trick taxonomy", font=("", 16, "bold")).pack(anchor="w")

        self.tree = ttk.Treeview(self, columns=("explanation",), show="tree headings")
        self.tree.heading("#0", text="Trick")
        self.tree.heading("explanation", text="How it works")
        self.tree.column("#0", width=260)
        self.tree.column("explanation", width=400)
        self.tree.pack(fill="both", expand=True, pady=(PAD, 0))

        for op in Operation:
            node = self.tree.insert("", "end", text=f"{op.name} ({op.value})", open=True)
            for trick in ALL_TRICKS:
                if op in trick.applies_to:
                    self.tree.insert(node, "end", text=trick.name, values=(trick.explanation,))

        ttk.Button(self, text="Back", command=self._back).pack(anchor="w", pady=(PAD, 0))

    def _back(self) -> None:
        self.app.show("DashboardScreen" if self.app.profile else "ProfileScreen")


class CoverageScreen(Screen):
    def __init__(self, parent: ttk.Frame, app: App) -> None:
        super().__init__(parent, app)
        ttk.Label(self, text="Trick coverage report", font=("", 16, "bold")).pack(anchor="w")
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, pady=(PAD, 0))
        self.text = tk.Text(frame, wrap="none", font=("Courier New", 9), state="disabled")
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=yscroll.set)
        yscroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        ttk.Button(self, text="Back", command=self._back).pack(anchor="w", pady=(PAD, 0))

        self._result: queue.Queue[str] = queue.Queue()
        self._started = False

    def refresh(self) -> None:
        if self._started:
            return
        self._started = True
        self._set_text("Computing coverage report…")
        threading.Thread(target=self._compute, daemon=True).start()
        self.after(100, self._poll)

    def _compute(self) -> None:
        try:
            self._result.put(coverage_mod.default_report())
        except Exception as exc:  # pragma: no cover - defensive
            self._result.put(f"Failed to compute report: {exc}")

    def _poll(self) -> None:
        try:
            report = self._result.get_nowait()
        except queue.Empty:
            self.after(100, self._poll)
            return
        self._set_text(report)

    def _set_text(self, content: str) -> None:
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.config(state="disabled")

    def _back(self) -> None:
        self.app.show("DashboardScreen" if self.app.profile else "ProfileScreen")
