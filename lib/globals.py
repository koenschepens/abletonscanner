import zlib
import sys

PATH_TYPE_MISSING = 0
PATH_TYPE_EXTERNAL = 1
PATH_TYPE_LIBRARY = 2
PATH_TYPE_CURRENT_PROJECT = 3

BYTES = 1
KB = 1024
MB = 1024*1024
GB = 1024*1024*1024

LOG_DEBUG = 0
LOG_INFO = 1
LOG_WARNING = 2
LOG_ERROR = 3

LOG_LEVEL = LOG_DEBUG

import lib.globals

def is_sample_file(filename, extensions=['.wav', '.aif', '.aiff', '.aif']):
    return any(filename.endswith(e) for e in extensions)

def getCrc(path, maxCrcSize):
    data = open(path, 'r').read(maxCrcSize)
    cksum = zlib.crc32(data)

    return cksum

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log(log, end = None, level = LOG_INFO):
    if level >= LOG_LEVEL:
        if level >= LOG_ERROR:
            print(f"{bcolors.FAIL}{log}{bcolors.ENDC}")
        elif level >= LOG_WARNING:
            print(f"{bcolors.WARNING}{log}{bcolors.ENDC}")
        else:
            print(log, end=end)

def toHumanReadableFileSize(size, unit=BYTES):
    size = size / unit
    if size == 0:
        return "0 KB"
    if size >= GB:
        return "{0:.1f} GB".format(size/GB)
    if size >= MB:
        return "{0:.1f} MB".format(size/MB)
    if size >= KB:
        return "{0:.1f} KB".format(size/KB)
    if size >= BYTES:
        return "{0:.1f} bytes".format(size/BYTES)
    return "{:,}".format(size)

def toHumanReadablePathType(value):
    if(value == lib.globals.PATH_TYPE_CURRENT_PROJECT):
        return "current project"
    elif(value == lib.globals.PATH_TYPE_EXTERNAL):
        return "external"
    elif(value == lib.globals.PATH_TYPE_LIBRARY):
        return "library"
    elif(value == lib.globals.PATH_TYPE_MISSING):
        return "missing"