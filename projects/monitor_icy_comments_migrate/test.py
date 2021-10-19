import unittest
from monitor_icy_comments_migrate.page.catch_tmall_comments import CatchTmallComments
from monitor_icy_comments_migrate.page.catch_taobao_comments import CatchTaoBaoComments
from monitor_icy_comments_migrate.page.catch_jd_comments import CatchJDComments


class Test(unittest.TestCase):
    def test_catch_taobao_comments(self):
        assert CatchTaoBaoComments('575813096566', '0827S00896').test()

    def test_catch_tmall_comments(self):
        assert CatchTmallComments('557543747654', '05473L0709').test()

    def test_catch_jd_comments(self):
        assert CatchJDComments('10663174783', '05473L0709').test()


if __name__ == '__main__':
    unittest.main()
