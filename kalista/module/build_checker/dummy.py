#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import logging

from module.abstract_build_checker import AbstractBuildChecker

class BuildChecker(AbstractBuildChecker):
    """
    Dummy checker for testing environment
    """

    def _self_desc(self):
        name = 'dummy'
        desc = 'just for testing executing environment'
        return name, desc

    def _init(self):
        pass

    def _do_check(self):
        logging.info('dummy checking')

    def _destroy(self):
       pass
