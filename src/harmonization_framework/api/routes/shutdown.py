import os
import signal
import threading
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ShutdownResponse(BaseModel):
    status: str
    message: str


def _send_shutdown_signal() -> None:
    """
    Send a platform-appropriate termination signal to the current process.

    Uvicorn will interpret this as a request to shut down gracefully.
    """
    # Windows does not support SIGTERM in the same way as POSIX.
    # CTRL_BREAK_EVENT is the closest equivalent for requesting a graceful stop.
    if os.name == "nt" and hasattr(signal, "CTRL_BREAK_EVENT"):
        os.kill(os.getpid(), signal.CTRL_BREAK_EVENT)
    else:
        # POSIX platforms (macOS/Linux) handle SIGTERM for graceful shutdown.
        os.kill(os.getpid(), signal.SIGTERM)


@router.post("/")
def shutdown() -> ShutdownResponse:
    """
    Request a graceful shutdown of the sidecar process.

    The response is returned immediately; the process exits shortly after.
    """
    threading.Timer(0.1, _send_shutdown_signal).start()
    return ShutdownResponse(status="ok", message="Shutdown initiated")
