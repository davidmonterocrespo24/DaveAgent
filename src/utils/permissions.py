"""
Permission Manager for Persistent User Approvals.
Handles loading, saving, and checking permissions from .daveagent/settings.local.json
"""
import json
import os
import fnmatch
from pathlib import Path
from typing import List, Dict, Optional, Literal

SETTINGS_FILE = Path(".daveagent/settings.local.json")

class PermissionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PermissionManager, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self):
        """Load permissions from settings file"""
        self.permissions = {
            "allow": [],
            "deny": [],
            "ask": []
        }
        
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "permissions" in data:
                        self.permissions.update(data["permissions"])
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_permission(self, pattern: str, action: Literal["allow", "deny"] = "allow"):
        """Save a new permission pattern"""
        if pattern not in self.permissions[action]:
            self.permissions[action].append(pattern)
            self._save_to_disk()

    def _save_to_disk(self):
        """Write current permissions to disk"""
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            data = {"permissions": self.permissions}
            
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def check_permission(self, action_string: str) -> Literal["allow", "deny", "ask"]:
        """
        Check if an action string matches any stored permissions.
        Returns 'allow', 'deny', or 'ask'.
        """
        # Check DENY first (security priority)
        for pattern in self.permissions["deny"]:
            if self._matches(pattern, action_string):
                return "deny"

        # Check ALLOW
        for pattern in self.permissions["allow"]:
            if self._matches(pattern, action_string):
                return "allow"

        return "ask"

    def _matches(self, pattern: str, text: str) -> bool:
        """
        Check if text matches the glob pattern.
        Handles simpler cases directly and complex path globs.
        """
        # Normalize slashes for path comparisons if it looks like a file path
        if "/" in pattern or "\\" in pattern:
            # Simple normalization for Windows/Unix compatibility
            pattern = pattern.replace("\\", "/")
            text = text.replace("\\", "/")
            
        return fnmatch.fnmatch(text, pattern)

def get_permission_manager() -> PermissionManager:
    return PermissionManager()
