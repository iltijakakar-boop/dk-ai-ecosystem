import asyncio
import math
from typing import Any, Callable, Optional

from app.config.settings import settings
from app.core.logging import logger


class RetryManager:
    """
    Manages job retries with exponential backoff and timeout checks.
    """

    @staticmethod
    def calculate_backoff(
        retry_count: int, base_delay: float = 2.0, max_delay: float = 60.0
    ) -> float:
        """
        Calculates exponential backoff delay.
        """
        if retry_count <= 0:
            return 0.0
        # Calculate base * 2^(retry_count - 1)
        delay = base_delay * math.pow(2, retry_count - 1)
        return min(max_delay, delay)

    @staticmethod
    def should_retry(retry_count: int, max_retries: Optional[int] = None) -> bool:
        """
        Checks if the job can be retried.
        """
        limit = max_retries if max_retries is not None else settings.MAX_JOB_RETRIES
        return retry_count < limit

    async def execute_with_retry(
        self,
        execution_uuid: str,
        job_id: int,
        execute_fn: Callable[[], Any],
        max_retries: Optional[int] = None,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        on_retry_callback: Optional[Callable[[int, Exception], None]] = None,
    ) -> Any:
        """
        Executes a callable with retries, backoff, and error reporting.
        """
        limit = max_retries if max_retries is not None else settings.MAX_JOB_RETRIES
        retry_count = 0

        while True:
            try:
                # Execute the job function
                result = await execute_fn()
                return result
            except Exception as e:
                # Check if we should retry
                if self.should_retry(retry_count, limit):
                    retry_count += 1
                    delay = self.calculate_backoff(retry_count, base_delay, max_delay)
                    logger.warning(
                        f"Job {job_id} (Execution: {execution_uuid}) failed with error: {e}. "
                        f"Retrying ({retry_count}/{limit}) in {delay} seconds..."
                    )

                    if on_retry_callback:
                        try:
                            on_retry_callback(retry_count, e)
                        except Exception as cb_err:
                            logger.error(f"Error executing retry callback: {cb_err}")

                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Job {job_id} (Execution: {execution_uuid}) failed after {retry_count} retries. "
                        f"Final error: {e}"
                    )
                    raise e


retry_manager = RetryManager()
