# Representing a maven artifact defined by:
#   http://maven.apache.org/pom.html#Maven_Coordinates


import os


class Artifact(object):
  '''
    The possible options are:
    - groupId:artifactId:version
    - groupId:artifactId:packaging:version
    - groupId:artifactId:packaging:classifier:version
  '''
  def __init__(self, group_id, artifact_id, version,
               classifier=None,
               extension=None,
               snapshot_version=None):
    if not group_id:
      raise ValueError('group_id must be set')
    if not artifact_id:
      raise ValueError('artifact_id must be set')
    
    self.group_id = group_id
    self.artifact_id = artifact_id
    self.version = version
    self.snapshot_version = snapshot_version
    self.classifier = classifier
    if not extension:
      self.extension = 'jar'
    else:
      self.extension = extension

  def GenerateSourcesJarArtifact(self):
    if self.extension != 'jar':
      return None
    if self.classifier == 'sources':
      return self
    arti = Artifact(self.group_id,
                    self.artifact_id,
                    self.version,
                    classifier='sources',
                    extension=self.extension,
                    snapshot_version=self.snapshot_version)
    return arti

  def IsSnapshot(self):
    return self.version.endswith('SNAPSHOT') if self.version else False

  def GetSnapshotVersion(self):
    assert self.IsSnapshot()
    return self.version[:self.version.find('SNAPSHOT')]

  def Path(self, with_version=True, with_filename=False):
    path = self.group_id.replace('.', '/') + '/' + self.artifact_id
    if with_version:
      path = path + '/' + self.version
    if with_filename:
      path = path + '/' + self._GenerateFilename(True)
    return path

  def _GenerateFilename(self, with_version=False):
    filename = self.artifact_id
    if with_version:
      v = self.version if not self.IsSnapshot() else self.snapshot_version
      assert v
      filename = filename + '-' + v
    if self.classifier:
      filename = filename + '-' + self.classifier
    return filename + '.' + self.extension

  def GetFilename(self, filepath=None, detailed=False):
    filename = self._GenerateFilename()
    if filepath:
      filename = os.path.join(filepath, filename)
    if detailed:
      filename = os.path.join(os.path.dirname(filename),
                              self.group_id.replace('.', '/'),
                              self.version,
                              os.path.basename(filename))
    return filename

  def GetPom(self):
    v = self.version if not self.IsSnapshot() else self.snapshot_version
    assert v
    return self.artifact_id + '-' + v + '.pom'

  def ArtifactEquel(self, other):
    return self.group_id == other.group_id \
        and self.artifact_id == other.artifact_id \
        and self.extension == other.extension \
        and self.classifier == other.classifier
  
  def __str__(self):
    if self.classifier:
      return '%s:%s:%s:%s:%s' % (self.group_id,
                                 self.artifact_id,
                                 self.extension,
                                 self.classifier,
                                 self.version)
    elif self.extension != 'jar':
      return '%s:%s:%s:%s' % (self.group_id,
                              self.artifact_id,
                              self.extension,
                              self.version)
    else:
      return '%s:%s:%s' % (self.group_id, self.artifact_id, self.version)

  @staticmethod
  def Parse(coordinate, downloader=None):
    parts = coordinate.split(':')
    assert len(parts) >= 3
    g = parts[0]
    a = parts[1]
    v = parts[len(parts) - 1]
    t = None
    c = None
    if len(parts) == 4:
      t = parts[2]
    if len(parts) == 5:
      t = parts[2]
      c = parts[3]
    arti = Artifact(g, a, v, c, t)
    if arti.IsSnapshot():
      # handle snapshot version
      assert downloader
      import metadata
      meta = metadata.Metadata.Parse(downloader, arti)
      arti.snapshot_version = meta.GetLastversion()
    return arti


if __name__ == '__main__':
  # Test1
  coordinate1 = 'junit:junit:4.2'
  arti1 = Artifact.Parse(coordinate1)
  assert coordinate1 == str(arti1)
  assert 'junit/junit/4.2' == arti1.Path()
  assert 'junit/junit' == arti1.Path(with_version=False)
  assert 'junit/junit/4.2/junit-4.2.jar' == arti1.Path(with_filename=True)
  assert 'junit.jar' == arti1.GetFilename()
  assert '/home/pymvn/junit.jar' == arti1.GetFilename(filepath='/home/pymvn/')
  assert 'junit/4.2/junit.jar' == arti1.GetFilename(detailed=True)
  assert '/home/pymvn/junit/4.2/junit.jar' == arti1.GetFilename(filepath='/home/pymvn/',
                                                                detailed=True)
  assert 'junit-4.2.pom' == arti1.GetPom()
  assert 'junit:junit:jar:sources:4.2' == str(arti1.GenerateSourcesJarArtifact())

  # Test2
  coordinate2 = 'junit:junit:so:4.2'
  arti2 = Artifact.Parse(coordinate2)
  assert coordinate2 == str(arti2)
  assert 'junit/junit/4.2' == arti2.Path()
  assert 'junit/junit' == arti2.Path(with_version=False)
  assert 'junit/junit/4.2/junit-4.2.so' == arti2.Path(with_filename=True)
  assert 'junit.so' == arti2.GetFilename()
  assert '/home/pymvn/junit.so' == arti2.GetFilename(filepath='/home/pymvn/')
  assert 'junit/4.2/junit.so' == arti2.GetFilename(detailed=True)
  assert '/home/pymvn/junit/4.2/junit.so' == arti2.GetFilename(filepath='/home/pymvn/',
                                                               detailed=True)

  # Test3
  coordinate3 = 'junit:junit:jar:sources:4.2'
  arti3 = Artifact.Parse(coordinate3)
  assert coordinate3 == str(arti3)
  assert 'junit/junit/4.2' == arti3.Path()
  assert 'junit/junit' == arti3.Path(with_version=False)
  assert 'junit/junit/4.2/junit-4.2-sources.jar' == arti3.Path(with_filename=True)
  assert 'junit-sources.jar' == arti3.GetFilename()
  assert '/home/pymvn/junit-sources.jar' == arti3.GetFilename(filepath='/home/pymvn/')
  assert 'junit/4.2/junit-sources.jar' == arti3.GetFilename(detailed=True)
  assert '/home/pymvn/junit/4.2/junit-sources.jar' == arti3.GetFilename(filepath='/home/pymvn/',
                                                                        detailed=True)
  assert 'junit:junit:jar:sources:4.2' == str(arti3.GenerateSourcesJarArtifact())

  # Test compare
  assert arti1.ArtifactEquel(arti1)
  assert arti2.ArtifactEquel(arti2)
  assert arti3.ArtifactEquel(arti3)
  assert not arti1.ArtifactEquel(arti2)
  assert not arti1.ArtifactEquel(arti3)
  assert not arti2.ArtifactEquel(arti3)

  # Test snapshot
  import downloader
  d = downloader.Downloader(
      base='http://100.84.73.82:8081/nexus/content/groups/public/')
  coordinate_snapshot = 'com.octopus:octopus-server:0.5.0-SNAPSHOT'
  arti_snapshot = Artifact.Parse(coordinate_snapshot, d)
  assert arti_snapshot.IsSnapshot() == True
  print arti_snapshot.GetSnapshotVersion()
  print arti_snapshot.snapshot_version
  print arti_snapshot.GetPom()
  print arti_snapshot.Path(with_version=True, with_filename=True)
  arti_sources_snapshot = arti_snapshot.GenerateSourcesJarArtifact() 
  assert arti_sources_snapshot.IsSnapshot() == True
  print str(arti_sources_snapshot)
  print arti_sources_snapshot.GetSnapshotVersion()
  print arti_sources_snapshot.snapshot_version
  print arti_sources_snapshot.GetPom()
  print arti_sources_snapshot.Path(with_version=True, with_filename=True)

  print 'Pass'
