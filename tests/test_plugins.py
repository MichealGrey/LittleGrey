import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.plugins.plugin_base import PluginBase
from src.plugins.registry import PluginCapabilityRegistry
from src.plugins.plugin_manager import PluginManager


class TestPluginBase:
    def test_default_properties(self):
        class TestPlugin(PluginBase):
            @property
            def plugin_id(self):
                return 'test.plugin'
            def initialize(self, config, plugin_root):
                pass
        plugin = TestPlugin()
        assert plugin.plugin_version == '0.1.0'
        assert plugin.plugin_name == 'plugin'
        assert plugin.plugin_description == ''
        assert plugin.plugin_author == ''
        assert plugin.enabled is True
        assert plugin.priority == 100

    def test_custom_properties(self):
        class CustomPlugin(PluginBase):
            @property
            def plugin_id(self):
                return 'com.custom.test'
            @property
            def plugin_version(self):
                return '2.0.0'
            @property
            def plugin_name(self):
                return 'Custom Test'
            @property
            def plugin_description(self):
                return 'A test plugin'
            @property
            def plugin_author(self):
                return 'Tester'
            @property
            def enabled(self):
                return False
            @property
            def priority(self):
                return 10
            def initialize(self, config, plugin_root):
                pass
        plugin = CustomPlugin()
        assert plugin.plugin_id == 'com.custom.test'
        assert plugin.plugin_version == '2.0.0'
        assert plugin.plugin_name == 'Custom Test'
        assert plugin.plugin_description == 'A test plugin'
        assert plugin.plugin_author == 'Tester'
        assert plugin.enabled is False
        assert plugin.priority == 10

    def test_shutdown_default(self):
        class TestPlugin(PluginBase):
            @property
            def plugin_id(self):
                return 'test.plugin'
            def initialize(self, config, plugin_root):
                pass
        plugin = TestPlugin()
        plugin.shutdown()


class TestPluginRegistry:
    def test_register_and_get_command(self):
        registry = PluginCapabilityRegistry()
        handler = lambda: 'test'
        registry.register_command('test_cmd', handler)
        assert registry.get_command('test_cmd') == handler
        assert registry.get_command('nonexistent') is None

    def test_register_event_handler(self):
        registry = PluginCapabilityRegistry()
        handler1 = lambda: 'handler1'
        handler2 = lambda: 'handler2'
        registry.register_event_handler('on_start', handler1)
        registry.register_event_handler('on_start', handler2)
        assert len(registry._event_handlers['on_start']) == 2

    def test_emit_event(self):
        registry = PluginCapabilityRegistry()
        results = []
        registry.register_event_handler('test', lambda x: results.append(x))
        registry.emit_event('test', 'hello')
        assert results == ['hello']

    def test_emit_event_with_error(self):
        registry = PluginCapabilityRegistry()
        registry.register_event_handler('test', lambda: 1/0)
        registry.emit_event('test')

    def test_middleware(self):
        registry = PluginCapabilityRegistry()
        registry.register_middleware(lambda: 'mw1')
        registry.register_middleware(lambda: 'mw2')
        assert len(registry.middlewares) == 2

    def test_config_storage(self):
        registry = PluginCapabilityRegistry()
        registry.store_config('test.plugin', {'key': 'value'})
        assert registry.get_config('test.plugin') == {'key': 'value'}
        assert registry.get_config('nonexistent') == {}


class TestPluginManager:
    def test_init(self):
        manager = PluginManager()
        assert manager.get_all_plugins() == {}
        assert manager.registry is not None

    def test_discover_plugins_empty_dir(self):
        manager = PluginManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins = manager.discover_plugins(Path(tmpdir))
            assert plugins == []

    def test_discover_plugins_nonexistent_dir(self):
        manager = PluginManager()
        plugins = manager.discover_plugins(Path('/nonexistent'))
        assert plugins == []

    def test_load_plugins_with_example(self):
        manager = PluginManager()
        plugin_dir = Path(__file__).parent.parent / 'src' / 'plugins'
        count = manager.load_plugins(plugin_dir)
        assert count >= 1
        assert manager.get_plugin('com.littlegrey.example') is not None

    def test_get_plugin_info(self):
        manager = PluginManager()
        plugin_dir = Path(__file__).parent.parent / 'src' / 'plugins'
        manager.load_plugins(plugin_dir)
        info = manager.get_plugin_info()
        assert len(info) >= 1
        assert info[0]['id'] == 'com.littlegrey.example'

    def test_shutdown(self):
        manager = PluginManager()
        plugin_dir = Path(__file__).parent.parent / 'src' / 'plugins'
        manager.load_plugins(plugin_dir)
        manager.shutdown()
        assert manager.get_all_plugins() == {}

    def test_load_plugins_idempotent(self):
        manager = PluginManager()
        plugin_dir = Path(__file__).parent.parent / 'src' / 'plugins'
        count1 = manager.load_plugins(plugin_dir)
        count2 = manager.load_plugins(plugin_dir)
        assert count1 == count2
