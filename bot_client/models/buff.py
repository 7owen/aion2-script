import time

from .metadata import BuffMetadata


class Buff:
    def __init__(self, metadata: BuffMetadata):
        self.metadata = metadata
        self.start_time = time.monotonic()
        self.clear()

    @property
    def code(self) -> str:
        return self.metadata.code

    @property
    def name(self) -> str:
        return self.metadata.name

    def __hash__(self) -> int:
        return hash(self.metadata.code)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Buff):
            return self.metadata.code == other.metadata.code
        return False

    def activate(self, start_time: float) -> None:
        self.start_time = start_time
        self.expires_at = self.start_time + self.metadata.duration

    def is_activated(self) -> bool:
        return time.monotonic() < self.expires_at

    def clear(self) -> None:
        self.expires_at = float("-inf")
