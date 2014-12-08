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
               extension=None):
    if not group_id:
      raise ValueError('group_id must be set')
    if not artifact_id:
      raise ValueError('artifact_id must be set')
    
    self.group_id = group_id
    self.artifact_id = artifact_id
    self.version = version
    self.classifier = classifier
    if not extension:
      self.extension = 'jar'
    else:
      self.extension = extension
  
  def IsSnapshot(self):
    return self.version.endswith('SNAPSHOT')
  
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
      assert self.version
      filename = filename + '-' + self.version
    if self.classifier:
      filename = filename + '-' + self.classifier
    return filename + '.' + self.extension
  
  def GetFilename(self, filepath=None):
    filename = self._GenerateFilename()
    if filepath:
      filename = os.path.join(filepath, filename)
    return filename

  def GetPom(self):
    assert self.version
    return self.artifact_id + '-' + self.version + '.pom'
  
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
  def Parse(coordinate):
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
    return Artifact(g, a, v, c, t)


if __name__ == '__main__':
  coordinate1 = 'junit:junit:4.2'
  coordinate2 = 'junit:junit:so:4.2'
  coordinate3 = 'junit:junit:jar:sources:4.2'

  # Test1
  arti1 = Artifact.Parse(coordinate1)
  assert coordinate1 == str(arti1)
  assert 'junit/junit/4.2' == arti1.Path()
  assert 'junit/junit' == arti1.Path(with_version=False)
  assert 'junit/junit/4.2/junit-4.2.jar' == arti1.Path(with_filename=True)
  assert 'junit.jar' == arti1.GetFilename()
  assert '/home/pymvn/junit.jar' == arti1.GetFilename('/home/pymvn/')
  assert 'junit-4.2.pom' == arti1.GetPom()

  # Test2
  arti2 = Artifact.Parse(coordinate2)
  assert coordinate2 == str(arti2)
  assert 'junit/junit/4.2' == arti2.Path()
  assert 'junit/junit' == arti2.Path(with_version=False)
  assert 'junit/junit/4.2/junit-4.2.so' == arti2.Path(with_filename=True)
  assert 'junit.so' == arti2.GetFilename()
  assert '/home/pymvn/junit.so' == arti2.GetFilename('/home/pymvn/')

  # Test3
  arti3 = Artifact.Parse(coordinate3)
  assert coordinate3 == str(arti3)
  assert 'junit/junit/4.2' == arti3.Path()
  assert 'junit/junit' == arti3.Path(with_version=False)
  assert 'junit/junit/4.2/junit-4.2-sources.jar' == arti3.Path(with_filename=True)
  assert 'junit-sources.jar' == arti3.GetFilename()
  assert '/home/pymvn/junit-sources.jar' == arti3.GetFilename('/home/pymvn/')

  print 'Pass'
