"""
Tests for Audit Log Endpoints
"""

import pytest
from fastapi.testclient import TestClient

class TestAuditLogs:
    def test_get_audit_logs(self, test_client, auth_headers_admin):
        response = test_client.get("/api/v1/audit/logs", headers=auth_headers_admin)
        assert response.status_code == 200

    def test_filter_audit_logs_by_action(self, test_client, auth_headers_admin):
        response = test_client.get(
            "/api/v1/audit/logs?action=USER_CREATE",
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
