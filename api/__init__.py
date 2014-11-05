"""
REST API for OSPy
"""

__author__ = [
    'Teodor Yantcheff',
]

__version__ = '0.9 aplha'

from api import urls, app_OSPyAPI
from errors import unauthorized, badrequest, notacceptable