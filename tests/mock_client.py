"""MockClient — DEMO istemcisinin (DemoClient) test takma adı.

Tek implementasyon paket içinde (`spotify_organizer/demo_client.py`); testler bunu
buradan alır ki app→tests bağımlılığı olmasın ama eski importlar (`from tests.mock_client
import MockClient`) çalışmaya devam etsin.
"""
from spotify_organizer.demo_client import DemoClient as MockClient

__all__ = ["MockClient"]
