#! /usr/bin/env python
from setuptools import setup

VERSION = '3.0'

with open("README.md", "rb") as f:
    long_descr = f.read()

def main():
    setup(name='flickrsimplesync',
          version=VERSION,
          description="Sync/backup your photos to flickr easily",
          long_description=open('README.md').read(),
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Programming Language :: Python :: 3',
              'Programming Language :: Python :: 3.5',
              'License :: OSI Approved :: LGPL License',
              'Topic :: Utilities',
              'Topic :: Multimedia :: Graphics',
              'Operating System :: OS Independent'
          ],
          keywords='flickr backup photo sync',
          author='Brent Huisman',
          author_email='mail@brenthuisman.net',
          url='https://github.com/brenthuisman/flickrsimplesync',
          license='LGPL',
          include_package_data=True,
          zip_safe=False,
          install_requires=['flickrapi'],
          packages=['flickrsimplesync'],
          entry_points={
              "console_scripts": ['flickrsimplesync = flickrsimplesync:main'],
          },
          )

if __name__ == '__main__':
    main()
