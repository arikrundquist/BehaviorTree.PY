from enum import Enum


class NodeStatus(Enum):
    """the status of a node"""

    # IDLE = 0
    RUNNING = 1
    SUCCESS = 2
    FAILURE = 3
    SKIPPED = 4
