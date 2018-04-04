"""Unit tests for scrape_and_push_calendar.py"""

import unittest, sys, os

wdir = os.path.dirname(__file__) # Find the current working directory
sys.path.append("..")
sys.path.append(".")
import scrape_and_push_calendar as ss

class test_metadata(unittest.TestCase):
    """Test for get_title()"""

    exp_result = {
        'title': '',
        'date' : '',
        'time' : '',
        'location' : '',
        'description' : '',
        'created' : '',
        'modified' : '',
        'url' : '',
        'host' : ''
    }
    
    def test_get_title(self):
        self.assertEqual(self.exp_result['title'], '')

    def test_get_date(self):
        self.assertEqual(self.exp_result['date'], '')

    def test_get_time(self):
        self.assertEqual(self.exp_result['time'], '')

    def test_get_location(self):
        self.assertEqual(self.exp_result['location'], '')

    def test_get_description(self):
        self.assertEqual(self.exp_result['description'], '')

    def test_get_created(self):
        self.assertEqual(self.exp_result['created'], '')

    def test_get_modified(self):
        self.assertEqual(self.exp_result['modified'], '')

    def test_get_url(self):
        self.assertEqual(self.exp_result['url'], '')

    def test_get_host(self):
        self.assertEqual(self.exp_result['host'], '')
    
