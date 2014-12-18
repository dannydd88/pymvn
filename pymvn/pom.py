# Representing a maven pom.xml.


import artifact as a
import metadata as m
import xml.etree.cElementTree as xml


POM_NS = '{http://maven.apache.org/POM/4.0.0}'
PROJECT_VERSION = '${project.version}'

IGNORE_DEPENDENCIES = [ 'javax.', 'com.sun.', ]
KNOWN_PACKAGES = [ 'jar', 'war', 'so', 'a', 'zip', 'rar', '7z' ]


def _InIgnoreDependencies(dep):
  for d in IGNORE_DEPENDENCIES:
    if dep.startswith(d):
      return True
  return False


# TODO introduce true tree dependencise analyze & runtime dependencise support
class Pom(object):
  def __init__(self, downloader, content, arti):
    self.downloader = downloader
    self.content = content
    self.this_artifact = arti
    self.tree = xml.fromstring(content)
    self.parent_artifact = self._GetParent()
    self.parent_pom = None
    self._UpdateExtension()

  def _UpdateExtension(self):
    ext = self.tree.findtext('%spackaging' % POM_NS)
    if ext:
      if ext in KNOWN_PACKAGES:
        self.this_artifact.extension = ext
      #else:
      #  print('Packaging[%s] is not in known package list'
      #        ' while parsing %s, ignore it' % (ext, self.this_artifact))

  def _GetProperty(self, p):
    key = '%sproperties/%s%s' % (POM_NS, POM_NS, p)
    value = self.tree.findtext(key)
    if not value:
      if not self.parent_pom:
        self.parent_pom = Pom.Parse(self.downloader, self.parent_artifact)
      value = self.parent_pom._GetProperty(p)
    return value

  def _BuildArtifact(self, tree):
    group_id = tree.findtext('%sgroupId'  % POM_NS)
    artifact_id = tree.findtext('%sartifactId'  % POM_NS)
    version = tree.findtext('%sversion'  % POM_NS)

    if version == PROJECT_VERSION:
      version = self.parent_artifact.version

    arti = a.Artifact(group_id, artifact_id, version)

    # check artifact version
    if not arti.version:
      # try to find out version according metadata.xml
      arti.version = m.Metadata.Parse(self.downloader,
                                      arti).GetLastversion()
    elif arti.version.startswith('${'):
      # property should in form of ${key}
      arti.version = self._GetProperty(arti.version[2:-1])

    #print '%s - %s' % (str(self.this_artifact), str(arti))
    assert arti.version
    return arti

  def _GetParent(self):
    parent = self.tree.findall('%sparent' % POM_NS)
    if len(parent) == 0:
      return None
    elif len(parent) > 1:
      raise Exception('More than one parent?')
    else:
      return self._BuildArtifact(parent[0])

  def _GetCompileDependencies(self, parent_needs):
    parent_str_needs = [str(a) for a in parent_needs] if parent_needs else []
    dep = []
    for d in self.tree.findall('%sdependencies/%sdependency' % (POM_NS,
                                                                POM_NS)):
      scope = d.findtext('%sscope' % POM_NS)
      if scope and scope != 'compile':
        # skip all the dependencise except for 'compile' and None
        continue
      optional = d.findtext('%soptional' % POM_NS)
      if optional and optional == 'true':
        # skip optional dependency
        continue
      pending_arti = self._BuildArtifact(d) 
      if str(pending_arti) not in parent_str_needs and not _InIgnoreDependencies(pending_arti.group_id):
        dep.append(pending_arti)
    return dep

  def GetCompileNeededArtifacts(self, parent_needs=None):
    needs = [ self.this_artifact ]
    for arti in self._GetCompileDependencies(parent_needs):
      needs.extend(Pom.Parse(self.downloader,
                             arti).GetCompileNeededArtifacts(needs))
    return Pom.Slim(needs)

  @staticmethod
  def Parse(downloader, arti):
    url = '%s/%s/%s' % (downloader.base, arti.Path(), arti.GetPom())
    content = downloader.Get(url, 'Failed to fetch pom.xml', lambda r: r.read())
    return Pom(downloader, content, arti)

  @staticmethod
  def Slim(origin_dependencies):
    '''Slim dependencise list by removing duplicate dependency'''
    dependencise = []
    for arti in origin_dependencies:
      match = False
      for new in dependencise:
        if new.group_id == arti.group_id and new.artifact_id == arti.artifact_id:
          if cmp(arti.version, new.version) > 0:
            # Trick: compare version in str,
            #  always use the highest version of dependency.
            new.version = arti.version
          match = True
          break
      if not match:
        dependencise.append(arti)
    return dependencise


if __name__ == '__main__':
  import downloader
  d = downloader.Downloader(base='http://repo1.maven.org/maven2/')

  # Test1
  coordinate1 = 'org.powermock:powermock-core:1.5.5'
  arti1 = a.Artifact.Parse(coordinate1)

  pom1 = Pom.Parse(d, arti1)
  print map(lambda a: str(a), pom1.GetCompileNeededArtifacts())

  # Test2
  coordinate2 = 'org.apache.hive:hive-common:0.13.1'
  #coordinate2 = 'org.apache.httpcomponents:httpcomponents-core:4.1.3'
  arti2 = a.Artifact.Parse(coordinate2)
  pom2 = Pom.Parse(d, arti2)
  print map(lambda a: str(a), pom2.GetCompileNeededArtifacts())
