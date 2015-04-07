# Downloader.

import os
import sys
import posixpath
import urllib2
import urlparse
import utils


DEFAULT_USER_AGENT = 'pymvn downloader/1.0'


class Downloader(object):
  def __init__(self, user_agent=DEFAULT_USER_AGENT, base=None):
    self.user_agent = user_agent
    # You can init download by giving the base url,
    # So you can invoke apis passing relative url.
    self.base = base

  def _NormalizeURL(self, url):
    if not self.base:
      urlobject = urlparse.urlparse(url)
      if not urlobject.scheme or not urlobject.netloc:
        raise Exception('Because self.base if None, '
                        'Giving url should in form of http[s]://xxx. '
                        'But now is %s' % url)
    joined_url = urlparse.urljoin(self.base, url)
    joined_urlobject = urlparse.urlparse(joined_url)
    normalized_url = urlparse.urlunparse((joined_urlobject.scheme,
                                          joined_urlobject.netloc,
                                          posixpath.normpath(joined_urlobject.path),
                                          joined_urlobject.params,
                                          joined_urlobject.query,
                                          joined_urlobject.fragment))
    #print 'normalized url -- %s' % normalized_url
    return normalized_url

  def Get(self, url, failmsg, func):
    '''Request url by HTTP GET'''
    headers = { 'User-Agent': self.user_agent, }
    request = urllib2.Request(self._NormalizeURL(url), None, headers)
    try:
      response = urllib2.urlopen(request)
    except Exception, e:
      raise Exception('%s because of %s while tried %s' % (failmsg,
                                                           str(e),
                                                           url))
    else:
      return func(response)


class FileDownloader(Downloader):
  def __init__(self, user_agent=DEFAULT_USER_AGENT, base=None):
    Downloader.__init__(self, user_agent, base)

  def Fetch(self, url, filename, quite=False):
    '''Fetch a file according url to filename'''
    dst_dir = os.path.dirname(filename)
    if not os.path.exists(dst_dir):
      utils.MakeDirectory(dst_dir)
    response = self.Get(url, 'Failed to download %s' % url, lambda r: r)

    if response:
      with open(filename, 'wb') as f:
        self._WriteChunks(response, f,
                          report_hook=None if quite else self._ChunkReport)
        if not quite:
          print('Fetched file to %s' % filename)
      return True
    else:
      return False

  def _ChunkReport(self, bytes_so_far, chunk_size, total_size):
    percent = float(bytes_so_far) / total_size
    percent = round(percent * 100, 2)
    sys.stdout.write('Downloaded %d of %d bytes (%0.2f%%)\r' % (bytes_so_far,
                                                                total_size, percent))
    
    if bytes_so_far >= total_size:
      sys.stdout.write('\n')

  def _WriteChunks(self, response, f, chunk_size=8192, report_hook=None):
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    
    while True:
      chunk = response.read(chunk_size)
      bytes_so_far += len(chunk)
      
      if not chunk:
        break
      
      f.write(chunk)
      if report_hook:
        report_hook(bytes_so_far, chunk_size, total_size)
    
    return bytes_so_far


if __name__ == '__main__':
  # Test job
  mvn_url = 'http://repo1.maven.org/maven2'
  metadata = mvn_url + '/junit/junit/maven-metadata.xml'
  metadata_md5 = metadata + '.md5'

  # Test1
  md5 = Downloader().Get(metadata_md5, 'Failed', lambda r: r.read())

  # Test2
  test2_filename = 'test2.xml'
  assert FileDownloader().Fetch(metadata, test2_filename)

  # Test3
  test3_filename = 'test3.xml'
  assert FileDownloader().Fetch(metadata, test3_filename, quite=True)

  # Test4
  md5_2 = Downloader(base='http://repo1.maven.org/maven2/').Get('junit/junit/maven-metadata.xml.md5',
                                                                'Failed',
                                                                lambda r: r.read())
  assert md5 == md5_2

  # Check job.
  import utils
  utils.VerifyMD5(test2_filename, md5)
  utils.VerifyMD5(test3_filename, md5)

  # Remove job.
  import os
  os.remove(test2_filename)
  os.remove(test3_filename)

  print 'Pass'

