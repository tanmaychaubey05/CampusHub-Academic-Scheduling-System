"""
Terminal UI formatting helpers: ASCII boxes, tables, headers, and color helpers.
Works without external dependencies.
"""

import os
from typing import List, Dict, Any, Optional


class TerminalUI:
    """Helper methods for clean ASCII terminal interfaces."""

    @staticmethod
    def clear_screen() -> None:
        """Clears terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def print_header(title: str, subtitle: Optional[str] = None) -> None:
        """Renders an attractive ASCII header."""
        width = 68
        print("\n" + "=" * width)
        print(f"  {title.upper()}".center(width))
        if subtitle:
            print(f"  {subtitle}".center(width))
        print("=" * width + "\n")

    @staticmethod
    def print_success(message: str) -> None:
        print(f" [SUCCESS] {message}")

    @staticmethod
    def print_error(message: str) -> None:
        print(f" [ERROR] {message}")

    @staticmethod
    def print_warning(message: str) -> None:
        print(f" [WARNING] {message}")

    @staticmethod
    def print_info(message: str) -> None:
        print(f" [INFO] {message}")

    @staticmethod
    def print_table(headers: List[str], rows: List[List[Any]]) -> None:
        """Renders a formatted ASCII table."""
        if not rows:
            print("  (No records found)\n")
            return

        col_widths = [len(h) for h in headers]
        for row in rows:
            for idx, val in enumerate(row):
                val_str = str(val) if val is not None else ""
                col_widths[idx] = max(col_widths[idx], len(val_str))

        # Format header
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))

        print(f"  {header_line}")
        print(f"  {separator}")

        for row in rows:
            row_line = " | ".join(str(val or "").ljust(col_widths[i]) for i, val in enumerate(row))
            print(f"  {row_line}")
        print()

    @staticmethod
    def prompt_input(label: str, default: Optional[str] = None) -> str:
        prompt_text = f"  > {label}"
        if default:
            prompt_text += f" [{default}]"
        prompt_text += ": "
        val = input(prompt_text).strip()
        return val if val else (default or "")

    @staticmethod
    def prompt_choice(options: List[str], title: str = "Select an option") -> int:
        print(f"  {title}:")
        for idx, opt in enumerate(options, 1):
            print(f"    [{idx}] {opt}")
        print()
        while True:
            choice = input("  Enter choice (number): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return int(choice)
            print("  [ERROR] Invalid choice. Please enter a valid number.")
