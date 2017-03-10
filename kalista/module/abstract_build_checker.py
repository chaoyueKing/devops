#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import logging

from module.components.common_utils import print_approach_title


class AbstractBuildChecker:

    def __init__(self, workspace_path, bc_config):
        self.workspace_path = workspace_path
        self.bc_config = bc_config
        self._init()

    def check(self):
        checker_name, checker_desc = self._self_desc()
        print_approach_title('- BUILD CHECKER ( %s ) # %s' % (checker_name, checker_desc))
        self._do_check()
        logging.info('Done.\n')
        self._destroy()

    def _self_desc(self):
        pass

    def _init(self):
        pass

    def _do_check(self):
        pass

    def _destroy(self):
        pass
