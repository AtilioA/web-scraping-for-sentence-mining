from url_encode_string import url_encode_string
import unittest
import re
import csv


class TestMain(unittest.TestCase):
    def test_url_encode_string1(self):
        with open("test_strings.txt", "r+") as f:
            readCSV = csv.reader(f)
            testingTuples = list(map(tuple, readCSV))
            print(f"Testing {len(testingTuples)} inputs.")
        for testingCase in testingTuples:
            with self.subTest(encodedURL=url_encode_string(testingCase[0][:10]), url=testingCase[1]):  
                encodedURL = url_encode_string(testingCase[0][:15])
                # print(encodedURL)
                # print(testingCase[1])
                self.assertTrue(encodedURL in testingCase[1])

    
unittest.main()
