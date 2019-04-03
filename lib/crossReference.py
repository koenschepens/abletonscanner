from lib.htmlable import Htmlable

class CrossReference(Htmlable):
    HtmlMappingName = "CrossReference"
    ReferringLiveSet = None
    UsedSample = None

    def __init__(self, referringLiveSet, usedSample):
        self.ReferringLiveSet =  referringLiveSet
        self.UsedSample = usedSample