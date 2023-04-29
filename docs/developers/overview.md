# Introduction to Developer Documentation

This documentation is intended for developers and expert users. 
It describes in more detail some of the internal workings of combine and details about specific methods.

# Program Flow


The main `combine` binary is compiled from `combine.cpp`

## bin/combine.cpp

`combine.cpp` first instantiates pointes to each of the fitting algorithms as derived classes of `LimitAlgo` objects (on the command line and in the documentation, what are referred to as "Methods").
It also initializes strings, floats, etc storing information about the run (datacard name, higgs mass, etc) and declares a `Combine` class object as well as the Cascade Minimizer.

It then takes the command line options from each of the algorithms (a.k.a. "Methods"), from the `Combine` object, and from the `CascadeMinimizer` and adds several generic, algorithm independent, options, all stored as boost `program_options`.

It then parses these command line options and performs checks (such as that the Algorithm/Method is known and that the datacard name is given).
The random seed is generated, strings for the higgs mass and toy part of file names are generated, and keyword-value settings for the model are parsed. 
Parsed options are applied to the `Combine` and `CascadeMinimizer` objects as well as to the Algorithm/Method object.

An output `ROOT` file is created, along with the `TTree` which will store results nad the `toys` folder.

A number of runtime definitions are then set (for `RooFit`?).

Finally the `Combine` objects `run` method is called, outputs are written and some performance metrics are printed.

```mermaid

graph TD;
   combine.cpp --> Combiner Object;
```
