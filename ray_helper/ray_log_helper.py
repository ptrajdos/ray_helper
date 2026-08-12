import logging
from log_keeper.log_keeper import LogKeeper

def _ray_queue_forwarder(ray_queue, logkeeper_queue, stop_event):
    """Background thread that drains a ``ray.util.queue.Queue`` into the
    LogKeeper ``multiprocessing.Manager().Queue()``.

    Runs until *stop_event* is set **and** the ray_queue is empty.

    Uses ``get(block=False)`` + sleep instead of ``get(timeout=...)`` to
    avoid Ray actor-level timeout tasks that raise ``Empty`` as a
    ``TASK_EXECUTION_EXCEPTION``.
    """
    import time

    while not stop_event.is_set():
        if ray_queue.empty():
            time.sleep(0.1)
            continue
        try:
            record = ray_queue.get(block=False)
            logkeeper_queue.put(record)
        except Exception:
            time.sleep(0.1)
            continue
    # Drain remaining records after stop signal
    while not ray_queue.empty():
        try:
            record = ray_queue.get(block=False)
            logkeeper_queue.put(record)
        except Exception:
            break


class RayLogKeeperHelper:
    """Helper for Ray-compatible LogKeeper logging.

    When using Ray, workers cannot receive the multiprocessing Manager
    queue because it cannot be serialized.  This helper creates a
    ray.util.queue.Queue for worker processes and forwards records into
    the real LogKeeper queue.
    """

    def __init__(self, logging_queue, backend="loky"):
        self.logging_queue = logging_queue
        self.backend = backend
        self.worker_logging_queue = logging_queue
        self._ray_forwarder_stop = None
        self._ray_forwarder_thread = None

        if self.backend == "ray":
            from ray.util.queue import Queue as RayQueue
            import threading

            self.worker_logging_queue = RayQueue()
            self._ray_forwarder_stop = threading.Event()
            self._ray_forwarder_thread = threading.Thread(
                target=_ray_queue_forwarder,
                args=(
                    self.worker_logging_queue,
                    self.logging_queue,
                    self._ray_forwarder_stop,
                ),
                daemon=True,
            )

    def start(self):
        if self._ray_forwarder_thread is not None:
            self._ray_forwarder_thread.start()

    def quit(self):
        if self._ray_forwarder_stop is not None:
            self._ray_forwarder_stop.set()
        if self._ray_forwarder_thread is not None:
            self._ray_forwarder_thread.join(timeout=5.0)

    def get_worker_queue(self):
        return self.worker_logging_queue

    @staticmethod
    def get_logger(logging_queue, name):
        """Return a LogKeeper client logger if queue is available, else a standard logger."""
        if logging_queue is not None:
            return LogKeeper.get_client_logger(logging_queue=logging_queue, logger_name=name)
        return logging.getLogger(name)

    @staticmethod
    def shutdown_logger(logging_queue, logger):
        """Shutdown LogKeeper client logger only when queue is available."""
        if logging_queue is not None:
            LogKeeper.shutdown_client_logger(logger)
