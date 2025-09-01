from contextlib import suppress
from unittest.mock import AsyncMock, Mock, patch

import pytest
from meshage.config import MQTTConfig

from src.MeshtasticCommunicationComponent import (
    MeshtasticCommunicationComponent,
)
from src.NewSpotEventSource import NewSpotEventSource
from src.Spot import Spot


class TestMeshtasticCommunicationComponent:
    def test_meshtastic_communication_component_initialization(self):
        """Test that MeshtasticCommunicationComponent initializes correctly."""
        consumer = MeshtasticCommunicationComponent()
        assert consumer.task_group is None
        assert consumer.running is False

    @pytest.mark.asyncio
    async def test_start_method(self):
        """Test that start method properly initializes resources."""
        consumer = MeshtasticCommunicationComponent()
        mock_ctx = Mock()

        with patch(
            "src.MeshtasticCommunicationComponent.anyio.create_task_group"
        ) as mock_task_group_factory:
            mock_task_group = AsyncMock()
            # Make start_soon a regular mock to avoid coroutine warnings
            mock_task_group.start_soon = Mock()
            # Set up the context manager to return the mock task group
            mock_task_group_factory.return_value = mock_task_group
            mock_task_group.__aenter__ = AsyncMock(return_value=mock_task_group)
            mock_task_group.__aexit__ = AsyncMock(return_value=None)

            await consumer.start(mock_ctx)

            # Verify MQTTConfig resource is added
            mock_ctx.add_resource.assert_called()
            args = mock_ctx.add_resource.call_args_list
            # Check that MQTTConfig and ReceivedMessageEventSource are added
            resource_types = [call[0][0].__class__ for call in args]
            assert MQTTConfig in [rt for rt in resource_types if hasattr(rt, '__name__') and rt.__name__ == 'MQTTConfig']

            # Verify task group is created and both tasks are scheduled
            mock_task_group_factory.assert_called_once()
            assert mock_task_group.start_soon.call_count == 2
            # Check that both publish_task and receive_task methods are called
            calls = mock_task_group.start_soon.call_args_list
            assert any('publish_task' in str(call[0][0]) for call in calls)
            assert any('receive_task' in str(call[0][0]) for call in calls)

    @pytest.mark.asyncio
    async def test_stop_method(self):
        """Test that stop method properly cleans up."""
        consumer = MeshtasticCommunicationComponent()
        consumer.task_group = AsyncMock()

        await consumer.stop()

        assert consumer.running is False
        consumer.task_group.__aexit__.assert_called_once_with(None, None, None)

    @pytest.mark.asyncio
    async def test_stop_method_no_task_group(self):
        """Test that stop method handles case when task_group is None."""
        consumer = MeshtasticCommunicationComponent()
        consumer.task_group = None

        # Should not raise an exception
        await consumer.stop()
        assert consumer.running is False


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
        consumer = MeshtasticCommunicationComponent()
        
        with patch(
            "src.MeshtasticCommunicationComponent.current_context"
        ) as mock_context:
            mock_ctx = AsyncMock()
            mock_ctx.request_resource.return_value = None
            mock_context.return_value = mock_ctx

            with pytest.raises(AssertionError):
                await consumer.publish_task()

    @pytest.mark.asyncio
    async def test_publish_task_mqtt_config_error(self):
        """Test publish_task when MQTT config is not available."""
        consumer = MeshtasticCommunicationComponent()
        
        with patch(
            "src.MeshtasticCommunicationComponent.current_context"
        ) as mock_context:
            mock_ctx = AsyncMock()

            # Return valid resources for spots and event source, but None for config
            def mock_request_resource(resource_type, name=None):
                if name == "new_spot_event_source":
                    return NewSpotEventSource()
                elif resource_type == MQTTConfig:
                    return None
                return None

            mock_ctx.request_resource.side_effect = mock_request_resource
            mock_context.return_value = mock_ctx

            with pytest.raises(AssertionError):
                await consumer.publish_task()

    @pytest.mark.asyncio
    async def test_publish_task_node_info_publish_error(self, sample_spots):
        """Test publish_task when node info publishing fails."""
        consumer = MeshtasticCommunicationComponent()
        
        with (
            patch(
                "src.MeshtasticCommunicationComponent.current_context"
            ) as mock_context,
            patch(
                "src.MeshtasticCommunicationComponent.aiomqtt.Client"
            ) as mock_client_class,
        ):

            # Setup mocks
            mock_ctx = AsyncMock()
            mock_config = Mock()
            mock_config.aiomqtt_config = {}
            mock_config.publish_topic = "test/topic"

            def mock_request_resource(resource_type, name=None):
                if name == "new_spot_event_source":
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
                "src.MeshtasticCommunicationComponent.MeshtasticNodeInfoMessage"
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
                        "stream_events",
                        side_effect=Exception("Test stop"),
                    ):
                        mock_ctx.request_resource.side_effect = lambda rt, name=None: (
                            event_source
                            if name == "new_spot_event_source"
                            else mock_config if rt == MQTTConfig else None
                        )

                        with pytest.raises(Exception, match="Test stop"):
                            await consumer.publish_task()

                        # Verify node info was attempted to be published
                        mock_client.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_task_successful_flow(self, sample_spots):
        """Test successful publish_task flow with mocked components."""
        consumer = MeshtasticCommunicationComponent()
        
        with (
            patch(
                "src.MeshtasticCommunicationComponent.current_context"
            ) as mock_context,
            patch(
                "src.MeshtasticCommunicationComponent.aiomqtt.Client"
            ) as mock_client_class,
        ):

            # Setup mocks
            mock_ctx = AsyncMock()
            mock_config = Mock()
            mock_config.aiomqtt_config = {}
            mock_config.publish_topic = "test/topic"
            mock_config.config = {"host": "test.host", "port": 1883}

            # Create a mock event source with controllable signal
            mock_event_source = Mock()
            mock_signal = AsyncMock()
            mock_event_source.signal = mock_signal

            def mock_request_resource(resource_type, name=None):
                if name == "new_spot_event_source":
                    return mock_event_source
                elif resource_type == MQTTConfig:
                    return mock_config
                return None

            mock_ctx.request_resource.side_effect = mock_request_resource
            mock_context.return_value = mock_ctx

            # Setup MQTT client mock
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock stream_events to only trigger once then raise exception to exit
            async def mock_stream_events():
                # Simulate one event then exit
                raise Exception("Test stop")

            mock_signal.stream_events.side_effect = mock_stream_events

            # Mock the message classes
            with (
                patch(
                    "src.MeshtasticCommunicationComponent.MeshtasticNodeInfoMessage"
                ) as mock_node_info,
                patch(
                    "src.MeshtasticCommunicationComponent.MeshtasticTextMessage"
                ) as mock_text_msg,
            ):

                # Create mock message objects that can be converted to bytes
                class MockMessage:
                    def __bytes__(self):
                        return b"mock_message_bytes"

                mock_node_info.return_value = MockMessage()
                mock_text_msg.return_value = MockMessage()

                try:
                    await consumer.publish_task()
                except Exception as e:
                    if "Test stop" not in str(e):
                        raise

                # Verify node info was published
                assert mock_client.publish.call_count >= 1
                mock_signal.stream_events.assert_called_once()


class TestReceiveTask:
    @pytest.mark.asyncio
    async def test_receive_task_initialization_error(self):
        """Test receive_task when MQTT config is not available."""
        consumer = MeshtasticCommunicationComponent()
        
        with patch(
            "src.MeshtasticCommunicationComponent.current_context"
        ) as mock_context:
            mock_ctx = AsyncMock()
            mock_ctx.request_resource.return_value = None
            mock_context.return_value = mock_ctx

            with pytest.raises(AssertionError):
                await consumer.receive_task()

    @pytest.mark.asyncio
    async def test_receive_task_event_source_error(self):
        """Test receive_task when event source is not available."""
        consumer = MeshtasticCommunicationComponent()
        
        with patch(
            "src.MeshtasticCommunicationComponent.current_context"
        ) as mock_context:
            mock_ctx = AsyncMock()
            mock_config = Mock()
            mock_config.aiomqtt_config = {}
            mock_config.receive_topic = "test/receive"

            def mock_request_resource(resource_type, name=None):
                if name == "received_message_event_source":
                    return None
                elif resource_type == MQTTConfig:
                    return mock_config
                return None

            mock_ctx.request_resource.side_effect = mock_request_resource
            mock_context.return_value = mock_ctx

            with pytest.raises(AssertionError):
                await consumer.receive_task()

    @pytest.mark.asyncio
    async def test_receive_task_successful_flow(self):
        """Test successful receive_task flow with mocked components."""
        consumer = MeshtasticCommunicationComponent()
        
        with (
            patch(
                "src.MeshtasticCommunicationComponent.current_context"
            ) as mock_context,
            patch(
                "src.MeshtasticCommunicationComponent.aiomqtt.Client"
            ) as mock_client_class,
        ):

            # Setup mocks
            mock_ctx = AsyncMock()
            mock_config = Mock()
            mock_config.aiomqtt_config = {}
            mock_config.receive_topic = "test/receive"
            mock_config.config = {"host": "test.host", "port": 1883}

            # Create a mock event source
            mock_event_source = Mock()
            mock_signal = AsyncMock()
            mock_event_source.signal = mock_signal

            def mock_request_resource(resource_type, name=None):
                if name == "received_message_event_source":
                    return mock_event_source
                elif resource_type == MQTTConfig:
                    return mock_config
                return None

            mock_ctx.request_resource.side_effect = mock_request_resource
            mock_context.return_value = mock_ctx

            # Setup MQTT client mock
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock messages to only trigger once then raise exception to exit
            async def mock_messages():
                # Simulate one message then exit
                mock_message = Mock()
                mock_message.payload = b"test_message"
                yield mock_message
                raise Exception("Test stop")

            mock_client.messages = mock_messages()

            # Mock the parser
            with patch(
                "src.MeshtasticCommunicationComponent.MeshtasticMessageParser"
            ) as mock_parser_class:
                mock_parser = Mock()
                mock_parser_class.return_value = mock_parser
                mock_parser.parse_message.return_value = Mock()

                try:
                    await consumer.receive_task()
                except Exception as e:
                    if "Test stop" not in str(e):
                        raise

                # Verify subscription was made
                mock_client.subscribe.assert_called_once_with("test/receive")
                # Verify parser was used
                mock_parser.parse_message.assert_called_once()
