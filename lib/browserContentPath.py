from lib import htmlable
import os
from lib.fileRef import FileRef
from lib.globals import is_sample_file, log


class BrowserContentPath(htmlable.Htmlable):
    #<BrowserContentPath Value="userfolder:/Users/macbook/Dropbox/Producing/Projects/#AbletonTest:Source%20Project:Samples:Recorded:0004%20Synth-1.aif" />

    def __init__(self, element, liveSet):
        self.element = element
        value = element.attrib["Value"]

        if value:
            pathElements = value.split("#")

            self.LiveSet = liveSet

            self.FolderType = pathElements[0].split(":")[0]
            self.Folder = pathElements[0].split(":")[1]
            self.RelativePath = pathElements[1].replace(":", os.sep)
            self.RelativeDir = os.path.dirname(self.RelativePath)

            self.RealPath = self.getBrowserContentPath()

            if not self.Exists:
                log(f"File not found: {os.path.join(self.RelativeDir, self.RelativePath)}")

            self.file_refs = []

    @property
    def exists(self):
        return self.RealPath and os.path.exists(self.RealPath)

    def getBrowserContentPath(self):
        if self.FolderType == "userfolder":
            userFolder = None
            if(os.path.exists(self.Folder.rstrip('/'))):
                # It's mostly an absolute path
                userFolder = self.Folder
            else:
                # Get it from the config
                userFolderName = os.path.split(self.Folder.rstrip('/'))[-1:][0]
                if(userFolderName in self.LiveSet.Project.Config.UserFolderInfoList):
                    userFolder = self.LiveSet.Project.Config.UserFolderInfoList[userFolderName]

            if(userFolder):
                return os.path.join(self.Folder, self.RelativePath)


