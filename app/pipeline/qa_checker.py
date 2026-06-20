# NO LLM IN THIS MODULE. Pure Python only.
# Enforces what models can't reliably do: count, measure, detect.

import re

WORD_COUNT_MIN = 200
WORD_COUNT_MAX = 280
CHAR_HARD_CAP = 3000

_STAT_RE = re.compile(
    r"\b\d+\s*%|\b\d+\s*x\b|\b\d+\s*(?:hour|hours|day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)


class LinkedInQAChecker:
    def count_words(self, text: str) -> int:
        # Exclude hashtag lines (lines starting with #) from word count.
        clean = " ".join(
            line for line in text.split("\n") if not line.strip().startswith("#")
        )
        return len(clean.split())

    def count_chars(self, text: str) -> int:
        return len(text)

    def count_hashtags(self, text: str) -> int:
        return len(re.findall(r"#\w+", text))

    def get_first_line(self, text: str) -> str:
        for line in text.split("\n"):
            if line.strip():
                return line.strip()
        return ""

    def count_words_in_line(self, line: str) -> int:
        return len(line.split())

    def get_long_lines(self, text: str, max_words: int = 30) -> list[str]:
        violations = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                if self.count_words_in_line(stripped) > max_words:
                    violations.append(stripped)
        return violations

    def has_banned_opener(self, text: str) -> bool:
        banned_openers = [
            "in today's",
            "i'm excited",
            "i'm thrilled",
            "thrilled to",
            "humbled to",
            "it's important",
            "let's dive",
            "in this fast",
        ]
        first_line = self.get_first_line(text).lower()
        return any(first_line.startswith(opener) for opener in banned_openers)

    def has_banned_words(self, text: str) -> list[str]:
        banned = [
            "delve",
            "leverage",
            "realm",
            "tapestry",
            "synergy",
            "seamlessly",
            "humbled to announce",
            "thrilled to share",
            "excited to share",
            "game-changer",
            "revolutionary",
            "cutting-edge",
            "utilize",
            "navigate",
            "moreover",
            "furthermore",
        ]
        text_lower = text.lower()
        return [word for word in banned if word in text_lower]

    def count_cta_signals(self, text: str) -> int:
        signals = len(re.findall(r"\?", text))
        soft_asks = len(
            re.findall(r"\b(save this|follow me|repost|share this)\b", text.lower())
        )
        return signals + soft_asks

    def has_packed_sentences(self, text: str) -> list[str]:
        """Return lines that pack 3+ independent sentences together without a line break.

        Counts mid-line sentence boundaries (period/exclamation followed by whitespace
        and a capital letter). Two or more such boundaries = genuine packing violation.
        One boundary ("A. B.") is normal LinkedIn rhythm and is NOT flagged.
        """
        violations = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                boundaries = re.findall(r"[.!]\s+[A-Z]", stripped)
                if len(boundaries) >= 2:
                    violations.append(stripped)
        return violations

    def has_wall_of_text(self, text: str) -> bool:
        for para in text.split("\n\n"):
            lines = [ln for ln in para.split("\n") if ln.strip()]
            if len(lines) > 6:
                return True
            if len(para.strip()) > 400:
                return True
        return False

    def has_fake_stats(self, text: str) -> list[str]:
        """Informational: flag lines containing number+unit patterns that may be invented stats.
        Does NOT affect overall_pass — used only as editor context.
        """
        return [
            ln.strip()
            for ln in text.split("\n")
            if ln.strip() and not ln.strip().startswith("#") and _STAT_RE.search(ln)
        ]

    def check(self, post_text: str) -> dict:
        word_count = self.count_words(post_text)
        char_count = self.count_chars(post_text)
        hashtag_count = self.count_hashtags(post_text)
        first_line = self.get_first_line(post_text)
        long_lines = self.get_long_lines(post_text)
        banned_opener = self.has_banned_opener(post_text)
        banned_words = self.has_banned_words(post_text)
        cta_count = self.count_cta_signals(post_text)
        wall = self.has_wall_of_text(post_text)
        packed_lines = self.has_packed_sentences(post_text)
        fake_stat_lines = self.has_fake_stats(post_text)

        passes = {
            "passes_word_count": WORD_COUNT_MIN <= word_count <= WORD_COUNT_MAX,
            "passes_char_count": char_count <= CHAR_HARD_CAP,
            "passes_hashtag_count": 3 <= hashtag_count <= 5,
            "passes_line_length": len(long_lines) == 0,
            "passes_hook": not banned_opener,
            "passes_banned_words": len(banned_words) == 0,
            "passes_cta": cta_count == 1,
            "passes_white_space": not wall,
            "passes_packed_sentences": len(packed_lines) == 0,
        }

        return {
            "word_count": word_count,
            "char_count": char_count,
            "hashtag_count": hashtag_count,
            "first_line": first_line,
            "first_line_word_count": self.count_words_in_line(first_line),
            "long_lines": long_lines,
            "packed_lines": packed_lines,
            "fake_stat_lines": fake_stat_lines,
            "has_banned_opener": banned_opener,
            "banned_words_found": banned_words,
            "cta_signal_count": cta_count,
            "has_wall_of_text": wall,
            **passes,
            "overall_pass": all(passes.values()),
        }
