from __future__ import print_function

import time
import datetime

from biomajmanager.plugins import BMPlugin


class Gensoft(BMPlugin):

    """
    Gensoft (Institut Pasteur, Paris) is an architecture providing bioinformtics
    tools for the campus.
    """

    def get_name(self):
        return 'GenSoft'

    def get_whatprovide(self):
        return self.config.get('gensoft', 'gensoft.bin.whatprovide')

    
