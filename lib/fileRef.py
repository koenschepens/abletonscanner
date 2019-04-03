from lib.htmlable import Htmlable
from lib.relativePath import RelativePath
from lib.searchHint import SearchHint
from lib.globals import *
import os
import fnmatch


class FileRef(Htmlable):
    HtmlMappingName = "FileRef"
    _realPath = None
    _initialPath = None
    SearchHint = None

    def __init__(self, fileRefElement, liveSet):
        self.Name = fileRefElement.find('Name').attrib["Value"]
        self.IsSample = is_sample_file(self.Name)
        self.HasRelativePath = fileRefElement.find('HasRelativePath').attrib["Value"].lower() == "true"
        self.RelativePathType = -1
        self.RelativePath = None
        self.is_valid = self.HasRelativePath
        self.file_ref_element = fileRefElement
        self._exists = False

        # Don't be concerned about finding a path if it doesn't cons a sample file
        if self.IsSample:
            if self.HasRelativePath:
                self.RelativePathType = int(fileRefElement.find("RelativePathType").attrib["Value"])
                self.RelativePath = RelativePath(fileRefElement.find("RelativePath"), liveSet.project, relative = self.HasRelativePath, relativePathType = self.RelativePathType)
                if self.RelativePath.FullDirPath:
                    self._initialPath = os.path.join(self.RelativePath.FullDirPath, self.Name)
                    self._realPath = self._initialPath

            self.SearchHint = SearchHint(fileRefElement.find("SearchHint"), liveSet.project)

        self.LiveSet = liveSet
        self.Status = ["InitialFileRef"]

    @property
    def exists(self):
        if self._exists:
            return True

        if self._realPath is not None and os.path.exists(self._realPath):
            self._exists = True

        if self.SearchHint is not None:
            if self.SearchHint.search(self.Name):
                self._real_path = self.SearchHint.path
                self.Status.append(self.SearchHint.Status)
                self._exists = True

        return self._exists

    @property
    def real_path(self):
        if self.exists:
            return self._realPath

        if self.RelativePath is not None and self.RelativePath.FullDirPath is not None:
            log(f"Getting real path for {self.Name}, RelativePath: {self.RelativePath.FullDirPath} IsSample: "
                   f"{self.IsSample} HasRelativePath: {self.HasRelativePath}", level=LOG_DEBUG)
            self._realPath = os.path.join(self.RelativePath.FullDirPath, self.Name)
            if(self._realPath and os.path.exists(self._realPath)):
                self.Status.append("Found in relative path")
                return self._realPath

        if self.SearchHint is not None and self.SearchHint.HasExtendedInfo:
            self._realPath = os.path.join(os.sep, self.SearchHint.PathHint, self.Name)
            if(self._realPath and os.path.exists(self._realPath)):
                self.Status.append(self.SearchHint.Status)
                return self._realPath

        if not self._realPath:
            self.Status.append("Error")
            self._realPath = self._initialPath

        return self._realPath

    """def updateBySearchingInFolders(self, folders):
        if(self.RelativePath is not None and self.SearchHint is not None):
            for folder in folders:
                for root, dirnames, filenames in os.walk(folder):
                    for filename in fnmatch.filter(filenames, self.Name):
                        foundFile = os.path.join(root, filename)
                        if(int(os.path.getsize(foundFile)) == int(self.SearchHint.FileSize)):
                            self.RealPath = foundFile
        self.Exists = self.RealPath and os.path.exists(self.RealPath)
        return self.Exists
    
    def updateFromBrowserContentPath(self, browserContentPath):
        if(browserContentPath is not None):
            browserContentPath = browserContentPath.replace('%20', ' ')
            if(browserContentPath.startswith("userfolder:")):
                splittedPath = browserContentPath.replace("userfolder:", "").split("#")
                afterHashPath = splittedPath[1].split(":")

                self.RealPath = os.path.join(splittedPath[0], *afterHashPath)
        self.Exists = os.path.exists(self.RealPath)
        return self.Exists"""

    @staticmethod
    def filterFileRef(elements):
        return filter(lambda e:
                      e.find("Name") is not None
                      and
                      "Value" in e.find("Name").attrib, elements)
