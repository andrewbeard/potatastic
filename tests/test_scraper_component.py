from unittest.mock import AsyncMock, Mock, patch

import pytest
import requests

from src.NewSpotEventSource import NewSpotEventSource
from src.ScraperComponent import ScraperComponent
from src.Spot import Spot


class TestScraperComponent:
    @pytest.fixture
    def sample_api_response(self):
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
        ]

    def test_scraper_component_initialization(self):
        """Test that ScraperComponent initializes correctly."""
        scraper = ScraperComponent()
        assert scraper.task_group is None
        assert scraper.running is False
        assert scraper.SPOT_URL == "https://api.pota.app/v1/spots"
        assert scraper.FETCH_PERIOD == 30

    @patch("src.ScraperComponent.requests.get")
    def test_get_spot_reports(self, mock_get, sample_api_response):
        """Test that get_spot_reports fetches and parses API data correctly."""
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_get.return_value = mock_response

        spots = ScraperComponent().get_spot_reports()

        mock_get.assert_called_once_with("https://api.pota.app/v1/spots")
        assert len(spots) == 2
        assert all(isinstance(spot, Spot) for spot in spots)
        assert spots[0].callsign == "W1ABC"
        assert spots[1].callsign == "W3DEF"

    def test_get_new_spots_with_empty_existing(self, sample_api_response):
        """Test get_new_spots when no existing spots are present."""
        scraper = ScraperComponent()
        existing_spots = {}
        new_scrape = [Spot(spot_data) for spot_data in sample_api_response]

        added = scraper.get_new_spots(existing_spots, new_scrape)

        assert len(added) == 2
        assert len(existing_spots) == 2
        assert "W1ABC-14.23-CW" in existing_spots
        assert "W3DEF-7.074-FT8" in existing_spots

    def test_get_new_spots_with_existing_spots(self, sample_api_response):
        """Test get_new_spots when some spots already exist."""
        scraper = ScraperComponent()
        first_spot = Spot(sample_api_response[0])
        existing_spots = {first_spot.key: first_spot}
        new_scrape = [Spot(spot_data) for spot_data in sample_api_response]

        added = scraper.get_new_spots(existing_spots, new_scrape)

        # Only the second spot should be added as new
        assert len(added) == 1
        assert added[0].callsign == "W3DEF"
        assert len(existing_spots) == 2

    def test_get_new_spots_no_new_spots(self, sample_api_response):
        """Test get_new_spots when all spots already exist."""
        scraper = ScraperComponent()
        existing_spots = {}
        initial_scrape = [Spot(spot_data) for spot_data in sample_api_response]

        # First scrape - all spots are new
        scraper.get_new_spots(existing_spots, initial_scrape)

        # Second scrape with same data - no new spots
        added = scraper.get_new_spots(existing_spots, initial_scrape)

        assert len(added) == 0
        assert len(existing_spots) == 2

    @pytest.mark.asyncio
    async def test_start_method(self):
        """Test that start method properly initializes resources."""
        scraper = ScraperComponent()
        mock_ctx = Mock()

        with patch(
            "src.ScraperComponent.anyio.create_task_group"
        ) as mock_task_group_factory:
            mock_task_group = AsyncMock()
            # Make start_soon a regular mock to avoid coroutine warnings
            mock_task_group.start_soon = Mock()
            mock_task_group_factory.return_value = mock_task_group

            await scraper.start(mock_ctx)

            # Verify resources are added
            assert mock_ctx.add_resource.call_count == 2
            calls = mock_ctx.add_resource.call_args_list

            # Check that NewSpotEventSource is added
            assert any(isinstance(call[0][0], NewSpotEventSource) for call in calls)
            # Check that spots dict is added
            assert any(
                call[0][0] == {} and call[1].get("name") == "spots" for call in calls
            )

            # Verify task group is started
            mock_task_group.__aenter__.assert_called_once()
            # The running attribute is not set in the new implementation
            mock_task_group.start_soon.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_method(self):
        """Test that stop method properly cleans up."""
        scraper = ScraperComponent()
        mock_task_group = AsyncMock()
        scraper.task_group = mock_task_group
        scraper.running = True

        await scraper.stop()

        assert scraper.running is False
        mock_task_group.__aexit__.assert_called_once_with(None, None, None)

    @pytest.mark.asyncio
    async def test_stop_method_no_task_group(self):
        """Test that stop method handles case when task_group is None."""
        scraper = ScraperComponent()
        scraper.running = True
        scraper.task_group = None

        # Should not raise an exception
        await scraper.stop()
        assert scraper.running is False

    @patch("src.ScraperComponent.requests.get")
    def test_get_spot_reports_api_error(self, mock_get):
        """Test that get_spot_reports handles API errors appropriately."""
        mock_get.side_effect = requests.RequestException("API Error")

        scraper = ScraperComponent()

        # Should raise the exception (component handles this in scraper_task)
        with pytest.raises(requests.RequestException):
            scraper.get_spot_reports()

    @patch("src.ScraperComponent.requests.get")
    def test_get_spot_reports_invalid_json(self, mock_get):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        scraper = ScraperComponent()

        with pytest.raises(ValueError):
            scraper.get_spot_reports()
