from __future__ import print_function

from tkinter import filedialog
from tkinter import *
from tkinter import messagebox

import webbrowser
from lib.abletonScanner import *
from os.path import expanduser


def findPreferencesFolder():
    folder = os.path.join(expanduser("~"), "Library", "Preferences", "Ableton")

    if not os.path.exists(folder):
        folder = expanduser("~")

    while True:
        folder = askForFolder(folder, "Your Ableton preferences folder. Where is your Library.cfg located?")
        if os.path.exists(os.path.join(folder, "Library.cfg")):
            return folder

        retry = messagebox.askretrycancel(message="Can't find Library.cfg. Mine was at ~/Library/Preferences/Ableton/Live 9.2. Try again?")

        if not retry:
            quit()

def askForFolder(root, text, quit_on_cancel = False):
    while True:
        scanFolder = filedialog.askdirectory(title=text, initialdir=root)

        if not scanFolder:
            if quit_on_cancel:
                quit()
            else:
                return None
        else:
            if os.path.exists(scanFolder):
                break
            else:
                print("That path doesn't exist. Try again.")

    return scanFolder

def main():
    #mainUser()
    mainDev()

def mainDev():
    preferencesFolder = "/Users/Koen Schepens/Library/Preferences/Ableton/Live 10.0.1"
    abletonProjectFolder = "/Users/Koen Schepens/Dropbox/Producing/Projects/Ableton/Years Project"
    #scanner = AbletonScanner(abletonProjectFolder, preferencesFolder, sampleFolders=["/Users/Koen Schepens/Dropbox/Producing/Samples", "/Users/Koen Schepens/Dropbox/Producing/Recordings_local"])
    scanner = AbletonScanner(abletonProjectFolder, preferencesFolder, sampleFolders=["/Users/Koen Schepens/Dropbox/Producing/Recordings_local"])
    #scanner = AbletonScanner(abletonProjectFolder, preferencesFolder, abletonFiles = ["Liveset 2015 - Oktober.als", "Chordinaal v3 beter.als"])
    #scanner = AbletonScanner(abletonProjectFolder, preferencesFolder, abletonFiles = ["Source.als"])
    #scanner = AbletonScanner(os.path.join(abletonProjectFolder, "AbletonTest"), preferencesFolder, sampleFolders=["/Users/macbook/Dropbox/Producing/Recordings"])
    scanner.scan(evaluate_orphans=True)
    saveDir = '/Users/Koen Schepens/Dropbox/Producing/Projects/AbletonTest/Results'
    scanner.saveHtml(saveDir)
    webbrowser.open("file://" + os.path.join(saveDir, "index.html"))
    #moveOrphans(scanner)

def mainUser():
    print("Preference folder")
    preferencesFolder = findPreferencesFolder()

    print("Folder to scan")
    abletonFolderToScan = askForFolder(expanduser("~"), "Please enter the folder to scan (containing your Ableton projects): ", quit_on_cancel = True)

    extraFolders = []

    print("Extra folder")
    extraFolder = askForFolder(expanduser("~"), "Add extra folder containing samples to scan (or cancel to just scan project subfolders)")

    while(extraFolder is not None):
        extraFolders.append(extraFolder)
        print("Extra folder")
        extraFolder = askForFolder(expanduser("~"), "Add another extra folder containing samples to scan (or cancel if ready)")

    scanner = AbletonScanner(abletonFolderToScan, preferencesFolder, sampleFolders=extraFolders)

    scan = messagebox.askyesno(message = "Scan all projects under {0}?".format(abletonFolderToScan))

    if(scan):
        scanner.Started = datetime.datetime.now()
        scanner.scan(logger = log)
    else:
        print("Ok suit yourself then.")
        quit()

    scanner._evaluate_orphans(logger = log)

    saveFolder = filedialog.askdirectory(title="Enter folder name to save", initialdir=expanduser("~"))

    if(saveFolder):
        scanner.saveHtml(saveFolder)

        webbrowser.open("file://" + os.path.join(saveFolder, "index.html"))

        moveOrphans(scanner)
    else:
        messagebox.Message("Cancelled")

def moveOrphans(scanner):
    if(any(scanner.orphans)):
        _moveOrphans = messagebox.askokcancel(message="Do you want to move all orphan samples to another folder (preferably another disk) to see if you can save {0}?".format(scanner.TotalOrphanedSampleFileSize))

        if(_moveOrphans):
            _moveOrphans = messagebox.askyesno(message="Warning! This is at your own risk! You hereby declare that you know what you're doing and understand that no-one but you can be held responsible for your own actions. Proceed?")

        if(_moveOrphans):
            target = filedialog.askdirectory(title="Where do you want to store the orphaned files?", initialdir=expanduser("~"))
            if(target):
                scanner.moveOrphanes(target)

if __name__ == "__main__":
    main()

#"/Users/macbook/Library/Preferences/Ableton/Live 9.2"

