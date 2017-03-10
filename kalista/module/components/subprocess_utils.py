#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import logging
import subprocess

import module.logger as logger
from module.sc_exception import SCException


def mvn_build(settings, pom):
    cmd = 'mvn -s %s -f %s clean install' % (settings, pom)
    logging.info('[ subprocess ] %s', cmd)
    result = subprocess.run(cmd, shell=True, stdout=logger.logfile_stream)
    if result.returncode != 0:
        raise SCException('command executing failed, check log.txt for detail')


def svn_export(remote_url, local_path):
    cmd = 'svn export --force ' + remote_url + ' ' + local_path
    logging.info('[ subprocess ] ' + cmd)
    result = subprocess.run(cmd, shell=True, stdout=logger.logfile_stream)
    if result.returncode != 0:
        raise SCException('command executing failed, check log.txt for detail')
