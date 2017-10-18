# s3 fetcher

import boto3
import downloader as d
import urlparse
from tempfile import NamedTemporaryFile


class S3Fetcher(d.Fetcher):
  def __init__(self):
    self.s3 = boto3.client('s3')

  def Fetch(self, url, failmsg):
    urlobject = urlparse.urlparse(url)
    bucket = urlobject.netloc
    key = urlobject.path

    print('Fetch from s3://{}{}'.format(bucket, key))

    try:
      with NamedTemporaryFile(delete=False) as data:
        self.s3.download_fileobj(bucket, key[1:], data)

      return open(data.name, 'rb')
    except Exception, e:
      raise Exception('%s because of %s while tried %s' % (failmsg,
                                                           str(e),
                                                           url))


if __name__ == '__main__':
  f = S3Fetcher()
  print f.Fetch('s3://ap-southeast-1.elasticmapreduce.samples/cloudfront/code/Hive_CloudFront.q', 'f').read()
  print 'OK'
