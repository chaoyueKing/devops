#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import filecmp
import logging
import os
import shutil
import subprocess
import zipfile

from module.abstract_build_checker import AbstractBuildChecker
import module.env as env
import module.logger as logger
from module.sc_exception import SCException

# directory where source code for building which copied from artifact located
TEMP_PATH_BUILD = 'cb/build'
# directory where assemble artifact which need to checksum copy to
TEMP_PATH_CHK_ASSEMBLE = 'cb/chk/assemble'


class BuildChecker(AbstractBuildChecker):
    """
    Checker for java web app (war).
    This checker will assume that your execute environment has program below installed :
        Apache Maven 3+
    """

    def _self_desc(self):
        name = 'java web app'
        desc = 'check whether war is exactly build from specified source'
        return name, desc

    def _init(self):
        self.temp_path = env.workspace['fpath_temp']

    def _do_check(self):
        # copy source code to temporary build directory
        src_path = os.path.join(env.workspace['fpath_artifact'], 'source')
        build_path = os.path.join(self.temp_path, TEMP_PATH_BUILD)
        shutil.copytree(src_path, build_path)

        # maven builds
        for pom_entry in self.bc_config['builds']:
            self.__mvn_build(
                os.path.join(env.workspace['fpath_conf'], self.bc_config['mvn_setting']),
                os.path.join(env.workspace['fpath_temp'], TEMP_PATH_BUILD,  pom_entry['pom'])
            )

        # loop compare assemble files
        temp_assemble_path = os.path.join(self.temp_path, TEMP_PATH_CHK_ASSEMBLE)
        os.makedirs(temp_assemble_path)
        for chk_entry in self.bc_config['checks']:
            # copy assemble file to TEMP_PATH_CHK_ASSEMBLE
            assemble = chk_entry['assemble']
            build = chk_entry['build']
            temp_assemble = shutil.copy(os.path.join(env.workspace['fpath_artifact_assemble'], assemble), temp_assemble_path)

            # exact zip and compare
            logging.info('[ checking ] %s -VS- %s', temp_assemble, build)
            self.__check_zip(temp_assemble, os.path.join(env.workspace['fpath_temp'], TEMP_PATH_BUILD,  build))

    def _destroy(self):
        if os.path.exists(self.temp_path):
            shutil.rmtree(self.temp_path)
        os.makedirs(self.temp_path)

    def __mvn_build(self, settings, pom):
        cmd = 'mvn -s %s -f %s clean install' % (settings, pom)
        logging.info('[ subprocess ] %s', cmd)
        result = subprocess.run(cmd, shell=True, stdout=logger.logfile_stream)
        if result.returncode != 0:
            raise SCException('command executing failed, check log.txt for detail')


    def __check_zip(self, assemble_file, build_file):
        self.exract(assemble_file)
        self.exract(build_file)
        cmp_results = []
        extract_assemble_path = self.__convert_extract_path(assemble_file, os.path.splitext(assemble_file)[1])
        extract_build_path = self.__convert_extract_path(build_file, os.path.splitext(build_file)[1])
        self.cmp(extract_build_path, extract_assemble_path, cmp_results)
        if len(cmp_results) > 0:
            logging.info('Comparing not passed ([A] means build has this file but assemble not):')
            for entry in cmp_results:
                logging.info('[%s] %s', entry[0], entry[1])

            os._exit(0)




    def exract(self, path):
        if os.path.isdir(path):
            for elem in os.listdir(path):
                self.exract(elem)
        elif os.path.isfile(path):
            file_ext = os.path.splitext(path)[1].lower()
            if file_ext == '.zip' or file_ext == '.jar' or file_ext == '.war':
                extract_path = self.__convert_extract_path(path, file_ext)
                zip = zipfile.ZipFile(path)
                zip.extractall(path=extract_path)
                zip.close()
                os.remove(path)

    def cmp(self, path1, path2, results):
        cmp_obj = filecmp.dircmp(path2, path1, [])
        if len(cmp_obj.diff_files) > 0 or len(cmp_obj.left_only) > 0 or len(cmp_obj.right_only) > 0:
            if len(cmp_obj.diff_files) > 0:
                for entry in cmp_obj.diff_files:
                    results.append(['U', entry])
            if len(cmp_obj.left_only) > 0:
                for entry in cmp_obj.left_only:
                    results.append(['D', entry])
            if len(cmp_obj.right_only) > 0:
                for entry in cmp_obj.right_only:
                    results.append(['A', entry])

        for entry in cmp_obj.common_dirs:
            self.cmp(os.path.join(path1, entry), os.path.join(path2, entry), results)

    def __convert_extract_path(self, zip_path, file_ext):
        path = zip_path[0:len(zip_path) - len(file_ext)] + '-' + file_ext[1:]
        return path


