#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import getopt
import importlib
import json
import logging
import os
import shutil
from string import Template
import sys

import module.const as constant
import module.env as env
import module.logger as logger
from module.components.subprocess_utils import svn_export
from module.components.common_utils import print_approach_title
from module.sc_exception import SCException


def main():

    # initialize the script running environment
    env.init_env()

    # reading configure according to command arguments
    try:
        arguments = chk_recv_cmd_args()
        config = load_cnf(arguments)
    except SCException as e:
        print(e)
        print_helper()
        sys.exit(0)

    env.init_workspace(config['workspace']['path'])

    if arguments['process'] == constant.PROCESS_INIT:
        init_workspace(config)
    elif arguments['process'] == constant.PROCESS_SC:
        init_workspace(config)
        init_logging(config)
        fetch_base_source_code(config)
        call_build_checker(config)
        call_scan_comparer(config)


def fetch_base_source_code(config):
    if not config['vcs']['ignore']:
        print_approach_title('Fetching source code (last version) from vcs')
        for working_copy in config['vcs']['working_copies']:
            svn_export(working_copy['remote'], os.path.join(env.workspace['fpath_workspace'], working_copy['local']))


def call_build_checker(config):
    for bc_entry in config['build_checkers']:
        processor_module_literal = bc_entry['processor']
        is_ignore = bc_entry['ignore']
        if not is_ignore:
            processor_module = importlib.import_module('module.build_checker.%s' % processor_module_literal)
            processor = processor_module.BuildChecker(config['workspace']['path'], bc_entry['configuration'])
            processor.check()


def call_scan_comparer(config):
    stat_arry = []
    for bc_entry in config['scan_comparers']:
        processor_module_literal = bc_entry['processor']
        is_ignore = bc_entry['ignore']
        if not is_ignore:
            processor_module = importlib.import_module(
                'module.scan_comparer.%s.%s' % (processor_module_literal, processor_module_literal)
            )
            processor = processor_module.ScanComparer(
                processor_module_literal,
                bc_entry['configuration']
            )
            processor.scan()
            stat_arry.append({
                "title": processor.self_desc()['cname'],
                "stat": processor.stat(),
                "href": './%s/index.html' % processor_module_literal
            })

    template_stream = open(os.path.join(env.runtime['fpath_module_scan_comparer'], 'index-template.html'), 'r')
    template = template_stream.read()
    template_stream.close()
    stat_content_arry = []
    for stat_entry in stat_arry:
        stat_content_arry.append(
            '<div class="plugin"><div class="plugin-name"><a href="%s">%s</a></div><div>%s</div></div>'
                % (stat_entry['href'], stat_entry['title'], stat_entry['stat'])
        )
    index_stream = open(os.path.join(env.workspace['fpath_output'], 'index.html'), 'w')
    index_stream.write(Template(template).substitute(stat=''.join(stat_content_arry)))
    index_stream.close()


def init_logging(config):
    logfile_path = os.path.join(env.workspace['fpath_output'], 'log.txt')
    logger.logfile_stream = open(logfile_path, 'w')
    handlers = [logging.StreamHandler(stream=logger.logfile_stream), logging.StreamHandler()]
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        handlers=handlers)


def print_helper():
    """
    command helper information

    :return:
        {string} helper information
    """

    print(constant.HELPER_INFO)


def chk_recv_cmd_args():
    """
    check the arguments of script command and parse it into a dict.

    :return: a dict include parsed command arguments, e.g.:
        {
            'process': 'sc',
            'options': {
                '-p': 'community'
            }
        }

    :raises:
        when command arguments is not legal
    """

    arguments = {
        'process': constant.PROCESS_SC,
        'options': {
            '-p': constant.DFT_CONF_FILE_NAME
        }
    }

    if len(sys.argv) == 1:
        arguments['process'] = constant.PROCESS_SC
    elif len(sys.argv) > 1:
        try:
            optlist, args = getopt.getopt(sys.argv[1:], 'p:')
        except getopt.GetoptError as e:
            raise SCException(e.msg)

        if len(optlist) > 0:
            for key, val in optlist:
                arguments['options'][key] = val
        if len(args) == 1:
            if args[0] == constant.PROCESS_INIT:
                arguments['process'] = constant.PROCESS_INIT
            else:
                raise SCException('unrecognized argument "%s"' % args[0])
        elif len(args) > 1:
            raise SCException('illegal command arguments')
    else:
        raise SCException('illegal command arguments')

    return arguments


def load_cnf(arguments):
    """
    Read configuration file according on command argument

    :param arguments: command arguments
    :return: a dict contains configuration information
    :raises: if configuration file not exist
    """

    conf_file_path = os.path.join(sys.path[0], constant.PRJ_DIR_CONF, arguments['options']['-p'] + '.json')
    if not os.path.exists(conf_file_path):
        raise SCException('configuration file not exist')
    config = json.load(open(conf_file_path))
    return config


def init_workspace(config):
    """
    Initialize workspace:
        - create directories if not exist
        - purge output directories

    :param config: configuration dictionary
    :return: None
    """

    print('Initialize workspace [ %s ]' % env.workspace['fpath_workspace'])

    # create workspace if not exist
    if not os.path.exists(env.workspace['fpath_workspace']):
        os.makedirs(env.workspace['fpath_workspace'])

    # create artifact, conf, base directories
    if not os.path.exists(env.workspace['fpath_artifact']):
        os.makedirs(env.workspace['fpath_artifact'])
    if not os.path.exists(env.workspace['fpath_conf']):
        os.makedirs(env.workspace['fpath_conf'])
    if not os.path.exists(env.workspace['fpath_base']):
        os.makedirs(env.workspace['fpath_base'])
    if not os.path.exists(env.workspace['fpath_artifact_assemble']):
        os.makedirs(env.workspace['fpath_artifact_assemble'])
    if not os.path.exists(env.workspace['fpath_artifact_source']):
        os.makedirs(env.workspace['fpath_artifact_source'])

    # create or purge output, temp directory
    if os.path.exists(env.workspace['fpath_output']):
        shutil.rmtree(env.workspace['fpath_output'])
    os.makedirs(env.workspace['fpath_output'])
    if os.path.exists(env.workspace['fpath_temp']):
        shutil.rmtree(env.workspace['fpath_temp'])
    os.makedirs(env.workspace['fpath_temp'])

    print('Done.')

main()
