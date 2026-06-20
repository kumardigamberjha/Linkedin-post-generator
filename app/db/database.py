import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "history.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                topic       TEXT    NOT NULL,
                niche       TEXT    DEFAULT 'ai',
                provider    TEXT    DEFAULT 'google',
                post_text   TEXT    NOT NULL,
                angle_type  TEXT,
                word_count  INTEGER DEFAULT 0,
                approved    INTEGER DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            conn.execute("ALTER TABLE history ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass  # already exists

        conn.execute("""
            CREATE TABLE IF NOT EXISTS trending_topics (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                niche       TEXT    NOT NULL,
                source      TEXT    NOT NULL,
                topic       TEXT    NOT NULL,
                used        INTEGER DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(topic, source)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role          TEXT DEFAULT 'user',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        except sqlite3.OperationalError:
            pass  # already exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id                         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id                    INTEGER UNIQUE NOT NULL,
                stripe_customer_id         TEXT,
                stripe_subscription_id     TEXT,
                plan_tier                  TEXT DEFAULT 'free',
                status                     TEXT DEFAULT 'inactive',
                current_period_end         TIMESTAMP,
                posts_generated_this_month INTEGER DEFAULT 0,
                last_generation_date       TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


def save_post(
    topic: str, niche: str, provider: str, result: dict, user_id: int = None
) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO history (user_id, topic, niche, provider, post_text, angle_type, word_count, approved)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                topic,
                niche,
                provider,
                result["post_text"],
                result.get("angle_type"),
                result.get("word_count", 0),
                1 if result.get("approved") else 0,
            ),
        )
        # Mark as used if it was a trending topic
        conn.execute("UPDATE trending_topics SET used = 1 WHERE topic = ?", (topic,))
        return cur.lastrowid


def save_trending_topics(niche: str, trends: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        for source, topics in trends.items():
            for t in topics:
                # INSERT OR IGNORE avoids duplicates if the same topic trends again
                conn.execute(
                    """INSERT OR IGNORE INTO trending_topics (niche, source, topic)
                       VALUES (?, ?, ?)""",
                    (niche, source, t),
                )


def get_history(limit: int = 20, offset: int = 0, user_id: int = None) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                "SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]


def get_post(item_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM history WHERE id = ?", (item_id,)).fetchone()
        return dict(row) if row else None


def count_history(user_id: int = None) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        if user_id:
            return conn.execute(
                "SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
        return conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]


def get_trending_topics(limit: int = 50, offset: int = 0) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM trending_topics ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def count_trending_topics() -> int:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT COUNT(*) FROM trending_topics").fetchone()[0]


def get_admin_stats(user_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        role = user["role"] if user else "user"

        if role == "admin":
            total_posts = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active_subs = conn.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
            ).fetchone()[0]
        else:
            total_posts = conn.execute(
                "SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            total_users = 1
            active_subs = (
                1
                if conn.execute(
                    "SELECT COUNT(*) FROM subscriptions WHERE user_id = ? AND status = 'active'",
                    (user_id,),
                ).fetchone()[0]
                else 0
            )

        total_trends = conn.execute("SELECT COUNT(*) FROM trending_topics").fetchone()[
            0
        ]
        used_trends = conn.execute(
            "SELECT COUNT(*) FROM trending_topics WHERE used = 1"
        ).fetchone()[0]

        return {
            "role": role,
            "total_posts": total_posts,
            "total_trends": total_trends,
            "used_trends": used_trends,
            "total_users": total_users,
            "active_subs": active_subs,
        }


# --- User & Auth DB Functions ---


def create_user(email: str, password_hash: str) -> int:
    role = "admin" if "admin" in email.lower() else "user"
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, password_hash, role),
        )
        user_id = cur.lastrowid
        # Give them an active free subscription tracking row automatically
        conn.execute(
            "INSERT INTO subscriptions (user_id, plan_tier, status) VALUES (?, ?, ?)",
            (user_id, "free", "active"),
        )
        return user_id


def get_user_by_email(email: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_subscription(user_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def update_subscription(user_id: int, updates: dict) -> None:
    if not updates:
        return
    with sqlite3.connect(DB_PATH) as conn:
        fields = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values())
        values.append(user_id)
        conn.execute(f"UPDATE subscriptions SET {fields} WHERE user_id = ?", values)


def increment_post_count(user_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE subscriptions SET posts_generated_this_month = posts_generated_this_month + 1, last_generation_date = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,),
        )

# Initialize the database tables immediately on import to prevent "no such table" errors
init_db()
