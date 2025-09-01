import pytest
from asphalt.core import Signal

from src.NewSpotEventSource import NewSpotEventSource


class TestNewSpotEventSource:
    def test_new_spot_event_source_initialization(self):
        """Test that NewSpotEventSource initializes correctly."""
        event_source = NewSpotEventSource()
        assert hasattr(event_source, "signal")
        assert isinstance(event_source.signal, Signal)

    def test_signal_type(self):
        """Test that the signal is properly typed for Event."""
        event_source = NewSpotEventSource()
        # The signal should be configured to handle Event types
        assert event_source.signal is not None

    @pytest.mark.asyncio
    async def test_signal_dispatch(self):
        """Test that the signal can be dispatched."""
        event_source = NewSpotEventSource()
        
        # Create a mock spot for testing
        from src.Spot import Spot
        mock_spot_data = {
            "activator": "W1ABC",
            "frequency": "14.230",
            "grid4": "FN42",
            "mode": "CW",
            "name": "Test Spot",
            "reference": "K-0001",
            "spotId": 12345,
            "spotter": "W2XYZ",
            "spotTime": "2024-01-15T14:30:00",
        }
        spot = Spot(mock_spot_data)

        # This should not raise an exception when run in async context
        await event_source.signal.dispatch(spot=spot)

    @pytest.mark.asyncio
    async def test_signal_wait_event(self):
        """Test that the signal can be waited on."""
        import asyncio

        event_source = NewSpotEventSource()
        
        # Create a mock spot for testing
        from src.Spot import Spot
        mock_spot_data = {
            "activator": "W1ABC",
            "frequency": "14.230",
            "grid4": "FN42",
            "mode": "CW",
            "name": "Test Spot",
            "reference": "K-0001",
            "spotId": 12345,
            "spotter": "W2XYZ",
            "spotTime": "2024-01-15T14:30:00",
        }
        spot = Spot(mock_spot_data)

        # Create a task that will dispatch the signal after a short delay
        async def dispatch_after_delay():
            await asyncio.sleep(0.01)
            event_source.signal.dispatch(spot=spot)

        # Start the dispatch task
        dispatch_task = asyncio.create_task(dispatch_after_delay())

        # Wait for the event - this should complete when signal is dispatched
        try:
            await asyncio.wait_for(event_source.signal.wait_event(), timeout=1.0)
        except asyncio.TimeoutError:
            pytest.fail("Signal wait_event timed out")
        finally:
            # Clean up the dispatch task
            if not dispatch_task.done():
                dispatch_task.cancel()
                try:
                    await dispatch_task
                except asyncio.CancelledError:
                    pass

    def test_multiple_event_sources(self):
        """Test that multiple event sources can be created."""
        event_source1 = NewSpotEventSource()
        event_source2 = NewSpotEventSource()

        # They should both have signal attributes
        assert hasattr(event_source1, "signal")
        assert hasattr(event_source2, "signal")
        assert event_source1.signal is not None
        assert event_source2.signal is not None

    def test_signal_is_class_attribute(self):
        """Test that signal is defined as a class attribute."""
        # The signal is defined at class level
        assert hasattr(NewSpotEventSource, "signal")

        # Instances can access the signal
        event_source = NewSpotEventSource()
        assert hasattr(event_source, "signal")
        assert event_source.signal is not None
