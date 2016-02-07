""" Writer class to be used with Jinja2 tamplates """
from __future__ import print_function
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound, TemplateSyntaxError, TemplateError
from biomajmanager.utils import Utils
import os
import sys


class Writer(object):

    """ Writer class for BioMAJ manager to create what's desired as output """

    def __init__(self, template_dir=None, output_format='txt', config=None, output=None):
        '''
        Create Writer object

        :param template_dir: Root directory where to find templates
        :type template_dir: String
        :param output_format: Template format. Default 'txt'
        :type output_format: String
        :param config: Global configuration file from BiomajConfig
        :type config: configparser
        :param output: Output file. Default STDOUT
        :type output: String
        :return:
        '''

        self.env = None
        self.format = None
        self.output = None
        self.template_dir = None

        if template_dir is not None:
            if not os.path.isdir(template_dir):
                Utils.error("Template dir %s is not a directory" % template_dir)
            self.template_dir = template_dir
        if config is not None:
            if not config.has_section('MANAGER'):
                Utils.error("Configuration has no 'MANAGER' section.")
            elif not config.has_option('MANAGER', 'template.dir'):
                Utils.error("Configuration has no 'template.dir' key.")
            else:
                self.template_dir = config.get('MANAGER', 'template.dir')
        if self.template_dir is None:
            Utils.error("'template.dir' not set")

        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.format = output_format
        self.output = output

    def write(self, file=None, data=None):
        '''
        Print template 'data' to stdout using template file 'file'
        data args can be left None, this way method can be used to render file
        from scratch

        :param file: Template file name
        :type file: String
        :param data: Template data
        :type data: Dictionary
        :return: True, throws on error
        '''
        if file is None:
            Utils.error("A template name is required")
        try:
            template = self.env.get_template(file)
        except TemplateNotFound as err:
            Utils.error("Template %s not found!" % err)
        except TemplateSyntaxError as err:
            Utils.error("Syntax error found in template '%s', line %d: %s" % (err.name, err.lineno, err.message))

        if self.output is None:
            self.output = sys.stdout
        else:
            try:
                with open(self.output, "w") as ofile:
                    print(template.render(data), file=ofile)
            except (IOError, TemplateError) as err:
                Utils.error("Rendering template '%s' encountered error: %s" % (file, str(err)))
        return True
