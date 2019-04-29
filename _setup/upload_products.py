from __future__ import print_function
from __future__ import unicode_literals
from distutils.core import Command
import os

__all__ = ["upload_products"]

class upload_products(Command):
    description = "upload FiPy compressed archives to website(s)"
    
    user_options = [('pdf', None, "upload the PDF variant of the documentation"),
                    ('html', None, "upload the HTML variant of the documentation"),
                    ('tarball', None, "upload the .tar.gz source distribution"),
                    ('winzip', None, "upload the .win32.zip distribution"),
                   ]

    def initialize_options (self):
        self.pdf = 0
        self.html = 0
        self.tarball = 0
        self.winzip = 0

    def finalize_options (self):
        pass

    def run(self):
        if self.pdf:
            print("setting permissions of manual...")
            os.system('chmod -R g+w documentation/_build/latex/fipy.pdf')
            
            print("linking manual to `dist/`...")
            os.system('mkdir dist/')
            os.system('ln -f documentation/_build/latex/fipy.pdf dist/fipy-%s.pdf'%self.distribution.metadata.get_version())
            
        if self.html:
            print("setting group and ownership of web pages...")
            os.system('chmod -R g+w documentation/_build/html/')
            
            print("uploading web pages...")
            # The -t flag (implicit in -a) is suddenly causing problems
            # os.system('rsync -aLC -e ssh %s %s'%('documentation/www/', os.environ['FIPY_WWWHOST']))
            os.system('rsync -rlpgoDLC -e ssh %s %s' % ('documentation/_build/html/', os.environ['FIPY_WWWHOST']))

        if self.tarball:
            file = 'dist/FiPy-%s.tar.gz' % self.distribution.metadata.get_version()
            print("setting permissions for %s ..." % file)
            os.system('chmod -R g+w %s' % file)

            print("uploading tarball...")
            os.system('rsync -pgoDLC -e ssh %s %s/download/' % (file, os.environ['FIPY_WWWHOST']))

        if self.winzip:
            file = 'dist/FiPy-%s.win32.zip' % self.distribution.metadata.get_version()
            print("setting permissions for %s ..." % file)
            os.system('chmod -R g+w %s' % file)
            
            print("uploading winzip...")
            os.system('rsync -pgoDLC -e ssh %s %s/download/' % (file, os.environ['FIPY_WWWHOST']))

        if self.pdf or self.tarball or self.winzip:
            print("activating web pages...")
            os.system(os.environ['FIPY_WWWACTIVATE'])
