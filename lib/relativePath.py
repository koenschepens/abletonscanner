import os
import urllib
from lib.htmlable import Htmlable
from lib.globals import *

class RelativePath(Htmlable):
    def __init__(self, element, project, relative=True, relativePathType = PATH_TYPE_CURRENT_PROJECT):
        relativePathList = []
        self.project = project

        self.FullDirPath = None

        for relativePathElement in element.findall("RelativePathElement"):
            if relativePathElement.attrib["Dir"] == "":
                relativePathList.append("..")
            else:
                relativePathList.append(relativePathElement.attrib["Dir"])

        if(relative and relativePathList):
            actualPaths = {
                PATH_TYPE_CURRENT_PROJECT: lambda: os.path.join(project.ProjectDir, *relativePathList),
                PATH_TYPE_EXTERNAL: lambda: os.path.join(self.getExternalFolder(relativePathList, project.Config)),
                PATH_TYPE_LIBRARY: lambda: os.path.join(self.getLibraryFolder(relativePathList, project.Config))
            }

            if relativePathType in actualPaths:
                dir_path = actualPaths[relativePathType]()
            else:
                dir_path = actualPaths[PATH_TYPE_EXTERNAL]()

            self.FullDirPath = os.path.realpath(dir_path)

    def equals(self, pathString):
        path = urllib.url2pathname(pathString)
        return self.FullDirPath.endswith(path)

    def getLibraryFolder(self, folder_list, config):
        if folder_list[0] in config.UserFolderInfoList:
            return config.UserFolderInfoList[folder_list[0]]
        else:
            return config.UserFolderInfoList[list(config.UserFolderInfoList.keys())[0]]

    def getExternalFolder(self, folder_list, config):
        return os.path.join(self.project.ProjectDir, *folder_list)
