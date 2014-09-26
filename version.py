__author__ = 'Rimco'

import subprocess

##############################
#### Revision information ####
##############################

major_ver = 2
minor_ver = 1

try:
    revision = int(subprocess.check_output(['git', 'rev-list', '--count', '--first-parent', 'HEAD']))
except Exception:
    print 'Could not use git to determine version!'
    revision = 999
ver_str = '%d.%d.%d' % (major_ver, minor_ver, revision)

try:
    ver_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short']).strip()
except Exception:
    print 'Could not use git to determine date of last commit!'
    ver_date = '2014-09-10'