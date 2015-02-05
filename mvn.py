#!/usr/bin/env python

import hashlib
import optparse
import os
import sys

from pymvn import artifact, downloader, pom, utils


class MavenDownloader(downloader.FileDownloader):
  def __init__(self, mvn_server):
    if not mvn_server.endswith('/'):
      mvn_server = mvn_server + '/'
    downloader.Downloader.__init__(self, base=mvn_server)

  def Download(self, options, artifacts):
    for arti in artifacts:
      filename = arti.GetFilename(filepath=options.output_dir,
                                  detailed=options.detailed_path)
      artifact_path = self.base + arti.Path(with_filename=True)
      if not self._VerifyMD5(filename, artifact_path + '.md5'):
        if not options.quite:
          print('Start to fetch %s' % str(arti))
        self.Fetch(artifact_path, filename, options.quite)
      else:
        if not options.quite:
          print('%s is already up to date' % str(arti))
  
  def _VerifyMD5(self, filename, url_path):
    remote_md5 = self.Get(url_path, 'Failed to fetch MD5', lambda r: r.read())
    return utils.VerifyMD5(filename, remote_md5)
  

def DoMain(argv):
  usage = 'Usage: %prog [options] coordinate1 coordinate2 ...'
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('--mvn-server', help='Custom maven server')
  parser.add_option('--output-dir', help='Directory to save downloaded files')
  parser.add_option('--print-only',
                    action='store_true',
                    default=False,
                    help='Only print paths of downloaded files')
  parser.add_option('--detailed-path',
                    action='store_true',
                    default=False,
                    help='Output files with groupId and version in its path')
  parser.add_option('--quite',
                    action='store_true',
                    default=False,
                    help='Do not output logs')

  options, args = parser.parse_args(argv)

  if not len(args):
    utils.PrintWarning('At least input a maven coordinates!')
    parser.print_help()
    return 2

  # prepare downloader.
  mvn_url = 'http://repo1.maven.org/maven2/' if not options.mvn_server \
      else options.mvn_server
  d = MavenDownloader(mvn_url)

  # prepare pending artifacts.
  artifacts = []
  for coordiante in args:
    artifacts.append(artifact.Artifact.Parse(coordiante, downloader=d))

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
