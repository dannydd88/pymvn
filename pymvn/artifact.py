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
  def __init__(self, group_id, artifact_id, version, classifier=None, extension=None):
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
  
  def is_snapshot(self):
    return self.version.endswith('SNAPSHOT')
  
  def path(self, with_version=True):
    base = self.group_id.replace('.', '/') + '/' + self.artifact_id
    if with_version:
      return base + '/' + self.version
    else:
      return base
  
  def _generate_filename(self):
    if not self.classifier:
      return self.artifact_id + '.' + self.extension
    else:
      return self.artifact_id + '-' + self.classifier + '.' + self.extension
  
  def get_filename(self, filename=None):
    if not filename:
      filename = self._generate_filename()
    elif os.path.isdir(filename):
      filename = os.path.join(filename, self._generate_filename())
    return filename
  
  def __str__(self):
    if self.classifier:
      return '%s:%s:%s:%s:%s' % (self.group_id, self.artifact_id, self.extension, self.classifier, self.version)
    elif self.extension != 'jar':
      return '%s:%s:%s:%s' % (self.group_id, self.artifact_id, self.extension, self.version)
    else:
      return '%s:%s:%s' % (self.group_id, self.artifact_id, self.version)
  
  @staticmethod
  def parse(input):
    parts = input.split(':')
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
