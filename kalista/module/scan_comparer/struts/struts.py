#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import filecmp
import logging
import os
import shutil
from string import Template
import xml.etree.ElementTree as ET

from module.abstract_scan_comparer import AbstractScanComparer
import module.components.common_utils as CUTILS
import module.env as env
import module.third.diff_match_patch as dmp_module



class ScanComparer(AbstractScanComparer):
    """

    """

    def self_desc(self):
        self_desc = {
            'name': 'struts2',
            'cname': 'struts2 配置文件扫描比对',
            'desc': 'scan the struts2 configuration files and find difference between 2 version'
        }
        return self_desc

    def stat(self):
        stat_template = '增加了 $add 个 action, 删除了 $delete 个action, 修改了 $change 个action.'
        add, delete, change = 0, 0, 0
        for key in self.change_stat['artifact_only']:
            add += len(self.change_stat['artifact_only'][key])
        for key in self.change_stat['base_only']:
            delete += len(self.change_stat['base_only'][key])
        for key in self.change_stat['diff']:
            change += len(self.change_stat['diff'][key])
        return Template(stat_template).substitute(
                add=add,
                delete=delete,
                change=change
        )

    def _init(self):
        """
        初始化

        一般用于创建执行过程中所需的临时目录

        :return:
        """
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
        self.change_stat = {
            'artifact_only': {},
            'base_only': {},
            'diff': {}
        }

    def _do_scan(self):
        artifact_path_prefix = os.path.join(env.workspace['fpath_artifact'], 'source')
        base_path_prefix = os.path.join(env.workspace['fpath_workspace'], 'base')
        left_list = []
        diff_list = []
        right_list = []
        for path in self.sc_config['conf_path']:
            self._cmp_sqlmap(base_path_prefix, artifact_path_prefix, path, left_list, diff_list, right_list)
        base_only_dict = {}
        artifact_only_dict = {}
        diff_dict = {}
        for entry in left_list:
            xml_tree = ET.parse(os.path.join(base_path_prefix, entry))
            packages = xml_tree.getroot().findall('package')
            for package_elem in packages:
                base_only_dict[package_elem.get('name')] = []
                actions = package_elem.findall('action')
                for action_elem in actions:
                    base_only_dict[package_elem.get('name')].append({
                        'cmp': 'D',
                        'name': action_elem.get('name'),
                        'elem': action_elem,
                        'file': path
                    })

        for entry in right_list:
            xml_tree = ET.parse(os.path.join(artifact_path_prefix, entry))
            packages = xml_tree.getroot().findall('package')
            for package_elem in packages:
                artifact_only_dict[package_elem.get('name')] = []
                actions = package_elem.findall('action')
                for action_elem in actions:
                    artifact_only_dict[package_elem.get('name')].append({
                        'cmp': 'A',
                        'name': action_elem.get('name'),
                        'elem': action_elem,
                        'file': path
                    })

        for entry in diff_list:
            base_xml_tree = ET.parse(os.path.join(base_path_prefix, entry))
            artifact_xml_tree = ET.parse(os.path.join(artifact_path_prefix, entry))
            base_packages = base_xml_tree.findall('package')
            artifact_packages = artifact_xml_tree.findall('package')
            base_only, artifact_only, common = self.compare_lists(base_packages, artifact_packages, self.__compare_package)
            for package in base_only:
                package_name = package.get('name')
                base_only_dict[package_name] = []
                actions = package.findall('action')
                for action in actions:
                    base_only_dict[package_name].append({
                        'cmp': 'D',
                        'name': action.get('name'),
                        'elem': action,
                        'file': entry
                    })
            for package in artifact_only:
                package_name = package.get('name')
                artifact_only_dict[package_name] = []
                actions = package.findall('action')
                for action in actions:
                    artifact_only_dict[package_name].append({
                        'cmp': 'A',
                        'name': action.get('name'),
                        'elem': action,
                        'file': entry
                    })
            i = 0
            for left_package in common[0]:
                right_package = common[1][i]
                package_name = left_package.get('name')
                diff_dict[package_name] = []
                base_only_dict[package_name] = []
                artifact_only_dict[package_name] = []
                left_actions = left_package.findall('action')
                right_actions = right_package.findall('action')
                for bitem in left_actions:
                    j = 0
                    is_existin_a = False
                    for aitem in right_actions:
                        if bitem.get('name') == aitem.get('name'):
                            del right_actions[j]
                            is_existin_a = True
                            if not xml_compare(bitem, aitem):
                                diff_dict[package_name].append({
                                    'cmp': 'U',
                                    'name': aitem.get('name'),
                                    'base_elem': bitem,
                                    'artifact_elem': aitem,
                                    'file': os.path.join(base_path_prefix, entry)
                                })
                            break
                        j += 1
                    if not is_existin_a:
                        base_only_dict[package_name].append({
                            'cmp': 'D',
                            'name': bitem.get('name'),
                            'elem': bitem,
                            'file': os.path.join(base_path_prefix, entry)
                        })

                for item in right_actions:
                    artifact_only_dict[package_name].append({
                        'cmp': 'A',
                        'name': item.get('name'),
                        'elem': item,
                        'file': os.path.join(base_path_prefix, entry)
                    })
                i += 1

        self.change_stat['base_only'] = base_only_dict
        self.change_stat['artifact_only'] = artifact_only_dict
        self.change_stat['diff'] = diff_dict

        print(base_only_dict)
        print(artifact_only_dict)
        print(diff_dict)

        # make outputs
        index_td_arry = []
        for key in base_only_dict:
            for entry in base_only_dict[key]:
                file_id = self.file_id_cnt
                self.file_id_cnt += 1
                index_td_arry.append({
                    'change_type': 'D',
                    'package': key,
                    'name': entry['name'],
                    'file': entry['file'],
                    'file_id': file_id
                })

                html_stream = open(os.path.join(self.data_output_path, str(file_id) + '.html'), 'w')
                html_stream.write(Template(self.template_single).substitute(
                        code=CUTILS.replace_html_entity(str(ET.tostring(entry['elem'], encoding="utf-8"), 'utf-8')),
                        file=entry['file'])
                )
                html_stream.close()

        for key in artifact_only_dict:
            for entry in artifact_only_dict[key]:
                file_id = self.file_id_cnt
                self.file_id_cnt += 1
                index_td_arry.append({
                    'change_type': 'A',
                    'package': key,
                    'name': entry['name'],
                    'file': entry['file'],
                    'file_id': file_id
                })

                html_stream = open(os.path.join(self.data_output_path, str(file_id) + '.html'), 'w')
                html_stream.write(Template(self.template_single).substitute(
                        code=CUTILS.replace_html_entity(str(ET.tostring(entry['elem'], encoding="utf-8"), 'utf-8')),
                        file=entry['file'])
                )
                html_stream.close()

        for key in diff_dict:
            for entry in diff_dict[key]:
                file_id = self.file_id_cnt
                self.file_id_cnt += 1
                index_td_arry.append({
                    'change_type': 'U',
                    'package': key,
                    'name': entry['name'],
                    'file': entry['file'],
                    'file_id': file_id
                })
                base_elem_content = str(ET.tostring(entry['base_elem'], encoding="utf-8"), 'utf-8')

                artifact_elem_content = str(ET.tostring(entry['artifact_elem'], encoding="utf-8"), 'utf-8')

                dmp = dmp_module.diff_match_patch()
                diffs = dmp.diff_main(base_elem_content, artifact_elem_content)
                dmp.diff_cleanupSemantic(diffs)
                html = dmp.diff_prettyHtml(diffs)

                html_stream = open(os.path.join(self.data_output_path, str(file_id) + '.html'), 'w')
                html_stream.write(Template(self.template_single).substitute(
                        code=html,
                        file=entry['file'])
                )
                html_stream.close()

        tbody_arry = []
        for entry in index_td_arry:
            logging.info('[%s] [ %s.%s ] %s' % (entry['change_type'], entry['package'], entry['name'], entry['file']))
            tbody_arry.append(
                    '<tr><td><span class="label_%s">%s</span></td><td>%s</td><td>%s</td><td><a href="%s">%s</a></td></tr>'
                    % (
                        entry['change_type'],
                        self.__convert_change_type_label(entry['change_type']),
                        entry['package'],
                        entry['name'],
                        './data/%s.html' % entry['file_id'],
                        entry['file']
                    )
            )

        index_stream = open(os.path.join(self.output_path, 'index.html'), 'w')
        index_stream.write(Template(self.template_index).substitute(
                tbody='\n'.join(tbody_arry)
        ))
        index_stream.close()

    def __compare_package(self, left_package, right_package):
        if left_package.get('name') == right_package.get('name'):
            return 1
        else:
            return 0

    def __convert_change_type_label(self, change_type):
        if (change_type == 'U'):
            return 'UPDATE'
        elif (change_type == 'D'):
            return 'DELETE'
        elif (change_type == 'A'):
            return 'ADD'

    def compare_lists(self, left_list, right_list, comparable):
        left_only, right_only, common = [], [], [[], []]
        for item in right_list:
            right_only.append(item)
        for left_item in left_list:
            j = 0
            is_existin_a = False
            for right_item in right_only:
                if comparable(left_item, right_item) == 1:
                    del right_only[j]
                    is_existin_a = True
                    common[0].append(left_item)
                    common[1].append(right_item)
                    break
                j += 1
            if not is_existin_a:
                left_only.append(left_item)
        return left_only, right_only, common

    def _cmp_sqlmap(self, left_prefix, right_prefix, path, left_list, diff_list, right_list):
        left_path = os.path.join(left_prefix, path)
        right_path = os.path.join(right_prefix, path)
        if os.path.exists(left_path) and os.path.exists(right_path):  # both exist
            if os.path.isfile(left_path) and os.path.isfile(right_path):
                diff_list.append(path)
            elif os.path.isdir(left_path) and os.path.isdir(right_path):
                cmp_obj = filecmp.dircmp(left_path, right_path, [])
                for entry in cmp_obj.diff_files:
                    diff_list.append(os.path.join(path, entry))
                for entry in cmp_obj.common_dirs:
                    self._cmp_sqlmap(left_prefix, right_prefix, os.path.join(path, entry), left_list, diff_list, right_list)
                for entry in cmp_obj.left_only:
                    if os.path.isfile(os.path.join(left_path, entry)):
                        left_list.append(os.path.join(path, entry))
                    elif os.path.isdir(os.path.join(left_path, entry)):
                        self._cmp_sqlmap(left_prefix, right_prefix, os.path.join(path, entry), left_list, diff_list, right_list)
                for entry in cmp_obj.right_only:
                    if os.path.isfile(os.path.join(right_path, entry)):
                        right_list.append(os.path.join(path, entry))
                    elif os.path.isdir(os.path.join(right_path, entry)):
                        self._cmp_sqlmap(left_prefix, right_prefix, os.path.join(path, entry), left_list, diff_list, right_list)
        elif os.path.exists(left_path):  # only left exist
            if os.path.isfile(left_path):
                left_list.append(path)
            elif os.path.isdir(left_path):
                for entry in os.listdir(left_path):
                    full_entry = os.path.join(left_path, entry)
                    if os.path.isfile(full_entry):
                        left_list.append(os.path.join(path, entry))
                    elif os.path.isdir(full_entry):
                        self._cmp_sqlmap(left_prefix, right_prefix, os.path.join(path, entry), left_list, diff_list, right_list)
        elif os.path.exists(right_path):  # only right exist
            if os.path.isfile(right_path):
                right_list.append(path)
            elif  os.path.isdir(right_path):
                for entry in os.listdir(right_path):
                    full_entry = os.path.join(right_path, entry)
                    if os.path.isfile(full_entry):
                        right_list.append(os.path.join(path, entry))
                    elif os.path.isdir(full_entry):
                        self._cmp_sqlmap(left_prefix, right_prefix, os.path.join(path, entry), left_list, diff_list, right_list)

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
