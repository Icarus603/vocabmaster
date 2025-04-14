# Dictation Library
# This package contains all the core functionality for the Dictation testing system

from .base import TestBase
from .bec import BECTest
from .terms import TermsTest
from .diy import DIYTest

__all__ = ['TestBase', 'BECTest', 'TermsTest', 'DIYTest']