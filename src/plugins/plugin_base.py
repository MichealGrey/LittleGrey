import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """Base class for all LittleGrey plugins."""

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Unique stable ID, e.g., 'com.example.myplugin'."""
        raise NotImplementedError

    @property
    def plugin_version(self) -> str:
        """Semantic version string."""
        return "0.1.0"

    @property
    def plugin_name(self) -> str:
        """Human-readable title."""
        pid = self.plugin_id
        tail = pid.rpartition(".")[-1]
        return tail.replace("_", " ").strip() or pid

    @property
    def plugin_description(self) -> str:
        """Short description."""
        return ""

    @property
    def plugin_author(self) -> str:
        """Author or vendor."""
        return ""

    @property
    def enabled(self) -> bool:
        """Whether this plugin should be initialized."""
        return True

    @property
    def priority(self) -> int:
        """Lower value means earlier initialization."""
        return 100

    def initialize(self, config: Dict[str, Any], plugin_root: Path) -> None:
        """Initialize the plugin with configuration and plugin root path."""
        pass

    def shutdown(self) -> None:
        """Lifecycle hook called when host is shutting down."""
        pass
