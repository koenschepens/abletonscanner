import os
import shutil
import string
import re
from _string import formatter_field_name_split
from lib.globals import *

filekeys = {}

class HtmlFormatter(string.Formatter):
    def __init__(self, sourceDir, targetDir):
        global filekeys
        self._last_field = None
        self.SourceDir = sourceDir
        self.TargetDir = targetDir
        self.AllowedFunctions = {
            "len" : len
        }

        self.Specs = {
            "menuitem" : self.get_file("project_item.html"),
            "menu" : self.get_file("menu.html"),
            "fileRef" : self.get_file("fileref.html"),
            "filesize": toHumanReadableFileSize,
            "li": "<li>{0}</li>",
            "relativepathtype": toHumanReadablePathType
            }

        for htmlfile in os.listdir(os.path.join(self.SourceDir, "html")):
            if(htmlfile.endswith(".html")):
                self.Specs[htmlfile.replace(".html", "")] = self.get_file(htmlfile)

    def get_spec(self, spec):
        if spec in self.Specs:
            return self.Specs[spec]

        return self.get_file(f"{spec}.html")

    def vformat(self, format_string, args, obj, mapping):
        used_args = set()
        result = self._vformat(format_string, args, obj, used_args, 2, mapping = mapping)
        self.check_unused_args(used_args, args, obj.__dict__)
        return result

    def _vformat(self, format_string, args, obj, used_args, recursion_depth, mapping):
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')
        result = []

        for literal_text, field_name, format_spec, conversion in \
                self.parse(format_string):
            functionName = None
            # output the literal text
            if literal_text:
                result.append(literal_text)

            # if there's a field, output it
            if field_name is not None:
                # this is some markup, find the object and do
                #  the formatting

                # given the field_name, find the object it references
                #  and the argument it came from
                m = re.match("(\\w*)\\(([^\\)]*?)\\)", field_name)
                if(m):
                    functionName = m.group(1)
                    if(functionName not in self.AllowedFunctions):
                        return "[function {0} is not allowed]".format(functionName)

                    field_name = m.group(2)

                _obj, arg_used = self.get_field(field_name, args, obj, format_spec, mapping = mapping)
                used_args.add(arg_used)

                # do any conversion on the resulting object
                _obj = self.convert_field(_obj, conversion)

                if(functionName is not None):
                    _obj = self.AllowedFunctions[functionName](_obj)

                # expand the format spec, if needed
                format_spec = self._vformat(format_spec, args, obj, used_args, recursion_depth-1, mapping = mapping)

                # format the object and append to the result
                result.append(str(self.format_field(_obj if _obj is not None else 0, format_spec)))

        return ''.join(result)

    # given a field_name, find the object it references.
    #  field_name:   the field being looked up, e.g. "0.name"
    #                 or "lookup[3]"
    #  used_args:    a set of which args have been used
    #  args, kwargs: as passed in to vformat
    def get_field(self, field_name, args, obj, spec, mapping):
        try:
            self._last_field = field_name

            first, rest = formatter_field_name_split(field_name)

            _obj = self.get_value(first, obj, spec, mapping = mapping)

            # loop through the rest of the field_name, doing
            #  getattr or getitem as needed
            for is_attr, i in rest:
                if is_attr:
                    _obj = getattr(_obj, i)
                else:
                    _obj = _obj[i]

            return _obj, first
        except Exception as e:
            log(f"Error getting field {field_name}", level=LOG_ERROR)
            raise e

    def format(self, obj, htmlSourceFileName = None, html = None, mapping = None, checkFilekeys = True):
        global filekeys
        if(htmlSourceFileName is None and html is None):
            if(mapping is not None):
                htmlSourceFileName = mapping["source"]
            else:
                html = ""

        if(htmlSourceFileName is not None):
            with open(os.path.join(self.SourceDir, "html", htmlSourceFileName) , 'r') as htmlFile:
                html = htmlFile.read()

        if(hasattr(obj, "is_html_root") and getattr(obj, "is_html_root") and checkFilekeys):
            filekeys["header"] = self.format(obj, html = self.get_file("header.html"), checkFilekeys = False)
            filekeys["footer"] = self.format(obj, html = self.get_file("footer.html"), checkFilekeys = False)

        for filekey in filekeys:
            # Yes, I'm lazy
            if not html.__contains__("{{" + filekey + "}}"):
                html = html.replace("{" + filekey + "}", filekeys[filekey])

        if(isinstance(obj, Htmlable)):
            if(mapping is not None):
                obj.FullDirPath = os.path.join(self.TargetDir, mapping["source"])
            else:
                obj.FullDirPath = self.TargetDir
            return self.vformat(format_string = html, args = None, obj = obj, mapping = mapping)
        else:
            if(isinstance(obj, list)):
                output = ""
                for o in obj:
                    res = self.format(obj = o, html = html)
                    if(res is not None):
                        output += res
                return output
            else:
                return obj

        #return self.get_value(self, key, obj)

    def get_file(self, htmlSourceFileName):
         if htmlSourceFileName is not None:
             path = "{0}/html/{1}".format(self.SourceDir, htmlSourceFileName)
             if os.path.exists(path):
                with open(path, 'r') as htmlFile:
                    return htmlFile.read()
         return None

    def format_field(self, value, spec, mapping=None):
        formatterSpec = self.get_spec(spec)
        if formatterSpec is not None:
            if(hasattr(formatterSpec, '__call__')):
                return formatterSpec(value)
            else:
                formatter = HtmlFormatter(self.SourceDir, self.TargetDir)
                return formatter.format(value, html=formatterSpec, mapping = mapping)

        return string.Formatter.format_field(self, value, spec)

    def get_value(self, key, obj, spec = None, mapping = None):
        if(obj is not None and isinstance(obj, Htmlable)):
            if(type(key) is int):
                return "use named parameters for object " + str(type(obj))
            elif(type(key) is int):
                return "use named parameters for object " + str(type(obj))
            elif(key == "FullPath"):
                if(mapping is None):
                    if(obj.defaultMapping() is not None):
                        return os.path.join(self.TargetDir, obj.getTarget(obj.defaultMapping()))
                    else:
                        return os.path.join(self.TargetDir)
                else:
                    return os.path.join(self.TargetDir, obj.getTarget(mapping))
            elif(key == "FullDir"):
                if(mapping is None):
                    return os.path.join(self.TargetDir)
                else:
                    return os.path.join(self.TargetDir, os.path.dirname(obj.getTarget(mapping)))
            elif(key == "filesize"):
                return toHumanReadableFileSize(obj)
            else:
                field = getattr(obj, key)
                return field

            if(isinstance(field, Htmlable)):
                formatter = HtmlFormatter(self.SourceDir, self.TargetDir)
                return formatter.format(field, mapping = None)
            elif(isinstance(field, list)):
                output = ""
                for o in field:
                    if(spec in self.Specs):
                        res = self.format(obj = o, html = self.Specs[spec])
                    else:
                        res = self.format(obj = o, mapping = mapping)
                    if(res is not None):
                        output += res
                return output

        elif(isinstance(obj, list)):
            output = ""
            for o in obj:
                res = self.format(obj = o, mapping = None)
                if(res is not None):
                    output += res
            return output

        return getattr(obj, key)

class Htmlable():
    Dir = os.path.dirname(os.path.abspath(__file__))
    HtmlMappingName = None
    HtmlMapping = {
        "index 2.html":
           {
               "class": "AbletonScanner",
                "type" : "page",
                "pagetype" : "index",
                "source": "index 2.html",
                "target": "index.html",
                "pages" :
                   {
                       "Projects overview" :
                            {
                                "type" : "page",
                                "class" : "AbletonScanner",
                                "source" : "projects.html",
                                "target" : "projects.html"
                            },
                       "Ableton projects" :
                            {
                                "type" : "page",
                                "class" : "AbletonProject",
                                "field" : "projects",
                                "source" : "abletonProject.html",
                                "target" : os.path.join("projects","{Name}.html")
                            },
                       "Cross references" :
                            {
                                "class" : "AbletonScanner",
                                "type" : "page",
                                "target" : "crossreferences.html",
                                "source" : "crossreferences.html",
                            },
                       "Orphaned samples" :
                            {
                                "class" : "AbletonScanner",
                                "type" : "page",
                                "target" : "orphanedsamples.html",
                                "source" : "orphanedsamples.html",
                            },
                       "All livesets" :
                            {
                                "class" : "AbletonScanner",
                                "type" : "page",
                                "target" : "livesets.html",
                                "source" : "livesets.html",
                            }
                    }
           }
    }
    def __init__(self):
        self.HtmlSourceFileNames = type(self).__name__ + '.html'

    def getMappings(self):
        return self.HtmlMapping[self.HtmlMappingName]

    def getMapping(self, mapping):
        if(self.HtmlMappingName is None):
            raise Exception("mapping for " + str(self.__class__) + " not available")
        for key, page in self.walkThroughPages(self.HtmlMapping, pageType="*"):
            if(page["class"] == self.HtmlMappingName):
                return page
        return self.HtmlMapping[self.HtmlMappingName][mapping]

    def getPageMappings(self):
        mappings = self.getMappings()
        return filter(lambda m: mappings[m]["type"] == "page", mappings)

    def walkThroughPages(self, item = None, pageType = "page"):
        def filterMapping(pageType, mapping): filter(lambda m: mapping[m]["type"] == pageType or pageType == "*", mapping)

        for key, value in item.items():
            if("type" in value and value["type"] == "page"):
                self._current_page = key
                yield key, value
            if("pages" in value):
                    for subkey, subvalue in self.walkThroughPages(value["pages"]):
                        self._current_page = subkey
                        yield subkey, subvalue

    def defaultMapping(self):
        for key, page in self.walkThroughPages(self.HtmlMapping, pageType="*"):
            if(page["class"] == self.HtmlMappingName):
                return page
        return None

    def getTarget(self, mapping):
        return mapping["target"].format(**self.__dict__)

    def parseHtml(self, targetDir, mapping):
        formatter = HtmlFormatter(self.Dir, targetDir)
        return formatter.format(self, mapping=mapping)

    def saveHtml(self, targetdir, isRoot = True):
        for key, page in self.walkThroughPages(self.HtmlMapping, pageType="*"):
            if(page["class"] == self.HtmlMappingName and "field" not in page):
                targetdir = self.createHtmlFile(targetdir, page, isRoot=isRoot)
                isRoot = False
            elif("field" in page and hasattr(self, page["field"])):
                field = getattr(self, page["field"])
                if(isinstance(field, list)):
                    for item in field:
                        item.createHtmlFile(targetdir, page)
                else:
                    field.createHtmlFile(targetdir, page)

    def createHtmlFile(self, targetdir, page, isRoot = False):
        targetPath = self.getTarget(page)
        htmlTargetPath = os.path.join(targetdir, targetPath)
        htmlTargetDir = os.path.dirname(htmlTargetPath)

        if(isRoot):
            htmlTargetDir = self.createRoot(htmlTargetDir)
            htmlTargetPath = os.path.join(htmlTargetDir, targetPath)
        else:
            if(not os.path.exists(htmlTargetDir)):
                os.makedirs(htmlTargetDir)
        result = self.parseHtml(htmlTargetDir, page)

        if(htmlTargetPath is None):
            print("No target name for: " + str(self.__class__))
        else:
            try:
                with open(htmlTargetPath, 'w+') as htmlResultFile:
                    htmlResultFile.write(result)
                    print("Saved to file " + htmlTargetPath)
            except:
                print("Could not save to file " + htmlTargetPath)

        return htmlTargetDir

    def createRoot(self, targetdir, createNewDirIfExists = False):
        # Create new dir if necessary

        if(createNewDirIfExists):
            while(os.path.exists(targetdir)):
                m = re.match("([a-zA-Z \/\\_\-\.$\(\)]*)([0-9]*)", targetdir)
                if(m and m.group(2).isdigit()):
                    targetdir = "{0}{1}".format(m.group(1), int(m.group(2)) + 1)
                else:
                    targetdir = "{0}1".format(targetdir)
        elif(os.path.exists(targetdir)):
            shutil.rmtree(targetdir)

        #copy layout
        dirsToCopy = ["layout", "images", "jwplayer", "script"]

        for dirToCopy in dirsToCopy:
            shutil.copytree(os.path.join(self.Dir, "html", dirToCopy), os.path.join(targetdir, dirToCopy))

        return targetdir