#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import filecmp
import logging
import os
import shutil
from string import Template

import module.third.diff_match_patch as dmp_module

from module.abstract_scan_comparer import AbstractScanComparer
import module.env as env


class ScanComparer(AbstractScanComparer):
    """

    """

    def self_desc(self):
        self_desc = {
            'name': 'raw file',
            'cname': '普通文本扫描比对',
            'desc': 'scan the files and compare as the raw text'
        }
        return self_desc

    def stat(self):

        stat_template = '增加了 $filescan_add 个文件, 删除了 $filescan_delete 个文件, 修改了 $filescan_change 个文件.'
        return Template(stat_template).substitute(
                filescan_add=self.change_stat['add'],
                filescan_delete=self.change_stat['delete'],
                filescan_change=self.change_stat['update']
        )

    def _init(self):
        self.output_path = os.path.join(env.workspace['fpath_output'], self.processor_key)
        self.data_output_path = os.path.join(self.output_path, 'data')
        if os.path.exists(self.output_path):
            shutil.rmtree(self.output_path)
        os.makedirs(self.output_path)
        os.makedirs(self.data_output_path)

        self.plugin_path = os.path.join(env.runtime['fpath_module_scan_comparer'], self.processor_key)
        template_stream = open(os.path.join(self.plugin_path, 'single-template.html'), 'r')
        self.template_single = template_stream.read()
        template_stream.close()
        template_stream = open(os.path.join(self.plugin_path, 'index-template.html'), 'r')
        self.template_index = template_stream.read()
        template_stream.close()

        self.file_id_cnt = 1
        self.change_list = []
        self.change_stat = {
            'add': 0,
            'update': 0,
            'delete': 0
        }
        self.filter = self.sc_config['filter']

    def _do_scan(self):
        artifact = env.workspace['fpath_artifact_source']
        base = env.workspace['fpath_base']

        self._cmp_dir(base, artifact, '')
        tbody = ''

        for entry in self.change_list:
            logging.info('[%s] %s' % (entry[0], entry[2]))
            tbody += '<tr><td><span class="label_' + entry[0] + '">' + self.__convert_change_type_label(entry[0]) + '</span></td><td><a href="data/'
            tbody += str(entry[1]) + '.html">' + entry[2] + '</a></td>'
            if entry[0] == 'U':
                self.change_stat['update'] += 1
            elif entry[0] == 'A':
                self.change_stat['add'] += 1
            elif entry[0] == 'D':
                self.change_stat['delete'] += 1

        index_stream  = open(os.path.join(self.output_path, 'index.html'), 'w')
        index_stream.write(Template(self.template_index).substitute(tbody=tbody))
        index_stream.close()

    def __convert_change_type_label(self, change_type):
        if (change_type == 'U'):
            return 'UPDATE'
        elif (change_type == 'D'):
            return 'DELETE'
        elif (change_type == 'A'):
            return 'ADD'

    def _cmp_dir(self, base_prefix_path, dest_prefix_path, path):
        cmp_obj = filecmp.dircmp(os.path.join(base_prefix_path, path), os.path.join(dest_prefix_path, path), [])
        for left_only in cmp_obj.left_only:
            if left_only in self.filter:
                continue
            self._d_a_handler('D', base_prefix_path, os.path.join(path, left_only))
        for right_only in cmp_obj.right_only:
            if right_only in self.filter:
                continue
            self._d_a_handler('A', dest_prefix_path, os.path.join(path, right_only))
        for change_file in cmp_obj.diff_files:
            if change_file in self.filter:
                continue
            self._u_handler(base_prefix_path, dest_prefix_path, os.path.join(path, change_file))
        for common_dir in cmp_obj.common_dirs:
            if common_dir in self.filter:
                continue
            self._cmp_dir(
                    base_prefix_path,
                    dest_prefix_path,
                    os.path.join(path, common_dir)
            )

    def _u_handler(self, base_prefix_path, dest_prefix_path, path):
        file_id = self.file_id_cnt
        self.file_id_cnt += 1
        self.change_list.append(['U', file_id, path])
        dmp = dmp_module.diff_match_patch()
        base_stream = open(os.path.join(base_prefix_path, path), 'r')
        base_content = base_stream.read()
        base_stream.close()
        dest_stream = open(os.path.join(dest_prefix_path, path), 'r')
        dest_content = dest_stream.read()
        dest_stream.close()
        diffs = dmp.diff_main(base_content, dest_content)
        dmp.diff_cleanupSemantic(diffs)
        html = dmp.diff_prettyHtml(diffs)

        html_stream = open(os.path.join(self.data_output_path, str(file_id) + '.html'), 'w')
        html_stream.write(Template(self.template_single).substitute(code=html, file=path))
        html_stream.close()

    def _d_a_handler(self, type, prefix_path, path):
        whole_path = os.path.join(prefix_path, path)
        if os.path.isfile(whole_path):
            file_id = self.file_id_cnt
            self.file_id_cnt += 1
            self.change_list.append([type, file_id, path])
            dest = os.path.join(self.data_output_path, str(file_id) + '.html')

            file_stream = open(whole_path, 'r')
            file_content = file_stream.read()
            file_stream.close()
            file_content = file_content.replace('\n', '<br/>')
            html_stream = open(dest, 'w')
            html_stream.write(Template(self.template_single).substitute(code=file_content, file=path))
            html_stream.close()
        elif os.path.isdir(whole_path):
            for entry in os.listdir(whole_path):
                if entry in self.filter:
                    continue
                self._d_a_handler(type, prefix_path, os.path.join(path, entry))

def xml_compare(x1, x2):
    if x1.tag != x2.tag:
        return False
    for name, value in x1.attrib.items():
        if x2.attrib.get(name) != value:
            return False
    for name in x2.attrib.keys():
        if name not in x1.attrib:
            return False
    if not text_compare(x1.text, x2.text):
        return False
    if not text_compare(x1.tail, x2.tail):
        return False
    cl1 = x1.getchildren()
    cl2 = x2.getchildren()
    if len(cl1) != len(cl2):
        return False
    i = 0
    for c1, c2 in zip(cl1, cl2):
        i += 1
        if not xml_compare(c1, c2):
            return False
    return True

def text_compare(t1, t2):
    if not t1 and not t2:
        return True
    if t1 == '*' or t2 == '*':
        return True
    return (t1 or '').strip() == (t2 or '').strip()
