"""Structured application-service errors for Concord teacher workflows."""

from __future__ import annotations


class ConcordWorkflowError(Exception):
    """Base exception for workflow-layer failures."""


class ConcordWorkflowValidationError(ConcordWorkflowError):
    """Raised when a workflow request is invalid before persistence."""


class ConcordWorkflowNotFoundError(ConcordWorkflowError):
    """Raised when an exact workflow target cannot be found."""


class ConcordWorkflowConflictError(ConcordWorkflowError):
    """Raised when a workflow operation would collide with existing identity."""
