#!/usr/bin/env python

import argparse
import hashlib
import os
import sys

from pymvn import artifact, downloader, pom, utils


def _http_fetcher():
  from pymvn import http_fetcher as hf
  return hf.HttpFetcher()


def _s3_fetcher():
  try:
    from pymvn import s3_fetcher as sf
  except ImportError:
    raise Exception('show install boto3 while using aws feature')
  return sf.S3Fetcher()


class MavenDownloader(downloader.FileDownloader):
  def __init__(self, mvn_server):
    # ). parse url scheme to find fetcher
    import urlparse
    urlobject = urlparse.urlparse(mvn_server)

    # ). decide fetcher
    fetcher = {
          's3': lambda : _s3_fetcher(),
          'http': lambda : _http_fetcher(),
          'https': lambda : _http_fetcher(),
        }[urlobject.scheme]()

    downloader.FileDownloader.__init__(self, fetcher=fetcher, base=mvn_server)

  def Download(self, options, artifacts):
    for arti in artifacts:
      self.DoDownload(options, arti)
      if options.with_sources:
        sources_arti = arti.GenerateSourcesJarArtifact()
        if sources_arti is None:
          continue
        self.DoDownload(options, sources_arti, raise_when_fail=False)

  def DoDownload(self, options, arti, raise_when_fail=True):
    filename = arti.GetFilename(filepath=options.output_dir,
                                detailed=options.detailed_path)
    artifact_path = '{}/{}'.format(self.base, arti.Path(with_filename=True))
    try:
      if not self._VerifyMD5(filename, artifact_path + '.md5'):
        if not options.quite:
          print('Start to fetch %s' % str(arti))
        self.Fetch(artifact_path, filename, options.quite)
      else:
        if not options.quite:
          print('%s is already up to date' % str(arti))
    except Exception as e:
      if raise_when_fail:
        raise e
      elif not options.quite:
        print('%s fetch error, skip' % str(arti))
  
  def _VerifyMD5(self, filename, url_path):
    remote_md5 = self.Get(url_path, 'Failed to fetch MD5', lambda r: r.read())
    return utils.VerifyMD5(filename, remote_md5)
  

def DoMain(argv):
  description = 'Fetch binary according maven coordinate protocol.'
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('--mvn-server', help='Custom maven server')
  parser.add_argument('--output-dir',
                      required=True,
                      help='Directory to save downloaded files')
  parser.add_argument('--print-only',
                      action='store_true',
                      default=False,
                      help='Only print paths of downloaded files')
  parser.add_argument('--detailed-path',
                      action='store_true',
                      default=False,
                      help='Output files with groupId and version in its path')
  parser.add_argument('--with-sources',
                      action='store_true',
                      default=False,
                      help='Try to download sources too')
  parser.add_argument('--quite',
                      action='store_true',
                      default=False,
                      help='Do not output logs')
  parser.add_argument('coordinate',
                      nargs='+',
                      help='Maven coordinate')

  options = parser.parse_args(argv)

  # prepare downloader.
  mvn_url = 'http://repo1.maven.org/maven2/' if not options.mvn_server \
      else options.mvn_server
  d = MavenDownloader(mvn_url)

  # prepare pending artifacts.
  artifacts = []
  for coordinate in options.coordinate:
    artifacts.append(artifact.Artifact.Parse(coordinate, downloader=d))

  # parse all dependencise according coordinate inputs.
  download_artifacts = []
  for arti in artifacts:
    p = pom.Pom.Parse(d, arti)
    download_artifacts.extend(p.GetCompileNeededArtifacts())

  # slim the all in one dependencise list, we know we are doing here!
  download_artifacts = pom.Pom.Slim(download_artifacts, artifacts)

  if options.print_only:
    utils.CheckOptions(options, parser, required=['output_dir'])
    return ' '.join([arti.GetFilename(filepath=options.output_dir,
                                      detailed=options.detailed_path) \
                     for arti in download_artifacts])
  
  d.Download(options, download_artifacts) 


if __name__ == '__main__':
  sys.exit(DoMain(sys.argv[1:]))
