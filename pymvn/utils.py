# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import fnmatch
import hashlib
import json
import os
import re
import pipes
import shutil
import subprocess
import sys
import tempfile
import zipfile


@contextlib.contextmanager
def TempDir():
  dirname = tempfile.mkdtemp()
  try:
    yield dirname
  finally:
    shutil.rmtree(dirname)


def CopyFile(src, dst):
  if os.path.isdir(dst) and not os.path.exists(dst):
    pass
  if os.path.exists(src):
    shutil.copy(src, dst)


def MakeDirectory(dir_path):
  try:
    os.makedirs(dir_path)
  except OSError:
    pass


def DeleteDirectory(dir_path):
  if os.path.exists(dir_path):
    shutil.rmtree(dir_path)


def Touch(path, fail_if_missing=False):
  if fail_if_missing and not os.path.exists(path):
    raise Exception(path + ' doesn\'t exist.')

  MakeDirectory(os.path.dirname(path))
  with open(path, 'a'):
    os.utime(path, None)


def FindInDirectory(directory, filter_words):
  files = []
  for root, dirnames, filenames in os.walk(directory):
    matched_files = fnmatch.filter(filenames, filter_words)
    files.extend((os.path.join(root, f) for f in matched_files))
  return files


def FindInDirectories(directories, filter_words):
  all_files = []
  for directory in directories:
    all_files.extend(FindInDirectory(directory, filter_words))
  return all_files


def CheckOptions(options, parser, required=[]):
  for option_name in required:
    if not getattr(options, option_name):
      parser.error('--%s is required' % option_name.replace('_', '-'))


def WriteJson(obj, path, only_if_changed=False):
  old_dump = None
  if os.path.exists(path):
    with open(path, 'r') as oldfile:
      old_dump = oldfile.read()

  new_dump = json.dumps(obj)

  if not only_if_changed or old_dump != new_dump:
    with open(path, 'w') as outfile:
      outfile.write(new_dump)


def ReadJson(path):
  with open(path, 'r') as jsonfile:
    return json.load(jsonfile)


def ReadPyValues(path):
  with open(path, 'r') as f:
    return eval(f.read(), {'__builtins__': None}, None)


class CalledProcessError(Exception):
  """This exception is raised when the process run by CheckOutput
  exits with a non-zero exit code."""

  def __init__(self, cwd, args, output):
    super(CalledProcessError, self).__init__()
    self.cwd = cwd
    self.args = args
    self.output = output

  def __str__(self):
    # A user should be able to simply copy and paste the command that failed
    # into their shell.
    copyable_command = '( cd {}; {} )'.format(os.path.abspath(self.cwd),
        ' '.join(map(pipes.quote, self.args)))
    return 'Command failed: {}\n{}'.format(copyable_command, self.output)


# This can be used in most cases like subprocess.check_output(). The output,
# particularly when the command fails, better highlights the command's failure.
# If the command fails, raises a build_utils.CalledProcessError.
def CheckOutput(args, cwd=None, inputs=None,
                print_stdout=False, print_stderr=True,
                stdout_filter=None,
                stderr_filter=None,
                fail_func=lambda returncode, stderr: returncode != 0):
  if not cwd:
    cwd = os.getcwd()

  stdin = None
  if inputs:
    stdin = subprocess.PIPE

  child = subprocess.Popen(args, stdin=stdin,
      stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
  stdout, stderr = child.communicate(inputs)

  if stdout_filter is not None:
    stdout = stdout_filter(stdout)

  if stderr_filter is not None:
    stderr = stderr_filter(stderr)

  if fail_func(child.returncode, stderr):
    raise CalledProcessError(cwd, args, stdout + stderr)

  if print_stdout:
    sys.stdout.write(stdout)
  if print_stderr:
    sys.stderr.write(stderr)

  return stdout


def GetModifiedTime(path):
  # For a symlink, the modified time should be the greater of the link's
  # modified time and the modified time of the target.
  return max(os.lstat(path).st_mtime, os.stat(path).st_mtime)


def IsTimeStale(output, inputs):
  if not os.path.exists(output):
    return True

  output_time = GetModifiedTime(output)
  for line in inputs:
    if GetModifiedTime(line) > output_time:
      return True
  return False


def CheckZipPath(name):
  if os.path.normpath(name) != name:
    raise Exception('Non-canonical zip path: %s' % name)
  if os.path.isabs(name):
    raise Exception('Absolute zip path: %s' % name)


def ExtractAll(zip_path, path=None, no_clobber=True, pattern=None):
  if path is None:
    path = os.getcwd()
  elif not os.path.exists(path):
    MakeDirectory(path)

  with zipfile.ZipFile(zip_path) as z:
    for name in z.namelist():
      if name.endswith('/'):
        continue
      if pattern is not None:
        if not fnmatch.fnmatch(name, pattern):
          continue
      CheckZipPath(name)
      if no_clobber:
        output_path = os.path.join(path, name)
        if os.path.exists(output_path):
          raise Exception(
              'Path already exists from zip: %s %s %s'
              % (zip_path, name, output_path))

    z.extractall(path=path)


def DoZip(inputs, output, base_dir):
  with zipfile.ZipFile(output, 'w') as outfile:
    for f in inputs:
      CheckZipPath(os.path.relpath(f, base_dir))
      outfile.write(f, os.path.relpath(f, base_dir))


def ZipDir(output, base_dir):
  with zipfile.ZipFile(output, 'w') as outfile:
    for root, _, files in os.walk(base_dir):
      for f in files:
        path = os.path.join(root, f)
        archive_path = os.path.relpath(path, base_dir)
        CheckZipPath(archive_path)
        outfile.write(path, archive_path)


def PrintWarning(message):
  print 'WARNING: ' + message


def PrintBigWarning(message):
  print '*****     ' * 8
  PrintWarning(message)
  print '*****     ' * 8


def ExpandFileArgs(args):
  """Replaces file-arg placeholders in args.

  These placeholders have the form:
    @FileArg(filename:key1:key2:...:keyn)

  The value of such a placeholder is calculated by reading 'filename' as json.
  And then extracting the value at [key1][key2]...[keyn].

  Note: This intentionally does not return the list of files that appear in such
  placeholders. An action that uses file-args *must* know the paths of those
  files prior to the parsing of the arguments (typically by explicitly listing
  them in the action's inputs in build files).
  """
  new_args = list(args)
  file_jsons = dict()
  r = re.compile('@FileArg\((.*?)\)')
  for i, arg in enumerate(args):
    match = r.search(arg)
    if not match:
      continue

    if match.end() != len(arg):
      raise Exception('Unexpected characters after FileArg: ' + arg)

    lookup_path = match.group(1).split(':')
    file_path = lookup_path[0]
    if not file_path in file_jsons:
      file_jsons[file_path] = ReadJson(file_path)

    expansion = file_jsons[file_path]
    for k in lookup_path[1:]:
      expansion = expansion[k]

    new_args[i] = arg[:match.start()] + str(expansion)

  return new_args


def VerifyMD5(filename, expected_md5):
  if not os.path.exists(filename):
    return False
  else:
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
      for chunk in iter(lambda: f.read(8192), ''):
        md5.update(chunk)
    return md5.hexdigest() == expected_md5
