import asyncio
import random
from collections.abc import Awaitable, Callable

class CatchQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[
            Callable[[], Awaitable[None]]
        ] = asyncio.Queue()

        self._worker_task: asyncio.Task | None = None

    async def add(self, task: Callable[[], Awaitable[None]]) -> None:
        await self._queue.put(task)

        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker())

    async def _worker(self) -> None:
        while not self._queue.empty():
            task = await self._queue.get()

            try:
                await task()
            except Exception as exc:
                print(f"[Queue] Task failed: {exc}")
            finally:
                self._queue.task_done()
                
            # Random human pause between back-to-back catches
            if not self._queue.empty():
                await asyncio.sleep(random.uniform(0.3, 0.8))

    def empty(self) -> bool:
        return self._queue.empty()
