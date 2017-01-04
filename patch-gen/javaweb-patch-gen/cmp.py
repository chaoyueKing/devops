import filecmp
import os
import shutil
import json
import subprocess
import sys
import logging


def main():

    project_type = read_project_type()

    config = json.load(open(project_type + '.json'))

    init_workspace(config['workspace'])

    global logfile
    logfile = open(os.path.join(config['workspace']['path'], 'log.txt'), 'w')

    init_logging_framework(logfile)

    logging.info('Workspace: [ %s ]  ( %s )',
                 config['workspace']['path'],
                 'you can remove the workspace directory to clear workspace')

    for approach in config['approaches']:
        if approach['ignore']:
            logging.info('Ignore processor: [ %s ]  ( %s )',
                         approach['processor'],
                         'you can change the ignore property to false in configuration file for recover this processor')
            continue
        processor_class = eval(approach['processor'])
        processor = processor_class(config['workspace']['path'], approach['configuration'])
        processor.process()

    logging.info('******************************* IMPORT DECLARATION *******************************')
    logging.info('This script is writing for studying and sharing.')
    logging.info('The author of this script is no responsible for any problem caused by this script.')
    logging.info('So we strongly recommended that you check the output before publish.')
    logging.info('**********************************************************************************')

def init_logging_framework(logfile):
    handlers = [logging.StreamHandler(stream=logfile), logging.StreamHandler()]
    logging.basicConfig(level = logging.DEBUG,
                        format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt = '%m-%d %H:%M',
                        handlers = handlers)

# initialize workspace directory (just clean the directory)
def init_workspace(config):
    if not os.path.exists(config['path']):
        os.makedirs(config['path'])


# read project type via argument
def read_project_type():
    if len(sys.argv) != 2:
        logging.info('missing project type argument.')
        logging.info('for example: py cmp.py suss')
        raise
    else:
        return sys.argv[1]


# abstract processor
class Processor:

    def process(self):
        logging.info('-' * 37)
        logging.info('- %s', self.processor_name)
        logging.info('-' * 37)
        self.do_process()
        logging.info('Done.')
        logging.info('')

    def do_process(self):
        pass

# PROCESSOR: VCSProcessor
class VCSProcessor(Processor):

    def __init__(self, workspace_path, config):
        self.processor_name = 'VCS Processor'
        self.workspace_path = workspace_path
        self.config = config

    def do_process(self):
        for working_copy in self.config['working_copies']:
            path = os.path.join(self.workspace_path, working_copy['path'])
            if os.path.exists(path):
                shutil.rmtree(path)
                os.makedirs(path)
            else:
                os.makedirs(path)
            cmd = 'svn export --force ' + working_copy['url'] + ' ' + path
            logging.info('[ subprocess ] ' + cmd)
            subprocess.run(cmd, shell=True, stdout=logfile)



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
            logging.info('[ subprocess ] %s', cmd)
            subprocess.run(cmd, shell=True, stdout=logfile)


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
        patchfile_path = os.path.join(self.workspace_path, self.config['patchfile_path'])

        if not os.path.exists(base_path):
            raise Exception('missing base path: ' + base_path)
        if not os.path.exists(dest_path):
            raise Exception('missing dest path: ' + dest_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        else:
            shutil.rmtree(output_path)
            os.makedirs(output_path)
        self.patchfile = open(patchfile_path, 'w')

        self._cmp_dir(
            base_path,
            dest_path,
            output_path
        )

        self.patchfile.close()


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
            logging.info('[U] %s', os.path.join(output_path, file))
            self.patchfile.write('[U] ' + os.path.join(output_path, file) + '\n')
            shutil.copyfile(
                os.path.join(dest_path, file),
                os.path.join(output_path, file)
            )

        for item in cmp_result['added_items']:
            item_dest_path = os.path.join(dest_path, item)
            item_output_path = os.path.join(output_path, item)
            if os.path.isdir(item_dest_path):
                logging.info('[A] %s', os.path.join(item_output_path, '*'))
                self.patchfile.write('[A] ' + os.path.join(item_output_path, '*') + '\n')
                shutil.copytree(item_dest_path, item_output_path)
            if os.path.isfile(item_dest_path):
                logging.info('[A] %s', item_output_path)
                self.patchfile.write('[A] ' + item_output_path + '\n')
                shutil.copyfile(item_dest_path, item_output_path)


def onerror(func, path, exc_info):
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def readonly_handler(func, path, execinfo):
    os.chmod(path, 128) #or os.chmod(path, stat.S_IWRITE) from "stat" module
    func(path)

def errorRemoveReadonly(func, path, exc):
    excvalue = exc[1]
    import stat
    import errno
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        # change the file to be readable,writable,executable: 0777
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        # retry
        func(path)
    else:
        raise


def on_rm_error( func, path, exc_info):
    import stat
    # path contains the path of the file that couldn't be removed
    # let's just assume that it's read-only and unlink it.
    os.chmod( path, stat.S_IWRITE )
    os.unlink( path )



main()
