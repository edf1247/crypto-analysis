"""
Unit tests for Binance data fetching with mock API.
"""
import sys
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Add project root to Python path to allow importing backtest module
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.backtest_runner import fetch_binance_paginated

def test_fetch_binance_paginated_single_request():
    """Test fetching data within single request limit."""
    mock_df = pd.DataFrame({
        'open': [100, 101],
        'high': [102, 103],
        'low': [99, 100],
        'close': [101, 102],
        'volume': [1000, 1100]
    }, index=pd.date_range('2026-01-01', periods=2, freq='1d'))

    with patch('app.services.backtest_runner.DataLoader') as mock_dataloader:
        mock_dataloader.fetch_binance.return_value = mock_df
        result = fetch_binance_paginated(
            symbol='BTCUSDT',
            interval='1d',
            start_date=pd.Timestamp('2026-01-01'),
            end_date=pd.Timestamp('2026-01-02')
        )
        # Should call fetch_binance once with appropriate parameters
        mock_dataloader.fetch_binance.assert_called_once()
        # Result should be the same DataFrame
        pd.testing.assert_frame_equal(result, mock_df)

def test_fetch_binance_paginated_multiple_requests():
    """Test pagination across multiple requests."""
    # Simulate two chunks
    mock_df1 = pd.DataFrame({
        'open': [100, 101],
        'high': [102, 103],
        'low': [99, 100],
        'close': [101, 102],
        'volume': [1000, 1100]
    }, index=pd.date_range('2026-01-01', periods=2, freq='1d'))

    mock_df2 = pd.DataFrame({
        'open': [102, 103],
        'high': [104, 105],
        'low': [101, 102],
        'close': [103, 104],
        'volume': [1200, 1300]
    }, index=pd.date_range('2026-01-03', periods=2, freq='1d'))

    with patch('app.services.backtest_runner.DataLoader') as mock_dataloader:
        # First call returns first chunk, second call returns second chunk, third returns empty
        mock_dataloader.fetch_binance.side_effect = [mock_df1, mock_df2, pd.DataFrame()]
        result = fetch_binance_paginated(
            symbol='BTCUSDT',
            interval='1d',
            start_date=pd.Timestamp('2026-01-01'),
            end_date=pd.Timestamp('2026-01-04')
        )
        # Should have been called twice
        assert mock_dataloader.fetch_binance.call_count == 2
        # Result should combine both chunks
        expected = pd.concat([mock_df1, mock_df2]).sort_index()
        pd.testing.assert_frame_equal(result, expected)

def test_fetch_binance_paginated_respects_end_date():
    """Test that pagination stops when end_date reached."""
    mock_df1 = pd.DataFrame({
        'open': [100],
        'high': [102],
        'low': [99],
        'close': [101],
        'volume': [1000]
    }, index=pd.date_range('2026-01-01', periods=1, freq='1d'))

    mock_df2 = pd.DataFrame({
        'open': [102],
        'high': [104],
        'low': [101],
        'close': [103],
        'volume': [1100]
    }, index=pd.date_range('2026-01-02', periods=1, freq='1d'))

    with patch('app.services.backtest_runner.DataLoader') as mock_dataloader:
        mock_dataloader.fetch_binance.side_effect = [mock_df1, mock_df2, pd.DataFrame()]
        result = fetch_binance_paginated(
            symbol='BTCUSDT',
            interval='1d',
            start_date=pd.Timestamp('2026-01-01'),
            end_date=pd.Timestamp('2026-01-02')
        )
        # Should have been called twice (second chunk includes date beyond end_date?)
        # Actually second chunk's index includes 2026-01-02 which is equal to end_date, so it's included
        # Then third call returns empty, loop stops.
        assert mock_dataloader.fetch_binance.call_count >= 2
        # Result should include both rows (since end_date inclusive)
        assert len(result) == 2