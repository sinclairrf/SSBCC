################################################################################
#
# Copyright 2015, Sinclair R.F., Inc.
#
################################################################################

from ssbccPeripheral import SSBCCinterruptPeripheral
from ssbccUtil import SSBCCException

class interrupt(SSBCCinterruptPeripheral):
  """
  Interrupt peripheral for 1 to 8 interrupt inputs.\n
  This implements a variable-width interrupt input of up to 8 bits and
  generates an interrupt when one of these goes from low to high, provided that
  an interrupt is not already in progress.\n
  Usage:
    PERIPHERAL interrupt insignal<N>=[!]{i_name|s__name}[,C_NAME]       \\
                         [inport=I_NAME]                                \\
                         [outmaskport=O_NAME]                           \\
                         [inmaskport=I_NAME]                            \\
                         [initmask=<value>]\n
  Where:
    insignal<N>={i_name|s__name}[,C_NAME]
      specifies one of the eight possible single-bit signal that will trigger
      the interrupt and optionally specify a constant defined by the interrupt
      bit position
      Note:  Replace <N> with 0, 1, ..., 7
      Note:  If the signal name starts with "i_" it will be added as a single
             bit wide input to the processor.  If the signal name starts with
             "s__" it must be a signal from another peripheral with the given
             name.
      Note:  If the signal name is preceded by a an exclamation mark, i.e., a
             "!", then the signal will be treated as falling-edge triggered
             instead of rising edge triggered.
      Note:  External signals may need to be synchronized to the micro
             controller clock.
    inport=I_NAME
      provide the input port name to read the interrupt signal
      Note:  This port is prohibited if there is only one interrupt signal and
             it is required if there is more than one interrupt signal.
    outmaskport=O_NAME
      optionally specifies a port to provide an enable/disable mask to
      the interrupt signals
    inmaskport=I_NAME
      optionally specifies a port to read the current enable/disable mask
      Note:  This cannot be used if outmaskport is not specified.
    initmask=<value>
      optionally specifies the initial value of the mask
      Note:  This cannot be used if outmaskport is not specified.
      Note:  The value is either a Verilog format value or a decimal value.
      Note:  If this is not specified then all interrupt bits will be enabled.\n
  Example:  Trigger an interrupt when a 1 clock wide strobe is received from an
            external timer.\n
            # In the architecture file
            PERIPHERAL interrupt insignal0=i_timer_strobe\n
            ; In the assembly file
            .interrupt
              ; Do the timer event.
              ...
              ; Return from the interrupt.
              .returni\n
  Example:  Monitor an external timer strobe and a FIFO empty flag (which is
            high when the FIFO is empty).\n
            # In the architecture file
            PERIPHERAL outFIFO_async data=o_fifo ... outempty=I_EMPTY
            PERIPHERAL interrupt insignal0=!s__o_fifo__outempty_in,C_INTERRUPT_MASK_FIFO \\
                                 insignal1=i_timer_strobe,C_INTERRUPT_MASK_TIMER         \\
                                 inport=I_INTERRUPT\n
            ; In the assembly file
            .interrupt
              ; Read the interrupt condition.
              .inport(I_INTERRUPT)
              ; If the interrupt was triggered by the timer, then handle the
              ; timer event (but don't throw away the rest of the interrupt
              ; condition).
              dup C_INTERRUPT_MASK_TIMER & .callc(...)
              ; If the interrupt was triggered by the FIFO becoming empty, then
              ; do whatever's appropriate (and throw away the interrupt
              ; condition).
              C_INTERRUPT_MASK_FIFO & .callc(...)
              ; Return from the interrupt.
              .returni\n
  WARNING:  Setting the interrupt mask does not disable interrupts occuring
            before a bit in the mask is cleared.  I.e., if a particular
            interrupt bit is disabled by a new interrupt mask, but an interrupt
            for that bit occured before the mask bit was cleared, then that
            interrupt bit will still have caused a pending interrupt.  This is
            particularly important when the processor is starting.\n
            This can be resolved in part by using the following code at the top
            of the interrupt handler:\n
              .inport(I_INTERRUPT) .inport(I_INTERRUPT_MASK) &
            where .inport(I_INTERRUPT) gets the interrupt event(s) and
            .inport(I_INTERRUPT_MASK) gets the current interrupt mask.
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    """
    Configure this peripheral as an interrupt peripheral.
    """
    # Invoke the base class __init__ function before doing anything else.
    SSBCCinterruptPeripheral.__init__(self,config,loc)
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'initmask',     r'\S+$',                lambda v : self.IntValueMethod(v), ),
      ( 'inmaskport',   r'I_\w+$',              None, ),
      ( 'inport',       r'I_\w+$',              None, ),
      ( 'outmaskport',  r'O_\w+$',              None, ),
    )
    names = [a[0] for a in allowables]
    self.insignal = [None for ix in range(config.Get('data_width'))]
    self.invert = 0
    for param_tuple in param_list:
      param = param_tuple[0]
      if re.match(r'insignal[0-7]$',param):
        if param_tuple[1] == None:
          raise SSBCCException('"%s" missing value at %s' % (param,loc,))
        ix = int(param[-1])
        if self.insignal[ix]:
          raise SSBCCException('%s already specified at %s' % (param,loc,))
        pars = re.findall(r'(!?)(i_\w+|s__\w+)(,C_\w+)?$',param_tuple[1])
        if not pars or not pars[0][1]:
          raise SSBCCException('I/O symbol at %s does not match required format "[!]{i_name|s__name}[,C_name]":  "%s"' % (loc,param_tuple[1],))
        pars = pars[0]
        if pars[0]:
          self.invert |= 2**ix
        self.insignal[ix] = pars[1]
        if pars[2]:
          config.AddConstant(pars[2][1:],2**ix,loc)
      elif param in names:
        param_test = allowables[names.index(param)]
        self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2])
      else:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,))
    # Ensure the required parameters are set.
    if not any(self.insignal):
      raise SSBCCException('Required parameter insignal<N> missing at %s' % loc)
    self.width = sum(1 for ix in range(len(self.insignal)) if self.insignal[ix])
    ixMissing = [ix for ix in range(self.width) if not self.insignal[ix]]
    if ixMissing:
      raise SSBCCException('insignal%d missing at %s' % (ixMissing[0],loc,))
    if self.width == 1:
      if hasattr(self,'inport'):
        raise SSBCCException('Parameter "inport" is prohibited when there is only one interrupt signal at %s' % loc)
    else:
      if not hasattr(self,'inport'):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # Ensure optional parameters are consistent.
    for opt in ('inmaskport','initmask',):
      if hasattr(self,opt) and not hasattr(self,'outmaskport'):
        raise SSBCCException('Optional parameter "%s" requires "outmaskport" at %s' % (opt,loc,))
    if hasattr(self,'initmask'):
      if self.initmask >= 2**self.width:
        raise SSBCCException('Value of "initmask" exceeds interrupt width at %s' % loc)
    # Create the signal for the triggering interrupt source.
    config.AddSignal('s_interrupt_trigger',self.width,loc)
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    for ix in [ix for ix in range(self.width) if re.match(r'i_',self.insignal[ix])]:
      config.AddIO(self.insignal[ix],1,'input',loc)
    if hasattr(self,'inport'):
      self.ix_inport = config.NInports()
      config.AddInport((self.inport,
                       ('s_interrupt_trigger',self.width,'data',),
                      ),
                      loc)
    if not hasattr(self,'initmask'):
      self.initmask= '%d\'h%X' % (self.width,2**self.width-1,)
    if hasattr(self,'outmaskport'):
      self.masksignal = 's_interrupt_mask'
      config.AddSignalWithInit(self.masksignal,self.width,None,loc)
      config.AddOutport((self.outmaskport,False,
                        (self.masksignal,self.width,'data',self.initmask,),
                       ),
                       loc)
      if hasattr(self,'inmaskport'):
        config.AddInport((self.inmaskport,
                         (self.masksignal,self.width,'data',),
                        ),
                        loc)
    else:
      self.masksignal = self.initmask

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v');
    if self.width == 1:
      body = re.sub(r'reg s_interrupt_trigger_any.*?\n','',body);
      while re.search(r' {4,}s_interrupt_trigger_any',body):
        body = re.sub(r' {4,}s_interrupt_trigger_any.*?\n','',body);
      body = re.sub(r's_interrupt_trigger_any','s_interrupt_trigger',body);
    if not hasattr(self,'inport'):
      clear_trigger = 's_interrupt';
    else:
      clear_trigger = 's_inport && (s_T == %d)' % self.ix_inport;
    for subpair in (
      ( r'@CLEAR_TRIGGER@',     clear_trigger, ),
      ( r'@IX_OUTPORT_DIS@',    '8\'h%02X' % self.ix_outport_interrupt_dis, ),
      ( r'@IX_OUTPORT_ENA@',    '8\'h%02X' % self.ix_outport_interrupt_ena, ),
      ( r'@INSIGNAL@',          '{ %s }' % ', '.join(self.insignal[ix] for ix in range(self.width-1,-1,-1)), ),
      ( r'@INVERT@',            '%d\'h%X' % (self.width,self.invert,), ),
      ( r'@MASK@',              self.masksignal, ),
      ( r'@WIDTH@ ',            '' if self.width==1 else '[%d:0] ' % (self.width-1,), ),
      ( r'@ZERO@',              '%d\'h0' % self.width, ),
    ):
      body = re.sub(subpair[0],subpair[1],body);
    body = self.GenVerilogFinal(config,body);
    fp.write(body);
