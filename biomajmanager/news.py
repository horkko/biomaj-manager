"""Utilities to create some news for BioMAJ"""
from __future__ import print_function
from stat import S_ISREG, ST_CTIME, ST_MODE
from biomajmanager.utils import Utils
import os


class News(object):

    """Class for creating news to be displayed for BioMAJ"""

    MAX_NEWS = 5

    def __init__(self, news_dir=None, config=None, max_news=None):
        """
        Initiate object building

        :param news_dir: Path to directory containing templates
        :type news_dir: String
        :param config: Configuration object
        :type config: ConfigParser object
        :param max_news: Number of news to get when displaying then
        :type max_news: int (default 5)
        :return:
        """

        self.news_dir = None
        self.max_news = News.MAX_NEWS
        self.data = None

        if max_news:
            self.max_news = max_news

        if news_dir is not None:
            if not os.path.isdir(news_dir):
                Utils.error("News dir %s is not a directory." % news_dir)
            self.news_dir = news_dir

        if config is not None:
            if not config.has_section('MANAGER'):
                Utils.error("Configuration has no 'MANAGER' section.")
            elif not config.has_option('MANAGER', 'news.dir'):
                Utils.error("Configuration has no 'news.dir' key.")
            else:
                self.news_dir = config.get('MANAGER', 'news.dir')

    def get_news(self, news_dir=None):
        """
        Get the news to be displayed from the specific news.dir directory

        :param news_dir:
        :return: news_files, list of news files found into 'news' directory
        """

        if news_dir is not None:
            if not os.path.isdir(news_dir):
                Utils.error("News dir %s is not a directory" % news_dir)
            else:
                self.news_dir = news_dir
        if not self.news_dir:
            Utils.error("Can't get news, no 'news.dir' defined.")

        news_data = []
        item = 0

        # shamefully copied from
        # http://stackoverflow.com/questions/168409/how-do-you-get-a-directory-listing-sorted-by-creation-date-in-python
        # get all entries in the directory w/ stats
        files = (os.path.join(self.news_dir, file) for file in os.listdir(self.news_dir))
        files = ((os.stat(path), path) for path in files)
        files = ((stat[ST_CTIME], path) for stat, path in files if S_ISREG(stat[ST_MODE]))
        for _, file in sorted(files):
            with open(file) as new:
                (label, date, title) = new.readline().strip().split(':')
                text = ''
                for line in new.readlines():
                    text += line
                news_data.append({'label': label, 'date': date, 'title': title, 'text': text, 'item': item})
                item += 1
                new.close()

        self.data = {'news': news_data}
        return self.data