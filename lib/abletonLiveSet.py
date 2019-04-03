from __future__ import print_function

import datetime
import gzip
import io
import struct
import xml.etree.ElementTree as ET
from lib.htmlable import *
from lib.sampleRef import SampleRef
from lib.globals import *

class AbletonLiveSet(Htmlable):
	def __init__(self, file_name, project, logger=log):
		self.Name = os.path.split(file_name)[1]
		self.Id = self.Name.replace(" ", "_").replace(".", "_")
		self.sample_refs = []
		self.missing_sample_files = []
		self.References = []
		self.project = project
		self.file_name = file_name
		self.IsValidLiveSetFile = True

	def scan(self, on_sample_ref_added, deepScan=True, ):
		try:
			log("Unpacking {0}".format(self.file_name))
			start_zip = datetime.datetime.now()
			with gzip.open(self.file_name, 'rb') as f:
				end_zip = datetime.datetime.now()
				f.seek(0, io.SEEK_END)
				size = f.tell()
				f.seek(0)
				log(f"Unpacked {toHumanReadableFileSize(size)} in {(end_zip - start_zip).total_seconds():.4f} "
				       f"seconds")

				log("Parsing...", end=" ")
				start_parse = datetime.datetime.now()

				# turn it into an iterator
				tree = ET.iterparse(f)

				totalElements = 0

				for event, elem in tree:
					if event == "end":
						totalElements += 1

						if elem.tag == "Ableton":
							if "Creator" in elem.attrib:
								self.Version = elem.attrib["Creator"]
							elif "MinorVersion" in elem.attrib:
								self.Version = "Ableton " + elem.attrib["MinorVersion"].replace("_", ".")
							else:
								self.Version = "Unknown version"

						if elem.tag == "SampleRef":
							sample_ref = SampleRef(elem, self)
							sample_ref.update([self.project])
							self.sample_refs.append(sample_ref)
							on_sample_ref_added(sample_ref)

				if self.project.scanner.saveXml:
					tree.write(self.file_name + ".xml")

				end_parse = datetime.datetime.now()
				log(f"Parsed in {(end_parse - start_parse).total_seconds():.3f} seconds", level=LOG_INFO)
				log(f"{len(self.sample_refs)} sample references found", level=LOG_INFO)
				log(f"sample_ref updates took {sum(map(lambda s: s.update_duration, self.sample_refs)):.3f} seconds", level=LOG_INFO)

			self.missing_sample_files = list(filter(lambda f: not f.exists, self.sample_refs))

			if any(self.missing_sample_files):
				log(f"{len(self.missing_sample_files)} files could not be found", level=LOG_WARNING)

			log("Created with {0}.".format(self.Version))

			log(f"Total for this project: {(datetime.datetime.now()-start_zip).total_seconds():.3f} seconds")
			log("=" * 80)

		except IOError:
			self.IsValidLiveSetFile = False
			self.Version = "Invalid live set file"
		except Exception as e:
			log(f"Error in live set {self.Name}: {e}", level=LOG_ERROR)

	def addFileRef(self, fileRef):
		log(f"Adding fileRef. Name: {fileRef.Name} RealPath: {fileRef.RealPath} IsSample: {fileRef.IsSample} "
			   f"HasRelativePath: {fileRef.HasRelativePath}", level=LOG_DEBUG)

		if is_sample_file(filename=fileRef.Name) and not any(filter(lambda f: f.RealPath == fileRef.RealPath, self.file_refs)):
			self.file_refs.append(fileRef)

	def getAllFileRefs(self):
		all = []
		for sourceContext in self.SourceContexts:
			all.extend(sourceContext.getAllFileRefs())
		return all
