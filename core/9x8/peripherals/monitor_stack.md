Copyright 2012-2014, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

Simulation peripheral to monitor stack validity.

This peripheral flags invalid stack operations and displays the execution
history immediately before detected invalid operations.

Invalid data stack operations are:

- pushing onto a full data stack

- dropping from an empty data stack

- nipping from an almost empty data stack

Invalid return stack operations are:

- pushing onto a full return stack

- dropping values from an empty return stack

- returns from a data entry on the return stack

- non-return  operations from an address entry on the return stack

Invalid data operations are:

- swap on an empty or almost empty data stack

- in-place operations on an empty or almost empty data stack

Usage
=====

```
PERIPHERAL monitor_stack        \
                [history==n]
```

or, when invoking ssbcc specifically for a simulation:

```
ssbcc -P monitor_stack ...
```

Where:

- history=n

  display the n most recent operations when a stack error is encountered

  Note:  The default value is 50 instructions.
