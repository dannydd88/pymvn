#!/usr/bin/env python

import hashlib
import optparse
import os
import sys

from pymvn import utils
from pymvn.artifact import Artifact
from xml import etree
from urllib2 import Request, urlopen, URLError, HTTPError


# TODO add dependency analyze.
class MavenDownloader:
  def __init__(self, base=None):
    if not base:
      base = 'http://repo1.maven.org/maven2'
    if base.endswith('/'):
      base = base.rstrip('/')
    self.base = base
    self.user_agent = 'Maven Artifact Downloader/1.0'
  
  def _find_latest_version_available(self, artifact):
    path = '/%s/maven-metadata.xml' % (artifact.path(False))
    xml = self._request(self.base + path,
                        'Failed to download maven-metadata.xml',
                        lambda r: etree.parse(r))
    v = xml.xpath('/metadata/versioning/versions/version[last()]/text()')
    if v:
      return v[0]
  
  def find_uri_for_artifact(self, artifact):
    if artifact.is_snapshot():
      path = '/%s/maven-metadata.xml' % (artifact.path())
      print path
      xml = self._request(self.base + path, 'Failed to download maven-metadata.xml', lambda r: etree.parse(r))
      basexpath = '/metadata/versioning/'
      p = xml.xpath(basexpath + '/snapshotVersions/snapshotVersion')
      if p:
        return self._find_matching_artifact(p, artifact)
    else:
      return self._uri_for_artifact(artifact)
  
  def _find_matching_artifact(self, elems, artifact):
    filtered = filter(lambda e: e.xpath('extension/text() = "%s"' % artifact.extension), elems)
    if artifact.classifier:
      filtered = filter(lambda e: e.xpath('classifier/text() = "%s"' % artifact.classifier), elems)
    
    if len(filtered) > 1:
      print('There was more than one match. Selecting the first one. Try adding a classifier to get a better match.')
    elif not len(filtered):
      print('There were no matches.')
      return None
    
    elem = filtered[0]
    value = elem.xpath('value/text()')
    return self._uri_for_artifact(artifact, value[0])
  
  def _uri_for_artifact(self, artifact, version=None):
    if artifact.is_snapshot() and not version:
      raise ValueError('Expected uniqueversion for snapshot artifact ' + str(artifact))
    elif not artifact.is_snapshot():
      version = artifact.version
    if artifact.classifier:
      return self.base + '/' + artifact.path() + '/' + artifact.artifact_id + '-' + version + '-' + artifact.classifier + '.' + artifact.extension
    return self.base + '/' + artifact.path() + '/' + artifact.artifact_id + '-' + version + '.' + artifact.extension
  
  def _request(self, url, failmsg, f):
    headers = {'User-Agent': self.user_agent}
    req = Request(url, None, headers)
    try:
      response = urlopen(req)
    except HTTPError, e:
      print(failmsg + ' because of ' + str(e))
      print('Tried url ' + url)
    except URLError, e:
      print(failmsg + ' because of ' + str(e))
      print('Tried url ' + url)
    else:
      return f(response)
  
  
  def download(self, artifact, filename=None):
    filename = artifact.get_filename(filename)
    if not artifact.version:
      artifact = Artifact(artifact.groupId,
                          artifact.artifactId,
                          self._find_latest_version_available(artifact),
                          artifact.classifier,
                          artifact.extension)
    
    url = self.find_uri_for_artifact(artifact)
    if not self.verify_md5(filename, url + '.md5'):
      print('Downloading artifact ' + str(artifact))
      response = self._request(url,
                               'Failed to download artifact ' + str(artifact),
                               lambda r: r)
      if response:
        with open(filename, 'wb') as f:
          #f.write(response.read())
          self._write_chunks(response, f, report_hook=self.chunk_report)
        print('Downloaded artifact %s to %s' % (artifact, filename))
        return True
      else:
        return False
    else:
      print('%s is already up to date' % artifact)
      return True
  
  def chunk_report(self, bytes_so_far, chunk_size, total_size):
    percent = float(bytes_so_far) / total_size
    percent = round(percent*100, 2)
    sys.stdout.write('Downloaded %d of %d bytes (%0.2f%%)\r' % (bytes_so_far,
                                                                total_size, percent))
    
    if bytes_so_far >= total_size:
      sys.stdout.write('\n')
  
  def _write_chunks(self, response, file, chunk_size=8192, report_hook=None):
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    
    while True:
      chunk = response.read(chunk_size)
      bytes_so_far += len(chunk)
      
      if not chunk:
        break
      
      file.write(chunk)
      if report_hook:
        report_hook(bytes_so_far, chunk_size, total_size)
    
    return bytes_so_far
  
  def verify_md5(self, file, remote_md5):
    if not os.path.exists(file):
      return False
    else:
      local_md5 = self._local_md5(file)
      remote = self._request(remote_md5, 'Failed to download MD5', lambda r: r.read())
      return local_md5 == remote
  
  def _local_md5(self, file):
    md5 = hashlib.md5()
    with open(file, 'rb') as f:
      for chunk in iter(lambda: f.read(8192), ''):
        md5.update(chunk)
    return md5.hexdigest()


def DoFetch(options, artifacts):
  downloader = MavenDownloader(options.mvn_server)
  for artifact in artifacts:
    downloader.download(artifact, options.output_dir)


def DoMain(argv):
  usage = 'Usage: %prog [options] coordinate1 coordinate2 ...'
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('--mvn-server', help='Custom maven server')
  parser.add_option('--output-dir', help='Directory to save downloaded files')
  parser.add_option('--print-only',
                    action='store_true',
                    default=False,
                    help='Only print paths of downloaded files')

  options, args = parser.parse_args(argv)

  if not len(args):
    utils.PrintWarning('At least input a maven coordinates!')
    parser.print_help()
    return 2

  artifacts = []
  for coordiante in args:
    artifacts.append(Artifact.parse(coordiante))

  if options.print_only:
    utils.CheckOptions(options, parser, required=['output_dir'])
    return ' '.join([artifact.get_filename(options.output_dir) for artifact in artifacts])
  
  DoFetch(options, artifacts)


if __name__ == '__main__':
  sys.exit(DoMain(sys.argv[1:]))
