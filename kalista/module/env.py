#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
Environment variables during script executing
"""

import os
import sys

import module.const as const

runtime = {
    'fpath_project': None,                  # full path where main script(kalista.py) located
    'fpath_conf': None,                     # full path where configuration file located
    'fpath_module': None,                   # full path where module located
    'fpath_module_build_checker': None,     # full path where build checker located
    'fpath_module_scan_comparer': None      # full path where scan comparer located
}

workspace = {
    'fpath_workspace': None,                # full path where workspace located
    'fpath_temp': None,                     # full path where temporary directory located
    'fpath_artifact': None,                 # full path where artifact directory located
    'fpath_artifact_assemble': None,        # full path where artifact assemble located
    'fpath_artifact_source': None,          # full path where artifact source located
    'fpath_base': None                      # full path where base directory located
}

def init_env():
    runtime['fpath_project'] = sys.path[0]
    runtime['fpath_conf'] = os.path.join(runtime['fpath_project'], const.PRJ_DIR_CONF)
    runtime['fpath_module'] = os.path.join(runtime['fpath_project'], const.PRJ_DIR_MODULE)
    runtime['fpath_module_build_checker'] = os.path.join(runtime['fpath_module'], const.PRJ_DIR_MODULE_BC)
    runtime['fpath_module_scan_comparer'] = os.path.join(runtime['fpath_module'], const.PRJ_DIR_MODULE_SC)

def init_workspace(workspace_path):
    workspace['fpath_workspace'] = workspace_path
    workspace['fpath_conf'] = os.path.join(workspace['fpath_workspace'], const.WORKSPACE_DIR_CONF)
    workspace['fpath_temp'] = os.path.join(workspace['fpath_workspace'], const.WORKSPACE_DIR_TEMP)
    workspace['fpath_artifact'] = os.path.join(workspace['fpath_workspace'], const.WORKSPACE_DIR_ARTIFACT)
    workspace['fpath_artifact_assemble'] = os.path.join(workspace['fpath_artifact'], const.WORKSPACE_DIR_ARTIFACT_ASSEMBLE)
    workspace['fpath_artifact_source'] = os.path.join(workspace['fpath_artifact'], const.WORKSPACE_DIR_ARTIFACT_SOURCE)
    workspace['fpath_base'] = os.path.join(workspace['fpath_workspace'], const.WORKSPACE_DIR_BASE)
    workspace['fpath_output'] = os.path.join(workspace['fpath_workspace'], const.WORKSPACE_DIR_OUTPUT)
