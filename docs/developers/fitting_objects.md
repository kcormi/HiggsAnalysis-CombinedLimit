

#  The Combine object

The `Combine.cc` file defines the main `Combine` object which controls the overall flow of the program

The Combine object contains approximately 50 boost program options which control its behaviour, grouped in to "i/o", "statistical" and "miscellaneous" groups.
The i/o options include things like the model name, and whether to save a workspace snapshot, but also some seemingly statistical otpions such as chosing to float some parameters.
The stat options include things like the confidence level min and max POI values, and wether to use toys as well as freezing some nuisance groups.
These program options are then passed to the `applyOptions` method which parses the options to store values in private member variables.

The main method used by the `Combine` class is the `run` method, which guides the overall program behaviour.
Other methods exist for 
- `toggleGlobalFillTree`: stop combine from filling the `TTree`
- `CommitPoint`: Adding a new evaluation point to the `TTree`
- `addBranch`: Adding a branch to the TTree

and Private methods for:
- `mklimit`
- `addDiscreteNuisances`
- `addNuisances`
- `addFloatingParameters`
- `addPOI`
- `addBranches`

## Run Method

The run method first sets up a temporary ROOT directory for its work.
Then the method checks the file defining the workspace. 
If this is already a combine workspace (`.root`) or an hlf file `.hlf` nothing is done; but if this file is a datacard, then combine calls the `text2workspace.py` script on the datacard to create the workspace.

Then the method adds some ROOT `INCLUDE_PATH` variables from CMMSW and RooFit.

Then combine loads information from either the workspace or the `hlf` file.

For the workspace it first gets the workspace object and then loads a number of objects from the workspace into variables, such as:
- The higgs mass setting
- the s+b mc model
- The b-only mc model
- The POIs (from the mc model object)
- The model pdf (from the mc model object)

And then does a number of checks, for example that there is at least one POI, at least one observable, and that if `expectSignal` is set then there is only one POI.
Depending on the command line options the background-only model may also be built from the mc model and some command line options, and/or the PDFs can be rebuilt.

The (default, from worskapce) poi ranges and central value are initialized here, and if a snapshot is provided it is loaded.
If the options have been set, then command line model parameters are also set at this point.

If the the provided file is a RooStats `HLFactory` object, it is loaded differently, in a separate code block. 
However, the logic is largely the same, loading the workspace, and the model.

Next the method creates `RooArgSet`s for the POI, nuisnaces, and observables.

Something strange is then done based on an `"ADD_DISCRETE_FALLBACK"` runtime def, where the behaviour depends on whether the nusiance matches the string:  "u\_CMS\_Hgg\_env\_pdf_"

The the data itself is loaded, either from a workspace or just from a root file and stored as a `RooAbsData` pointer, which is then loaded into the workspace.
In some cases the `RooAbsData` is empty, but this is because observables have been preset to their observed values, in which case the `RooDataSet` is loaded from the observables
Then the `RooDataSet` is loaded into the workspace.

KYLE NOTE: There is some distinction here between the `RooAbsData* data` object and the `RooDataSet* obs_data`, that I don't reall understand yet.

The `RooMessageService`  object is created for logging.

Then POIs are redefined if the corresponding argument has been set. 
Any constraints on the new POIs are removed, and the new POIs are removed from the list of nuisance parameters.

If any nuisances have been set to floating in the arguments, they are then set floating here, via the `utils::setAllConstant` function.

If any nuisances are frozen, then the regular expression for the frozen nuisance is parsed.
Once the string of all matching nuisances is constructed, the list of nuisances is iterated over and frozen using the `utils::setAllConstant` function.
All frozen nuisance parameters are then removed from the list of nuisances.

Then if any nuisance groups have been flagged to be frozen, then they are fronzen using the `utils::setAllConstant` function and removed from the list of nuisances.
If any nuisances are set to be frozen by Attribute, they are then frozen using the `utils::setAllConstant` function and removed from the list of nuisances.

**_NOTE:_**  This nuisance freezing/floating is done a few times for different cases, using mostly inline code. Perhaps these could be grouped and upt into a function which handles this (more than the `utils::setAllConstant` already does).


After the nuisance parameters are frozen, the prior pdf (presumably only for the bayesian methods) is set to either a flat prior, 1/sqrt(r), or a pdf in the model.

if the `validateModel_` flag is set, model validation is checked
Then if all nuisances are set to be floating, or all global observables are set to be frozen that is done.

Then the private member functions `addDiscreteNuisances`, `addNuisances`, `addFloatingParameters` and `addPOI` are called to be passed to CascadeMinimizer.

If Parameter tracking or Error tracking is set, then those branches are added to the TTree, via the private `addBranches` function.

Next the list of channel masks is printed

**_NOTE_**: But the channel masks are not actually implement here it seems? (around l.800) maybe this could be changed in the code to have the printing closer to the masking.

Then MH, the observed data, the genPDF, and weightVar are taken from the workspace/modles. (Again?)

For toys: The value of `r` is then set based on the `--expectSignal` and `--setPhysicsModelParameters` values.

Then if the `FAST_VERTICAL_MORPH` runtime definition is set, Fast Vertical Morphing is enabled.

If an initial snapshot of the worskpace should be saved it is done now.

The rest of the code runs separately for two distinct cases: <= 0 Toys (real or asimov data); or > 0 toys.

*For asimov or real data the execution proceeds as*:
The observed data is read either from its usual spot, or from an asimov toy. 
If an asimov toy can either be provided from a snapshot, or generated on the spot.
If the asmiov toy is generated on the spot, it is done using the `asimovutils::asimovDatasetWithFit` function.
lastly the private `mklimit` method is called, which runs the actual routine, and the `commitPoint` method is called to add the result to the TTree.

*For toy data*:
Before generating any toys, checks are done for floating parameters and consistency.
Then, unless `--bypassFrequentistFit` has been set, the `CascadeMinimizer` is called to minimize the nll. 
KYLE NOTE: I don't see in the code yet where/how this minimization gets used, though of course it in general should be in the toy generation and fitting.
The nuisance pdf object then generates the required number of toys.
The number of toys is then set in the Algorithm (a.k.a. Method)
Then for each toy, the clean workspace is loaded, the toy index is is used to retrieve the nuisance toys, the logger prints some info, then the toy data is generated (or read from saved toys), and then the `mklimit` method is called which runs the actual routine and `commitPoint` is called to add the point to the TTree.
If toys are saved it is done here.
Then, after all the toys have completed some summary information is printed.



Finally, if the workspace is to be saved, it is done here, at the end of the `run` method.



## The mklimit method

The `mklimit` first checks if there is a hint Algorithm (Method), and if it does runs the hintAlgorithm
KYLE NOTE: Note quire sure what that means.

Then, the main algorithms `LimitAlgo::run` method is called (passing it the hintAlgo result, if there was one)

The return value of the main algorithms `run` method is then returned.

### The  commitPoint method

Simply adds an entry to the TTree.

### The AddNuisances method

Simply adds a nuisance parameter to the `CascadeMinimizer` object.

### The addPOI method

Simply adds a parameter of interest to the `CascadeMinimizer` object.

### The addFloatingParameters method

Simply adds a floating point parameter the `CascadeMinimizer` object.

### The addDiscreteNuisances method

Takes all discrete nuisances in a workspace
KYLE NOTE: Also something going on here with pdf index and other things, I need to look into


# LimitAlgo

The LimitAlgo object defines a base clase from which the fitting algorithms derive

it has methods for applying options, applying default options, setting toys, and crucially running

# FitterAlgoBase

Derived class of LimitAlgo, but now with fit-specific variables and methods, such as doFit, nLLValue, findCrossing, etc...

## doFit method

after some preliminaries, create a CascadeMinimizer object, set some settings (ErrorLevel, bounds, ...)

then call the minmizers `minimize` method
optionally run HESSE after the fit (the minimizers.hesse method), if the hesse options has been set

## run Method

sets up a CoutSentry (redirecting output)

adds all parameters to the RooArgSet allParams_
creates new ttree branches if necessary (nll, nll0)

Sets the right profiling mode (ProfileUnconstrained, ProfilePOI, NoProfiling, or ProfileAll) 
by either looping over all nuisances, looping over all non-POIs, or over all parameters and freezing them

Do something about protecting unbinned channels
KYLE NOTE: look into this

Do something about optimizing bounds
KYLE NOTE: look into this

then call the `runSpecific` method (to be implemented per Fit Algorithm)

something with protecting unbinned channels 
KYLE NOTE: look into this

and unset bounds

    
# CascadeMinimizer

Custom Minimizer object used by combine for its fits

Has a RooAbsReal nll object and a pointer too a RooMinimizer

## the minimize method

## the trivialMinimize method

for a single parameter, r, step through its range, keep track of the lowest nll value and set r to the lowest nll value

## hesse method





# RobustHesse object








