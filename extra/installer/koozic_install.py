#!/usr/bin/env python3

import argparse
from collections import OrderedDict
from glob import glob
from multiprocessing import cpu_count
import os
from shutil import copyfileobj, rmtree
import subprocess as s
import sys
import tarfile
from tempfile import NamedTemporaryFile
import urllib.request

DOWN_URL = 'https://github.com/DocMarty84/koozic/releases/download/{v}/koozic-{v}.tar.gz'


class Driver():
    def __init__(self, args):
        self.dep = set([])
        self.pip_dep = set([])
        self.user = args.user
        self.dir = os.path.join(args.directory, 'koozic')

    def __setitem__(self, key, val):
        return setattr(self, key, val)

    def set_config(self):
        with open(os.path.join(os.sep, 'etc', 'odoo.conf'), 'w') as f:
            f.write('USER={}\n'.format(self.user))
            f.write('DIR={}\n'.format(self.dir))

    def get_config(self):
        fn = os.path.join(os.sep, 'etc', 'odoo.conf')
        if not os.path.isfile(fn):
            sys.exit('Configuration file {} could not be found! Exiting...'.format(fn))
        with open(fn, 'r') as f:
            for line in f:
                data = line.split('=')
                self[data[0].lower()] = data[1].rstrip()

    def install_dep(self):
        print('Installing package dependencies...')
        self._install(list(self.dep))

    def install_pip_dep(self):
        print('Installing pip dependencies...')
        self._pip_install(list(self.pip_dep))

    def setup_postgresql(self):
        s.call('su - postgres -c "createuser -s {}"'.format(self.user), shell=True)

    def download_and_extract(self):
        print('Downloading the latest KooZic version...')
        with urllib.request.urlopen(DOWN_URL) as response, NamedTemporaryFile() as out_file:
            dir = os.path.split(self.dir)[0]
            copyfileobj(response, out_file)
            tarfile.open(name=out_file.name).extractall(path=dir)
        s.call(['chown', '-R', '{u}:{u}'.format(u=self.user), self.dir])

    def copy_ffmpeg(self):
        ffmpeg = glob(os.path.join(self.dir, 'extra', 'ffmpeg', '*.tar.gz'))
        if ffmpeg:
            path = os.path.join(os.sep, 'usr', 'local', 'bin')
            tarfile.open(name=ffmpeg[0]).extractall(path=path)
            s.call(['chown', '{u}:{u}'.format(u=self.user), os.path.join(path, 'ffmpeg')])

    def init_koozic(self):
        print('Initializing KooZic...')
        s.call(self._init_koozic_cmd(), shell=True)

    def enable_systemd(self):
        service = glob(
            os.path.join(self.dir, 'extra', 'linux-systemd', 'system', 'koozic@.service'))
        output = ''
        with open(service[0], 'r') as f:
            for line in f:
                if line.startswith('ExecStart'):
                    output += 'ExecStart={} -d koozic '.format(os.path.join(self.dir, 'odoo-bin'))
                    if cpu_count() > 1:
                        output += (
                            '--workers={} --limit-time-cpu=1800 --limit-time-real=3600'
                            .format(cpu_count())
                        )
                    output += '\n'
                else:
                    output += '{}'.format(line)

        with open(os.path.join(os.sep, 'etc', 'systemd', 'system', 'koozic@.service'), 'w') as f:
            f.write(output)

        s.call(['systemctl', 'enable', 'koozic@{}.service'.format(self.user)])
        s.call(['systemctl', 'start', 'koozic@{}.service'.format(self.user)])

    def clean_system(self):
        if self._ask_user('Do you want to deactivate the KooZic systemd service? '):
            s.call(['systemctl', 'stop', 'koozic@{}.service'.format(self.user)])
            s.call(['systemctl', 'disable', 'koozic@{}.service'.format(self.user)])
        if self._ask_user('Do you want to drop the KooZic database? '):
            s.call('su - {} -c "dropdb koozic"'.format(self.user), shell=True)

    def clean_files(self):
        to_delete = [
            os.path.expanduser('~{}/.local/share/Odoo'.format(self.user)),
            os.path.join(os.sep, 'etc', 'systemd', 'system', 'koozic@.service'),
            os.path.join(os.sep, 'etc', 'koozic.conf'),
            os.path.join(os.sep, 'usr', 'local', 'bin', 'ffmpeg'),
            self.dir,
        ]
        if self._ask_user(
                'Do you want to delete the following files/folders?\n{}\n'
                .format('\n'.join(to_delete))):
            for dir in to_delete:
                if os.path.isfile(dir):
                    os.remove(dir)
                elif os.path.isdir(dir):
                    rmtree(dir, ignore_errors=True)

    def upgrade(self):
        s.call(['systemctl', 'stop', 'koozic@{}.service'.format(self.user)])
        if self._ask_user(
                'Delete content of folder {} and replace with new sources? '.format(self.dir)):
            rmtree(self.dir, ignore_errors=True)
            self.download_and_extract()
        self.init_koozic()
        s.call(['systemctl', 'start', 'koozic@{}.service'.format(self.user)])

    def install_message(self):
        print("""
  ___           _        _ _       _   _
 |_ _|_ __  ___| |_ __ _| | | __ _| |_(_) ___  _ __
  | || '_ \/ __| __/ _` | | |/ _` | __| |/ _ \| '_ \\
  | || | | \__ \ || (_| | | | (_| | |_| | (_) | | | |
 |___|_| |_|___/\__\__,_|_|_|\__,_|\__|_|\___/|_| |_|
  ____                               __       _ _
 / ___| _   _  ___ ___ ___  ___ ___ / _|_   _| | |
 \___ \| | | |/ __/ __/ _ \/ __/ __| |_| | | | | |
  ___) | |_| | (_| (_|  __/\__ \__ \  _| |_| | |_|
 |____/ \__,_|\___\___\___||___/___/_|  \__,_|_(_)

        """)
        print('You can now connect to http://localhost:8069/.')
        print('Default credentials:')
        print('    Email:    admin')
        print('    Password: admin')

    def _install(self, packages=[]):
        raise NotImplementedError()

    def _pip_install(self, packages=[]):
        if packages:
            s.call(['pip', 'install', '-q'] + packages)

    def _init_koozic_cmd(self):
        return (
            'su - {} -c "{}{}odoo-bin -i oomusic,oovideo -d koozic '
            '--without-demo=all --stop-after-init --log-level=warn"'.format(
                self.user, self.dir, os.sep
            )
        )

    def _ask_user(self, question):
        accepted_answers = ['y', 'n', 'yes', 'no']
        while True:
            ans = input('\n{}(Y/n) '.format(question))
            if ans and ans.lower() not in accepted_answers:
                print('Valid answers are: {}'.format(', '.join(accepted_answers)))
            else:
                return False if ans.lower() in ['n', 'no'] else True


class DriverDeb(Driver):
    def __init__(self, args):
        super().__init__(args)
        self.dep |= set([
            'adduser',
            'build-essential',
            'libtag1-dev',
            'mediainfo',
            'node-less',
            'postgresql',
            'postgresql-client',
            'python',
            'python-dateutil',
            'python-decorator',
            'python-dev',
            'python-docutils',
            'python-feedparser',
            'python-gevent',
            'python-imaging',
            'python-jinja2',
            'python-ldap',
            'python-libxslt1',
            'python-lxml',
            'python-mako',
            'python-mock',
            'python-mutagen',
            'python-openid',
            'python-passlib',
            'python-pip',
            'python-psutil',
            'python-psycogreen',
            'python-psycopg2',
            'python-pybabel',
            'python-pychart',
            'python-pydot',
            'python-pyparsing',
            'python-pypdf',
            'python-reportlab',
            'python-requests',
            'python-setuptools',
            'python-suds',
            'python-tz',
            'python-vatnumber',
            'python-vobject',
            'python-werkzeug',
            'python-wheel',
            'python-xlsxwriter',
            'python-xlwt',
            'python-yaml',
        ])
        self.pip_dep |= set([
            'pytaglib==1.4.1',
        ])

    def _install(self, packages=[]):
        if packages:
            s.call(['apt-get', 'install', '-y', '--no-install-recommends', '-qq'] + packages)


class DriverRpm(Driver):
    def __init__(self, args):
        super().__init__(args)
        self.dep |= set([
            'babel',
            'gcc',
            'gcc-c++',
            'libxslt-python',
            'mediainfo',
            'nodejs-less',
            'redhat-rpm-config',
            'postgresql',
            'postgresql-contrib',
            'postgresql-devel',
            'postgresql-libs',
            'postgresql-server',
            'pychart',
            'pyparsing',
            'python-babel',
            'python-dateutil',
            'python-decorator',
            'python-devel',
            'python-docutils',
            'python-feedparser',
            'python-gevent',
            'python-imaging',
            'python-jinja2',
            'python-ldap',
            'python-lxml',
            'python-mako',
            'python-mock',
            'python-mutagen',
            'python-openid',
            'python-passlib',
            'python-pip',
            'python-psutil',
            'python-psycogreen',
            'python-psycopg2',
            'python-reportlab',
            'python-requests',
            'python-vobject',
            'python-werkzeug',
            'python-xlwt',
            'python-yaml',
            'pytz',
            'taglib-devel',
        ])
        self.pip_dep |= set([
            'ofxparse',
            'pydot',
            'pyPdf',
            'pytaglib==1.4.1',
            'suds',
            'vatnumber',
            'XlsxWriter',
        ])

    def setup_postgresql(self):
        s.call(['systemctl', 'enable', 'postgresql'])
        s.call(['systemctl', 'start', 'postgresql'])
        super().setup_postgresql()

    def clean_system(self):
        super().clean_system()
        if self._ask_user('Do you want to deactivate the PostgreSQL systemd service? '):
            s.call(['systemctl', 'stop', 'postgresql'])
            s.call(['systemctl', 'disable', 'postgresql'])

    def _install(self, packages=[]):
        if packages:
            s.call(['dnf', 'install', '-y', '-q'] + packages)


class DriverUbuntu1604(DriverDeb):
    def __init__(self, args):
        super().__init__(args)


class DriverDebian9(DriverDeb):
    def __init__(self, args):
        super().__init__(args)
        self.dep.discard('python-pypdf')
        self.dep.discard('python-pybabel')
        self.pip_dep.add('pypdf')
        self.pip_dep.add('babel')


class DriverDebian8(DriverDeb):
    def __init__(self, args):
        super().__init__(args)
        self.dep.discard('python-psycogreen')
        self.pip_dep.add('psycogreen')


class DriverFedora27(DriverRpm):
    def setup_postgresql(self):
        s.call(['postgresql-setup', '--initdb', '--unit', 'postgresql'])
        super().setup_postgresql()

    def _init_koozic_cmd(self):
        return super()._init_koozic_cmd()[:-1] + ' --db-template=template0"'


class DriverCentos74(DriverRpm):
    def setup_postgresql(self):
        s.call(['postgresql-setup', 'initdb'])
        super().setup_postgresql()

    def _install(self, packages=[]):
        if packages:
            s.call(['yum', 'install', '-y', '-q'] + packages)


def get_driver(args):
    # Choose OS
    os_choices = OrderedDict()
    os_choices['1'] = ('Ubuntu 16.04', DriverUbuntu1604)
    os_choices['2'] = ('Debian 9', DriverDebian9)
    os_choices['3'] = ('Debian 8 (*)', DriverDebian8)
    os_choices['4'] = ('Fedora 27', DriverFedora27)
    os_choices['5'] = ('CentOS 7.4', DriverCentos74)

    print('Choose your operating system:')
    while True:
        for k, v in os_choices.items():
            print('  {} : {}'.format(k, v[0]))
        print('  0 : exit this installer')
        print('(*) are deprecated OS')

        os_choice = input('Your choice: ')
        if os_choice == '0':
            sys.exit()
        if os_choices.get(os_choice):
            return os_choices[os_choice][1](args)
        else:
            print('\nIncorrect choice! Please choose from the following list:')


def install(args):
    driver = get_driver(args)
    driver.set_config()
    driver.install_dep()
    driver.install_pip_dep()
    driver.setup_postgresql()
    driver.download_and_extract()
    driver.copy_ffmpeg()
    driver.init_koozic()
    driver.enable_systemd()
    driver.install_message()


def uninstall():
    driver = get_driver(args)
    driver.get_config()
    driver.clean_system()
    driver.clean_files()


def upgrade():
    driver = get_driver(args)
    driver.get_config()
    driver.upgrade()


# Only root can run the installer
if os.getuid():
    sys.exit('Please execute this script as root! Exiting...')

# Parse arguments
parser = argparse.ArgumentParser(description='KooZic (un)-installer')
parser.add_argument(
    'mode', choices=['install', 'uninstall', 'upgrade'], help='install or uninstall mode')
parser.add_argument('-u', '--user', default='root', help='user running koozic')
parser.add_argument('-d', '--directory', default='/opt', help='install directory')
args = parser.parse_args()

# Get latest version
url_versions = 'https://raw.githubusercontent.com/DocMarty84/koozic/master/VERSIONS.md'
with urllib.request.urlopen(url_versions) as response:
    version = response.readline()[:-1].decode('utf-8')
    DOWN_URL = DOWN_URL.format(v=version)

if args.mode == 'install':
    # Check directory
    dir = os.path.join(args.directory, 'koozic')
    if os.path.exists(dir):
        sys.exit(
            'Directory {} already exists. Delete this directory of choose another one.'
            .format(dir)
        )
    install(args)

elif args.mode == 'uninstall':
    uninstall()

elif args.mode == 'upgrade':
    upgrade()
