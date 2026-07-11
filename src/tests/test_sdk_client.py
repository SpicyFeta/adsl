# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Tests for Palantir SDK client skeleton (ADR-007 preparation)."""

import pytest

from adsl.ontology.sdk_client import (
    OntologySdkConfig,
    OntologySdkClient,
    OntologySdkNotActiveError,
)


def test_sdk_client_not_live_ready_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ADSL_ONTOLOGY_SYNC_ENABLED", raising=False)
    client = OntologySdkClient.from_env()
    assert client.is_live_ready() is False


def test_validate_config_reports_missing_credentials(monkeypatch) -> None:
    monkeypatch.setenv("ADSL_ONTOLOGY_SYNC_ENABLED", "true")
    monkeypatch.delenv("FOUNDRY_URL", raising=False)
    monkeypatch.delenv("FOUNDRY_TOKEN", raising=False)
    monkeypatch.delenv("ONTOLOGY_RID", raising=False)

    summary = OntologySdkClient.from_env().validate_config()
    assert summary["sync_enabled"] is True
    assert summary["live_ready"] is False
    assert summary["mode"] == "offline_placeholder"
    assert "FOUNDRY_URL" in summary["missing_credentials"]


def test_write_object_returns_placeholder_rid(monkeypatch) -> None:
    monkeypatch.delenv("ADSL_ONTOLOGY_SYNC_ENABLED", raising=False)
    client = OntologySdkClient.from_env()
    rid = client.write_object(
        {"object_type": "ADSL_AuditTrace", "primary_key": "trace-1"}
    )
    assert rid == "ri.ontology.main.object.ADSL_AuditTrace.trace-1"


def test_read_raises_when_sync_enabled_but_foundry_not_active(monkeypatch) -> None:
    monkeypatch.setenv("ADSL_ONTOLOGY_SYNC_ENABLED", "true")
    monkeypatch.setenv("FOUNDRY_URL", "https://example.com")
    monkeypatch.setenv("FOUNDRY_TOKEN", "token")
    monkeypatch.setenv("ONTOLOGY_RID", "ri.ontology.main.ontology.test")
    monkeypatch.delenv("ADSL_FOUNDRY_ENABLED", raising=False)

    client = OntologySdkClient.from_env()
    with pytest.raises(OntologySdkNotActiveError):
        client.read_object("ADSL_AuditTrace", "trace-1")


def test_live_ready_when_foundry_gate_passes(monkeypatch) -> None:
    monkeypatch.setenv("ADSL_ONTOLOGY_SYNC_ENABLED", "true")
    monkeypatch.setenv("ADSL_FOUNDRY_ENABLED", "true")
    monkeypatch.setenv("FOUNDRY_URL", "https://example.com")
    monkeypatch.setenv("FOUNDRY_TOKEN", "token")
    monkeypatch.setenv("ONTOLOGY_RID", "ri.ontology.main.ontology.test")

    client = OntologySdkClient.from_env()
    assert client.is_live_ready() is True
    summary = client.validate_config()
    assert summary["mode"] == "live_http"


def test_config_from_env_parses_sync_flag(monkeypatch) -> None:
    monkeypatch.setenv("ADSL_ONTOLOGY_SYNC_ENABLED", "yes")
    config = OntologySdkConfig.from_env()
    assert config.sync_enabled is True