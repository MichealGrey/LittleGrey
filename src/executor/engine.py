from typing import Any, Callable

from src.core.config import AppConfig
from src.core.logger import AgentLogger
from src.core.types import ExecutionChain, TaskStatus, ToolResult
from src.executor.registry import ToolRegistry


class ExecutionEngine:
    def __init__(
        self,
        config: AppConfig,
        registry: ToolRegistry,
        logger: AgentLogger,
        confirm_fn: Callable[[str], bool] | None = None,
    ):
        self.config = config
        self.registry = registry
        self.logger = logger
        self.confirm_fn = confirm_fn or (lambda msg: True)

    def execute_chain(self, chain: ExecutionChain) -> list[ToolResult]:
        results: list[ToolResult] = []

        while chain.current_task is not None:
            if chain.is_exhausted:
                self.logger.log(
                    "executor", "max_steps_reached",
                    input_data={"steps": chain.current_step, "max": chain.max_steps},
                    status="warning",
                )
                break

            task = chain.current_task
            tool = self.registry.get(task.tool_name)

            if tool is None:
                task.status = TaskStatus.FAILED
                task.error = f"工具未注册: {task.tool_name}"
                results.append(ToolResult(success=False, message=task.error))
                chain.advance()
                continue

            valid, err = tool.validate_input(task.input_params)
            if not valid:
                task.status = TaskStatus.FAILED
                task.error = f"输入校验失败: {err}"
                results.append(ToolResult(success=False, message=task.error))
                chain.advance()
                continue

            is_risky, risk_msg = tool.check_risky(task.input_params)
            if is_risky and self.config.agent.human_in_the_loop:
                confirmed = self.confirm_fn(risk_msg)
                if not confirmed:
                    task.status = TaskStatus.SKIPPED
                    results.append(ToolResult(success=False, message=f"用户取消操作: {risk_msg}"))
                    chain.advance()
                    continue

            result = self._execute_with_retry(tool, task)
            task.result = result.data if result.success else None
            task.status = TaskStatus.SUCCESS if result.success else TaskStatus.FAILED
            task.error = result.message if not result.success else None
            results.append(result)

            chain.advance()

        return results

    def _execute_with_retry(self, tool: Any, task: Any) -> ToolResult:
        max_retries = self.config.agent.max_retries
        last_result = None

        for attempt in range(max_retries + 1):
            result = tool.execute(task.input_params)

            self.logger.log(
                "executor", f"{tool.name}.execute",
                input_data=task.input_params,
                output_data={"success": result.success, "message": result.message},
                extra={"attempt": attempt, "task_index": task.retry_count if hasattr(task, 'retry_count') else 0},
            )

            if result.success:
                return result

            last_result = result
            task.retry_count = attempt + 1

            if attempt < max_retries:
                self.logger.log(
                    "executor", "retry",
                    input_data={"tool": tool.name, "attempt": attempt + 1},
                    status="warning",
                    error=result.message,
                )

        if self.config.agent.human_in_the_loop and last_result and not last_result.success:
            msg = f"工具 {tool.name} 重试 {max_retries} 次后仍失败: {last_result.message}\n是否继续执行其他任务？"
            self.confirm_fn(msg)

        return last_result or ToolResult(success=False, message="未知错误")

    def execute_single(self, tool_name: str, params: dict[str, Any]) -> ToolResult:
        tool = self.registry.get(tool_name)
        if tool is None:
            return ToolResult(success=False, message=f"工具未注册: {tool_name}")

        valid, err = tool.validate_input(params)
        if not valid:
            return ToolResult(success=False, message=f"输入校验失败: {err}")

        is_risky, risk_msg = tool.check_risky(params)
        if is_risky and self.config.agent.human_in_the_loop:
            if not self.confirm_fn(risk_msg):
                return ToolResult(success=False, message=f"用户取消操作: {risk_msg}")

        return tool.execute(params)
