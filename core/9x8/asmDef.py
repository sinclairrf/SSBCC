################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Collection of utilities for the assembler.
#
################################################################################

import os
import re

################################################################################
#
# Exception class for the assembler.
#
################################################################################

class AsmException(Exception):
  def __init__(self,message):
    self.msg = message;
  def __str__(self):
    return self.msg;

################################################################################
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

class FileBodyIterator:

  def __init__(self, constants, fps, ad):
    # Do sanity check on arguments.
    if ad.IsDirective(".include"):
      raise Exception('".include" directive defined by FileBodyIterator');
    # Initialize the raw processing states
    self.ixConstants = 0;
    self.constants = constants;
    self.fpPending = list(fps);
    self.ad = ad;
    self.current = list();
    self.pending = list();
    # Initialize the include search paths
    self.searchPaths = list();
    self.searchPaths.append('.');
    # Prepare the file parsing
    self.included = list();
    for fp in self.fpPending:
      if fp.name in self.included:
        raise AsmException('Input file %s listed more than once' % fp.name);
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
    # Process command-line constants first.
    if self.ixConstants < len(self.constants):
      thisConstant = self.constants[self.ixConstants];
      self.ixConstants = self.ixConstants + 1;
      self.current = list();
      self.current.append('command line');
      self.current.append(0);
      self.current.append('.constant');
      self.current.append(thisConstant[0]);
      self.current.append(thisConstant[1]);
      return self.current;
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
          raise AsmException('File "%s" already included' % self.pendingInclude);
        self.included.append(self.pendingInclude);
        fp_pending = None;
        for path in self.searchPaths:
          fullInclude = os.path.join(path,self.pendingInclude);
          if os.path.exists(fullInclude):
            fp_pending = open('%s/%s' % (path,self.pendingInclude),'r');
            break;
        if not fp_pending:
          raise AsmException('%s not found' % self.pendingInclude);
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
            raise AsmException('Malformed .include directive at %s:%d' % (fp['fp'].name, fp['line']));
          if not self.pending:
            self.pending.append(fp['fp'].name);
            self.pending.append(fp['line']);
          self.pending.append(line);
          self.pendingInclude = a[0][0];
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
          self.current += self.pending[0:2];
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

  def AddSearchPath(self,path):
    self.searchPaths.append(path);

################################################################################
#
# Parse strings into the desired types.
#
################################################################################

def ParseNumber(inString):
  # look for single-digit 0
  if inString == '0':
    return 0;
  # look for decimal value
  a = re.match(r'[+\-]?[1-9]\d*\b',inString);
  if a:
    return int(a.group(0),10);
  # look for an octal value
  a = re.match(r'0[0-7]+\b',inString);
  if a:
    return int(a.group(0),8);
  # look for a hex value
  a = re.match(r'0x[0-9A-Fa-f]+\b',inString);
  if a:
    return int(a.group(0),16);
  # Everything else is an error
  return None;

def ParseString(inString):
  if inString[0] in 'CNc':
    ix = 2;
  else:
    ix = 1;
  outString = list();
  while ix < len(inString)-1:
    if inString[ix] == '\\':
      if ix == len(inString)-1:
        return ix;
      ix = ix + 1;
      if inString[ix] in ('\\', '\'', '"',):
        outString.append(ord(inString[ix]));
        ix = ix + 1;
      elif inString[ix] == '0': # null terminator
        outString.append(0);
        ix = ix + 1;
      elif inString[ix] == 'a': # bell
        outString.append(7); # control-G
        ix = ix + 1;
      elif inString[ix] == 'b': # backspace
        outString.append(8); # control-H
        ix = ix + 1;
      elif inString[ix] == 'f': # form-feed
        outString.append(12); # control-L
        ix = ix + 1;
      elif inString[ix] == 'n': # line feed
        outString.append(10); # control-J
        ix = ix + 1;
      elif inString[ix] == 'r': # carriage-return
        outString.append(13); # control-M
        ix = ix + 1;
      elif inString[ix] == 't': # horizontal tab
        outString.append(9); # control-I
        ix = ix + 1;
      elif re.match(r'[0-7]',inString[ix]): # octal character
        if ix >= len(inString)-3:
          return ix;
        if not re.match(r'[0-7]{3}',inString[ix:ix+3]):
          return ix;
        outString.append(int(inString[ix:ix+3],8));
        ix = ix + 3;
      elif inString[ix] in ('X','x',): # hex character
        if ix >= len(inString)-3:
          return ix;
        if not re.match(r'[0-9A-Fa-f]{2}',inString[ix+1:ix+3]):
          return ix;
        outString.append(int(inString[ix+1:ix+3],16));
        ix = ix + 3;
      else:
        outString.append(ord(inString[ix]));
        ix = ix + 1;
    else:
      outString.append(ord(inString[ix]));
      ix = ix + 1;
  if inString[0] == 'C':
    outString.insert(0,len(outString));
  elif inString[0] == 'N':
    outString.append(0);
  elif inString[0] == 'c':
    outString.insert(0,len(outString)-1);
  return outString;

def ParseToken(ad,fl_loc,col,raw,allowed):
  flc_loc = fl_loc + ':' + str(col+1);
  # look for instructions
  # Note:  Do this before anything else because instructions can be a
  #        strange mix of symbols.
  if ad.IsInstruction(raw):
    if 'instruction' not in allowed:
      raise AsmException('instruction "%s" not allowed at %s' % (raw,flc_loc));
    return dict(type='instruction', value=raw, loc=flc_loc);
  # look for computation
  a = re.match(r'\${\S+}$',raw);
  if a:
    if 'singlevalue' not in allowed:
      raise AsmException('Computed value not allowed at %s' % flc_loc);
    try:
      tParseNumber = eval(raw[2:-1],ad.SymbolDict());
    except:
      raise AsmException('Malformed computed value at %s: "%s"' % (flc_loc,raw,));
    if type(tParseNumber) != int:
      raise AsmException('Malformed single-byte value at %s' % flc_loc);
    return dict(type='value', value=tParseNumber, loc=flc_loc);
  # look for a repeated single-byte numeric value
  a = re.match(r'[1-9][0-9]*\*(0|[+\-]?[1-9]\d*|0[0-7]+|0x[0-9A-Fa-f]{1,2})$',raw);
  if a:
    if 'multivalue' not in allowed:
      raise AsmException('Multi-byte value not allowed at %s' % flc_loc);
    b = re.findall(r'([1-9][0-9]*)\*(0|[+\-]?[1-9]\d*|0[0-7]+|0x[0-9A-Fa-f]{1,2})\b',a.group(0));
    b = b[0];
    tParseNumber = ParseNumber(b[1]);
    if type(tParseNumber) != int:
      raise AsmException('Malformed multi-byte value at %s' % (fl_loc + ':' + str(col+len(b[0])+2)));
    tValue = list();
    for ix in range(int(b[0])):
      tValue.append(tParseNumber);
    return dict(type='value', value=tValue, loc=flc_loc);
  # look for a single-byte numeric value
  a = re.match(r'(0|[+\-]?[1-9]\d*|0[07]+|0x[0-9A-Fa-f]{1,2})$',raw);
  if a:
    if 'singlevalue' not in allowed:
      raise AsmException('Value not allowed at %s' % flc_loc);
    tParseNumber = ParseNumber(raw);
    if type(tParseNumber) != int:
      raise AsmException('Malformed single-byte value at %s' % flc_loc);
    return dict(type='value', value=tParseNumber, loc=flc_loc);
  # capture double-quoted strings
  if re.match(r'[CNc]?"',raw):
    if 'string' not in allowed:
      raise AsmException('String not allowed at %s' % flc_loc);
    parsedString = ParseString(raw);
    if type(parsedString) == int:
      raise AsmException('Malformed string at %s' % (fl_loc + ':' + str(col+parsedString)));
    return dict(type='value', value=parsedString, loc=flc_loc);
  # capture single-quoted character
  if raw[0] == "'":
    if 'singlevalue' not in allowed:
      raise AsmException('Character not allowed at %s' % flc_loc);
    a = re.match(r'\'.\'$',raw);
    if not a:
      raise AsmException('Malformed \'.\' in %s' % flc_loc);
    return dict(type='value', value=ord(a.group(0)[1]), loc=flc_loc);
  # look for directives
  if ad.IsDirective(raw):
    if 'directive' not in allowed:
      raise AsmException('Directive not allowed at %s' % flc_loc);
    return dict(type='directive', value=raw, loc=flc_loc);
  # look for macros
  a = re.match(r'\.[A-Za-z]\S*(\(\S+(,\S+|,\${\S+})*\))?$',raw);
  if a:
    b = re.match(r'\.[^(]+',raw);
    if not ad.IsMacro(b.group(0)):
      raise AsmException('Unrecognized directive or macro at %s:%d' % (fl_loc,col+1));
    if ('macro' not in allowed) and not ('singlemacro' in allowed and ad.IsSingleMacro(b.group(0))):
      raise AsmException('Macro "%s" not allowed at %s:%d' % (b.group(0),fl_loc,col+1,));
    macroArgs = re.findall(r'([^,]+)',raw[len(b.group(0))+1:-1]);
    nArgs = ad.MacroNumberArgs(b.group(0))
    if len(macroArgs) not in nArgs:
      raise AsmException('Wrong number of arguments to macro at %s:%d' % (fl_loc,col+1));
    while len(macroArgs) < nArgs[-1]:
      macroArgs.append(ad.MacroDefault(b.group(0),len(macroArgs)));
    outArgs = list();
    col = col + len(b.group(0))+1;
    for ixArg in range(len(macroArgs)):
      outArgs.append(ParseToken(ad,fl_loc,col,macroArgs[ixArg],ad.MacroArgTypes(b.group(0),ixArg)));
      col = col + len(macroArgs[ixArg]) + 1;
    return dict(type='macro', value=b.group(0), loc=fl_loc + ':' + str(col+1), argument=outArgs);
  # look for a label definition
  a = re.match(r':[A-Za-z]\w*$',raw);
  if a:
    if 'label' not in allowed:
      raise AsmException('Label not allowed at %s' % flc_loc);
    return dict(type='label', value=raw[1:], loc=flc_loc);
  # look for parameters with range specification
  a = re.match('G_\w+[[]\d+\+?:\d+]$',raw);
  if a:
    if 'symbol' not in allowed:
      raise AsmException('Symbol not allowed at %s' % flc_loc);
    a = re.findall('(G_\w+)([[].*)',raw)[0];
    return dict(type='symbol', value=a[0], range=a[1], loc=flc_loc);
  # look for symbols
  # Note:  This should be the last check performed as every other kind of
  #        token should be recognizable
  a = re.match(r'[A-Za-z]\w+$',raw);
  if a:
    if 'symbol' not in allowed:
      raise AsmException('Symbol not allowed at %s' % flc_loc);
    return dict(type='symbol', value=a.group(0), loc=flc_loc);
  # anything else is an error
  raise AsmException('Malformed entry at %s:  "%s"' % (flc_loc,raw,));

################################################################################
#
# Extract the tokens from a block of code.
#
# These blocks of code should be generated by FileBodyIterator.
#
################################################################################

def RawTokens(ad,filename,startLineNumber,lines):
  """Extract the list of tokens from the provided list of lines"""
  allowed = [
              'instruction',
              'label',
              'macro',
              'multivalue',
              'singlevalue',
              'string',
              'symbol'
            ];
  tokens = list();
  lineNumber = startLineNumber - 1;
  for line in lines:
    lineNumber = lineNumber + 1;
    fl_loc = '%s:%d' % (filename,lineNumber);
    col = 0;
    spaceFound = True;
    while col < len(line):
      flc_loc = fl_loc + ':' + str(col+1);
      # ignore white-space characters
      if re.match(r'\s',line[col:]):
        spaceFound = True;
        col = col + 1;
        continue;
      if not spaceFound:
        raise AsmException('Missing space in %s:%d' % (fl_loc,col+1));
      spaceFound = False;
      # ignore comments
      if line[col] == ';':
        break;
      # Catch strings
      if re.match(r'[CNc]?"',line[col:]):
        a = re.match(r'[CNc]?"([^\\"]|\\.)+"',line[col:]);
        if not a:
          raise AsmException('Malformed string at %s' % flc_loc);
      # Catch single-quoted characters
      elif re.match(r'\'',line[col:]):
        a = re.match(r'\'.\'',line[col:]);
        if not a:
          raise AsmException('Malformed \'.\' at %s' % flc_loc);
      else:
        # everything else is a white-space delimited token that needs to be parsed
        a = re.match(r'\S+',line[col:]);
      if not tokens:
        selAllowed = 'directive';
      else:
        selAllowed = allowed;
      tokens.append(ParseToken(ad,fl_loc,col,a.group(0),selAllowed));
      col = col + len(a.group(0));
  return tokens;
