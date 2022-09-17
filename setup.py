'''
Modified from https://www.delftstack.com/howto/python/python-setup.py/ on 8/31/2022
'''

from setuptools import setup

setup(
   name='rowing',
   version='1.0',
   description='Rowing related functions.',
   author='Dan Knorr',
   packages=['rowing'],  # would be the same as name
#    install_requires=['wheel', 'bar', 'greek'], #external packages acting as dependencies
)
