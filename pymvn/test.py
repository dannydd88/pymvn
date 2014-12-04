import xml.etree.ElementTree as xml

def getMappingsNode(node, nodeName):
    if node.findall('*'):
        for n in node.findall('*'):
            if nodeName in n.tag:
                return n
        else:
            return getMappingsNode(n, nodeName)

def getMappings(rootNode):
    mappingsNode = getMappingsNode(rootNode, 'parent')
    print mappingsNode.tag
    print mappingsNode.findall('*')
    mapping = {}

    for prop in mappingsNode.findall('*'):
        print prop.tag
        key = ''
        val = ''

        for child in prop.findall('*'):
            if 'groupId' in child.tag:
                key = child.text

            if 'artifactId' in child.tag:
                val = child.text

        if val and key:
            mapping[key] = val

    return mapping

pomFile = xml.parse('hive-shims-0.13.1.pom')
root = pomFile.getroot()
print root.findtext('parent/groupId')

mappings = getMappings(root)
print mappings
