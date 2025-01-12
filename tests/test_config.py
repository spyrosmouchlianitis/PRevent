from src.config import rewrite_setting
from unittest.mock import patch, mock_open


def test_rewrite_setting():
    setting_name = 'DEBUG'
    new_value = 'True'

    with patch('app.config.get_app_root', return_value='/mock/path'), \
         patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open()) as mock_file:

        rewrite_setting(setting_name, new_value)

        # Corrected assertion to match actual write call with leading newline
        mock_file().write.assert_any_call(f"\n{setting_name} = {new_value}\n")

