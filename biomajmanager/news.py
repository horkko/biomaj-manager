from __future__ import print_function
from stat import S_ISREG, ST_CTIME, ST_MODE
from biomajmanager.utils import Utils
import os


class News(object):
    '''

    '''

    MAX_NEWS = 5

    def __init__(self, news_dir=None, config=None, max_news=None):
        '''

        :param news_dir:
        :param config:
        :param max_new:
        :return:
        '''

        self.news_dir = None
        if max_news:
            self.max_news = max_news
        else:
            self.max_news = News.MAX_NEWS

        if news_dir is not None:
            if not os.path.isdir(news_dir):
                Utils.error("News dir %s is not a directory" % news_dir)
            self.news_dir = news_dir
        if config is not None:
            if not config.has_section('MANAGER'):
                Utils.error("Configuration has no 'MANAGER' section")
            else:
                self.news_dir = config.get('MANAGER', 'news_dir')
        if max_news is not None:
            self.max_news = max_news
        self.data = None


    def get_news(self, news_dir=None):
        '''

        :param news_dir:
        :return: news_files, list of news files found into 'news' directory
        '''

        if news_dir is not None:
            if not os.path.isdir(news_dir):
                Utils.error("News dir %s is not a directory" % news_dir)
            else:
                self.news_dir = news_dir

        news_data = []
        item = 0

        # shamefully copied from
        # http://stackoverflow.com/questions/168409/how-do-you-get-a-directory-listing-sorted-by-creation-date-in-python
        # get all entries in the directory w/ stats
        files = (os.path.join(self.news_dir, file) for file in os.listdir(self.news_dir))
        files = ((os.stat(path), path) for path in files)
        files = ((stat[ST_CTIME], path) for stat, path in files if S_ISREG(stat[ST_MODE]))
        for time, file in sorted(files):
            with open(file) as new:
                (type, date, title) = new.readline().strip().split(':')
                text = ''
                for line in new.readlines():
                    text += line
                news_data.append({'type': type, 'date': date, 'title': title, 'text': text, 'item': item})
                item += 1
                new.close()

        self.data = {'news': news_data}
        return self.data