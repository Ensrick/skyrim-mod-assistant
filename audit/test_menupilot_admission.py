"""No-game admission must not leave a command for the next launch."""
import unittest
from unittest.mock import patch
import menupilot


class MenuPilotAdmissionTests(unittest.TestCase):
    def test_no_game_means_no_queue(self):
        with patch.object(menupilot, 'game_running', return_value=False), \
                patch.object(menupilot.os, 'makedirs') as mkdir, \
                patch('builtins.open') as opened:
            self.assertEqual(menupilot.send(['{"op":"ping"}'], 0), 2)
            mkdir.assert_not_called()
            opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
