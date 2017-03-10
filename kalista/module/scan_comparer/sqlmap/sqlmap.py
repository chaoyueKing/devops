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
            'name': 'i(my)batis sqlmap',
            'cname': 'sqlmap文件扫描比对',
            'desc': 'scan the sqlmap configuration files and find difference between 2 version'
        }
        return self_desc

    def stat(self):
        stat_template = '增加了 $add 个元素, 删除了 $delete 个元素, 修改了 $change 个元素.'
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
            namespace = xml_tree.getroot().get('namespace')
            root_elem = xml_tree.getroot()
            base_only_dict[namespace] = []
            for child in root_elem:
                if child.tag == 'sql' or child.tag == 'select' or child.tag == 'delete' or child.tag == 'insert':
                    base_only_dict[namespace].append({
                        'cmp': 'D',
                        'id': child.get('id'),
                        'type': child.tag,
                        'elem': child,
                        'file': os.path.join(base_path_prefix, entry)
                    })

        for entry in right_list:
            xml_tree = ET.parse(os.path.join(artifact_path_prefix, entry))
            namespace = xml_tree.getroot().get('namespace')
            root_elem = xml_tree.getroot()
            artifact_only_dict[namespace] = []
            for child in root_elem:
                if child.tag == 'sql' or child.tag == 'select' or child.tag == 'delete' or child.tag == 'insert':
                    artifact_only_dict[namespace].append({
                        'cmp': 'A',
                        'id': child.get('id'),
                        'type': child.tag,
                        'elem': child,
                        'file': os.path.join(artifact_path_prefix, entry)
                    })

        for entry in diff_list:
            base_xml_tree = ET.parse(os.path.join(base_path_prefix, entry))
            artifact_xml_tree = ET.parse(os.path.join(artifact_path_prefix, entry))
            base_namespace = base_xml_tree.getroot().get('namespace')
            artifact_namespace = artifact_xml_tree.getroot().get('namespace')
            # if namespace changed, we think all the elements were changed
            if (base_namespace != artifact_namespace):
                base_only_dict[base_namespace] = []
                artifact_only_dict[artifact_namespace] = []
                for child in base_xml_tree.getroot():
                    if child.tag == 'sql' or child.tag == 'select' or child.tag == 'delete' or child.tag == 'insert':
                        base_only_dict[base_namespace].append({
                            'cmp': 'D',
                            'id': child.get('id'),
                            'type': child.tag,
                            'elem': child,
                            'file': os.path.join(base_path_prefix, entry)
                        })
                for child in artifact_xml_tree.getroot():
                    if child.tag == 'sql' or child.tag == 'select' or child.tag == 'delete' or child.tag == 'insert':
                        artifact_only_dict[artifact_namespace].append({
                            'cmp': 'A',
                            'id': child.get('id'),
                            'type': child.tag,
                            'elem': child,
                            'file': os.path.join(base_path_prefix, entry)
                        })
            else:
                base_only_dict[base_namespace] = []
                artifact_only_dict[artifact_namespace] = []
                diff_dict[base_namespace] = []
                base_elem_list = []
                artifact_elem_list = []
                for child in base_xml_tree.getroot():
                    if child.tag == 'sql' or child.tag == 'select' or child.tag == 'delete' or child.tag == 'insert':
                        base_elem_list.append(child)
                for child in artifact_xml_tree.getroot():
                    if child.tag == 'sql' or child.tag == 'select' or child.tag == 'delete' or child.tag == 'insert':
                        artifact_elem_list.append(child)
                i = 0
                for bitem in base_elem_list:
                    j = 0
                    is_existin_a = False
                    for aitem in artifact_elem_list:
                        if bitem.get('id') == aitem.get('id'):
                            del artifact_elem_list[j]
                            is_existin_a = True
                            if not xml_compare(bitem, aitem):{
                                diff_dict[base_namespace].append({
                                    'cmp': 'U',
                                    'id': aitem.get('id'),
                                    'type': aitem.tag,
                                    'base_elem': bitem,
                                    'artifact_elem': aitem,
                                    'file': os.path.join(base_path_prefix, entry)
                                })
                            }
                            break
                        j += 1
                    if not is_existin_a:
                        base_only_dict[base_namespace].append({
                            'cmp': 'D',
                            'id': bitem.get('id'),
                            'type': bitem.tag,
                            'elem': bitem,
                            'file': os.path.join(base_path_prefix, entry)
                        })
                    i += 1
                for item in artifact_elem_list:
                    artifact_only_dict[base_namespace].append({
                        'cmp': 'A',
                        'id': item.get('id'),
                        'type': item.tag,
                        'elem': item,
                        'file': os.path.join(base_path_prefix, entry)
                    })

        self.change_stat['base_only'] = base_only_dict
        self.change_stat['artifact_only'] = artifact_only_dict
        self.change_stat['diff'] = diff_dict

        # make outputs
        index_td_arry = []
        for key in base_only_dict:
            for entry in base_only_dict[key]:
                file_id = self.file_id_cnt
                self.file_id_cnt += 1
                index_td_arry.append({
                    'change_type': 'D',
                    'namespace': key,
                    'elem_type': entry['type'],
                    'id': entry['id'],
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
                    'namespace': key,
                    'elem_type': entry['type'],
                    'id': entry['id'],
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
                    'namespace': key,
                    'elem_type': entry['type'],
                    'id': entry['id'],
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
            logging.info('[%s] [ - %s - %s.%s ] %s' % (entry['change_type'], entry['elem_type'], entry['namespace'], entry['id'], entry['file']))
            tbody_arry.append(
                '<tr><td><span class="label_%s">%s</span></td><td>%s</td><td>%s</td><td>%s</td><td><a href="%s">%s</a></td></tr>'
                % (
                    entry['change_type'],
                    self.__convert_change_type_label(entry['change_type']),
                    entry['namespace'],
                    entry['elem_type'],
                    entry['id'],
                    './data/%s.html' % entry['file_id'],
                    entry['file']
                )
            )

        index_stream = open(os.path.join(self.output_path, 'index.html'), 'w')
        index_stream.write(Template(self.template_index).substitute(
                tbody='\n'.join(tbody_arry)
        ))
        index_stream.close()


    def __convert_change_type_label(self, change_type):
        if (change_type == 'U'):
            return 'UPDATE'
        elif (change_type == 'D'):
            return 'DELETE'
        elif (change_type == 'A'):
            return 'ADD'

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
