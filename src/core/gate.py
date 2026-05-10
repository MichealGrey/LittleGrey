import threading
import time


class PriorityGate:
    """主线程优先的协调原语：后台线程在主线程活跃时主动让步。"""

    def __init__(self, cooldown: float = 30.0):
        self._lock = threading.Lock()
        self._main_active = False
        self._main_release_time: float = 0.0
        self._cooldown = cooldown
        self._condition = threading.Condition(self._lock)

    def acquire(self) -> None:
        """主线程声明优先权。"""
        with self._lock:
            self._main_active = True

    def release(self) -> None:
        """主线程释放优先权。"""
        with self._lock:
            self._main_active = False
            self._main_release_time = time.monotonic()
            self._condition.notify_all()

    def wait_for_turn(self, timeout: float = 120.0) -> bool:
        """后台线程等待主线程空闲且冷却期结束。返回 True 表示可以继续，False 表示超时。"""
        deadline = time.monotonic() + timeout
        with self._lock:
            while True:
                if not self._main_active:
                    remaining_cooldown = self._cooldown - (time.monotonic() - self._main_release_time)
                    if remaining_cooldown <= 0:
                        return True
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                if self._main_active:
                    wait_time = min(remaining, 5.0)
                else:
                    wait_time = min(remaining, max(remaining_cooldown, 1.0))
                self._condition.wait(timeout=wait_time)

    def is_main_active(self) -> bool:
        with self._lock:
            return self._main_active
