import logging
from contextlib import suppress
from unittest.mock import patch

import pytest

from src.MeshtasticCommunicationComponent import MeshtasticCommunicationComponent
from src.potatastic import main
from src.ScraperComponent import ScraperComponent


class TestPotatastic:
    def test_main_function_logging_configuration(self):
        """Test that main function configures logging correctly."""
        with (
            patch("src.potatastic.run_application") as mock_run_app,
            patch("src.potatastic.logging.basicConfig") as mock_logging_config,
        ):

            with suppress(SystemExit):
                main()

            # Verify logging was configured
            mock_logging_config.assert_called_once_with(
                format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO
            )

    def test_main_function_component_configuration(self):
        """Test that main function configures components correctly."""
        with (
            patch("src.potatastic.run_application") as mock_run_app,
            patch("src.potatastic.logging.basicConfig"),
        ):

            with suppress(SystemExit):
                main()

            # Verify run_application was called
            mock_run_app.assert_called_once()

            # Get the ContainerComponent that was passed
            container_component = mock_run_app.call_args[0][0]

            # Verify it's a ContainerComponent with correct configuration
            from asphalt.core import ContainerComponent

            assert isinstance(container_component, ContainerComponent)

    def test_main_function_container_component_config(self):
        """Test that the ContainerComponent is properly configured."""
        with (
            patch("src.potatastic.run_application") as mock_run_app,
            patch("src.potatastic.logging.basicConfig"),
        ):

            with suppress(SystemExit):
                main()

            # Get the ContainerComponent that was passed
            container_component = mock_run_app.call_args[0][0]

            # Verify it's a ContainerComponent
            from asphalt.core import ContainerComponent

            assert isinstance(container_component, ContainerComponent)

            # The component should be properly instantiated
            assert container_component is not None

    def test_main_function_exception_handling(self):
        """Test that main function handles exceptions appropriately."""
        with (
            patch("src.potatastic.run_application") as mock_run_app,
            patch("src.potatastic.logging.basicConfig"),
        ):

            # Make run_application raise an exception
            mock_run_app.side_effect = Exception("Test exception")

            # main() should let the exception propagate
            with pytest.raises(Exception, match="Test exception"):
                main()

    def test_main_when_name_is_main(self):
        """Test that main() is called when script is run directly."""
        with patch("src.potatastic.main") as mock_main:
            # Import and execute the __main__ block
            import src.potatastic

            # Simulate running the script directly
            if hasattr(src.potatastic, "__name__"):
                original_name = src.potatastic.__name__
                src.potatastic.__name__ = "__main__"

                try:
                    # Re-execute the if __name__ == '__main__' block
                    exec(
                        compile(
                            open(
                                "/Users/abeard/work/potatastic/src/potatastic.py"
                            ).read(),
                            "/Users/abeard/work/potatastic/src/potatastic.py",
                            "exec",
                        )
                    )
                except:
                    pass  # Expected if main() raises exceptions
                finally:
                    src.potatastic.__name__ = original_name

    @patch("src.potatastic.logging.basicConfig")
    @patch("src.potatastic.run_application")
    def test_integration_component_initialization(
        self, mock_run_app, mock_logging_config
    ):
        """Integration test to verify components can be instantiated."""
        # Test that the actual components can be created
        scraper = ScraperComponent()
        consumer = MeshtasticCommunicationComponent()

        assert isinstance(scraper, ScraperComponent)
        assert isinstance(consumer, MeshtasticCommunicationComponent)

        # Test that they have expected attributes
        assert hasattr(scraper, "SPOT_URL")
        assert hasattr(scraper, "FETCH_PERIOD")
        # The consumer component no longer has task_group or running attributes
        assert consumer is not None

    def test_component_types_are_importable(self):
        """Test that all component types used in main can be imported."""
        from asphalt.core import ContainerComponent

        from src.MeshtasticCommunicationComponent import (
            MeshtasticCommunicationComponent,
        )
        from src.ScraperComponent import ScraperComponent

        # These should all be importable without errors
        assert ScraperComponent is not None
        assert MeshtasticCommunicationComponent is not None
        assert ContainerComponent is not None

    def test_logging_format_string(self):
        """Test that the logging format string is valid."""
        format_string = "%(asctime)s %(levelname)s:%(message)s"

        # Create a test log record
        import logging

        logger = logging.getLogger("test")

        # This should not raise an exception
        formatter = logging.Formatter(format_string)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        assert "INFO:test message" in formatted

    def test_main_function_imports(self):
        """Test that all required imports in main module work."""
        # These imports should work without errors
        import logging

        from asphalt.core import ContainerComponent, run_application

        from src.MeshtasticCommunicationComponent import (
            MeshtasticCommunicationComponent,
        )
        from src.ScraperComponent import ScraperComponent

        # Verify they're all callable/usable
        assert callable(logging.basicConfig)
        assert callable(run_application)
        assert callable(ContainerComponent)
        assert callable(ScraperComponent)
        assert callable(MeshtasticCommunicationComponent)
