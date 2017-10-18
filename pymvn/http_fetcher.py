# http fetcher

import downloader as d
import urllib2


DEFAULT_USER_AGENT = 'pymvn downloader/1.0'


class HttpFetcher(d.Fetcher):
  def __init__(self, user_agent=DEFAULT_USER_AGENT):
    self.user_agent = user_agent

  def Fetch(self, url, failmsg):
    '''Request url by HTTP GET'''
    headers = { 'User-Agent': self.user_agent, }
    request = urllib2.Request(url, None, headers)
    try:
      return urllib2.urlopen(request)
    except Exception, e:
      raise Exception('%s because of %s while tried %s' % (failmsg,
                                                           str(e),
                                                           url))
