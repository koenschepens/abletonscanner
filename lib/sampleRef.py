import datetime

from lib.browserContentPath import BrowserContentPath
from lib.fileRef import FileRef
from lib.globals import *
from lib.htmlable import Htmlable
from lib.sampleFile import SampleFile
from lib.sourceContext import SourceContext


class SampleRef(Htmlable):
	def __init__(self, elem, liveset):
		self.fileRefs = []
		self.browserContentPaths = []
		self.sourceContexts = []
		self.status = []
		self.liveset = liveset
		self.update_duration = 0
		self.name = None

		self._real_path = None
		self._exists = None

		for child in elem:
			if child.tag == "FileRef":
				file_ref = FileRef(child, self.liveset)
				if file_ref.is_valid:
					self.fileRefs.append(file_ref)
					self.name = file_ref.Name

			if child.tag == "SourceContext":
				source_context = SourceContext(child, self.liveset)
				if source_context.is_valid:
					self.sourceContexts.append(source_context)
					if self.name is None:
						self.name = str(source_context.BrowserContentPath[-1:])

			if child.tag == "BrowserContentPath":
				browser_content_path = BrowserContentPath(child, self.liveset)
				if browser_content_path.is_valid():
					self.browserContentPaths.append(browser_content_path)
					if self.name is None:
						self.name = str(browser_content_path.RelativePath)

	# update the file ref for a sample by scanning other projects

	def update(self, projects = None):
		update_start_time = datetime.datetime.now()
		self._exists = False

		for fileRef in self.fileRefs:
			if fileRef.exists:
				self._exists = True
				self._real_path = fileRef.real_path
				return

		for browserContentPath in self.browserContentPaths:
			if browserContentPath.exists:
				self._exists = True
				self._real_path = browserContentPath.real_path
				return

		for sourceContext in self.sourceContexts:
			if sourceContext.exists:
				self._exists = True
				self._real_path = sourceContext.real_path
				return

		self.update_duration = (datetime.datetime.now() - update_start_time).total_seconds()
		return self._exists

	def __eq__(self, other):
		return self._real_path == other._real_path

	@property
	def real_path(self):
		if self.exists:
			return self._real_path

	@property
	def exists(self):
		if self._exists is None:
			self.update()

		return self._exists

	@property
	def sample_file(self):
		if self.exists:
			try:
				return SampleFile(self._real_path, self.liveset.project)
			except Exception as e:
				log(f"Error getting sample file for real_path: {self._real_path}. self.liveset = {self.liveset.Name}", level=LOG_ERROR)

		return None
