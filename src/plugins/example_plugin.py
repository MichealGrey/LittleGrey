from src.plugins.plugin_base import PluginBase
import logging

logger = logging.getLogger(__name__)


class ExamplePlugin(PluginBase):
    @property
    def plugin_id(self) -> str:
        return 'com.littlegrey.example'

    @property
    def plugin_version(self) -> str:
        return '1.0.0'

    @property
    def plugin_name(self) -> str:
        return 'Example Plugin'

    @property
    def plugin_description(self) -> str:
        return 'A simple example plugin for testing'

    @property
    def plugin_author(self) -> str:
        return 'LittleGrey Team'

    def initialize(self, config: dict, plugin_root):
        logger.info(f'ExamplePlugin initialized with config: {config}')
        self._initialized = True

    def shutdown(self):
        logger.info('ExamplePlugin shutting down')
        self._initialized = False
