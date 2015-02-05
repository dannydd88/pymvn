# Representing a maven metadata.xml.


import xml.etree.cElementTree as xml


class Metadata(object):
  def __init__(self, content, arti):
    self.content = content
    self.tree = xml.fromstring(content)
    self.arti = arti

  def GetLastversion(self):
    if self.arti.IsSnapshot():
      version = self.arti.GetSnapshotVersion()
      timestamp = self.tree.findtext('versioning/snapshot/timestamp')
      build_number = self.tree.findtext('versioning/snapshot/buildNumber')
      return version + timestamp + '-' + build_number

    # not snapshot
    return self.tree.findtext('versioning/latest')

  @staticmethod
  def Parse(downloader, arti):
    is_snapshot = arti.IsSnapshot()
    url = '%s/%s/maven-metadata.xml' % (downloader.base,
                                        arti.Path(with_version=is_snapshot))
    content = downloader.Get(url, 'Failed to fetch metadata.xml',
                             lambda r: r.read())
    return Metadata(content, arti)


if __name__ == '__main__':
  import artifact, downloader
  arti1 = artifact.Artifact.Parse('junit:junit:4.2')
  d1 = downloader.Downloader(base='http://repo1.maven.org/maven2/')
  meta = Metadata.Parse(d1, arti1)
  print meta.GetLastversion()

  # self server test.
  d2 = downloader.Downloader(
      base='http://10.1.73.82:8081/nexus/content/groups/public/')
  arti2 = artifact.Artifact.Parse('com.octopus:server:0.1.0-SNAPSHOT', d2)
  meta = Metadata.Parse(d2, arti2)
  print meta.GetLastversion()
