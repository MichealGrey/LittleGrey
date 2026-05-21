import json
import random as random_module
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm

from src.agent.emotion import EmotionEngine
from src.agent.emotion_result import EmotionResult
from src.agent.heartbeat import Heartbeat
from src.agent.idle_intent import IdleIntentAnalyzer
from src.agent.interest_learner import InterestLearner
from src.agent.llm import LLMClient, parse_emotion_tag
from src.agent.planner import Planner
from src.agent.reflector import Reflector
from src.agent.relationship import RelationshipManager
from src.core.config import AppConfig, load_config
from src.core.gate import PriorityGate
from src.core.logger import AgentLogger
from src.core.thought_logger import ThoughtLogger
from src.core.types import ToolResult
from src.executor.engine import ExecutionEngine
from src.executor.registry import ToolRegistry, get_registry
from src.memory.dream import DreamEngine
from src.memory.long_term import LongTermMemory
from src.memory.rag import RAG
from src.memory.short_term import ShortTermMemory
from src.tools.chart_tool import ChartTool
from src.tools.excel_tool import ExcelTool
from src.tools.search_tool import SearchNewsTool
from src.tools.word_tool import WordTool


console = Console()


class AgentApp:
    def __init__(self, config_path: str | None = None):
        self.config = load_config(config_path)
        self.logger = AgentLogger(
            log_dir=self.config.resolve_path(self.config.logging.path),
            level=self.config.logging.level,
        )
        self.registry = get_registry()
        self._register_tools()

        self.thought_logger = ThoughtLogger(self.config.resolve_path(self.config.logging.path) / "thoughts")
        self.llm = LLMClient(self.config.llm, self.config.personality, self.thought_logger)
        self.planner = Planner(self.config.agent)
        self.reflector = Reflector(self.llm, self.config.agent.max_retries)
        self.emotion = EmotionEngine(llm=self.llm, logger=self.logger)

        self.gate = PriorityGate(cooldown=30.0)

        self.short_term = ShortTermMemory(
            self.config.memory,
            summary_fn=lambda text, existing: self.llm.summarize(text, existing),
            gate=self.gate,
        )

        db_path = str(self.config.resolve_path(self.config.memory.vector_db_path))
        self.long_term = LongTermMemory(
            db_path=db_path,
            embedding_model=self.config.memory.embedding_model,
        )
        self.rag = RAG(self.long_term)

        self.dream_engine = DreamEngine(
            config=self.config.dream,
            llm=self.llm,
            short_term=self.short_term,
            long_term=self.long_term,
            logger=self.logger,
            gate=self.gate,
        )

        self.engine = ExecutionEngine(
            config=self.config,
            registry=self.registry,
            logger=self.logger,
            confirm_fn=self._confirm,
        )

        self.intent_analyzer = IdleIntentAnalyzer(
            config=self.config.intent,
            personality=self.config.personality,
            llm=self.llm,
            short_term=self.short_term,
            logger=self.logger,
            gate=self.gate,
            emotion_analyzer=self.emotion,
        )

        self.relationship = RelationshipManager(
            long_term_memory=self.long_term,
            logger=self.logger,
        )
        self.emotion.set_relationship(self.relationship)

        self.heartbeat = Heartbeat(
            config=self.config.agent,
            personality=self.config.personality,
            llm=self.llm,
            short_term=self.short_term,
            long_term=self.long_term,
            rag=self.rag,
            registry=self.registry,
            engine=self.engine,
            logger=self.logger,
            on_message=self._on_heartbeat_message,
            gate=self.gate,
            on_idle=self._on_idle,
            intent_analyzer=self.intent_analyzer,
            emotion_analyzer=self.emotion,
        )

        self.interest_learner = InterestLearner(
            config=self.config.agent,
            personality=self.config.personality,
            llm=self.llm,
            long_term=self.long_term,
            registry=self.registry,
            engine=self.engine,
            logger=self.logger,
            gate=self.gate,
        )

        self._load_history()

    def _register_tools(self) -> None:
        enabled = set(self.config.tools)
        tool_map = {
            "excel_tool": ExcelTool,
            "word_tool": WordTool,
            "drawing_tool": ChartTool,
        }
        for tool_name in enabled:
            tool_cls = tool_map.get(tool_name)
            if tool_cls:
                self.registry.register(tool_cls())

    def _confirm(self, message: str) -> bool:
        return Confirm.ask(f"[yellow]{message}[/yellow]")

    def _load_history(self) -> None:
        history_path = self.config.resolve_path(
            self.config.memory.chat_history_path
        ) / "last_session.json"
        self.short_term.load(history_path)
        self.emotion._load_emotion_state(self.long_term)
        self.relationship._load_state()

    def _save_history(self) -> None:
        history_path = self.config.resolve_path(
            self.config.memory.chat_history_path
        )
        history_path.mkdir(parents=True, exist_ok=True)
        self.short_term.save(history_path / "last_session.json")
        self.emotion._save_emotion_state(self.long_term)
        self.relationship._save_state()

    def _on_idle(self) -> None:
        if random_module.random() < self.config.dream.dream_trigger_prob:
            self.dream_engine.dream()

    def _on_heartbeat_message(self, message: str) -> None:
        with patch_stdout(raw=True):
            console.print()
            console.print(
                Panel(
                    Markdown(message),
                    title=f"[bold magenta]{self.config.personality.name} (主动)[/bold magenta]",
                    border_style="magenta",
                )
            )
            console.print()
        self._save_history()

    def run(self) -> None:
        console.print(
            Panel(
                f"[bold cyan]{self.config.personality.name}[/bold cyan] 已启动！\n"
                f"输入消息与我对话，输入 /quit 退出。\n"
                f"如果你一段时间不说话，我会主动找你聊天哦～",
                title="小小灰 Agent",
                border_style="cyan",
            )
        )

        self.heartbeat.start()
        self.interest_learner.start()
        session = PromptSession()

        try:
            with patch_stdout(raw=True):
                while True:
                    try:
                        user_input = session.prompt(
                            "你> ",
                        ).strip()
                    except (EOFError, KeyboardInterrupt):
                        break

                    self.heartbeat.touch()
                    self.gate.acquire()

                    try:
                        if not user_input:
                            continue
                        if user_input == "/quit":
                            break
                        if user_input == "/clear":
                            self.short_term.clear()
                            console.print("[dim]对话已清空[/dim]")
                            continue
                        if user_input == "/history":
                            self._show_history()
                            continue

                        self.logger.new_trace()
                        response = self._process_input(user_input)
                        self._display_response(response)
                        self._display_emotion()

                        self.short_term.add("user", user_input)
                        self.short_term.add("assistant", response)

                        self._save_history()
                    finally:
                        self.gate.release()
        finally:
            self.heartbeat.stop()
            self.interest_learner.stop()
            self._save_history()
            console.print("再见！")

    def _process_input(self, user_input: str) -> str:
        with ThreadPoolExecutor(max_workers=2) as executor:
            emotion_future = executor.submit(self.emotion.understand, user_input)
            rag_future = executor.submit(self.rag.build_context, user_input)

            emotion_result = emotion_future.result()
            rag_context = rag_future.result()

        self.logger.log(
            "emotion", "understand",
            input_data={"text": user_input},
            output_data={
                "user_intent": emotion_result.user_intent,
                "primary_emotion": emotion_result.primary_emotion,
                "primary_intensity": emotion_result.primary_intensity,
                "boundary_violation": emotion_result.boundary_violation,
            },
        )

        triggered = self.emotion.check_triggers(user_input)
        if triggered:
            self.logger.log("emotion", "triggers", output_data=triggered)

        self._check_memory_recall_trigger(user_input)

        messages = self.short_term.get_messages()
        if rag_context:
            messages.append({"role": "system", "content": rag_context})
        messages.append({"role": "user", "content": user_input})

        self.logger.log("cli", "user_input", input_data={"text": user_input})

        behavior_mods = self.emotion.get_behavior_modifiers()
        relationship_desc = self.relationship.get_state_description()
        mood_info = self.emotion.get_recent_mood()
        mood_description = ""
        if mood_info.get("dominant") != "neutral":
            mood_description = f"你最近整体偏{mood_info['dominant']}，情绪{mood_info['trend']}"

        if behavior_mods.get("boundary_violation"):
            emotion_summary = self.emotion.get_recent_mood_string() if hasattr(self.emotion, "get_recent_mood_string") else ""
            defense = emotion_result.my_defense if emotion_result.boundary_violation else ""
            llm_result = self.llm.emotion_only_chat(
                user_input,
                emotion_summary=emotion_summary,
                defense=defense,
            )
        else:
            llm_result = self.llm.chat(
                messages,
                behavior_modifiers=behavior_mods,
                relationship_desc=relationship_desc,
                mood_description=mood_description,
                stream=True,
            )

        if llm_result.get("tool_calls") and not behavior_mods.get("refuse_tools"):
            return self._handle_tool_calls(llm_result["tool_calls"], user_input)

        content, agent_emotion, agent_intensity = parse_emotion_tag(llm_result.get("content", ""))
        self.emotion.apply_self_response(agent_emotion, agent_intensity)
        self.emotion._record_mood(
            emotion_result.primary_emotion,
            emotion_result.primary_intensity,
            "user_input",
            f"用户说了{emotion_result.primary_emotion}的话",
        )
        self.emotion._record_mood(agent_emotion, agent_intensity, "self_response", "自身回复")
        self.relationship.update(user_input, emotion_result, content)
        self._store_to_long_term(user_input, content, emotion_result)
        self._persist_mood_summary()
        return content

    def _handle_tool_calls(self, tool_calls: list[dict[str, Any]], original_input: str) -> str:
        chain = self.planner.plan_from_tool_calls(tool_calls)

        if chain.is_exhausted:
            return "唔...步骤太多了，我有点搞不过来qwq，能简化一下嘛？"

        results = self.engine.execute_chain(chain)

        response_parts = []
        for i, (task, result) in enumerate(zip(chain.tasks, results)):
            if result.success:
                detail = result.message
                if result.file_path:
                    detail += f"\n文件保存在: {result.file_path}"
                response_parts.append(detail)
            else:
                response_parts.append(f"步骤 {i+1} 失败了qwq: {result.message}")

        tool_summary = "\n".join(response_parts)

        followup_messages = self.short_term.get_messages()
        followup_messages.append({"role": "user", "content": original_input})
        followup_messages.append({
            "role": "assistant",
            "content": (
                f"我已经执行了操作，结果如下：\n{tool_summary}\n\n"
                f"请用小小灰的说话风格向用户汇报这些结果。"
                f"要像朋友聊天一样自然，简短一点，不要像工作报告。"
            ),
        })

        behavior_mods = self.emotion.get_behavior_modifiers()
        relationship_desc = self.relationship.get_state_description()
        followup = self.llm.chat(
            followup_messages,
            use_tools=False,
            behavior_modifiers=behavior_mods,
            relationship_desc=relationship_desc,
        )
        final_response, agent_emotion, agent_intensity = parse_emotion_tag(followup.get("content", tool_summary))
        self.emotion.apply_self_response(agent_emotion, agent_intensity)

        self._store_to_long_term(original_input, final_response)
        return final_response

    def _store_to_long_term(self, user_input: str, response: str, emotion: EmotionResult | dict | None = None) -> None:
        if any(kw in user_input.lower() for kw in ["喜欢", "偏好", "习惯", "总是", "每次", "关注", "感兴趣", "爱好"]):
            self.long_term.store_user_preference(f"用户说: {user_input}")

        if emotion is not None:
            if isinstance(emotion, EmotionResult):
                emo = emotion.primary_emotion
                intensity = emotion.primary_intensity
                weight = emotion.memory_weight
                summary = emotion.memory_summary
            else:
                emo = emotion.get("emotion", "neutral")
                intensity = emotion.get("intensity", 0)
                weight = emotion.get("memory_weight", 0.5)
                summary = ""

            if intensity >= 0.6 and emo != "neutral":
                self.long_term.store(
                    f"用户情绪[{emo}]: {user_input}",
                    metadata={"type": "emotional_event", "emotion": emo, "importance": weight},
                )

            if summary:
                self.long_term.store(
                    summary,
                    metadata={"type": "interaction_summary", "importance": weight},
                )

    def _check_memory_recall_trigger(self, user_input: str) -> None:
        recall_keywords = ['记得', '还记得', '之前', '以前', '之前做', '之前说']
        if any(kw in user_input for kw in recall_keywords):
            recent_memories = self.long_term.search(user_input, top_k=3)
            if recent_memories:
                for mem in recent_memories:
                    mem_type = mem.get('metadata', {}).get('type', '')
                    emotion_impact = mem.get('metadata', {}).get('emotion_impact', {})
                    if mem_type or emotion_impact:
                        self.emotion.recall_trigger({
                            'type': mem_type,
                            'emotion_impact': emotion_impact
                        })

    def _display_response(self, response: str) -> None:
        mods = self.emotion.get_behavior_modifiers()
        density = mods.get("emotional_density", 0.5)
        if density > 0.6:
            border = "magenta"
        elif density < 0.3:
            border = "dim"
        else:
            border = "blue"
        console.print()
        console.print(
            Panel(
                Markdown(response),
                title=f"[bold cyan]{self.config.personality.name}[/bold cyan]",
                border_style=border,
            )
        )

    def _display_emotion(self) -> None:
        bar = self.emotion.render_bar()
        console.print(
            Panel(
                bar,
                title=f"[dim]{self.config.personality.name} 情绪[/dim]",
                border_style="dim",
                padding=(0, 1),
            ),
            style="dim",
        )
        console.print()

    def _persist_mood_summary(self) -> None:
        if len(self.emotion._mood_journal) % 10 != 0:
            return
        mood = self.emotion.get_recent_mood(hours=24)
        if mood.get("count", 0) == 0:
            return
        dominant = mood.get("dominant", "neutral")
        trend = mood.get("trend", "平静")
        summary_text = f"最近24小时情绪概况：偏{dominant}，{trend}，共{mood['count']}条记录"
        try:
            self.long_term.store_mood_summary(
                text=summary_text,
                metadata={"type": "mood_summary", "dominant": dominant, "trend": trend},
            )
        except Exception:
            pass

    def _show_history(self) -> None:
        messages = self.short_term.get_messages()
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                console.print(f"[green]你>[/green] {content}")
            elif role == "assistant":
                console.print(f"[cyan]小小灰>[/cyan] {content[:100]}...")
