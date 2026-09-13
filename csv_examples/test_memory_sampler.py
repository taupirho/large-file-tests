import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import psutil

from benchmark_common import MemorySampler


class MemorySamplerTests(unittest.TestCase):
    def test_records_peak_even_if_final_reading_is_lower(self):
        process = Mock()
        process.memory_info.side_effect = [
            SimpleNamespace(rss=value) for value in (100, 500, 200, 150)
        ]
        stop = Mock()
        stop.wait.side_effect = [False, False, True]
        with patch("benchmark_common.psutil.Process", return_value=process):
            with patch("benchmark_common.Event", return_value=stop):
                with MemorySampler() as memory:
                    pass
        self.assertEqual(memory.baseline, 100)
        self.assertEqual(memory.peak, 500)
        self.assertFalse(memory.thread.is_alive())
        stop.set.assert_called_once()

    def test_processing_error_stops_sampler(self):
        with self.assertRaisesRegex(ValueError, "processing failed"):
            with MemorySampler() as memory:
                raise ValueError("processing failed")
        self.assertFalse(memory.thread.is_alive())

    def test_sampling_error_is_reported(self):
        process = Mock()
        process.memory_info.side_effect = [
            SimpleNamespace(rss=100), psutil.AccessDenied()
        ]
        stop = Mock()
        stop.wait.return_value = False
        with patch("benchmark_common.psutil.Process", return_value=process):
            with patch("benchmark_common.Event", return_value=stop):
                with self.assertRaisesRegex(RuntimeError, "RAM sampling failed"):
                    with MemorySampler() as memory:
                        pass
        self.assertFalse(memory.thread.is_alive())


if __name__ == "__main__":
    unittest.main()
