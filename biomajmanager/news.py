"""Utilities to create some news for BioMAJ"""
from __future__ import print_function
from stat import S_ISREG, ST_CTIME, ST_MODE
from biomajmanager.utils import Utils
from biomajmanager.manager import Manager
from rfeed import *
from datetime import datetime
import os
import sys


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
            Utils.verbose("[news] 'news_dir' set from %s" % str(news_dir))
            if not os.path.isdir(news_dir):
                Utils.error("News dir %s is not a directory." % news_dir)
            self.news_dir = news_dir

        if config is not None:
            if not config.has_section('NEWS'):
                Utils.error("Configuration has no 'NEWS' section.")
            elif not config.has_option('NEWS', 'news.dir'):
                Utils.error("Configuration has no 'news.dir' key.")
            else:
                self.news_dir = config.get('NEWS', 'news.dir')
        Utils.verbose("[news] 'news_dir' set to %s" % str(self.news_dir))

    def get_news(self, news_dir=None, reverse=True):
        """
        Get the news to be displayed from the specific news.dir directory

        :param news_dir: Path to news directory
        :type news_dir: str
        :param reverse: Reverse list of news files, default True
        :type reverse: bool
        :return: news_files, list of news files found into 'news' directory
        :rtype: list
        :raises SystemExit: If path 'news_dir' does not exist
                            If 'news_dir' not set
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
        #files = ((os.stat(path), path) for path in files)
        #files = ((stat[ST_CTIME], path) for stat, path in files if S_ISREG(stat[ST_MODE]))
        #for _, ifile in sorted(files):
        for ifile in sorted(files):
            with open(ifile) as new:
                Utils.verbose("[news] Reading news file %s ..." % ifile)
                (label, date, title) = new.readline().strip().split(':')
                text = ''
                for line in new.readlines():
                    text += line
                news_data.append({'label': label, 'date': date, 'title': title, 'text': text, 'item': item})
                item += 1
                new.close()
        if reverse:
            Utils.verbose("Reversing news list ...")
            news_data.reverse()
        self.data = {'news': news_data}
        return self.data


class RSS(News):

    """Class for generating RSS feed from news files"""

    def __init__(self, rss_file=None, *args, **kwargs):
        """
        Initiate object building

        :return:
        """
        super(RSS, self).__init__(*args, **kwargs)
        self.rss_file = None
        self.fh = None
        if rss_file is not None:
            self.rss_file = rss_file
        elif 'config' in kwargs:
            self.config = kwargs['config']
            if self.config.has_option('RSS', 'rss.file'):
                self.rss_file = self.config.get('RSS', 'rss.file')
        if self.rss_file is None:
            self.fh = sys.stdout
        Utils.verbose("[rss] rss_file set to %s" % str(self.rss_file))

    def generate_rss(self, rss_file=None, data=None):
        """
        Generate RSS file from news

        :param rss_file: Path to file rss.xml
        :type rss_file: String
        :param data: Data to create RSS from
        :type data: Dict data['news'] = { ... }
        :return: Boolean
        """
        if rss_file is not None:
            Utils.verbose("[rss] rss_file set to %s" % rss_file)
            self.rss_file = rss_file

        if data is None:
            data = self.get_news()
        elif 'news' not in data:
            Utils.error("Could not find 'news' key in data")
        if len(data['news']) == 0:
            Utils.verbose("No data to display")
            return True

        items = []
        for new in data['news']:
            item = Item(title=new['title'],
                        description=new['text'],
                        author=self.config.get('RSS', 'feed.author'),
                        guid=Guid(self.config.get('RSS', 'feed.news.link') + '#' + str(new['item'])),
                        pubDate=datetime.strptime(new['date'], self.config.get('RSS', 'rss.date.format')
                                                                           .replace('%%', '%'))
                        )
            items.append(item)
        feed = Feed(title=self.config.get('RSS', 'feed.title'),
                    link=self.config.get('RSS', 'feed.link'),
                    description=self.config.get('RSS', 'feed.description'),
                    language=self.config.get('RSS', 'feed.language'),
                    lastBuildDate=datetime.now(),
                    items=items)
        if self.fh is None:
            try:
                self.fh = open(self.rss_file, 'w')
            except (OSError, IOError) as err:
                Utils.error("Can't open file %s: %s" % (self.rss_file, str(err)))
        print(feed.rss(), file=self.fh)
        if self.rss_file is not None:
            self.fh.close()
        return True
