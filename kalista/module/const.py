#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
Constant variables definition
"""

# processes
PROCESS_INIT = 'init'   # process for initializing workspace
PROCESS_SC = 'sc'       # process for scanning & comparing

# project directory relative path
PRJ_DIR_CONF = 'conf'                  # directory where configuration file located
PRJ_DIR_MODULE = 'module'              # directory where custom & 3rd modules located
PRJ_DIR_MODULE_BC = 'build_checker'    # directory where build checkers located
PRJ_DIR_MODULE_SC = 'scan_comparer'    # directory where scan comparers located

# workspace directory relative path
WORKSPACE_DIR_OUTPUT = 'output'                # directory where program output located
WORKSPACE_DIR_TEMP = 'temp'                    # directory where the temp files generated during executing located
WORKSPACE_DIR_ARTIFACT = 'artifact'            # directory where artifacts located
WORKSPACE_DIR_ARTIFACT_ASSEMBLE = 'assemble'   # directory where artifact assemble located
WORKSPACE_DIR_ARTIFACT_SOURCE = 'source'       # directory where artifact source located
WORKSPACE_DIR_BASE = 'base'                    # directory where last version source code located
WORKSPACE_DIR_CONF = 'conf'                    # directory where configuration files plugins needed located

# helper information
HELPER_INFO = '''usage:
 > python3 kalista.py [-p <conf_file_name>] init
initialize the workspace, create directories, purging outputs
if conf_file_name was set to 'community', then ./conf/community.json file will be used for executing.
if conf_file_name was omit, the default ./conf/config.json will be used
example:
 > python3 kalista.py -p community init
 > python3 kalista.py init

 > python3 kalista.py [-p <conf_file_name>]
run scanning & comparing
if conf_file_name was set to 'community', then ./conf/community.json file will be used for executing.
if conf_file_name was omit, the default ./conf/config.json will be used
example:
 > python3 kalista.py -p community
 > python3 kalista.py
'''

# default configuration file name
DFT_CONF_FILE_NAME = 'config'
