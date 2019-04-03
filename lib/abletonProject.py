from __future__ import print_function

import datetime
import fnmatch

from lib.htmlable import *
from lib.sampleFile import SampleFile
from lib.globals import *
from lib.abletonLiveSet import AbletonLiveSet

class AbletonProject(Htmlable):
    HtmlMappingName = "AbletonProject"

    def __init__(self, projectFolder, abletonConfig, file_filters, logger=log, root_folder=None, name = None, scanner = None):
        self.Config = abletonConfig
        self.ProjectDir = projectFolder
        self.scanner = scanner
        self.file_filters = file_filters
        self.RootFolder = root_folder

        if name is None:
            # This is a normal project.
            self.Name = os.path.split(projectFolder.rstrip(os.sep))[1]
            self.SampleFolderPath = os.path.join(projectFolder, "Samples")
            self.SampleFolder = "/Samples/"
        else:
            self.Name = name
            self.SampleFolderPath = projectFolder
            self.SampleFolder = None

        self.Id = self.Name.replace(" ", "_").replace(".", "_")

        # Scan results
        # A list of the livesets within this project
        self.livesets = []
        # The amount of livesets that were scanned within this project
        self.livesets_count = 0
        # A list of livesets that one of the livesets in this project refers to
        self.References = []
        # A list of livesets that refer to this project
        self.ReferencedBy = []

        # The sample files that were found in the sample subfolder of this project
        self.sample_files = []
        # The amount of sample files in the Samples folder of this project
        self.sample_file_count = 0
        # The sum of all sample sizes
        self.sample_files_size_total = 0

        # Keeps track of the scanned livesets
        self._liveset_counter = 0

    @property
    def missing_sample_files(self):
        """Samples that occur in one of this projects live sets but couldn't be found on disk"""
        return list(map(lambda l: l.missing_sample_files, self.livesets))

    @property
    def unused_sample_files(self):
        return list(filter(lambda l: len(l.references) <= 0, self.sample_files))

    def count_livesets(self, limit=0):
        if self.livesets_count > 0:
            return self.livesets_count

        total_files = 0

        # Scan all live set files (*.als)
        log("Counting project files...")
        for root, dir_names, file_names in os.walk(self.RootFolder, topdown=True):
            if not root.endswith("Backup"):
                for fileFilter in self.file_filters:
                    file_names = list(fnmatch.filter(file_names, fileFilter))
                    total_files += len(file_names)

        self.livesets_count = total_files if limit == 0 or limit > total_files else limit

        return self.livesets_count

    def scan_livesets(self, on_liveset_scanned, on_sample_ref_added, i, max):
        self._liveset_counter = i
        assert self.livesets_count >= 0, "You have to run count_livesets before calling this function"

        log("Scanning livesets...")

        for fileFilter in self.file_filters:
            file_names = list(fnmatch.filter(os.listdir(self.ProjectDir), fileFilter))
            for filename in file_names:
                self._liveset_counter += 1
                log(f"[ {self.Name} ({self._liveset_counter}/{max}) ] ", level=LOG_INFO)
                liveset = AbletonLiveSet(file_name=os.path.join(self.ProjectDir, filename), project=self, logger=log)
                liveset.scan(on_sample_ref_added)

                on_liveset_scanned(liveset)

                self.livesets.append(liveset)

                if self._liveset_counter >= max:
                    # Max reached
                    return

    def scan_sample_folders(self, on_sample_file_found):
        # Scan all samples in this project
        start_samples_scan = datetime.datetime.now()

        log(f"[ {self.Name} ] Sample dir is {self.SampleFolderPath}", level=LOG_DEBUG)

        for sample_root, dirnames, sample_file_names in os.walk(self.SampleFolderPath, topdown=True):
            log(f"[ {self.Name} ] Scanning dir {sample_root}", level=LOG_DEBUG)

            for sample_file_name in filter(is_sample_file, sample_file_names):
                if not any(filter(lambda s: s.file_name == sample_file_name, self.sample_files)):
                    sample_file = SampleFile(os.path.join(sample_root, sample_file_name), self)
                    self.sample_files.append(sample_file)
                    self.sample_files_size_total += sample_file.file_size
                    on_sample_file_found(sample_file)

        self.sample_file_count = len(self.sample_files)

        log(f"Scanned {self.sample_file_count} files in "
               f"{(datetime.datetime.now() - start_samples_scan).total_seconds():.3f} seconds.")
