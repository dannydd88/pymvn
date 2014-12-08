# Representing a maven metadata.xml.


import xml.etree.cElementTree as xml


class Metadata(object):
  def __init__(self, content):
    self.content = content
    self.tree = xml.fromstring(content)

  def GetLastversion(self):
    return self.tree.findtext('versioning/latest')

  @staticmethod
  def Parse(downloader, arti):
    url = '%s/%s/maven-metadata.xml' % (downloader.base, 
                                        arti.Path(with_version=False))
    content = downloader.Get(url, 'Failed to fetch metadata.xml',
                             lambda r: r.read())
    return Metadata(content)


if __name__ == '__main__':
  import artifact, downloader
  arti = artifact.Artifact.Parse('junit:junit:4.2')
  d = downloader.Downloader(base='http://repo1.maven.org/maven2/')
  meta = Metadata.Parse(d, arti)
  print meta.GetLastversion()
