# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Integration tests for Cloud Database API endpoints.
Tests cover all acceptance scenarios from the spec using mocked database layer.
"""
import pytest
from httpx import AsyncClient


class TestListCloudFiles:
    """Tests for GET /api/cloud/load_files_cloud"""

    ENDPOINT = "/api/cloud/load_files_cloud"
    HEADERS = {"Authorization": "Bearer test-token"}

    async def test_returns_file_list(self, async_client: AsyncClient, mock_db_service):
        """Given authenticated user has saved files, returns a list of file names."""
        mock_db_service["fetchrow"].return_value = {
            "files": ["file1", "file2"]
        }

        response = await async_client.get(self.ENDPOINT, headers=self.HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert data["files"] == ["file1", "file2"]

    async def test_empty_list_when_no_files(self, async_client: AsyncClient, mock_db_service):
        """Given authenticated user has no saved files, returns an empty list."""
        mock_db_service["fetchrow"].return_value = {"files": []}

        response = await async_client.get(self.ENDPOINT, headers=self.HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["files"] == []

    async def test_unauthorized_returns_401(self, async_client: AsyncClient):
        """Given no auth token, returns 401."""
        response = await async_client.get(self.ENDPOINT)
        assert response.status_code == 401


class TestSaveCloudData:
    """Tests for POST /api/cloud/save_files_cloud"""

    ENDPOINT = "/api/cloud/save_files_cloud"
    HEADERS = {"Authorization": "Bearer test-token"}

    VALID_PAYLOAD = {
        "file_name": "test-reconciliation",
        "file_data": [
            {
                "transaction_details": "Vendor Payment",
                "transaction_date": "2026-07-10",
                "debit_credit_amount": 15000.00,
                "category": "Unpresented Checks",
            }
        ],
    }

    async def test_valid_save_returns_success(
        self, async_client: AsyncClient, mock_db_service
    ):
        """Given valid POST data and no existing record, stores it and returns success."""
        # Simulate no existing record (new insert)
        mock_db_service["fetchrow"].return_value = None

        response = await async_client.post(
            self.ENDPOINT, json=self.VALID_PAYLOAD, headers=self.HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_name"] == "test-reconciliation"
        # Two executes: INSERT + UPDATE users.files
        assert mock_db_service["execute"].call_count == 2

    async def test_upsert_overwrites_existing(
        self, async_client: AsyncClient, mock_db_service
    ):
        """Given existing file_name, overwrites record (upsert)."""
        # Simulate existing record
        mock_db_service["fetchrow"].return_value = {"id": 1}

        response = await async_client.post(
            self.ENDPOINT, json=self.VALID_PAYLOAD, headers=self.HEADERS
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        # One execute: UPDATE reconciliation_data only
        assert mock_db_service["execute"].call_count == 1

    async def test_empty_file_name_returns_422(self, async_client: AsyncClient):
        """Given empty file_name, returns validation error."""
        payload = {
            "file_name": "",
            "file_data": [{"transaction_details": "test", "transaction_date": "2026-01-01", "debit_credit_amount": 1.0, "category": "test"}],
        }
        response = await async_client.post(
            self.ENDPOINT, json=payload, headers=self.HEADERS
        )
        assert response.status_code == 422

    async def test_empty_file_data_returns_422(self, async_client: AsyncClient):
        """Given empty file_data array, returns validation error."""
        payload = {
            "file_name": "test",
            "file_data": [],  # Min length 1
        }
        response = await async_client.post(
            self.ENDPOINT, json=payload, headers=self.HEADERS
        )
        assert response.status_code == 422

    async def test_unauthorized_returns_401(self, async_client: AsyncClient):
        """Given no auth token, returns 401."""
        response = await async_client.post(
            self.ENDPOINT, json=self.VALID_PAYLOAD
        )
        assert response.status_code == 401

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
