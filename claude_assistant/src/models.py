"""Data models for Claude Slack Agent.

Defines configuration, generation results, and status update models using Pydantic.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class Config(BaseModel):
    """Configuration for document generation request."""

    slack_channel_id: str = Field(
        ..., description="Slack channel ID where requests are received"
    )
    template_local_file: str = Field(
        ..., description="Path to tokenized template (.docx)"
    )
    data_source_spreadsheet: str = Field(
        ..., description="Path to Excel data file with headers matching template tokens"
    )
    local_output_directory: Optional[str] = Field(
        None, description="(Optional) Local filesystem path for output documents"
    )
    output_google_drive_directory: Optional[str] = Field(
        None, description="(Optional) Google Drive folder URL for output"
    )
    output_formats: List[str] = Field(
        default=["docx", "pdf"], description="Document formats to generate"
    )

    @validator("output_formats")
    def validate_formats(cls, v: List[str]) -> List[str]:
        """Validate that output formats are supported."""
        valid_formats = {"docx", "pdf", "xlsx"}
        for fmt in v:
            if fmt not in valid_formats:
                raise ValueError(f"Unsupported format: {fmt}. Must be one of {valid_formats}")
        return v

    class Config:
        """Pydantic config."""

        extra = "forbid"


class FailureDetail(BaseModel):
    """Details about a failed row during generation."""

    row_index: int = Field(..., description="0-based row index")
    identifier: str = Field(..., description="Row identifier (e.g., name, email)")
    error: str = Field(..., description="Error message")


class GenerationResult(BaseModel):
    """Result of document generation operation."""

    total_rows: int = Field(..., description="Total rows processed")
    successful: int = Field(..., description="Number of successful generations")
    failed: int = Field(..., description="Number of failed generations")
    failed_details: List[FailureDetail] = Field(
        default_factory=list, description="Details about failed rows"
    )
    formats_generated: List[str] = Field(
        default=["docx"], description="Document formats generated"
    )
    output_path: str = Field(..., description="Path where documents were saved")

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.successful / self.total_rows) * 100

    def is_complete_success(self) -> bool:
        """Check if all rows were processed successfully."""
        return self.failed == 0 and self.total_rows > 0


class StatusUpdate(BaseModel):
    """Record of a status update for a data row."""

    row_index: int = Field(..., description="0-based row index")
    identifier: str = Field(..., description="Row identifier")
    old_status: str = Field(..., description="Previous status (e.g., 'todo')")
    new_status: str = Field(..., description="New status (e.g., 'done')")
    reason: str = Field(..., description="Reason for update")
    timestamp: Optional[str] = Field(None, description="ISO8601 timestamp of update")

    @validator("old_status", "new_status")
    def validate_status_values(cls, v: str) -> str:
        """Validate that status is one of known values."""
        valid_statuses = {"todo", "done", "skip"}
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v

    class Config:
        """Pydantic config."""

        extra = "forbid"
