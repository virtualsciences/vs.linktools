from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='vs.linktools',
      version=version,
      description="Library to find and fix dead links and files in a Plone site.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['vs'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'vs.uidfixer',
          'vs.deadfiles',
          'vs.plonehtml',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
