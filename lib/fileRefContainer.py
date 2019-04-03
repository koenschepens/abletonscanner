class FileRefContainer():
    FileRef = None

    def __init__(self, element, liveSet):
        pass
        '''fileRefElement = element.find('FileRef')

        if(fileRefElement is not None
           and fileRefElement.find("Name") is not None
           and "Value" in fileRefElement.find("Name").attrib):
            fileRef = FileRef(fileRefElement, liveSet)

            if(is_sample_file(filename = fileRef.Name)):
                self.FileRef = fileRef'''

    @staticmethod
    def create(element, liveSet):
        if(element.tag == "OriginalFileRef"):
            return OriginalFileRef(element, liveSet)

class OriginalFileRef(FileRefContainer):
    pass