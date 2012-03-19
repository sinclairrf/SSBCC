################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Collection of utilities for the assembler.
#
################################################################################

import re

def TokenList(filename,startLineNumber,lines):
  """Extract the list of tokens from the provided list of lines"""

  tokens = list();
  lineNumber = startLineNumber - 1;
  for line in lines:
    lineNumber = lineNumber + 1;
    col = 0;
    spaceFound = True;
    while col < len(line):
      # TODO -- ensure tokens are separated by whitespace
      # ignore white-space characters
      if re.match(r'\s',line[col:]):
        spaceFound = True;
        col = col + 1;
        continue;
      if not spaceFound:
        raise Exception('Missing space in %s(%d), column %d' % (filename, lineNumber, col+1));
      spaceFound = False;
      # ignore comments
      if line[col] == ';':
        break;
      # capture double-quoted strings (won't capture embedded double quotes)
      # TODO -- improve double-quoted string capture and escape character interpretation
      if line[col] == '"':
        a = re.match(r'"[^"]+"',line[col:]);
        if ~a:
          raise Exception('Unmatched " in %s(%d), column %d' % (filename, lineNumber, col+1));
        tokens.append(dict(type='string', value=a.group(0)[1:len(a)-1], line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # capture single-quoted character
      if line[col] == "'":
        a = re.match(r'\'.\'',line[col:]);
        if ~a:
          raise Exception('Malformed \'.\' in %s(%d), column %d' % (filename, lineNumber, col+1));
        tokens.append(dict(type='character', value=a.group(0)[1], line=lineNumber, col=col+1));
        continue;
      # look for directives and macros
      a = re.match(r'\.[A-Za-z]\w*\(\w+\)',line[col:]);
      if a:
        tokens.append(dict(type='macro', value=a.group(0), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      a = re.match(r'\.\w+',line[col:]);
      if a:
        tokens.append(dict(type='macro', value=a.group(0), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # look for symbols
      a = re.match(r'[A-Za-z]\w+',line[col:]);
      if a:
        tokens.append(dict(type='symbol', value=a.group(0), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      a = re.match(r'[+\-&\^]',line[col:]);
      if a:
        tokens.append(dict(type='symbol', value=a.group(0), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # look for decimal value
      a = re.match(r'[0-9]+',line[col:]);
      if a:
        tokens.append(dict(type='value', value=int(a.group(0)), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # look for a label definition
      a = re.match(r':[A-Za-z]\w+',line[col:]);
      if a:
        tokens.append(dict(type='label', value=a.group(0)[1:], line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # anything else is an error
      raise Exception('Malformed statement in %s(%d), column %d' % (filename, lineNumber, col+1));
  return tokens;
