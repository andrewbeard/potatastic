"""
Shared test configuration and fixtures for potatastic tests.
"""

import asyncio
from unittest.mock import Mock

import pytest


@pytest.fixture
def sample_spot_data():
    """Sample spot data for testing."""
    return {
        "activator": "W1ABC",
        "frequency": "14.230",
        "grid4": "FN42",
        "mode": "CW",
        "name": "Mount Washington State Park",
        "reference": "K-0001",
        "spotId": 12345,
        "spotter": "W2XYZ",
        "spotTime": "2024-01-15T14:30:00",
    }


@pytest.fixture
def multiple_spot_data():
    """Multiple spot data records for testing."""
    return [
        {
            "activator": "W1ABC",
            "frequency": "14.230",
            "grid4": "FN42",
            "mode": "CW",
            "name": "Mount Washington State Park",
            "reference": "K-0001",
            "spotId": 12345,
            "spotter": "W2XYZ",
            "spotTime": "2024-01-15T14:30:00",
        },
        {
            "activator": "W3DEF",
            "frequency": "7.074",
            "grid4": "FM19",
            "mode": "FT8",
            "name": "Valley Forge National Park",
            "reference": "K-0234",
            "spotId": 12346,
            "spotter": "W3GHI",
            "spotTime": "2024-01-15T14:35:00",
        },
        {
            "activator": "VE3JKL",
            "frequency": "21.205",
            "grid4": "FN03",
            "mode": "SSB",
            "name": "Algonquin Provincial Park",
            "reference": "VE-0123",
            "spotId": 12347,
            "spotter": "VE3MNO",
            "spotTime": "2024-01-15T14:40:00",
        },
    ]


@pytest.fixture
def mock_context():
    """Mock Asphalt context for testing."""
    return Mock()


@pytest.fixture
def mock_mqtt_config():
    """Mock MQTT configuration for testing."""
    config = Mock()
    config.aiomqtt_config = {
        "hostname": "localhost",
        "port": 1883,
        "username": "test",
        "password": "test",
    }
    config.topic = "test/topic"
    return config


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_requests_response():
    """Mock requests response for API testing."""
    response = Mock()
    response.json.return_value = []
    response.status_code = 200
    return response


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers."""
    for item in items:
        # Add unit marker to all tests by default
        if not any(marker.name == "integration" for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
