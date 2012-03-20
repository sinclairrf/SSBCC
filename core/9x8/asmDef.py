################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Collection of utilities for the assembler.
#
################################################################################

import re

def TokenList(filename,startLineNumber,lines,ad):
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
      # look for decimal value
      a = re.match(r'([+\-]?[1-9]+|0)',line[col:]);
      if a:
        tokens.append(dict(type='value', value=int(a.group(0)), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # look for an octal value
      # TODO -- get correct conversion function
      a = re.match(r'0[0-9]+',line[col:]);
      if a:
        tokens.append(dict(type='value', value=int(a.group(0)), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # look for a hex value
      # TODO -- get correct conversion function
      a = re.match(r'0x[0-9A-Fa-f]+',line[col:]);
      if a:
        tokens.append(dict(type='value', value=int(a.group(0)), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
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
      a = re.match(r'\.[A-Za-z]\w*(\(\w+\))?',line[col:]);
      if a:
        b = re.match(r'\.[A-Za-z]\w*',a.group(0));
        if ad.IsDirective(b.group(0)):
          if b.group(0) != a.group(0):
            raise Exception('Malformed directive in %s(%d), column %d' % (filename, lineNumber, col+1));
          if len(tokens) > 0:
            raise Exception('Directive must be first entry on line in %s(%d), column %d' % (filename, lineNumber, col+1));
          tokens.append(dict(type='directive', value=a.group(0), line=lineNumber, col=col+1));
          col = col + len(a.group(0));
          continue;
        if ad.IsMacro(b.group(0)):
          if b.group(0) == a.group(0):
            macroArgs = list();
          else:
            macroArgs = re.findall(r'([^,)]+)',a.group(0)[len(b.group(0))+1:]);
          if len(macroArgs) != ad.MacroNumberArgs(b.group(0)):
            raise Exception('Wrong number of arguments to macro in %s(%d), column %d' % (filename, lineNumber, col+1));
          tokens.append(dict(type='macro', value=b.group(0), line=lineNumber, col=col+1, argument=macroArgs));
          col = col + len(a.group(0));
          continue;
        raise Exception('Unrecognized directive or macro "%s" in %s(%d), column(%d)' % (a.group(0), filename, lineNumber, col+1));
      # look for instructions
      a = re.match(r'\S+',line[col:]);
      if ad.IsInstruction(a.group(0)):
        tokens.append(dict(type='instruction', value=a.group(0), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # look for a label definition
      a = re.match(r':[A-Za-z]\w+',line[col:]);
      if a:
        tokens.append(dict(type='label', value=a.group(0)[1:], line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # look for symbols
      # Note:  This should be the last check performed as every other kind of
      #        token should be recognizable
      a = re.match(r'[A-Za-z]\w+',line[col:]);
      if a:
        tokens.append(dict(type='symbol', value=a.group(0), line=lineNumber, col=col+1));
        col = col + len(a.group(0));
        continue;
      # anything else is an error
      raise Exception('Malformed statement in %s(%d), column %d' % (filename, lineNumber, col+1));
  return tokens;
