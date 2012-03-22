################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Iterator for files that returns bodies of lines of the file.  Each body
# contains optional comment lines preceding the directive, the line with the
# directive, and optional lines following the directive up to the optional
# comments preceding the next directive.
#
# The directive must be the first non-white spaces on a line.
#
# The iterator outputs a list whos first element is the line number for the
# first line of the block and whose subsequent elements are the lines with the
# content of the block.
#
# This iterator handles the ".include" directive.
#
################################################################################

import re

class fileBodyIterator:

  def __init__(self, fps, ad):
    # Do sanity check on arguments.
    if ad.IsDirective(".include"):
      raise Exception('".include" directive defined by fileBodyIterator');
    # Initialize the raw processing states
    self.fpPending = list(fps);
    self.ad = ad;
    self.current = list();
    self.pending = list();
    # Prepare the file parsing
    self.included = list();
    for fp in self.fpPending:
      if fp.name in self.included:
        raise Exception('Input file %s listed more than once' % fp.name);
      self.included.append(fp.name);
    self.fpStack = list();
    self.fpStack.append(dict(fp=self.fpPending.pop(0), line=0));
    self.pendingInclude = str();

  def __iter__(self):
    return self;

  def next(self):
    # Discard the body emitted by the previous call.
    self.current = self.pending;
    self.pending = list();
    # Loop until all of the files have been processed
    while self.fpStack or self.fpPending or self.pendingInclude:
      # Ensure the bodies in closed files are all emitted before continuing to
      # the next/enclosing file.
      if 'closed' in self.fpStack[-1]:
        if self.current:
          return self.current;
        self.fpStack.pop();
        continue;
      # Handle a queued ".include" directive.
      if self.pendingInclude:
        # Don't open the include file until all previous content has been emitted.
        if self.current:
          return self.current;
        if self.pendingInclude in self.included:
          raise Exception('File "%s" already included' % self.pendingInclude);
        self.included.append(self.pendingInclude);
        fp_pending = open(self.pendingInclude,'r');
        self.fpStack.append(dict(fp=fp_pending, line=0));
        self.pendingInclude = str();
      # Get the next file to process if fpStack is empty.
      if not self.fpStack:
        self.fpStack.append(dict(fp=self.fpPending.pop(0),line=0));
      # Process/continue processing the top file.
      fp = self.fpStack[-1];
      for line in fp['fp']:
        fp['line'] = fp['line'] + 1;
        # Handle '.include' directives.
        if re.match(r'\s*\.include\s', line):
          a = re.findall(r'\s*\.include\s+(\S+)(\s*|\s*;.*)$', line);
          if not a:
            raise Exception('Malformed .include directive at %s(%d)' % (fp['fp'].name, fp['line']));
          if not self.pending:
            self.pending.append(fp['fp'].name);
            self.pending.append(fp['line']);
          self.pending.append(line);
          self.pendingInclude = a[0][1];
          if not self.current:
            self.current = self.pending;
            self.pending = list();
          return self.current;
        # Append empty and comment lines to the pending block.
        if re.match(r'\s*(;|$)', line):
          if not self.pending:
            self.pending.append(fp['fp'].name);
            self.pending.append(fp['line']);
          self.pending.append(line);
          continue;
        # See if the line starts with a directive.
        tokens = re.findall(r'\s*(\S+)',line);
        if self.ad.IsDirective(tokens[0]):
          if not self.pending:
            self.pending.append(fp['fp'].name);
            self.pending.append(fp['line']);
          self.pending.append(line);
          if self.current:
            return self.current;
          self.current = self.pending;
          self.pending = list();
          continue;
        # Otherwise, this line belongs to the body of the preceding directive.
        if not self.current:
          self.current += self.pending[0:1];
        self.current += self.pending[2:];
        self.current.append(line);
        self.pending = list();
      # Past the last line of the current file -- close it.
      self.fpStack[-1]['fp'].close();
      self.fpStack[-1]['closed'] = True;
      # Prepare to emit pending bodies if any.
      if not self.current:
        self.current = self.pending;
        self.pending = list();
    raise StopIteration;
