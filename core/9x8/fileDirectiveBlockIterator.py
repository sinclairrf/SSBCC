################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Iterator for files that returns blocks of lines of the file.  Each block
# contains optional comment lines preceding the directive, the line with the
# directive, and optional lines following thee directive up to the optional
# comments preceding the next directive.
#
# The directive must be the first non-white spaces on a line.
#
# The iterator outputs a list whos first element is the line number for the
# first line of the block and whose subsequent elements are the lines with the
# content of the block.
#
################################################################################

import re

class fileDirectiveBlockIterator:

  def __init__(self, fp, directivesList):
    self.fp = fp;
    self.directivesList = directivesList;
    self.state = 0;
    self.lineNumber = 0;
    self.current = list();
    self.pending = list();

  def __iter__(self):
    return self;

  def next(self):
    self.current = self.pending;
    self.pending = list();
    if self.state == 1:
      self.state = 2;
      if len(self.current) > 0:
        return self.current;
    if self.state == 2:
      raise StopIteration;
    for line in self.fp:
      self.lineNumber = self.lineNumber + 1;
      if re.match(r'\s*(;|$)', line):
        if len(self.pending) == 0:
          self.pending.append(self.lineNumber);
        self.pending.append(line);
        continue;
      tokens = re.findall(r'\s*(\S+)',line);
      if tokens[0] in self.directivesList:
        if len(self.pending) == 0:
          self.pending.append(self.lineNumber);
        self.pending.append(line);
        if self.current > 0:
          return self.current;
        self.current = self.pending;
        self.pending = list();
        continue;
      if len(self.current) == 0:
        self.current.append(self.pending[0]);
      self.current += self.pending[1:];
      self.pending = list();
      self.current.append(line);
    self.fp.close();
    self.state = 1;
    self.current += self.pending[1:];
    self.pending = list();
    return self.current;
