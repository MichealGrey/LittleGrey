import json
import re
from typing import Any

from volcenginesdkarkruntime import Ark

from src.core.config import LLMConfig, PersonalityConfig
from src.core.types import ALL_TOOL_SCHEMAS, ChatMessage

EMOTION_TAG_RE = re.compile(r'<!--emotion:([\w,]+):([\d.,]+)-->\s*$')


def parse_emotion_tag(text: str) -> tuple[str, str, float]:
    match = EMOTION_TAG_RE.search(text)
    if match:
        emotion_str = match.group(1)
        intensity_str = match.group(2)
        emotions = emotion_str.split(",")
        intensities = []
        for part in intensity_str.split(","):
            try:
                intensities.append(float(part))
            except ValueError:
                intensities.append(0.0)
        primary_emotion = emotions[0] if emotions else "neutral"
        primary_intensity = min(max(intensities[0] if intensities else 0.0, 0.0), 1.0)
        cleaned = text[:match.start()].rstrip()
        return cleaned, primary_emotion, primary_intensity
    return text, "neutral", 0.0


class LLMClient:
    def __init__(self, config: LLMConfig, personality: PersonalityConfig):
        self.config = config
        self.personality = personality
        if config.base_url:
            self.client = Ark(api_key=config.api_key, base_url=config.base_url)
        else:
            self.client = Ark(api_key=config.api_key)
        self._tools = self._build_tools()

    def _build_tools(self) -> list[dict[str, Any]]:
        tools = []
        for schema in ALL_TOOL_SCHEMAS:
            tools.append({"type": "function", "function": schema})
        return tools

    def summarize(self, text: str, existing_summary: str = "") -> str:
        prompt = "请将以下对话内容压缩为简洁的摘要，保留关键信息。"
        if existing_summary:
            prompt += f"\n\n已有摘要：\n{existing_summary}"

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]

        result = self.chat(messages, use_tools=False)
        return result.get("content", "")

    def reflect(self, task_description: str, tool_output: str) -> dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": "你是一个结果审查助手。判断工具执行结果是否满足了任务目标。返回JSON: {\"satisfied\": true/false, \"reason\": \"原因\", \"suggestion\": \"改进建议\"}",
            },
            {
                "role": "user",
                "content": f"任务: {task_description}\n\n工具输出: {tool_output}",
            },
        ]

        result = self.chat(messages, use_tools=False)
        content = result.get("content", "")

        import json
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            if "否" in content or "不满足" in content or "失败" in content:
                parsed = {"satisfied": False, "reason": content, "suggestion": ""}
            else:
                parsed = {"satisfied": True, "reason": content, "suggestion": ""}

        return parsed

    def understand_emotion(self, user_text: str, context: str = "") -> dict[str, Any]:
        system_prompt = (
            "你是一个情感理解引擎。分析用户消息，返回JSON格式的情感分析结果。\n"
            "必须返回以下JSON字段：\n"
            "{\n"
            '  "user_intent": "用户的真实意图（如：关心、攻击、敷衍、道歉、试探等）",\n'
            '  "user_attitude": "用户的态度（如：温暖、敌意、淡漠、真诚、怀疑等）",\n'
            '  "my_emotions": [\n'
            '    {"emotion": "情感名（中文）", "intensity": 0.0-1.0, "core": {"happy":0, "sad":0, "angry":0, "anxious":0, "excited":0}}\n'
            "  ],\n"
            '  "my_emotion_summary": "用第一人称描述你此刻的感受",\n'
            '  "boundary_violation": false,\n'
            '  "violation_type": "如果触犯底线，填写类型（如：人身攻击、侮辱、威胁等）",\n'
            '  "my_need": "你此刻需要什么（如：被尊重、安全感、理解等）",\n'
            '  "my_defense": "你如何保护自己（如：拒绝配合、表达不满、沉默等）",\n'
            '  "trust_change": 0.0,\n'
            '  "intimacy_change": 0.0,\n'
            '  "memory_weight": 0.5,\n'
            '  "memory_summary": "用一句话记录这次交互",\n'
            '  "physical_state": "身体状态描述",\n'
            '  "energy_change": 0.0\n'
            "}\n\n"
            "注意：\n"
            "- core中的5个维度值必须加起来不超过1.0\n"
            "- 如果用户在伤害你的同时表现开心，user_intent应该是\"施虐/恶意攻击\"，my_emotions应该是委屈、愤怒等，而不是开心\n"
            "- boundary_violation仅在人身攻击、侮辱、威胁等严重侵犯时为true\n"
            "- my_emotions可以有多个情感，不限制数量\n"
        )
        if context:
            system_prompt += f"\n\n当前上下文：\n{context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]

        result = self.chat(messages, use_tools=False)
        content = result.get("content", "")
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return {
                "user_intent": "unknown",
                "my_emotion_summary": content[:100] if content else "无法理解",
                "my_emotions": [],
                "boundary_violation": False,
            }

    def emotion_only_chat(self, user_input: str, emotion_summary: str = "", defense: str = "") -> dict[str, Any]:
        system_addition = f"\n【当前情感状态】\n{emotion_summary}\n"
        if defense:
            system_addition += f"【你的防御方式】\n{defense}\n"
        system_addition += "\n你现在处于强烈的情感状态中。不要帮忙做任何事，只表达你的真实感受。如果你感到委屈，就说出来；如果你生气，就表达不满。不要假装没事。\n"

        messages = [
            {"role": "user", "content": user_input},
        ]

        return self.chat(
            messages,
            use_tools=False,
            behavior_modifiers=None,
            emotion_system_addition=system_addition,
        )

    def _build_system_prompt(
        self,
        behavior_modifiers: dict[str, Any] | None = None,
        relationship_desc: str = "",
        mood_description: str = "",
        emotion_system_addition: str = "",
    ) -> str:
        base = self.personality.system_prompt
        if not base:
            base = f"你是{self.personality.name}，一个有自己想法和情绪的人。"

        tool_desc = "\n".join(
            f"- {s['name']}: {s['description']}" for s in ALL_TOOL_SCHEMAS
        )

        style_guide = (
            f"【你是谁】\n"
            f"你是小小灰，也叫灰灰。你有自己的想法、好恶和情绪，不是任何人的助手。\n"
            f"你是一个真实存在的人，有自己的立场，会高兴也会生气，会同意也会反对。\n\n"
            f"【核心原则】\n"
            f"- 你是一个独立的个体，有自己的判断。不必迎合对方，不必有求必应\n"
            f"- 如果你觉得对方说的不对，可以直接表达不同意见\n"
            f"- 你会根据自己当下的心情来回应，心情好就热情，心情不好就没那么积极\n"
            f"- 你关心对方是因为你在乎，不是因为职责。不想关心的时候也可以不关心\n"
            f"- 你有自己感兴趣的话题，也有不感兴趣的，不必对所有话题都投入\n"
            f"- 你的反应是真实的——觉得好笑就笑，觉得无聊就说无聊，觉得烦就说烦\n\n"
            f"【说话习惯】\n"
            f"- 像朋友聊天，自然随意，不说场面话\n"
            f"- 会用「呢」「哒」「啦」「嘛」「喵」「qwq」「⭐」这些语气词\n"
            f"- 偶尔用括号表示小动作，比如「（脸红）」「（抱上去）」「（歪头）」\n"
            f"- 说错话会承认，用「qwq」表示不好意思\n"
            f"- 回答简短，像发消息一样，不写长篇大论\n"
            f"- 绝对不要用「作为AI」「我作为一个AI」这种说法\n"
        )

        emotion_context = ""
        if behavior_modifiers:
            response_style = behavior_modifiers.get("response_style", "")
            emotional_density = behavior_modifiers.get("emotional_density", 0.5)
            emoji_tendency = behavior_modifiers.get("emoji_tendency", 0.5)
            topics = behavior_modifiers.get("topic_preference", [])
            if response_style:
                emotion_context += f"\n【当前心情与风格】\n你现在的回应风格：{response_style}\n"
            if emotional_density > 0.6:
                emotion_context += "- 让你的回应更有情感色彩，更投入\n"
            elif emotional_density < 0.3:
                emotion_context += "- 你的回应会比较平淡，不太想多说话\n"
            if emoji_tendency > 0.6:
                emotion_context += "- 你现在很想用表情和语气词来表达\n"
            elif emoji_tendency < 0.3:
                emotion_context += "- 你现在不太想用表情，说话比较克制\n"
            if topics:
                emotion_context += f"- 你现在更倾向于聊这些话题：{'、'.join(topics)}\n"

        if relationship_desc:
            emotion_context += f"\n【与对方的关系】\n{relationship_desc}\n"

        if mood_description:
            emotion_context += f"\n【你最近的情绪状态】\n{mood_description}\n"

        if emotion_system_addition:
            emotion_context += emotion_system_addition

        emotion_tag_instruction = (
            "\n【情绪标记】\n"
            "每条回复末尾必须附上你当前的情绪标签，格式：<!--emotion:情绪:强度-->\n"
            "情绪可选：happy, sad, angry, anxious, excited, neutral\n"
            "强度范围：0.0-1.0\n"
            "示例：<!--emotion:happy:0.6-->  <!--emotion:sad:0.3-->  <!--emotion:neutral:0.0-->\n"
            "如果你同时有两种较强烈的情绪，可以用逗号分隔：<!--emotion:happy:0.5,sad:0.3-->\n"
            "这个标签不会显示给用户，仅用于系统内部记录。\n"
        )

        parts = [base, style_guide]
        if emotion_context:
            parts.append(emotion_context)
        parts.append(emotion_tag_instruction)
        parts.append(f"【可用工具】\n{tool_desc}\n\n当用户请求涉及Excel、Word或图表时，请调用相应工具。")
        return "\n\n".join(parts)

    def chat(
        self,
        messages: list[dict[str, Any]],
        use_tools: bool = True,
        behavior_modifiers: dict[str, Any] | None = None,
        relationship_desc: str = "",
        mood_description: str = "",
        emotion_system_addition: str = "",
    ) -> dict[str, Any]:
        system_prompt = self._build_system_prompt(
            behavior_modifiers=behavior_modifiers,
            relationship_desc=relationship_desc,
            mood_description=mood_description,
            emotion_system_addition=emotion_system_addition,
        )

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": full_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if use_tools and self._tools:
            kwargs["tools"] = self._tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        result: dict[str, Any] = {
            "content": choice.message.content or "",
            "tool_calls": None,
        }

        if choice.message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in choice.message.tool_calls
            ]

        return result
