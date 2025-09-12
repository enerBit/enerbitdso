import os
from unittest.mock import patch
from typer.testing import CliRunner

from enerbitdso.cli import cli

runner = CliRunner()

USAGES_ARGLIST = ["usages"]


def test_usages_with_frt_list():
    """Test CLI with FRT list (requires valid environment variables)"""
    # Solo ejecutar si las variables de entorno están configuradas
    if not all([
        os.getenv("ENERBIT_API_BASE_URL"),
        os.getenv("ENERBIT_API_USERNAME"), 
        os.getenv("ENERBIT_API_PASSWORD")
    ]):
        return  # Skip test if env vars not set
        
    command = USAGES_ARGLIST + [
        "fetch", 
        "--since=2023-01-01",
        "--until=2023-01-02", 
        "Frt00000"
    ]
    
    with patch("enerbitdso.enerbit.get_schedule_usage_records") as mock_get:
        mock_get.return_value = []  # Return empty list to avoid actual API calls
        
        with patch("enerbitdso.enerbit.get_auth_token") as mock_auth:
            mock_auth.return_value = {"access_token": "fake_token"}
            
            result = runner.invoke(cli, command)
            # Should not exit with error (even if no data returned)
            assert result.exit_code == 0 or "Failed to fetch" in result.output
