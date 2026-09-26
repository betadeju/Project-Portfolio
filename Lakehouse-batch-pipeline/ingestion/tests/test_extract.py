"""Unit tests for the ingestion layer.

Run with: pytest ingestion/tests -v
External calls (NOAA API, S3) are mocked so these run offline and in CI
without real credentials.
"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import requests

from ingestion.config import Settings
from ingestion.extract import fetch_observations, run, write_raw_partition

TEST_SETTINGS = Settings(
    noaa_api_token="fake-token",
    noaa_base_url="https://example.test/api",
    station_ids=["USW00094728"],
    storage_endpoint="http://localhost:9000",
    storage_bucket="test-bucket",
    storage_access_key="test",
    storage_secret_key="test",
    max_retries=2,
)


def test_fetch_observations_success():
    with patch("ingestion.extract.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"value": 12.3}]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = fetch_observations(TEST_SETTINGS, "USW00094728", date(2024, 1, 1))

        assert result == {"results": [{"value": 12.3}]}
        mock_get.assert_called_once()


def test_fetch_observations_retries_then_raises():
    with patch("ingestion.extract.requests.get") as mock_get, patch("ingestion.extract.time.sleep"):
        mock_get.side_effect = requests.ConnectionError("boom")

        with pytest.raises(RuntimeError, match="Failed to fetch"):
            fetch_observations(TEST_SETTINGS, "USW00094728", date(2024, 1, 1))

        assert mock_get.call_count == TEST_SETTINGS.max_retries


def test_write_raw_partition_uses_partitioned_key():
    with patch("ingestion.extract.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client

        key = write_raw_partition(
            TEST_SETTINGS, "USW00094728", date(2024, 1, 1), {"results": []}
        )

        assert key == (
            "raw/station_id=USW00094728/ingestion_date=2024-01-01/observations.json"
        )
        mock_client.upload_fileobj.assert_called_once()


def test_run_covers_late_arrival_lookback_window():
    with patch("ingestion.extract.load_settings", return_value=TEST_SETTINGS), patch(
        "ingestion.extract.fetch_observations", return_value={"results": []}
    ) as mock_fetch, patch("ingestion.extract.write_raw_partition", return_value="key"):

        run(date(2024, 1, 10))

        # 1 station x (1 target day + 3 lookback days) = 4 calls
        assert mock_fetch.call_count == 4
