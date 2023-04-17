# Workspace Creation

the workspaces are always created by invoking `scripts/text2workspace.py`. 
If this script is not invoked explicitly by the user, it is invoked by the combine code when the raw text datacard is passed to combine.

## text2workspace.py

The `textworkspace.py` script is a mostly simple wrapper. 
Firstly it parses command line options, then it opens the datacard file and passes it to the `parseCard` function define in `python/DatacardParser.py`.

The object return by `parseCard` is then passed to either the `ShapeBuilder` or `CountingModelBuilder` class constructor, defined in `python/ShapeTools.py` or `python/ModelTools.py` respectively.

Next the `PhysicsModel` is defined and has the physics options sets.
Then the physics model is passed to the model object which was built and the models `doModel` function is called.

# DatacardParser.py

## the parseCard method

This method is passed a textfile datacard a `Datacard` object as defined in `python/Datacard.py`

**_NOTE:_** This is a very long (~320 lines) function with many many if/else statements.  It might be possible to restructure nicely

The `Datacard` object is first instantiated and then some default values are set

**_NOTE:_**: Can probably just build the default values into the class efinition?

The parser then loops over each line of the input file twice, and splits each line (by whitespace).
For the first pass the behaviour depends on the first "word" of the line, and handles the following cases:
- "imax"
- "jmax"
- "kmax"
- "shapes"
- "Observation"
- "bin"
- "process"
- "rate"

Other valid lines (such as those define nuisances) are parsed in the second loop.

__First Loop__:

*imax, kmax, jmax* lines: simply set integer values for `nbins`, `nprocesses`, `nuisances`.

*shapes* line: adds the shape to the `DataCard` objects `shapeMap`
**_NOTE:_** Sometimes the `shapesUseBin` local variable is set to `True` but this appears never to be used anywhere?

*Observation* line: checks the number of observations is consistent with `imax`.
If the bin line has already been parsed then check the number of observations is also consistent and add the value to the `Datacard` `obs` dictionary.

**_NOTE:_**: I guess if there is not a bin line above, this just fails silently?

*bin* line: check none of the words start with a digit, store the value for when parsing other lines

*process* line: If its the first process line, check it is the same length as the binline and store the names.
If it is the second process line: check that the order of the two process lines is right and if not, flip them for processing.
Then check the two lines have the same length.
Then store each bin, process name, and if its signal or not in a list of tuple stored in the `Datacard` `keyline` attribute.
Then if the bins have been added to the `Datacard` object already they are checked for consistency. 
If they hadn't been added they are added here, then the processes are added.
The `Datacard` `obs`,`isSignal`, and `signal` attributes are then updated.

**_NOTE:_** why does the datacard have `isSignal` attribute and a list of signals as a separate attribute!

*rate* line: check line consistency and add info to the `Datacard` `exp` attribute.

__Second Loop__:

The first "word" (called `lsyst`) and the second "word" (called `pdf`) define the different case behaviours, checking in order: 

*lsyst is alreadyin the `Datacard` `systIDMap` and pdf is one of shape, shapeN, lnN*: just makes sure that there wasn't a previous shape type defined that is now lnN or vice versa?

*lsyst ends with [nofloat]*: set a nofloat flag (not sure why yet)

*the nuisance should be excluded*: excludes it

*lsyst starts with a digit*: appends "theta" to the start of the name

*pdf cases*: store some info about the line, depending on what type (e.g. lnN, rateparam, autoMCstats, etc ... )

Then, for every case (with the exception of some special cases, such as groups) add some info to the `Datacard` `systs` attribute




# Datacard.py

This file defines the `Datacard` class.
It contains several attributes, which mostly mimic the structure of the text datacard (list of observables, bins, nuisances, rate params, etc...).

The class methods are able to print the datacard structure, or return value of the atrributes. 
Some other methods such as for renaming nuisance parameters are also implemented.



# ModelBuilder.py

**_NOTE:_**: It's not really clear to me why this class exists, I think the only inheriting class is `ModelBuilder`,
But this base class does not have methods such as `setPhysics` and `doModel` which are called by text2workspace.
So it seems even the class interface is not useful?


## ModelBuilderBase class

The base class all ModelBuilders Inherit from. 

### init method

Takes one options object, which is stored as an attribute. Then set some ROOT parameters (libraries to lad "RooMessageService" etc )
It defines a `RooWorkspace` as the output object which it writres to if the `bin` option is set (but this seems to be the only allowed option).

## ModelBuilder class

inherits from the `ModelBuilderBase`

### init method

Stores the `Datacard` object and a few other extra attributes after calling the `ModelBuildBase` `__init__` function

### doModel method

This method mostly class `do<ThingX>` for other important parts of the model, such as `doObservbales`, `doNuisances`, `doExtArgs`, `doRateParams` etc..
Most of these methods are implemented directly in the `ModelBuilder` class from which the `CountingModelBuilder` and `ShapeModelBuilder` derive.
However, some are implemented in the derived classes, and `doObservables` is not implemented, only raising an error when it is called, so must be reimplemented.

## CountingModelBuilder class

Implements the functionality for non-shape based analysis (i.e. simple counting experiments)

### doObservables method

calls the `doVar` method, which in turns calls the `factory_` method which uses the `RooWorkspace::factory( RooStringView expr )` method to create `RooFit` objects from the expression.
This method  creates one Variable for each `obs` in the `Datacard` object and sets its minimum value to 0.
A set is defined `RooWorkspace::defineSet` for the observables, and they are added to the workspace as a `RooDataSet`

### doIndividualModels method

creates a `sum` objects (n\_exp for each bin) and `Poisson` objects (pdf\_bin) objects for each bin for the signal plus background and background only models.

### doCombination method

creates `PROD` (pdf\_bin) objects of all the bins for the background-only and signal+background models. 
If there is a large number of bins (>50) this is done in batches, first concatenating many bins into one `PROD` object, then concatenating the `PROD` objects together at the end.

# ShapeTools.py

Defines the functions necessary for shape-based analyses, particulary the `ShapeBuilder`.

## ShapeBuilder class

Does the model building for shape based models. requires a lot more code than the simple `CountingModelBuilder` class!

### doObservables method

first calls its own `prepareAllShapes` method before adding the observables. 
Then also adds bin Categories on top of the normal `doVar` functionality seen in the `CountingModelBuilder`
Then calls the `doCombineDataset` method. (This is not done in the `CountingModelBuilder`)


### doIndividualModels method

This method creates the model of the bin contents (or contents, if unbinned) for each of the individual bins as well as adding bb-lite uncertainties (if they should be added), by creating the constraint pdf
this makes the `shape<bin>_<process>_<rebin>Pdf` and `n_exp_bin<bin>_proc_<proc>` functions (or funciton and Pdf) which get used in the model.

loops over bins, and for each bin starts by making a list of pdfs, bgpdfs, coeffcs, bgcoeffs, signal coeffs

    Inner loop over processes contributing to the bin
    
        skips processes with no expected contribution (also processes where `getYeildScale =0` 
        
        gets (or creates, because it probably doesnt exist yet) the pdf and coefficient functions via `getPdf` call.
        
        Optionally does some `optimizeExistingTemplates` on the pdf -- this seems to just be a performance thing for fast evaluation?
        
        Retrieves the `extraNorm` for the bin, process if it exists -- (i.e. the overall normalization factors)
         if `--X-pack-asymmpows` is set or not. Then for each systematic it tries to pack the normalization object from the systematic into a single `ProcessNormalization` object. 
        Otherwise a `RooProduct` is created from the expected normalization `n_exp_bin<bin>_proc<proc>` and the systematic `AsymPow` objects, call `n_exp_final_bin<bin>_proc<proc>`.
        This adds both the default normalization coefficient and the normalization for each of the associated systematics.
        
        Appends some string atrributes (process, channel, is signal) to the pdf and coefficient objects just created. Then adds these pdf, coefficient to the list of bkg pdfs and coeffs, or the signal ones
        
        Adds the background pdf and coefficent (if bkg). Adds the signal coefficient 
    
    then if barlow beeston parameters are being used:
    
    build either a `CMSHistSum` or `CMSHistErrorPropagator` (depending if the `useCMSHistSum` flag is set), passing it all of the coefficients and pdfs
    
    Checks if a gaussian constraint should be added, or a poisson constraint should be added -- and adds the corresponding constraint
    it also adds this constraint to the list of `extraNuisances` and the list of `extraGlobalObservables` of the model.
    
    Then adds a RooRealSumPDF called `pdf_bin<bin>_proc<proc>_nuis` of all the individual functions contributing to the bblite (`prop_bin<bin>_proc<proc>`) for that bin and process
    
    Then maybe does some optimization stuff.
    
    Then add a `CMSHistFuncWrapper` if bblite is being done, which include the `CMSHistFunc` but also the bblite propbin functoin

then defines the autoMCstats parameter group


### doCombination method

Combines the pdfs created for each of the bins to make the big model pdf

check if channel masks are set, if so add masked channels to a list of masked channels

then for signal, bonly:
    make a RooSimultaneousPdf (the "model")
    
    for each bin:
        get the pdf
        do some  RenameDupObjs
        add the bin pdf to the simulataneous pdf
        
    



### RenameDupObjs method

>>>>> Start of "High-Level helpers"

### prepareAllShapes method

loops over bins

    checks barlow-beeston flag
    loops over processes
        skips processes with no contribution  
        calls `getShape` on the bin + process

        if the shape is None (fake Shape):
            make CMS_fakeObs CMS_fakeObsSet and CMS_fakeWeight objects for this shape
            if the process is data 
                    use binned data-mode and add a RooDataHist to the shapesType list
            otherwise
                    add a RooAbsPdf to the shapeType list

        if the shape is a TH1
           add TH1 to the shapeType List 
           get the number of bins, set that to the value for this channel 
           get the norm
           if th process is data
               set the pdf mode to either poisson or binned (poisson only if poisson option is set and the norm is large enough) 
               set databins to True for every bin that has data
            otherwise
               set background bins to to True for every bin that has background 

        if its a RooDataHist 
            if the process is data
            get the norm and set the pdf type to either binned or poisson (if poisson option is fit and norm is high enough) 
        if tis a RooDataSet:
            get the norm and set the pdf type to unbinned
        if its a TTree
            if the process is data
                set the pdf type to unbinned

        if its a RooAbsPdf or CMSHistFunc:
            just append it to the list of ShapeTypes

        if the normalization isnt 0:
            run some checks that the normalization matches what is specififed in the datacard

    make sure that no bin has data but is empty in all backgrounds (write an error otherwise, ubt do not raise an error)

If there are TH1s in the shapeType list                
   if optimizeTemplateBins:
        find the maximum number of bins any TH1 has 
        add a variable `CMS_th1x`
   otherwise:
        add a separate variable for each combine bin, with the number of histogram bins for that channel

if all channels are TH1s    
    use binned mode
elif theres a RooDataSet or TTree 
    use unbinned mode 
    KYLE NOTE: Also some stuff about the ArgList is being done here
otherwise
    use binned mode
    
### doCombinedDataset method

if theres only one bin, and forceNonSimPDF is set just clone the dataset, import it into the output workspace and return

Make a CombDataSetFactory object and add the data from each bin to it
import the data obs to the output workspace,
print some info

>>>> Start of "Low-level helpers"

### getShape method

returns the cached shape if the object is already cached. If the object doesnt exist for some systematic and allowNoSyst is set, then returns none

finds the process name in the datacard ShapeMap

if it is "FAKE" shape, returns None

does some keyword replacement (for keywords such as $MASS $PROCESS $CHANNEL and $SYSTEMATIC used in the datacard) and then for any user defined model parameters

Then tries to open the appropriate file specified in the datacard

if there is a ":" in the object name, treat it as one of workspace:obj ttree:xvar  or th1:xvar
    if it a workspace 
        tries to get the object from the workspace (first as data, then pdf, then function)
        clone the object (multiple bin/process/systs can refer to the same object)
        do some Optimize MH dependency?
        KYLE NOTE: ?? Look into this
        
        add the object to the cache

        if there is no syst (i.e. it is nominal) 
            then get the normalization through the workspace `arg(normname)` where normname is `%s_norm` and  %s is the object name
            or through a remapping if the norm name has been remapped
            sets a flatParam attribute if is set in the datacard for this normalization

            does OPtimize MH dependency (KYLE NOTE: look into this)
            do some renaming 
        returns the shape object

    if its a TTree:
       makes a new variable using the `doVar` method setting range to min and max of value in TTree
       then makes a RooDataSet
       adds dataset to the cache and returns the dataset

    if its a TH1
       makes a new variable with `doVar` from the object name, setting the range to the histogram X axis range
       makes a RooDataHist 
       adds RooDataHist to a _neverDelete list
       returns the DataHist

    
otherwise should just be a histogram:
    get the histogram, set the name, add it to the cahce, return it 


### getData method

    call the shape2Data method on the result of the `getShape` method and return its return

### getPdf method

Called for a specific process + channel

Returns a pdf if it is already in the cache, if not:

Otherwise:

Makes a nominal pdf using `shape2pdf`, 
then loops over systematics in the datacard:
   -- skips non-shape systematics 
   -- skips systs where the keyline element is 0 for that channel + process
   -- does some parsing of the "pdf" part of the syst spec in the datacard
   -- appends a "morph" to the list of morphs being stored for this process+channel which contains :syst name, datacrd value for that process+channel, the up and down variations.
        IF the `useHistPdf` flag is set to always, these variations are constructed with `shape2pdf`. Otherwise, they are just the result of the `getShape` function
if no morphs have been added, returns the pdf

Then makes an Arglist (or TList) of "pdfs",
loops over the morphs and:
    adds them to the list of pdfs
    if the scaling is not 1 (taken from the datacard) then adds a coefficient (via the `doObj` method)

then handles cases slightly differently depending on the input type (TH1, RooAbsPdf etc ...)

For `TH1`:
   rebins the all "pdfs",
   if the barlow-beeston is used:
        makes a morph CMSHistFunc from the first pdf, 
        sets the vertical morphs to the list of pdf coefficiencts
        sets the vertical morph type ot either quadlinear or logquadlinear
        sets the vertical smoothing region
        calss the `CMsHistFunc` `SetShape` function, for each rebinned hist
   else:
       makes a FastVerticalInterpHistPdf2 with all of the rebinned objects, coefficients and vertical morphing info
    adds the CMSHistFunc or FastVeerticalInterpHistPdf2 object to the cache
    returns the cache cached objects

for `RooHistPdf`:
   similar to above, but always uses FastVerticalInterpHistPdf2 (Possibly also 2D!?) 
    returns the cached objects

for `RooParametricHist`:
   calls the `addMorphs` function on the nominal pdf 
    returns the cached objects

otherwise:
    just has the list of pdf objects

then depending on the shapeAlgo (can be "2a" "2" or else) adds a VerticalInterpHistPdf, FastVerticalInterpHistPdf or VerticalInterpPdf object to the cache.

Returns the cache
   


### isShapeSystematic method

get the systName (possibly remapped), try getting the systUp shape from the `getShape` method. 
If that is None, return False, otherwise return True

### getExtraNorm method

creates the overall normalization functions for shape uncertainties for a given process in a given bin

For fake shapes, None is returned for RooAbsPdfs that are not RooParametricHists or CMSHistFuncs, the nominal normalization is returned (or None)

First gets the normalization of the nominal shape (e.g. by the integral of the histogram)
the loops over systematics
    for each systematic gets the raio of the up and down systematic templates to the nominal
    if necessary (based on datacard input) does appropriate scaling
    RooConstVar objects are created for each of the kappas, and an `AsymPow` object is created for the normalization itself.
    the AsymPow for each syst is added to the list
the list of AsymPows is returned

### rebinH1 method

if OptimizeTemplateBins has been set (all histograms with the same number of bins)
   make a new TH1 with the max number of bins, set only the bin content and errors from the original TH1 
   bin edges are integers (i.e. 0,1,2,3, .... max_bins)

Otherwise just make a new TH1 where the bin edges are the integers

return the rebinned object
    

### shape2Data method

if its not already in the cache
if the shape type is None (i.e. fake shape)
    make a CMS_fakeObs and CMS_fakeWeight object
    add to the cache, return it
otherwise if its TH1
    call the `rebinH1` method and make a RooDataHist
    add to the cache, return it
otherwise return the RooDataHist or RooDataSet object
    

### shape2Pdf method

This function creates (if it is not already created, and in the cache) and then returns an shape object which may be one of

if no shape is provided:
`CMS_fakeObs` (ROOUniform)

if the shape is a TH1:
`CMSHistFunc`
`FastVerticalInterpHistPdf2`
`RooHistPdf`

if the shape is a RooAbsPdf:
`RooAddPdf` : Just does a check, does not create it

if the shape is a RooDataHist:
`RooHistPdf`

if the shape is a RooDataSet:
`RooKeysPdf`

if the shape is `CMSHistFunc`:
`CMSHistFunc`



### checkRooAddPdf method

Makes sure the coefficients in the `RooAddPdf` sum to approximately 1 

### argSetToString method

### optimizeExistingTemplates method

### optimizeMHDependency method
