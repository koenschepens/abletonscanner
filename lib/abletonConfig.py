import xml.etree.ElementTree as ET
from lib.htmlable import Htmlable

class AbletonConfig(Htmlable):
    def __init__(self, configFile):
        tree = ET.parse(configFile)

        root = tree.getroot()

        print (str(root.attrib))
        _contentLibrary = root.find("ContentLibrary")

        self.UserFolderInfoList = {}

        for element in _contentLibrary.find("UserFolderInfoList").findall("UserFolderInfo"):
            if "DisplayName" in element.attrib:
                self.UserFolderInfoList[element.attrib["DisplayName"]] = element.attrib["Path"]

    class UserFolderInfo():
        def __init__(self, element):
            self.Path = element.attrib["Path"]
            self.DisplayName = element.attrib["DisplayName"]
