import filecmp
import os
import shutil
import json
import subprocess


def main():

    config = json.load(open('config.json'))

    init_workspace(config['workspace'])

    for approach in config['approaches']:
        if approach['ignore']:
            continue
        processor_class = eval(approach['processor'])
        processor = processor_class(config['workspace']['path'], approach['configuration'])
        processor.process()


# initialize workspace directory (just clean the directory)
def init_workspace(config):
    if not os.path.exists(config['path']):
        os.makedirs(config['path'])

# abstract processor
class Processor:

    def process(self):
        print('-' * 37)
        print('-', self.processor_name)
        print('-' * 37)
        self.do_process()
        print('Done.')
        print()

    def do_process(self):
        pass

# PROCESSOR: VCSProcessor
class VCSProcessor(Processor):

    def __init__(self, workspace_path, config):
        self.processor_name = 'VCS Processor'
        self.workspace_path = workspace_path
        self.config = config

    def do_process(self):
        print('aaaaaaaaaaaaaa')



# PROCESSOR: BUILDProcessor
class BUILDProcessor(Processor):

    def __init__(self, workspace_path, config):
        self.processor_name = 'BUILD Processor'
        self.workspace_path = workspace_path
        self.config = config

    def do_process(self):
        for build in self.config['builds']:
            cmd = 'mvn -s ' + os.path.join(self.workspace_path, self.config['mvn_setting'])
            cmd += ' -f ' + os.path.join(self.workspace_path, build['path'], 'pom.xml')
            cmd += ' ' + build['lp']
            subprocess.run(cmd)



# PROCESSOR: PATCHProcessor
class PATCHProcessor(Processor):

    def __init__(self, workspace_path, config):
        self.processor_name = 'PATCH Processor'
        self.workspace_path = workspace_path
        self.config = config
        self.handlers = [
            self._diff_output_handler
        ]


    def do_process(self):

        base_path = os.path.join(self.workspace_path, self.config['base_path'])
        dest_path = os.path.join(self.workspace_path, self.config['dest_path'])
        output_path = os.path.join(self.workspace_path, self.config['output_path'])

        if not os.path.exists(base_path):
            raise Exception('missing base path: ' + base_path)
        if not os.path.exists(dest_path):
            raise Exception('missing dest path: ' + dest_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        else:
            shutil.rmtree(output_path)
            os.makedirs(output_path)

        self._cmp_dir(
            base_path,
            dest_path,
            output_path
        )


    def _cmp_dir(self, base_path, dest_path, output_path):
        cmp_result = {}
        cmp_obj = filecmp.dircmp(base_path, dest_path, [])
        cmp_result['diff_files'] = cmp_obj.diff_files
        cmp_result['added_items'] = cmp_obj.right_only
        for handler in self.handlers:
            handler(cmp_result, base_path, dest_path, output_path)
        for common_dir in cmp_obj.common_dirs:
            self._cmp_dir(
                os.path.join(base_path, common_dir),
                os.path.join(dest_path, common_dir),
                os.path.join(output_path, common_dir)
            )


    def _diff_output_handler(self, cmp_result, base_path, dest_path, output_path):

        if len(cmp_result['diff_files']) == 0 and len(cmp_result['added_items']) == 0:
            return

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        for file in cmp_result['diff_files']:
            print('[U]', os.path.join(output_path, file))
            shutil.copyfile(
                os.path.join(dest_path, file),
                os.path.join(output_path, file)
            )

        for item in cmp_result['added_items']:
            item_dest_path = os.path.join(dest_path, item)
            item_output_path = os.path.join(output_path, item)
            if os.path.isdir(item_dest_path):
                print('[A]', os.path.join(item_output_path, '*'))
                shutil.copytree(item_dest_path, item_output_path)
            if os.path.isfile(item_dest_path):
                print('[A]', item_output_path)
                shutil.copyfile(item_dest_path, item_output_path)

main()
