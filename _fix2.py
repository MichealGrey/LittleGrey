# Fix script: Modify emotion.py
import pathlib

p = pathlib.Path('e:/Proj/AgentProj/src/agent/emotion.py')
c = p.read_text('utf-8')

old = '''        constraints = self.get_hard_constraints()
        if constraints.get("short_replies"):
            response_style = "试等、不指增订"
        if constraints.get("proactive_disabled"):
            proactive_prob = 0.0

        return {
            "emotional_density": round(min(emotional_density, 1.0), 2),
            "emoji_tendency": round(min(max(emoji_tendency, 0.0), 1.0), 2),
            "response_style": response_style,
            "topic_preference": topic_preference,
            "proactive_prob": round(min(max(proactive_prob, 0.0), 1.0), 2),
        }'''

new = '''        constraints = self.get_hard_constraints()
        boundary = self._last_result.boundary_violation if self._last_result else False

        if boundary:
            response_style = "转口突、战掉"
            emotional_density = 0.9
            emoji_tendency = 0.1
            proactive_prob = 0.0
            topic_preference = []
        elif constraints.get("short_replies"):
            response_style = "试等、不指墢订"
        if constraints.get("proactive_disabled"):
            proactive_prob = 0.0
        if constraints.get("refuse_tools"):
            proactive_prob = 0.0

        return {
            "emotional_density": round(min(emotional_density, 1.0), 2),
            "emoji_tendency": round(min(max(emoji_tendency, 0.0), 1.0), 2),
            "response_style": response_style,
            "topic_preference": topic_preference,
            "proactive_prob": round(min(max(proactive_prob, 0.0), 1.0), 2),
            "refuse_tools": constraints.get("refuse_tools", False),
            "short_replies": constraints.get("short_replies", False),
            "boundary_violation": boundary,
        }'''

assert old in c, 'old not found'
c = c.replace(old, new)
p.write_text(c, 'utf-8')
print('emotion.py get_behavior_modifiers fixed')
