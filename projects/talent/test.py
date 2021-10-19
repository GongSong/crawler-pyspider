import unittest
from talent.page.upload_to_ai import UploadToAi


class Test(unittest.TestCase):
    def test_upload_to_ai(self):
        assert UploadToAi('crawler/table/talent/蔻特信息/2018-12-10--2019-01-08.xls').test()


if __name__ == '__main__':
    unittest.main()
