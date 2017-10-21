# Downloader.

import os
import sys
import posixpath
import urlparse
import utils


class Fetcher(object):
  def __init__(self):
    pass

  def Fetch(self, url):
    pass


class Downloader(object):
  def __init__(self, fetcher, base=None):
    self.fetcher = fetcher
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
    formated_url = self._NormalizeURL(url)
    response = self.fetcher.Fetch(formated_url, failmsg)
    return func(response)


class FileDownloader(Downloader):
  def __init__(self, fetcher, base=None):
    Downloader.__init__(self, fetcher, base)

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

  def _ChunkReport(self, bytes_so_far, chunk_size):
    sys.stdout.write('Downloaded {} bytes\r'.format(bytes_so_far))

  def _WriteChunks(self, response, f, chunk_size=8192, report_hook=None):
    bytes_so_far = 0
    
    while True:
      chunk = response.read(chunk_size)
      bytes_so_far += len(chunk)
      
      if not chunk:
        if report_hook:
          print('\n')
        break
      
      f.write(chunk)
      if report_hook:
        report_hook(bytes_so_far, chunk_size)
    
    return bytes_so_far


if __name__ == '__main__':
  import http_fetcher as hf

  # Test job
  mvn_url = 'http://repo1.maven.org/maven2'
  metadata = mvn_url + '/junit/junit/maven-metadata.xml'
  metadata_md5 = metadata + '.md5'

  # Test1
  md5 = Downloader(hf.HttpFetcher()).Get(metadata_md5, 'Failed', lambda r: r.read())

  # Test2
  test2_filename = 'test2.xml'
  assert FileDownloader(hf.HttpFetcher()).Fetch(metadata, test2_filename)

  # Test3
  test3_filename = 'test3.xml'
  assert FileDownloader(hf.HttpFetcher()).Fetch(metadata, test3_filename, quite=True)

  # Test4
  md5_2 = Downloader(hf.HttpFetcher(), base='http://repo1.maven.org/maven2/').Get('junit/junit/maven-metadata.xml.md5',
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

  import s3_fetcher as sf
  target_url = 's3://ap-southeast-1.elasticmapreduce.samples/cloudfront/code/Hive_CloudFront.q'

  # Test1
  payload = Downloader(sf.S3Fetcher()).Get(target_url, 'Failed', lambda r: r.read())
  print payload

  print 'Pass'
