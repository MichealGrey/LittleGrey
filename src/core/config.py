import yaml
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    provider: str = "volcengine"
    model: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: str = ""


@dataclass
class MemoryConfig:
    short_term_max: int = 20
    summary_threshold: int = 15
    vector_db_path: str = "storage/vector_db"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    chat_history_path: str = "storage/chat_history"


@dataclass
class StorageConfig:
    files_path: str = "storage/files"


@dataclass
class DreamConfig:
    enabled: bool = True
    short_term_dream_base_prob: float = 0.3
    long_term_dream_base_prob: float = 0.5
    similarity_threshold: float = 0.7
    dream_trigger_prob: float = 0.8


@dataclass
class IntentConfig:
    enabled: bool = True
    min_idle_seconds: int = 180


@dataclass
class AgentConfig:
    max_steps: int = 10
    max_retries: int = 2
    human_in_the_loop: bool = True
    heartbeat_interval: int = 300
    heartbeat_enabled: bool = True
    interest_learning_enabled: bool = True
    interest_learning_interval: int = 600  # 兴趣学习周期（秒）


@dataclass
class LoggingConfig:
    level: str = "INFO"
    path: str = "storage/logs"
    format: str = "jsonl"


@dataclass
class DecayStrategyConfig:
    strategy_type: str = "exponential"
    rate: float = 0.02
    duration_hours: float = 5.0
    interval_hours: float = 1.0
    decay_factor: float = 0.5

@dataclass
class EmotionConfig:
    dimensions: list[str] = field(default_factory=lambda: [
        'happy', 'sad', 'angry', 'anxious', 'excited'
    ])
    decay_strategies: dict[str, DecayStrategyConfig] = field(default_factory=lambda: {
        'happy': DecayStrategyConfig(strategy_type='exponential', rate=0.05),
        'excited': DecayStrategyConfig(strategy_type='exponential', rate=0.06),
        'sad': DecayStrategyConfig(strategy_type='exponential', rate=0.02),
        'angry': DecayStrategyConfig(strategy_type='slow_negative', rate=0.003),
        'anxious': DecayStrategyConfig(strategy_type='exponential', rate=0.025),
    })
    default_strategy: str = "exponential"
    min_threshold: float = 0.005
    autonomous_drift_enabled: bool = True
    loneliness_threshold: int = 600
    drift_probability: float = 0.15
    time_mood_enabled: bool = True
    baseline_happy: float = 0.05
    baseline_sad: float = 0.0
    baseline_angry: float = 0.0
    baseline_anxious: float = 0.0
    baseline_excited: float = 0.0
    llm_understand_enabled: bool = True
    hard_constraints_enabled: bool = True
    angry_refuse_threshold: float = 0.7
    sad_short_reply_threshold: float = 0.8
    anxious_ask_threshold: float = 0.6
    trust_defensive_threshold: float = 0.2


@dataclass
class PersonalityConfig:
    name: str = "小小灰"
    system_prompt: str = ""


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    dream: DreamConfig = field(default_factory=DreamConfig)
    intent: IntentConfig = field(default_factory=IntentConfig)
    personality: PersonalityConfig = field(default_factory=PersonalityConfig)
    emotion: EmotionConfig = field(default_factory=EmotionConfig)
    tools: list[str] = field(default_factory=list)

    @property
    def project_root(self) -> Path:
        return self._project_root

    _project_root: Path = field(default_factory=lambda: Path.cwd())

    def resolve_path(self, relative_path: str) -> Path:
        return self._project_root / relative_path


def load_config(config_path: str | Path | None = None) -> AppConfig:
    if config_path is None:
        config_path = Path.cwd() / "config" / "settings.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        return AppConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cfg = AppConfig()
    cfg._project_root = config_path.parent.parent

    if "llm" in raw:
        for k, v in raw["llm"].items():
            if hasattr(cfg.llm, k):
                setattr(cfg.llm, k, v)

    if "memory" in raw:
        for k, v in raw["memory"].items():
            if hasattr(cfg.memory, k):
                setattr(cfg.memory, k, v)

    if "storage" in raw:
        for k, v in raw["storage"].items():
            if hasattr(cfg.storage, k):
                setattr(cfg.storage, k, v)

    if "agent" in raw:
        for k, v in raw["agent"].items():
            if hasattr(cfg.agent, k):
                setattr(cfg.agent, k, v)

    if "logging" in raw:
        for k, v in raw["logging"].items():
            if hasattr(cfg.logging, k):
                setattr(cfg.logging, k, v)

    if "dream" in raw:
        for k, v in raw["dream"].items():
            if hasattr(cfg.dream, k):
                setattr(cfg.dream, k, v)

    if "intent" in raw:
        for k, v in raw["intent"].items():
            if hasattr(cfg.intent, k):
                setattr(cfg.intent, k, v)

    if "personality" in raw:
        for k, v in raw["personality"].items():
            if hasattr(cfg.personality, k):
                setattr(cfg.personality, k, v)

    if "emotion" in raw:
        for k, v in raw["emotion"].items():
            if hasattr(cfg.emotion, k):
                setattr(cfg.emotion, k, v)

    if "tools" in raw and "enabled_tools" in raw["tools"]:
        cfg.tools = raw["tools"]["enabled_tools"]

    return cfg
