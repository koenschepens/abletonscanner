from lib.browserContentPath import BrowserContentPath
from lib.fileRefContainer import FileRefContainer

class SourceContext():
    FileRefContainerTags = [
        "SampleRef",
        "OriginalFileRef"
    ]

    def __init__(self, element, liveSet):
        self.FileRefContainers = []
        self.BrowserContentPath = None

        self.is_valid = False

        '''for fileRefTag in self.FileRefContainerTags:
            for fileRefContainerElement in element.findall(fileRefTag):
                self.FileRefContainers.append(FileRefContainer.create(fileRefContainerElement, liveSet))'''

        '''browserContentPathElement  = element.find("BrowserContentPath")
        if(browserContentPathElement is not None):
            self.BrowserContentPath = BrowserContentPath(browserContentPathElement, liveSet)'''

    def getAllFileRefs(self):
        fileRefs = []
        for fileRefContainer in filter(lambda f: f.FileRef is not None, self.FileRefContainers):
            fileRefs.append(fileRefContainer.FileRef)
        return fileRefs

    @property
    def exists(self):
        # TODO
        return False
