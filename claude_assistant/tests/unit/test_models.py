"""Unit tests for data models."""

import json
import pytest
from pydantic import ValidationError

from src.models import Config, GenerationResult, FailureDetail, StatusUpdate


class TestConfig:
    """Tests for Config model."""

    def test_config_valid_all_fields(self):
        """Config with all fields validates successfully."""
        config = Config(
            slack_channel_id="C01234567890",
            template_local_file="templates/invitation_letter.docx",
            data_source_spreadsheet="data/applicants_2026.xlsx",
            local_output_directory="./output/",
            output_google_drive_directory="https://drive.google.com/drive/folders/1ELyFup7-8zTd3fl2JLRmY41wcRN1Sf6y?usp=drive_link",
            output_formats=["docx", "pdf"],
        )
        assert config.slack_channel_id == "C01234567890"
        assert config.template_local_file == "templates/invitation_letter.docx"
        assert config.output_formats == ["docx", "pdf"]

    def test_config_missing_required_field(self):
        """Config missing slack_channel_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                template_local_file="templates/invitation_letter.docx",
                data_source_spreadsheet="data/applicants_2026.xlsx",
                local_output_directory="./output/",
            )
        assert "slack_channel_id" in str(exc_info.value)

    def test_config_optional_output_fields(self):
        """Config without optional output directories is valid."""
        config = Config(
            slack_channel_id="C01234567890",
            template_local_file="templates/invitation_letter.docx",
            data_source_spreadsheet="data/applicants_2026.xlsx",
        )
        assert config.local_output_directory is None
        assert config.output_google_drive_directory is None
        assert config.output_formats == ["docx", "pdf"]

    def test_config_json_serialization(self):
        """Config converts to/from JSON."""
        config = Config(
            slack_channel_id="C01234567890",
            template_local_file="templates/invitation_letter.docx",
            data_source_spreadsheet="data/applicants_2026.xlsx",
            local_output_directory="./output/",
        )
        json_str = config.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["slack_channel_id"] == "C01234567890"

        # Reconstruct from JSON
        config2 = Config(**json.loads(json_str))
        assert config2.slack_channel_id == config.slack_channel_id

    def test_config_invalid_output_format(self):
        """Config with invalid output format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                slack_channel_id="C01234567890",
                template_local_file="templates/invitation_letter.docx",
                data_source_spreadsheet="data/applicants_2026.xlsx",
                local_output_directory="./output/",
                output_formats=["docx", "invalid_format"],
            )
        assert "Unsupported format" in str(exc_info.value)


class TestGenerationResult:
    """Tests for GenerationResult model."""

    def test_generation_result_all_success(self):
        """GenerationResult with all successful rows."""
        result = GenerationResult(
            total_rows=3,
            successful=3,
            failed=0,
            formats_generated=["docx", "pdf"],
            output_path="./output/",
        )
        assert result.success_rate == 100.0
        assert result.is_complete_success() is True

    def test_generation_result_partial_success(self):
        """GenerationResult with some failures."""
        result = GenerationResult(
            total_rows=3,
            successful=2,
            failed=1,
            failed_details=[
                FailureDetail(
                    row_index=1,
                    identifier="Bob",
                    error="Missing required field: email",
                )
            ],
            formats_generated=["docx", "pdf"],
            output_path="./output/",
        )
        assert result.success_rate == pytest.approx(66.67, rel=0.01)
        assert result.is_complete_success() is False

    def test_generation_result_json_serialization(self):
        """GenerationResult converts to/from JSON."""
        result = GenerationResult(
            total_rows=2,
            successful=2,
            failed=0,
            formats_generated=["docx"],
            output_path="./output/",
        )
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["total_rows"] == 2
        assert parsed["successful"] == 2


class TestStatusUpdate:
    """Tests for StatusUpdate model."""

    def test_status_update_captures_all_data(self):
        """StatusUpdate captures row identifier and reason."""
        update = StatusUpdate(
            row_index=0,
            identifier="Alice",
            old_status="todo",
            new_status="done",
            reason="Document generated successfully",
        )
        assert update.identifier == "Alice"
        assert update.old_status == "todo"
        assert update.new_status == "done"
        assert "successfully" in update.reason

    def test_status_update_invalid_status(self):
        """StatusUpdate with invalid status raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            StatusUpdate(
                row_index=0,
                identifier="Alice",
                old_status="todo",
                new_status="invalid_status",
                reason="Test",
            )
        assert "Invalid status" in str(exc_info.value)

    def test_status_update_json_serialization(self):
        """StatusUpdate converts to/from JSON."""
        update = StatusUpdate(
            row_index=0,
            identifier="Alice",
            old_status="todo",
            new_status="done",
            reason="Test update",
        )
        json_str = update.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["identifier"] == "Alice"

        # Reconstruct from JSON
        update2 = StatusUpdate(**json.loads(json_str))
        assert update2.identifier == update.identifier
