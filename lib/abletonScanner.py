from __future__ import print_function
from lib.htmlable import *
from lib.abletonProject import AbletonProject
from lib.abletonConfig import AbletonConfig
from lib.crossReference import CrossReference
import os
import collections
import fnmatch
import shutil
from lib.globals import *
import resource
import datetime

def using(point=""):
    usage=resource.getrusage(resource.RUSAGE_SELF)
    return '''%s: usertime=%s systime=%s mem=%s mb
           '''%(point,usage[0],usage[1],
                (usage[2]*resource.getpagesize())/1000000.0)

class AbletonScanner(Htmlable):
    HtmlMappingName = "AbletonScanner"
    is_html_root = True

    def __init__(self, root_folder, abletonPreferencesFolder, abletonFiles = None, sampleFolders = []):
        self.Started = None
        self.Ended = None
        self.ProjectFolders = []
        self.ProcessedSamples = []
        self.RecordedSamples = []
        self.orphans = []
        self.CrossReferences = []
        self.total_orphans_file_size = 0
        self._scanned_livesets_count = 0

        if abletonPreferencesFolder:
            self.Config = AbletonConfig(os.path.join(abletonPreferencesFolder, "Library.cfg"))

        self.ExtraSampleFolders = sampleFolders
        self.saveXml = False

        self.TotalSampleFileSize = 0
        self.TotalOrphanedSampleFileSize = 0

        if abletonFiles is None:
            self.FileFilters = ["*.als"]
        else:
            self.FileFilters = abletonFiles

        self.RootFolder = root_folder

        if root_folder:
            for root, dirnames, filenames in os.walk(root_folder):
                for fileFilter in self.FileFilters:
                    if any(fnmatch.filter(filenames, fileFilter)) and root not in self.ProjectFolders and not root.endswith("Backup"):
                        self.ProjectFolders.append(root)

        # sample files that were found during the sample folder scan
        self.found_sample_files = []

        # references to samples in the scanned projects
        self.sample_refs = []
        self.projects = []
        self.livesets = []
        self.TempFiles = []
        self._abort = False

    def scan(self, max_livesets=0, scan_samples=True, evaluate_orphans=True):
        self.Started = datetime.datetime.now()
        self.FullScan = False

        if max_livesets == 0:
            self._max_livesets = sys.maxsize
            self.FullScan = True
        else:
            self._max_livesets = max_livesets

        log("Scanning {0} projects...".format(self._max_livesets))

        i = 0
        p = 0

        while self._scanned_livesets_count <= self._max_livesets and len(self.ProjectFolders) > p:
            projectFolder = self.ProjectFolders[p]
            p += 1

            abletonProject = AbletonProject(projectFolder, self.Config, self.FileFilters,
                                            root_folder=self.RootFolder, logger=log, scanner=self)

            live_set_count = abletonProject.count_livesets(self._max_livesets)

            if projectFolder == self.RootFolder:
                self._max_livesets = live_set_count

            abletonProject.scan_livesets(self.on_liveset_scanned, self.on_sample_ref_added, self._scanned_livesets_count, self._max_livesets)

            if scan_samples:
                abletonProject.scan_sample_folders(self.on_sample_file_found)

            self.projects.append(abletonProject)

        for extraSampleFolder in self.ExtraSampleFolders:
            log(f"Adding sample folder {extraSampleFolder}")
            project = AbletonProject(extraSampleFolder, self.Config, self.FileFilters, name=f"Extra sample folder {i}: {extraSampleFolder}")
            self.projects.append(project)
            p += 1

        for extraSampleFolder in self.projects:
            extraSampleFolder.scan_sample_folders(self.on_sample_file_found)

            live_set_count = 1
            valid_live_sets = list(filter(lambda l: l.IsValidLiveSetFile, abletonProject.livesets))
            for live_set in valid_live_sets:
                sample_ref_count = 1

                for sample_ref in live_set.sample_refs:
                    self.sample_refs.append(sample_ref)

                    if not sample_ref.exists:
                        sample_ref.update(self.projects)

                    if sample_ref.exists:
                        self.found_sample_files.append(sample_ref.sample_file)

                    sample_ref_count += 1
                live_set_count += 1

        if evaluate_orphans:
            self._evaluate_orphans()

        self.SuccessfulProjectCount = len(self.projects)

        self.TotalSampleCount = len(self.found_sample_files)
        self.TotalSampleFileSize = sum(s.file_size for s in self.found_sample_files)
        self.Ended = datetime.datetime.now()

    @property
    def duration(self):
        if self.Started and self.Ended:
            return self.Ended - self.Started

        return datetime.timedelta(minutes=0)

    @property
    def missing_sample_files(self):
        return list(filter(lambda s: not s.exists, self.sample_refs))

    def on_liveset_scanned(self, liveset):
        self._scanned_livesets_count += 1
        self.livesets.append(liveset)

    def on_sample_ref_added(self, sample_ref):
        self.sample_refs.append(sample_ref)

        for sample_file_match in filter(lambda s: s == sample_ref.sample_file, self.found_sample_files or []):
            log(f"{sample_ref.name} ({sample_ref.liveset.Name}) refers to sample file {sample_file_match.file_name} "
                   f"({sample_file_match.project.Name})", level=LOG_INFO)
            sample_file_match.add_reference(sample_ref)

    def on_sample_file_found(self, sample_file):
        self.found_sample_files.append(sample_file)
        matches = 0

        # Update the sample references
        for sample_reference_match in filter(lambda s: s.sample_file == sample_file, self.sample_refs or []):
            matches += 1

            log(f"{sample_reference_match.name} ({sample_reference_match.liveset.Name}) refers to sample file "
                   f"{sample_file.file_name} ({sample_file.project.Name})", level=LOG_INFO)
            sample_file.add_reference(sample_reference_match)

            # All good! However, we'd like to check if it is hosted in another project (which can cause problems)
            if sample_reference_match.liveset.project != sample_file.project:
                self.CrossReferences.append(CrossReference(sample_reference_match.liveset, sample_file))

                # Also add it to the referring project and live set as reference
                if sample_file.project not in sample_reference_match.liveset.project.References:
                    sample_reference_match.liveset.project.References.append(sample_file.project)
                    sample_reference_match.liveset.References.append(sample_file.project)

                # Add it to the referred project as referenced by
                if sample_reference_match.liveset.project not in sample_file.project.ReferencedBy:
                    sample_file.project.ReferencedBy.append(sample_reference_match.liveset.project)

        if matches == 0:
            # No match was found, add as orphan
            self.orphans.append(sample_file)

    def _evaluate_orphans(self):
        self.total_orphans_file_size = sum(map(lambda o: o.file_size, self.orphans))

        log(f"Found {len(self.orphans)} orphans", level=LOG_DEBUG)

        if not self.FullScan:
            log("WARNING: You didn't scan all files!", level=LOG_WARNING)

        log("Done scanning orphans")

    def save(self, filename, logger=log):
        with open(filename, 'w+') as f:
            f.write("Found user folders:\n")
            for name in self.Config.UserFolderInfoList.keys():
                f.write("{0}: {1}\n".format(name, self.Config.UserFolderInfoList[name]))

            f.write("\n\n")
            f.write("Scan results:\n")

            f.write("Projects successfully scanned: {0}\n".format(self.SuccessfulProjectCount))
            f.write("Invalid projects: {0}\n".format(self.FailedProjectCount))
            f.write("Samples found: {0}\n".format(len(self.sample_refs)))

            if self.sample_refs:
                f.write("Total filesize of samples: {0}\n".format(toHumanReadableFileSize(sum(s.FileSize for s in self.sample_refs))))
                f.write("Total number of orphaned samples: {0}\n".format(len(self.orphans)))
                f.write("Total filesize of orphaned samples: {0}\n".format(toHumanReadableFileSize(sum(s.FileSize for s in self.orphans))))

            for project in self.projects:
                f.write("\n{0}".format('='*80))
                f.write("\n[Project {0}]".format(project.Name))
                f.write("\n{0}\n".format('-'*80))
                prefix = "\n"
                if(project.IsValidProjectFile):
                    f.write(prefix + "Project dir: {0}".format(project.ProjectDir))
                    f.write(prefix + "Ableton version: {0}\n".format(project.Version))
                    f.write(prefix + "Number of references in project: {0}".format(len(project.file_refs)))
                    f.write("\n")
                    f.write(prefix + "[Samples]")
                    f.write(prefix + "Total sample files found: {0}".format(len(project.sample_files)))

                    sampleTypeCounts = collections.Counter(map(lambda x: x.SampleType, project.sample_files)).most_common()
                    for sampleType in sampleTypeCounts:
                        f.write(prefix + "{0}: {1}".format(sampleType[0], sampleType[1]))

                    f.write(prefix + "\n[Missing files]")
                    f.write(prefix + "The following files have references in your project but could not be located.")
                    
                    missingFiles = list(filter(lambda f: not f.Exists, project.file_refs))
                    f.write(prefix + "Number of missing files: {0}".format(len(missingFiles)))
                    for missingFile in missingFiles:
                        f.write(prefix + "{0}".format(missingFile.RealPath))

                else:
                    f.write(prefix + "Could not open this file because it is corrupted.")
            
            f.write("\n{0}".format('='*80))
            f.write("\n\n{0}".format('='*80))
            f.write("\n[Orphaned samples]\n")
            f.write("The following sample files are in your project's sample folders but are not used in this or any other project:\n")
            for orphanedSample in self.orphans:
                f.write("{0}/{1}/Samples/{2} ({3})\n".format(orphanedSample.Name, orphanedSample.SampleType, orphanedSample.FileName, toHumanReadableFileSize(orphanedSample.FileSize)))

            f.write("\n\n[Cross references]\n")
            f.write("The following sample files are in a project's sample folder but are referred to by other projects:\n")
            for crossRef in self.CrossReferences:
                f.write("\n" + crossRef.UsedSample)
            f.write("\n\n{0}".format('-'*80))

            f.write("\n\n* = Only references to samples not from Ableton Libraries are included\n")
            f.write("** = Even after attempts to locate the files\n")
            f.write("*** = Sample files in project dir\n")

    def moveOrphanes(self, target, logger=log):
        for orphan in self.orphans:
            targetDir = os.path.join(target, orphan.Project.Name, "Samples", orphan.SampleType)

            if not os.path.exists(targetDir):
                logger("Creating dir " + targetDir)
                os.makedirs(targetDir)

            targetFile = os.path.join(targetDir, orphan.FileName)
            logger("Moving {0} to {1}".format(orphan.Path, targetFile))
            shutil.move(orphan.Path, targetFile)