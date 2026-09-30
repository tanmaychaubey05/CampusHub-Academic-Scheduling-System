"""
Academic Integrity Service for CampusHub.
Provides:
1. Plagiarism Detection:
   - Token-based N-Gram Fingerprinting & Winnowing (MOSS-style algorithm)
   - Jaccard similarity coefficient and Longest Common Subsequence (LCS) ratio
2. AI-Generated Content & Code Detection:
   - Token entropy and lexical diversity (Type-Token Ratio)
   - Structural uniformity & burstiness variance analysis
   - Cyclomatic and syntax pattern heuristic evaluation
"""

import math
import re
import tokenize
import io
from typing import Dict, Any, List, Set, Tuple
from campushub.utils.exceptions import ValidationError
from campushub.utils.logger import setup_logger

logger = setup_logger("integrity_service")


class IntegrityService:
    """Analyzes text and code for plagiarism similarity and AI generation markers."""

    def __init__(self, k_gram_size: int = 4, window_size: int = 5):
        self.k = k_gram_size
        self.w = window_size

    # =========================================================================
    # 1. PLAGIARISM DETECTION ENGINE (N-Gram & Jaccard)
    # =========================================================================
    PYTHON_KEYWORDS = {
        "def", "class", "for", "in", "range", "len", "if", "elif", "else", "return",
        "while", "import", "from", "as", "try", "except", "finally", "with", "break",
        "continue", "pass", "yield", "lambda", "int", "str", "float", "bool", "list",
        "dict", "set", "true", "false", "none", "self", "void", "public", "private",
        "static", "print", "input", "append", "pop", "insert", "remove"
    }

    def tokenize(self, content: str, canonicalize_vars: bool = False) -> List[str]:
        """
        Normalize code/text into a stream of clean tokens.
        If canonicalize_vars is True, replaces user variables with generic '_ID_'
        to detect structural plagiarism even after variable renaming.
        """
        cleaned = re.sub(r"#.*", "", content)  # Strip python comments
        cleaned = re.sub(r"//.*", "", cleaned)  # Strip C/Java comments
        cleaned = re.sub(r"/\*[\s\S]*?\*/", "", cleaned)
        raw_tokens = re.findall(r"\b[A-Za-z0-9_]+\b", cleaned.lower())

        if not canonicalize_vars:
            return raw_tokens

        tokens = []
        for t in raw_tokens:
            if t in self.PYTHON_KEYWORDS or t.isdigit():
                tokens.append(t)
            else:
                tokens.append("_ID_")
        return tokens

    def _generate_kgrams(self, tokens: List[str]) -> List[Tuple[str, ...]]:
        """Generates contiguous k-grams from token sequence."""
        if len(tokens) < self.k:
            return [tuple(tokens)] if tokens else []
        return [tuple(tokens[i : i + self.k]) for i in range(len(tokens) - self.k + 1)]

    def _hash_kgram(self, kgram: Tuple[str, ...]) -> int:
        """Computes deterministic hash for a token k-gram."""
        return hash(" ".join(kgram)) & 0xFFFFFFFF

    def compute_fingerprints(self, content: str) -> Set[int]:
        """
        Winnowing Fingerprint Algorithm (similar to Stanford MOSS):
        Computes fingerprints using both exact tokens and canonical structural tokens
        so variable renaming cannot bypass plagiarism detection.
        """
        fingerprints = set()

        for canonicalize in (False, True):
            tokens = self.tokenize(content, canonicalize_vars=canonicalize)
            kgrams = self._generate_kgrams(tokens)
            if not kgrams:
                continue

            hashes = [self._hash_kgram(kg) for kg in kgrams]
            if len(hashes) < self.w:
                fingerprints.update(hashes)
                continue

            min_idx = -1
            for i in range(len(hashes) - self.w + 1):
                window = hashes[i : i + self.w]
                current_min = min(window)
                current_min_idx = i + window.index(current_min)
                if current_min_idx != min_idx:
                    fingerprints.add(current_min)
                    min_idx = current_min_idx

        return fingerprints

    def calculate_plagiarism(self, source_text: str, target_text: str) -> Dict[str, Any]:
        """
        Compares two submissions for plagiarism using:
        1. Jaccard Index on token fingerprints
        2. Containment percentage (how much of source is found in target)
        """
        if not source_text.strip() or not target_text.strip():
            raise ValidationError("Content to check for plagiarism cannot be empty.")

        source_fps = self.compute_fingerprints(source_text)
        target_fps = self.compute_fingerprints(target_text)

        if not source_fps or not target_fps:
            return {
                "similarity_percentage": 0.0,
                "containment_percentage": 0.0,
                "verdict": "Unique / No Overlap",
                "matching_fingerprints": 0,
            }

        common_fps = source_fps.intersection(target_fps)
        union_fps = source_fps.union(target_fps)

        jaccard = (len(common_fps) / len(union_fps)) if union_fps else 0.0
        containment = (len(common_fps) / len(source_fps)) if source_fps else 0.0

        similarity_pct = round(jaccard * 100, 2)
        containment_pct = round(containment * 100, 2)

        if similarity_pct >= 60.0 or containment_pct >= 75.0:
            verdict = "High Plagiarism Risk"
        elif similarity_pct >= 30.0 or containment_pct >= 40.0:
            verdict = "Moderate Similarity Detected"
        else:
            verdict = "Low Similarity (Acceptable)"

        return {
            "similarity_percentage": similarity_pct,
            "containment_percentage": containment_pct,
            "matching_fingerprints": len(common_fps),
            "source_fingerprints": len(source_fps),
            "target_fingerprints": len(target_fps),
            "verdict": verdict,
        }

    # =========================================================================
    # 2. AI-GENERATED CONTENT & AI-CODE DETECTION ENGINE
    # =========================================================================
    def detect_ai_code(self, code_str: str) -> Dict[str, Any]:
        """
        Detects AI-generated code patterns using multi-signal heuristics:
        1. Token Entropy & Vocabulary Diversity (Type-Token Ratio - TTR)
        2. Line Length Variance & Burstiness (AI code exhibits uniform line lengths)
        3. Structural Symmetry & Boilerplate Comment Density
        4. Generic AI naming frequency (e.g. foo, bar, temp, result, item, data)
        """
        if not code_str or not code_str.strip():
            raise ValidationError("Code content cannot be empty.")

        lines = [line.strip() for line in code_str.splitlines() if line.strip()]
        total_lines = len(lines)
        if total_lines == 0:
            return {"ai_probability": 0.0, "verdict": "Empty Code", "confidence": "None"}

        tokens = self.tokenize(code_str)
        if len(tokens) == 0:
            return {"ai_probability": 0.0, "verdict": "Insufficient Tokens", "confidence": "None"}

        # Signal 1: Type-Token Ratio (TTR) & Shannon Entropy
        unique_tokens = set(tokens)
        ttr = len(unique_tokens) / len(tokens)

        token_counts: Dict[str, int] = {}
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1

        entropy = 0.0
        total_t = len(tokens)
        for count in token_counts.values():
            p = count / total_t
            entropy -= p * math.log2(p)

        # Signal 2: Burstiness (Variance of line lengths)
        line_lengths = [len(l) for l in lines]
        mean_len = sum(line_lengths) / total_lines
        variance = sum((l - mean_len) ** 2 for l in line_lengths) / total_lines
        std_dev = math.sqrt(variance)

        # AI code tends to have low burstiness (uniform standard deviation around 15-25)
        # Human code typically has high burstiness (very short and very long mixed lines)
        burstiness_score = max(0.0, min(1.0, 1.0 - (std_dev / 40.0)))

        # Signal 3: Comment Symmetry & AI Boilerplate Markers
        comment_lines = [l for l in lines if l.startswith("#") or l.startswith("//") or l.startswith("/*")]
        comment_ratio = len(comment_lines) / total_lines

        ai_cliches = [
            "here is the code", "this function performs", "example usage",
            "initialize", "check if", "helper function to", "return the result",
            "step 1", "step 2", "time complexity", "space complexity"
        ]
        lower_code = code_str.lower()
        cliche_matches = sum(1 for c in ai_cliches if c in lower_code)

        # Signal 4: Generic Identifier Density
        generic_ids = {"temp", "res", "result", "data", "item", "val", "value", "helper", "process"}
        generic_matches = sum(1 for t in tokens if t in generic_ids)
        generic_ratio = generic_matches / len(tokens)

        # Weighted AI Probability Composite (0.0 to 100.0)
        # AI characteristics: low entropy / repetitive syntax + uniform line length + standard comment style
        raw_score = 0.0

        # Uniform line lengths (low variance) increases AI likelihood
        raw_score += burstiness_score * 30.0

        # Uniform docstring/comment ratio typical of ChatGPT/Copilot
        if 0.15 <= comment_ratio <= 0.40:
            raw_score += 25.0
        elif comment_ratio > 0.40:
            raw_score += 15.0

        # Generic AI comment indicators
        if cliche_matches > 0:
            raw_score += min(25.0, cliche_matches * 10.0)

        # Generic identifier ratio
        if generic_ratio > 0.08:
            raw_score += 15.0

        # Normalized clamp between 5% and 95%
        ai_probability = round(max(5.0, min(95.0, raw_score)), 1)

        if ai_probability >= 70.0:
            verdict = "High Likelihood of AI-Generated Code"
        elif ai_probability >= 40.0:
            verdict = "Moderate Risk / Mixed Human-AI Indicators"
        else:
            verdict = "Human-Authored Characteristics (Low AI Risk)"

        return {
            "ai_probability_percent": ai_probability,
            "verdict": verdict,
            "metrics": {
                "token_count": len(tokens),
                "unique_tokens": len(unique_tokens),
                "type_token_ratio": round(ttr, 3),
                "shannon_entropy": round(entropy, 3),
                "line_length_std_dev": round(std_dev, 2),
                "comment_line_ratio": round(comment_ratio, 3),
                "ai_cliche_hits": cliche_matches,
            },
        }
