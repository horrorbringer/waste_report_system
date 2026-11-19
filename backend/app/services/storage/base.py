from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderMetadata:
    id: str
    label: str
    description: str
    supports_cdn: bool


class StorageProvider(ABC):
    """Abstract contract for pluggable file storage backends."""

    metadata: ProviderMetadata

    @abstractmethod
    def upload(self, contents: bytes, public_id: str, extension: str, content_type: str) -> str:
        """Persist validated image bytes and return a public URL or path."""

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Verify provider credentials and connectivity."""
