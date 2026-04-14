from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SessionState:
    current: Dict[str, str] = field(
        default_factory=lambda: {
            "app_name": "",
            "package_name": "",
            "url": "",
            "engine": "webview",
        }
    )
    _undo_stack: List[Dict[str, str]] = field(default_factory=list)
    _redo_stack: List[Dict[str, str]] = field(default_factory=list)

    def snapshot(self) -> Dict[str, str]:
        return dict(self.current)

    def set_value(self, key: str, value: str) -> Dict[str, str]:
        self._undo_stack.append(self.snapshot())
        self._redo_stack.clear()
        self.current[key] = value
        return self.snapshot()

    def undo(self) -> Dict[str, str]:
        if not self._undo_stack:
            return self.snapshot()
        self._redo_stack.append(self.snapshot())
        self.current = self._undo_stack.pop()
        return self.snapshot()

    def redo(self) -> Dict[str, str]:
        if not self._redo_stack:
            return self.snapshot()
        self._undo_stack.append(self.snapshot())
        self.current = self._redo_stack.pop()
        return self.snapshot()
