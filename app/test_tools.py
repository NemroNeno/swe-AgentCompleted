import unittest
from tools import *

class TestTools(unittest.TestCase):

    def test_ls(self):

        self.assertAlmostEqual(ls(), """
Current Directory: /

Files: 
matplotlib
scikit-learn
""")