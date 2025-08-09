from datetime import datetime

import pytest

from src.Spot import Spot


class TestSpot:
    @pytest.fixture
    def sample_spot_data(self):
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

    def test_spot_initialization(self, sample_spot_data):
        """Test that a Spot is correctly initialized from dictionary data."""
        spot = Spot(sample_spot_data)

        assert spot.callsign == "W1ABC"
        assert spot.frequency == 14.230
        assert spot.grid == "FN42"
        assert spot.mode == "CW"
        assert spot.name == "Mount Washington State Park"
        assert spot.reference == "K-0001"
        assert spot.id == 12345
        assert spot.spotter == "W2XYZ"
        assert isinstance(spot.timestamp, datetime)
        assert spot.timestamp.year == 2024
        assert spot.timestamp.month == 1
        assert spot.timestamp.day == 15

    def test_spot_str_representation(self, sample_spot_data):
        """Test the string representation of a Spot."""
        spot = Spot(sample_spot_data)
        expected = "W1ABC @ 14.23 CW\nK-0001 (Mount Washington State Park)"
        assert str(spot) == expected

    def test_spot_key_property(self, sample_spot_data):
        """Test the key property generates correct unique identifier."""
        spot = Spot(sample_spot_data)
        expected_key = "W1ABC-14.23-CW"
        assert spot.key == expected_key

    def test_spot_with_different_data(self):
        """Test Spot with different data types and values."""
        spot_data = {
            "activator": "VE3DEF",
            "frequency": "7.074",
            "grid4": "FN03",
            "mode": "FT8",
            "name": "Algonquin Provincial Park",
            "reference": "VE-0123",
            "spotId": 67890,
            "spotter": "VE3GHI",
            "spotTime": "2024-12-25T09:15:30",
        }
        spot = Spot(spot_data)

        assert spot.callsign == "VE3DEF"
        assert spot.frequency == 7.074
        assert spot.mode == "FT8"
        assert spot.key == "VE3DEF-7.074-FT8"

    def test_spot_frequency_conversion(self):
        """Test that frequency is properly converted to float."""
        spot_data = {
            "activator": "G0ABC",
            "frequency": "21.205",
            "grid4": "IO91",
            "mode": "SSB",
            "name": "Test Park",
            "reference": "G-0001",
            "spotId": 11111,
            "spotter": "G0DEF",
            "spotTime": "2024-06-01T12:00:00",
        }
        spot = Spot(spot_data)
        assert isinstance(spot.frequency, float)
        assert spot.frequency == 21.205

    def test_spot_timestamp_parsing(self):
        """Test various timestamp formats are properly parsed."""
        spot_data = {
            "activator": "JA1ABC",
            "frequency": "28.400",
            "grid4": "PM95",
            "mode": "CW",
            "name": "Test Park",
            "reference": "JA-0001",
            "spotId": 22222,
            "spotter": "JA1DEF",
            "spotTime": "2024-03-15T23:45:59",
        }
        spot = Spot(spot_data)
        assert spot.timestamp.hour == 23
        assert spot.timestamp.minute == 45
        assert spot.timestamp.second == 59
