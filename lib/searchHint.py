import os
from lib.globals import *
from lib.relativePath import RelativePath

class SearchHint():
    def __init__(self, searchHintElement, project):
        self.HasExtendedInfo = searchHintElement.find("HasExtendedInfo").attrib["Value"] == "true"
        self.project = project
        self.searchHintElement = searchHintElement
        self.RelativePath = RelativePath(self.searchHintElement, project)
        self.FileSize = int(searchHintElement.find("FileSize").attrib["Value"])
        self.Crc = int(searchHintElement.find("Crc").attrib["Value"])
        self.MaxCrcSize = int(searchHintElement.find("MaxCrcSize").attrib["Value"])
        self.Status = ["Hint: Initial"]

        dirs = list(map(lambda e: e.attrib["Dir"], searchHintElement.iter("RelativePathElement")))
        if self.HasExtendedInfo:
            self.update_dir(dirs)

    def update_dir(self, dirs, reason=None):
        self.PathHint = dirs
        if reason:
            self.Status.append(reason)

    @property
    def path(self):
        return os.path.join(*self.PathHint)

    def search(self, sample_file_name, projects=None):
        if not self.HasExtendedInfo:
            return []

        #splitted_path = os.path.split(self.PathHint.split("/Samples/")[0])
        #project_name = splitted_path[-1:][0]

        search_methods = [self._update_home_folder]
        '''self._search_in_projects_sample_folders,
        self._scan_samples_folder,
        self._scan_libraries]'''

        for search_method in search_methods:
            for suggestion in search_method(sample_file_name, projects):
                if os.path.exists(suggestion):
                    self.update_dir(suggestion.split(os.sep), "Home folder moved")
                    return True

    def _update_home_folder(self, sample_file_name, projects):
        if "Users" in self.PathHint:
            from pathlib import Path
            home = str(Path.home())
            i = self.PathHint.index("Users")
            # Try current user
            yield os.path.join(home, *self.PathHint[i + 2:])

        '''# First look in all projects with the suspected name
        result = self.search_in(filter(lambda p: p.Name == project_name, projects), sample_file_name)

        if result:
            self.Status.append("Hint: Project moved")
        else:
            # Then look the other projects
            result = self.search_in(filter(lambda p: project_name != p.Name, projects), sample_file_name)
            if result:
                self.Status.append("Hint: Project renamed")

        if result:
            self.PathHint = result
        else:
            self.Status.append("Hint: Nothing found")'''

    def search_in(self, projects, sampleFileName):
        for matchedProject in projects:
            for matchedSample in filter(lambda s: s.file_name == sampleFileName, matchedProject.sample_files):
                if (self.FileSize == matchedSample.FileSize):
                    if(self.Crc == matchedSample.getCrc()):
                        self.Status.append("Found file")
                        return matchedSample.Folder
                    else:
                        self.Status.append("Crc doesn't match")
                else:
                    self.Status.append("Hint: Project renamed")

        return []