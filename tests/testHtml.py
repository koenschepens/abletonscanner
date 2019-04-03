import datetime
import os
import unittest

from lib.abletonLiveSet import AbletonLiveSet
from lib.abletonProject import AbletonProject
from lib.abletonScanner import AbletonScanner, Htmlable
from lib.htmlable import HtmlFormatter


class MockAbletonProject(AbletonProject):
	def __init__(self):
		super().__init__(projectFolder="/Test", abletonConfig=None, file_filters=["*.als"])
		self.scanned_livesets = [AbletonLiveSet(file_name="Dummy", project=self)]

class MockAbletonScanner(AbletonScanner):
	def __init__(self):
		super().__init__(abletonPreferencesFolder=None, root_folder=None)
		self.scanned_projects = [MockAbletonProject()]
		self.Started = datetime.datetime.now()
		self.Ended = self.Started + datetime.timedelta(hours=1)

		self.TotalSampleCount = len(self.found_sample_files)
		self.TotalSampleFileSize = 4440
		self.total_orphans_file_size = 388

class TestHtmlFiles(unittest.TestCase):
	def test_scan_ableton_html(self):
		scanner = MockAbletonScanner()
		scanner.HtmlMappingName = "AbletonScanner"

		dir = os.path.dirname(os.path.realpath(__file__))

		formatter = HtmlFormatter(os.path.join(dir, "..", "lib"), ".")

		result = formatter.format(scanner, html=formatter.get_file("index 2.html"), checkFilekeys=True)

		assert result.__contains__("388.0 bytes")
		assert result.__contains__("4.3 KB")

if __name__ == '__main__':
	unittest.main()
