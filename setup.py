#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

import sys
import os
import subprocess
import shutil
import stat


def yes_no(msg):
    response = ''
    while response.lower().strip() not in ['y', 'yes', 'n', 'no']:
        response = raw_input('%s [y/yes/n/no]\n' % msg)
    return response.lower().strip() in ['y', 'yes']


def del_rw(action, name, exc):
    if os.path.exists(name):
        os.chmod(name, stat.S_IWRITE)
    if os.path.isfile(name):
        os.remove(name)
    elif os.path.isdir(name):
        os.rmdir(name)


def install_package(module, easy_install=None, package=None, git=None, git_exec=None):
    try:
        print 'Checking %s' % module
        __import__(module)
        print '%s is available' % module
        return
    except ImportError:
        if not yes_no('%s not available, do you want to install it?' % module):
            return

    done = False
    if not done and easy_install is not None:
        try:
            subprocess.check_call(['easy_install', easy_install])
            done = True
        except subprocess.CalledProcessError:
            print 'Failed to use easy_install.'

    if sys.platform.startswith('linux'):
        if not done and package is not None:
            try:
                subprocess.check_call('apt-get install'.split() + [package])
                done = True
            except subprocess.CalledProcessError:
                print 'Failed to use apt-get.'

        if not done and package is not None:
            try:
                subprocess.check_call('yum install'.split() + [package])
                done = True
            except subprocess.CalledProcessError:
                print 'Failed to use yum.'

    if not done and git is not None and git_exec is not None:
        try:
            shutil.rmtree('tmp', onerror=del_rw)
            subprocess.check_call(['git', 'clone', git, 'tmp'])
            subprocess.check_call(git_exec, cwd='tmp')
            shutil.rmtree('tmp', onerror=del_rw)
            done = True
        except Exception:
            print 'Failed to use git.'

    if not done:
        print 'Failed to install %s.' % module

def install_service():
    my_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join('/etc', 'init.d', 'ospy')
    if sys.platform.startswith('linux'):
        if yes_no('Do you want to install OSPy as a service?'):
            with open(os.path.join(my_dir, 'service', 'ospy.sh')) as source:
                with open(path, 'w') as target:
                    target.write(source.read().replace('{{OSPY_DIR}}', my_dir))
            os.chmod(path, 0755)
            subprocess.check_call(['update-rc.d', 'ospy', 'defaults'])
    else:
        print 'Service installation is only possible on unix systems.'


def uninstall_service():
    if sys.platform.startswith('linux'):
        subprocess.check_call(['service', 'ospy', 'stop'])

        path = os.path.join('/etc', 'init.d', 'ospy')
        if os.path.isfile(path):
            try:
                subprocess.check_call(['update-rc.d', '-f', 'ospy', 'remove'])
            except subprocess.CalledProcessError:
                print 'Could not remove using update-rc.d'

            os.unlink(path)

            print 'Service removed'
        else:
            print 'Service not installed'
    else:
        print 'Service uninstall is only possible on unix systems.'

def check_password():
    from ospy.options import options
    from ospy.helpers import test_password, password_salt, password_hash
    if not options.no_password and test_password('opendoor'):
        if yes_no('You are still using the default password, you should change it! Do you want to change it now?'):
            from getpass import getpass
            pw1 = pw2 = ''
            while True:
                pw1 = getpass('New password: ')
                pw2 = getpass('Repeat password: ')
                if pw1 != '' and pw1 == pw2:
                    break
                print 'Invalid input!'

            options.password_salt = password_salt()  # Make a new salt
            options.password_hash = password_hash(pw1, options.password_salt)

def start():
    if yes_no('Do you want to start OSPy now?'):
        if sys.platform.startswith('linux'):
            try:
                subprocess.check_call(['service', 'ospy', 'start'])
            except subprocess.CalledProcessError:
                subprocess.check_call([sys.executable, 'run.py'])

        else:
            subprocess.check_call(['cmd.exe', '/c', 'start', sys.executable, 'run.py'])


if __name__ == '__main__':
    # On unix systems we need to be root:
    if sys.platform.startswith('linux'):
        if not os.getuid() == 0:
            sys.exit("This script needs to be run as root.")

    if len(sys.argv) == 2 and sys.argv[1] == 'install':
        # Check if packages are available:
        install_package('web', 'web.py', 'python-webpy',
                        'https://github.com/webpy/webpy.git', [sys.executable, 'setup.py', 'install'])

        install_package('gfm', None, None,
                        'https://github.com/dart-lang/py-gfm.git', [sys.executable, 'setup.py', 'install'])

        install_package('pygments', 'pygments', 'python-pygments',
                        'http://bitbucket.org/birkenfeld/pygments-main', [sys.executable, 'setup.py', 'install'])

        install_service()

        check_password()

        start()

    elif len(sys.argv) == 2 and sys.argv[1] == 'uninstall':
        uninstall_service()

    else:
        sys.exit("Usage:\n"
                 "setup.py install:   Interactive install.\n"
                 "setup.py uninstall: Removes the service if installed.")
