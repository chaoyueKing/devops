import filecmp
import os
import shutil
import json


# SCRIPT ENVIRONMENT

# the default script workspace
WORKSPACE = 'C:/Users/watertao/Desktop/workspace'
# the default absolute path of last production build
DFT_BASE_BUILD_ABS_PATH = os.path.join(WORKSPACE, 'original')
# the default absolute path of this production build
DFT_TARGET_BUILD_ABS_PATH = os.path.join(WORKSPACE, 'target')
# the default absolute path where patch to output
DFT_PATCH_ABS_PATH = os.path.join(WORKSPACE, 'patch')

# base url of svn
SVN_URL_PREFIX = 'http://10.10.10.176:88/svn/accountcenter/Code/accountcenter/'
SVN_BASE_BUILD_URL = SVN_URL_PREFIX + 'branches/2.9.7.4/'


def main():

    CONFIG = json.load(open('config.json'))

    print(CONFIG['workspace']['is_purge'])

    print(123)
    # if initworkspace

    # svn checkout


    # build base version


    # build target version




    # initialize patch output directory'
    init_patch_dir(DFT_PATCH_ABS_PATH)

    # compare 2 builds and generate patch'
    cmp_dir(
        DFT_BASE_BUILD_ABS_PATH,
        DFT_TARGET_BUILD_ABS_PATH,
        DFT_PATCH_ABS_PATH,
        [diff_output_handler]
    )


# initialize patch directory (just clean the directory)
def init_patch_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


# compare two directory and return the comparison result:
#   {
#       'common_dirs': [],
#       'diff_files': [],
#       'added_items': []
#   }
def cmp_dir(base_path, target_path, patch_path, handlers):
    cmp_result = {}
    cmp_obj = filecmp.dircmp(base_path, target_path, [])

    cmp_result['common_dirs'] = cmp_obj.common_dirs
    cmp_result['diff_files'] = cmp_obj.diff_files
    cmp_result['added_items'] = cmp_obj.right_only

    # processing handler, passing the comparing result to handlers
    for handler in handlers:
        handler(cmp_result, base_path, target_path, patch_path)

    # recursively process common directory
    for common_dir in cmp_obj.common_dirs:
        cmp_dir(
            os.path.join(base_path, common_dir),
            os.path.join(target_path, common_dir),
            os.path.join(patch_path, common_dir),
            handlers
        )


# handler for output patch files
def diff_output_handler(cmp_result, base_path, target_path, patch_path):
    # if no diff files and added items, handler will do nothing
    if len(cmp_result['diff_files']) == 0 and len(cmp_result['added_items']) == 0:
        return

    # if current directory does not exist, create it
    if not os.path.exists(patch_path):
        os.makedirs(patch_path)

    # output diff files
    for file in cmp_result['diff_files']:
        shutil.copyfile(
            os.path.join(target_path, file),
            os.path.join(patch_path, file)
        )


main()
