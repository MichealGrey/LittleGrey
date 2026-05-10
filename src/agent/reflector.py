from src.core.types import SubTask, TaskStatus, ToolResult


class Reflector:
    def __init__(self, llm_client=None, max_reflect_retries: int = 2):
        self.llm_client = llm_client
        self.max_retries = max_reflect_retries

    def check_result(self, task: SubTask, result: ToolResult) -> tuple[bool, str]:
        if not result.success:
            return False, result.message

        if result.data is None and result.file_path is None and not result.message:
            return False, "工具返回了空结果"

        return True, ""

    def reflect_with_llm(self, task: SubTask, result: ToolResult) -> dict:
        if not self.llm_client:
            satisfied, reason = self.check_result(task, result)
            return {"satisfied": satisfied, "reason": reason, "suggestion": ""}

        task_desc = f"工具: {task.tool_name}, 参数: {task.input_params}"
        tool_output = result.message or str(result.data or "")
        return self.llm_client.reflect(task_desc, tool_output)

    def should_retry(self, task: SubTask) -> bool:
        return task.retry_count < self.max_retries and task.status != TaskStatus.SUCCESS
