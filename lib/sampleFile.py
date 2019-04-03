import os
from lib.htmlable import Htmlable
from lib.globals import *
import crc16

class SampleFile(Htmlable):
    def __init__(self, full_path, project):
        self.HtmlMappingName = "SampleFile"
        self._exists = False
        self.path = full_path
        (folder, file_name) = os.path.split(full_path)
        self.folder = folder
        self.file_name = file_name
        self.project = project
        self.references = []

        if project.SampleFolder is not None:
            try:
                self.SampleType = self.folder[self.folder.index(project.SampleFolder)+len(project.SampleFolder):]
            except Exception as e:
                self.SampleType = "External"
        else:
            self.SampleType = "External"

    def __eq__(self, other):
        return self is None if other is None else self.path == other.path

    def add_reference(self, sample_ref):
        if not any(filter(lambda r: r == sample_ref, self.references)):
            self.references.append(sample_ref)

    @property
    def file_size(self):
        if self.exists():
            return os.path.getsize(self.path)

        return 0

    def exists(self):
        if self._exists:
            return True

        if os.path.exists(self.path):
            self._exists = True

        return self._exists

    def getCrc(self, maxCrcSize):
        try:
            data = open(self.path, 'rb').read()
            cksum = crc16.crc16xmodem(data)
            return cksum
        except UnicodeDecodeError as e:
            print(e.reason)
            print(self.path)
            return -1
