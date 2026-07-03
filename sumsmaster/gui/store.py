"""Local, unauthenticated profile storage for the free edition.

One JSON file per profile under ``~/.sumsmaster/profiles/``. No accounts,
no passwords — a profile is just a named progress ledger on this machine.
The storage root can be overridden with the ``SUMSMASTER_HOME`` environment
variable (used by tests and by self-hosters who want portable data).

The schema carries a ``version`` field so a future SQLite/SQLAlchemy
backend can migrate these documents.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

PROFILE_SCHEMA_VERSION = 1
DEFAULT_PROFILE_NAME = "default"
MASTERY_STREAK = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def data_root() -> Path:
    """Directory holding all sumsmaster local data."""
    override = os.environ.get("SUMSMASTER_HOME")
    if override:
        return Path(override)
    return Path.home() / ".sumsmaster"


def slugify(name: str) -> str:
    """Filesystem-safe identifier for a profile display name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "profile"


@dataclass
class TrickProgress:
    """Per-trick learning stats for one profile."""

    attempts: int = 0
    correct: int = 0
    streak: int = 0
    last_practiced: str | None = None

    @property
    def accuracy(self) -> float:
        return self.correct / self.attempts if self.attempts else 0.0

    @property
    def mastered(self) -> bool:
        return self.streak >= MASTERY_STREAK

    def record(self, is_correct: bool) -> None:
        self.attempts += 1
        if is_correct:
            self.correct += 1
            self.streak += 1
        else:
            self.streak = 0
        self.last_practiced = _now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempts": self.attempts,
            "correct": self.correct,
            "streak": self.streak,
            "last_practiced": self.last_practiced,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TrickProgress:
        return cls(
            attempts=int(d.get("attempts", 0)),
            correct=int(d.get("correct", 0)),
            streak=int(d.get("streak", 0)),
            last_practiced=d.get("last_practiced"),
        )


@dataclass
class SessionState:
    """A paused practice session, serialized into the profile for resume.

    ``queue`` holds the not-yet-answered problems as
    ``[a, b, op_symbol, trick_name]`` rows; ``total``/``answered``/``correct``
    describe overall session progress.
    """

    queue: list[list[Any]] = field(default_factory=list)
    total: int = 0
    answered: int = 0
    correct: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue": self.queue,
            "total": self.total,
            "answered": self.answered,
            "correct": self.correct,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SessionState:
        return cls(
            queue=list(d.get("queue", [])),
            total=int(d.get("total", 0)),
            answered=int(d.get("answered", 0)),
            correct=int(d.get("correct", 0)),
        )


@dataclass
class Profile:
    """A local learner profile."""

    name: str
    plan: str
    created_at: str = field(default_factory=_now)
    progress: dict[str, TrickProgress] = field(default_factory=dict)
    session: SessionState | None = None

    @property
    def slug(self) -> str:
        return slugify(self.name)

    def progress_for(self, trick_name: str) -> TrickProgress:
        return self.progress.setdefault(trick_name, TrickProgress())

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": PROFILE_SCHEMA_VERSION,
            "name": self.name,
            "plan": self.plan,
            "created_at": self.created_at,
            "progress": {k: v.to_dict() for k, v in self.progress.items()},
            "session": self.session.to_dict() if self.session else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Profile:
        session = d.get("session")
        return cls(
            name=str(d.get("name", DEFAULT_PROFILE_NAME)),
            plan=str(d.get("plan", "everything")),
            created_at=str(d.get("created_at", _now())),
            progress={k: TrickProgress.from_dict(v) for k, v in dict(d.get("progress", {})).items()},
            session=SessionState.from_dict(session) if session else None,
        )


class ProfileStore:
    """Loads and saves profiles plus app-level settings (last profile)."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or data_root()
        self.profiles_dir = self.root / "profiles"
        self.settings_path = self.root / "settings.json"

    # -- profiles -----------------------------------------------------------

    def _path(self, slug: str) -> Path:
        return self.profiles_dir / f"{slug}.json"

    def list_profiles(self) -> list[Profile]:
        if not self.profiles_dir.is_dir():
            return []
        out = []
        for path in sorted(self.profiles_dir.glob("*.json")):
            profile = self._read(path)
            if profile is not None:
                out.append(profile)
        return out

    def _read(self, path: Path) -> Profile | None:
        # Tolerate corrupt/foreign files: a broken profile should not brick
        # the whole app, just disappear from the list.
        try:
            return Profile.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError, AttributeError):
            return None

    def load(self, slug: str) -> Profile | None:
        path = self._path(slug)
        return self._read(path) if path.is_file() else None

    def save(self, profile: Profile) -> None:
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        path = self._path(profile.slug)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(profile.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(path)

    def delete(self, slug: str) -> None:
        self._path(slug).unlink(missing_ok=True)

    def exists(self, name: str) -> bool:
        return self._path(slugify(name)).is_file()

    def ensure_default(self) -> Profile:
        """Create the zero-setup default profile on first launch."""
        existing = self.load(DEFAULT_PROFILE_NAME)
        if existing is not None:
            return existing
        profile = Profile(name=DEFAULT_PROFILE_NAME, plan="everything")
        self.save(profile)
        return profile

    # -- settings -----------------------------------------------------------

    def last_profile_slug(self) -> str | None:
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            slug = data.get("last_profile")
            return slug if isinstance(slug, str) else None
        except (OSError, ValueError):
            return None

    def remember_profile(self, slug: str) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps({"last_profile": slug}, indent=2), encoding="utf-8")
