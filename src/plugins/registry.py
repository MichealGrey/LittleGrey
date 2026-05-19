import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginCapabilityRegistry:
    def __init__(self):
        self._commands: Dict[str, Callable] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._middlewares: List[Callable] = []
        self._configs: Dict[str, Dict] = {}

    def register_command(self, name: str, handler: Callable) -> None:
        self._commands[name] = handler
        logger.info(f"Registered command: {name}")

    def get_command(self, name: str) -> Optional[Callable]:
        return self._commands.get(name)

    def register_event_handler(self, event: str, handler: Callable) -> None:
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
        logger.info(f"Registered event handler: {event}")

    def emit_event(self, event: str, *args, **kwargs) -> None:
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"Event handler failed for {event}: {e}")

    def register_middleware(self, middleware: Callable) -> None:
        self._middlewares.append(middleware)
        logger.info("Registered middleware")

    @property
    def middlewares(self) -> List[Callable]:
        return list(self._middlewares)

    def store_config(self, plugin_id: str, config: Dict) -> None:
        self._configs[plugin_id] = config

    def get_config(self, plugin_id: str) -> Dict:
        return self._configs.get(plugin_id, {})
