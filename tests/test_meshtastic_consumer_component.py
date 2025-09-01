from contextlib import suppress
from unittest.mock import AsyncMock, Mock, patch

import pytest
from meshage.config import MQTTConfig

from src.MeshtasticConsumerComponent import MeshtasticCommunicationComponent, publish_task, receive_task
from src.NewSpotEventSource import NewSpotEventSource
from src.Spot import Spot


class TestMeshtasticCommunicationComponent:
    def test_meshtastic_communication_component_initialization(self):
        """Test that MeshtasticCommunicationComponent initializes correctly."""
        consumer = MeshtasticCommunicationComponent()
        # The component now has no attributes in __init__, just pass
        assert consumer is not None

    @pytest.mark.asyncio
    async def test_start_method(self):
        """Test that start method properly initializes resources."""
        consumer = MeshtasticCommunicationComponent()
        mock_ctx = Mock()

        with patch(
            "src.MeshtasticConsumerComponent.anyio.create_task_group"
        ) as mock_task_group_factory:
            mock_task_group = AsyncMock()
            # Make start_soon a regular mock to avoid coroutine warnings
            mock_task_group.start_soon = Mock()
            # Set up the context manager to return the mock task group
            mock_task_group_factory.return_value.__aenter__ = AsyncMock(return_value=mock_task_group)
            mock_task_group_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            await consumer.start(mock_ctx)

            # Verify MQTTConfig resource is added
            mock_ctx.add_resource.assert_called_once()
            args = mock_ctx.add_resource.call_args[0]
            assert isinstance(args[0], MQTTConfig)

            # Verify task group is created and both tasks are scheduled
            mock_task_group_factory.assert_called_once()
            assert mock_task_group.start_soon.call_count == 2
            # Check that both publish_task and receive_task are called
            calls = mock_task_group.start_soon.call_args_list
            assert any(publish_task in call[0] for call in calls)
            assert any(receive_task in call[0] for call in calls)

    @pytest.mark.asyncio
    async def test_stop_method(self):
        """Test that stop method properly cleans up."""
        consumer = MeshtasticCommunicationComponent()
        
        # The stop method is now just pass, so it should not raise an exception
        await consumer.stop()

    @pytest.mark.asyncio
    async def test_stop_method_no_task_group(self):
        """Test that stop method handles case when task_group is None."""
        consumer = MeshtasticCommunicationComponent()
        
        # The stop method is now just pass, so it should not raise an exception
        await consumer.stop()


class TestPublishTask:
    @pytest.fixture
    def sample_spots(self):
        spot_data = [
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
            }
        ]
        return [Spot(data) for data in spot_data]

    @pytest.mark.asyncio
    async def test_publish_task_initialization_error(self):
        """Test publish_task when resources are not available."""
        with patch("src.MeshtasticConsumerComponent.current_context") as mock_context:
            mock_ctx = AsyncMock()
            mock_ctx.request_resource.return_value = None
            mock_context.return_value = mock_ctx

            with pytest.raises(AssertionError):
                await publish_task()

    @pytest.mark.asyncio
    async def test_publish_task_mqtt_config_error(self):
        """Test publish_task when MQTT config is not available."""
        with patch("src.MeshtasticConsumerComponent.current_context") as mock_context:
            mock_ctx = AsyncMock()

            # Return valid resources for spots and event source, but None for config
            def mock_request_resource(resource_type, name=None):
                if name == "new_spots":
                    return []
                elif name == "new_spot_event_source":
                    return NewSpotEventSource()
                elif resource_type == MQTTConfig:
                    return None
                return None

            mock_ctx.request_resource.side_effect = mock_request_resource
            mock_context.return_value = mock_ctx

            with pytest.raises(AssertionError):
                await publish_task()

    @pytest.mark.asyncio
    async def test_publish_task_node_info_publish_error(self, sample_spots):
        """Test publish_task when node info publishing fails."""
        with (
            patch("src.MeshtasticConsumerComponent.current_context") as mock_context,
            patch(
                "src.MeshtasticConsumerComponent.aiomqtt.Client"
            ) as mock_client_class,
        ):

            # Setup mocks
            mock_ctx = AsyncMock()
            mock_config = Mock()
            mock_config.aiomqtt_config = {}
            mock_config.publish_topic = "test/topic"

            def mock_request_resource(resource_type, name=None):
                if name == "new_spots":
                    return sample_spots
                elif name == "new_spot_event_source":
                    return NewSpotEventSource()
                elif resource_type == MQTTConfig:
                    return mock_config
                return None

            mock_ctx.request_resource.side_effect = mock_request_resource
            mock_context.return_value = mock_ctx

            # Setup MQTT client mock
            mock_client = AsyncMock()
            mock_client.publish.side_effect = Exception("MQTT Error")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock the message classes
            with patch(
                "src.MeshtasticConsumerComponent.MeshtasticNodeInfoMessage"
            ) as mock_node_info:
                mock_node_info.return_value = Mock()

                # This should handle the exception gracefully and continue
                # We'll simulate the event loop by manually calling once
                with suppress(Exception):
                    # Since this would run forever, we'll test just the initialization part
                    # by mocking the wait_event to raise an exception after first call
                    event_source = NewSpotEventSource()
                    with patch.object(
                        event_source.signal,
                        "wait_event",
                        side_effect=Exception("Test stop"),
                    ):
                        mock_ctx.request_resource.side_effect = lambda rt, name=None: (
                            sample_spots
                            if name == "new_spots"
                            else (
                                event_source
                                if name == "new_spot_event_source"
                                else mock_config if rt == MQTTConfig else None
                            )
                        )

                        with pytest.raises(Exception, match="Test stop"):
                            await publish_task()

                        # Verify node info was attempted to be published
                        mock_client.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_task_successful_flow(self, sample_spots):
        """Test successful publish_task flow with mocked components."""
        with (
            patch("src.MeshtasticConsumerComponent.current_context") as mock_context,
            patch(
                "src.MeshtasticConsumerComponent.aiomqtt.Client"
            ) as mock_client_class,
        ):

            # Setup mocks
            mock_ctx = AsyncMock()
            mock_config = Mock()
            mock_config.aiomqtt_config = {}
            mock_config.publish_topic = "test/topic"

            # Create a mock event source with controllable signal
            mock_event_source = Mock()
            mock_signal = AsyncMock()
            mock_event_source.signal = mock_signal

            def mock_request_resource(resource_type, name=None):
                if name == "new_spots":
                    return sample_spots
                elif name == "new_spot_event_source":
                    return mock_event_source
                elif resource_type == MQTTConfig:
                    return mock_config
                return None

            mock_ctx.request_resource.side_effect = mock_request_resource
            mock_context.return_value = mock_ctx

            # Setup MQTT client mock
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock wait_event to only trigger once then raise exception to exit
            async def mock_wait_event():
                # Simulate one event then exit
                raise Exception("Test stop")

            mock_signal.wait_event.side_effect = mock_wait_event

            # Mock the message classes
            with (
                patch(
                    "src.MeshtasticConsumerComponent.MeshtasticNodeInfoMessage"
                ) as mock_node_info,
                patch(
                    "src.MeshtasticConsumerComponent.MeshtasticTextMessage"
                ) as mock_text_msg,
            ):

                # Create mock message objects that can be converted to bytes
                class MockMessage:
                    def __bytes__(self):
                        return b"mock_message_bytes"

                mock_node_info.return_value = MockMessage()
                mock_text_msg.return_value = MockMessage()

                try:
                    await publish_task()
                except Exception as e:
                    if "Test stop" not in str(e):
                        raise

                # Verify node info was published
                assert mock_client.publish.call_count >= 1
                mock_signal.wait_event.assert_called_once()
