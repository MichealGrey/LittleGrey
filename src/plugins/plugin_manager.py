import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from .plugin_base import PluginBase
from .registry import PluginCapabilityRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self):
        self._plugins: Dict[str, PluginBase] = {}
        self._registry = PluginCapabilityRegistry()
        self._initialized = False

    def discover_plugins(self, plugin_dir: Path):
        plugin_classes = []
        if not plugin_dir.is_dir():
            return plugin_classes
        
        plugin_dir = plugin_dir.resolve()
        parent_dir = plugin_dir.parent
        
        for pyfile in plugin_dir.glob("*.py"):
            if pyfile.name.startswith("_"):
                continue
            try:
                module_name = f"plugins.{pyfile.stem}"
                spec = importlib.util.spec_from_file_location(module_name, str(pyfile))
                if spec is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                module.__package__ = "plugins"
                if module_name not in sys.modules:
                    sys.modules[module_name] = module
                
                if "plugins" not in sys.modules:
                    import src.plugins
                    sys.modules["plugins"] = src.plugins
                
                spec.loader.exec_module(module)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and issubclass(attr, PluginBase) and attr != PluginBase):
                        plugin_classes.append(attr)
            except Exception as e:
                logger.error(f"Failed to load plugin from {pyfile}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        return plugin_classes

    def load_plugins(self, plugin_dir: Path, config: Dict | None = None):
        if self._initialized:
            return len(self._plugins)
        plugin_classes = self.discover_plugins(plugin_dir)
        plugin_classes.sort(key=lambda p: p.priority)
        for plugin_cls in plugin_classes:
            try:
                plugin = plugin_cls()
                if not plugin.enabled:
                    continue
                plugin_root = plugin_dir / plugin.plugin_id.replace(".", "/")
                plugin.initialize(config=config or {}, plugin_root=plugin_root)
                self._plugins[plugin.plugin_id] = plugin
                logger.info(f"Initialized plugin: {plugin.plugin_id} v{plugin.plugin_version}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin_cls.__name__}: {e}")
        self._initialized = True
        return len(self._plugins)

    def shutdown(self):
        for pid, plugin in self._plugins.items():
            try:
                plugin.shutdown()
                logger.info(f"Shut down plugin: {pid}")
            except Exception as e:
                logger.error(f"Failed to shut down plugin {pid}: {e}")
        self._plugins.clear()
        self._initialized = False

    def get_plugin(self, plugin_id):
        return self._plugins.get(plugin_id)

    def get_all_plugins(self):
        return dict(self._plugins)

    @property
    def registry(self):
        return self._registry

    def get_plugin_info(self):
        info = []
        for pid, plugin in self._plugins.items():
            info.append({"id": pid, "name": plugin.plugin_name, "version": plugin.plugin_version, "author": plugin.plugin_author, "description": plugin.plugin_description, "enabled": plugin.enabled})
        return info
