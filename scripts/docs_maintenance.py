#!/usr/bin/env python3
"""
Documentation Maintenance Script
Performs automated quality assurance on documentation files.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class DocumentationAuditor:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.docs_dir = self.root_dir  # Can be customized
        self.md_files = []
        self.issues = []

    def find_files(self):
        """Finds all markdown files in the project."""
        self.md_files = list(self.docs_dir.rglob("*.md"))
        print(f"Found {len(self.md_files)} markdown files.")

    def check_links(self, file_path: Path):
        """Checks for broken internal links."""
        content = file_path.read_text(encoding="utf-8")
        # Match [text](link)
        links = re.findall(r'\[.*?\]\((.*?)\)', content)

        for link in links:
            if link.startswith("http"):
                continue # Skip external links for now to avoid network calls in basic audit

            if link.startswith("#"):
                continue # Skip anchors for now

            # Handle absolute paths relative to repo root (simplified)
            if link.startswith("/"):
                target = self.root_dir / link.lstrip("/")
            else:
                target = file_path.parent / link

            # Remove anchors from target
            target_path = str(target).split("#")[0]

            if not os.path.exists(target_path):
                self.issues.append({
                    "file": str(file_path),
                    "type": "Broken Link",
                    "details": f"Link not found: {link}"
                })

    def check_quality(self, file_path: Path):
        """Checks for content quality indicators."""
        content = file_path.read_text(encoding="utf-8")

        # Check for TODO/FIXME
        if "TODO" in content:
            self.issues.append({
                "file": str(file_path),
                "type": "Content Quality",
                "details": "Contains TODO marker"
            })

        if "FIXME" in content:
            self.issues.append({
                "file": str(file_path),
                "type": "Content Quality",
                "details": "Contains FIXME marker"
            })

        # Check for empty sections (simplified: Header followed immediately by another Header)
        if re.search(r'^#+ .*\n\s*#+', content, re.MULTILINE):
             self.issues.append({
                "file": str(file_path),
                "type": "Structure",
                "details": "Possible empty section detected"
            })

    def audit(self):
        """Runs the full audit."""
        self.find_files()

        print("\nStarting Audit...")
        for file_path in self.md_files:
            try:
                self.check_links(file_path)
                self.check_quality(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        self.report()

    def report(self):
        """Prints the audit report."""
        print("\n=== Documentation Audit Report ===")
        if not self.issues:
            print("✅ No issues found!")
            return

        print(f"Found {len(self.issues)} issues:")
        for issue in self.issues:
            print(f"[{issue['type']}] {issue['file']}: {issue['details']}")

        print("\n==================================")
        # Exit with error code if issues found (optional, good for CI)
        # sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Documentation Maintenance Tool")
    parser.add_argument("--audit", action="store_true", help="Run full documentation audit")
    parser.add_argument("--file", type=str, help="Audit specific file")

    args = parser.parse_args()

    auditor = DocumentationAuditor()

    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            auditor.check_links(file_path)
            auditor.check_quality(file_path)
            auditor.report()
        else:
            print(f"File not found: {args.file}")
    else:
        # Default to full audit if --audit is passed or no args
        auditor.audit()

if __name__ == "__main__":
    main()
