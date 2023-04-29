# overview

# ChannelCompatibilityCheck

# run method 

   First gets the parameter of interest and the RooSimultaneousPDf 
   
   Then loops over channels and gets the pdf for each channel
   then replaces the POI in each channel pdf with a new POI specific to that channel
   and adds this new channel pdf to a new SimultaneousPDF created for the full fit

   creates a `CascadeMimizer` object and 

...


# AsymptoticLimits

Calculates the expected and observed limits using the asymptotic formulae from https://arxiv.org/abs/1007.1727

particularly using as the test statistic either qmu or qmu(tilde)
which use the log likelihood ratio  for r > r\_bestfit and 0 otherwise.
qmu(tilde) uses the additional change that if r\_bestfit < 0, then the ratio is taken with respect to the likelihood at r=0, rather than at r\_bestfit.

For the asymptotic approximation, the pdf of these test statistics is calculated in the paper using the Wald approximation.
from the calculation of this pdf, relations for the CLs limits can be found and are given in
cms.cern.ch/iCMS/jsp/openfile.jsp?tp=draft&files=AN2011_298_v3.pdf

in particular:
CL_s  = (1 - normal_cdf(sqrt(qmu_data)))/(normal_cdf(qmu_Asimov)-sqrt(qmu_data))

and the uncertainties are given by analytic functions.

to find mu for particular CLs value (e.g. 0.05), the algorithm sequentially guesses values of mu, keeping track of the final CLs
and if it is above or below the desired result. Once the desired result has been reached to sufficient precision, the algorithm stops.

## run method

First iterates over parameters to see if there any discrete parameters in the model

Then runs the `runLimitExpected` method (unless expected is explicitly not requested)
Then runs the `runLimit` method (unless only expected is requested)

Then prints the results and returns the boolean of if the limit ran succesfully

### runLimitExpected method

checks if the limit is being calculated from a grid, if so, calls the `calculateLimitFromGrid` on the grid.

If not, then the limit is calculated by first creating an asimov dataset. 
The parameter of interest, r, is set to a small value (1% of rmax) and then a fit is performed to get the best fit point and best fit nll.
Once the fit is run, for each of the requested quantiles for the expected limit, they are found using a minos-method, scanning the poi and looking for the appropriate crossing.
This is done by calling the `findExpectedLimitFromCrossing` method. 
For the various calls,  to `findExpectedLimitFromCrossing` appropriate maximum and minimum r values are set to avoid rescanning or going to far in the scan

### findExpectedLimitFromCrossing method

# Signficance

### run method

Does some basic setup, if `prefit_` is set, then runs an initial prefit

then calls the `runSignificance` method

### RunSignificance method

Uses either a Brute force method, or a minos method

The brute force method uses `significanceFromScan`

if Brute force is not used then "minos" is used, a `ProfileLikelihoodTestStat` object is created

### significanceFromScan method

Creates a CascadeMinimizer, and runs an initial fit.

then steps through poi values and calls the minimizer `improve` function at every point.
The nll is compared to the best fit nll, and if a better nll is found, then it is taken as the new best fit point

At each point the difference between the nll and the refnll is saved to a tgraph.
Optionally the points on the graph can be fit with a function "A\*b^(abs(x-c)) + d"
Then the fit result is taken either from the fit or the maximum difference between the nll values


# MultiDimFit

### runSpecific method

gets the pdf

make an iterator over the parameters of interest
get the rooRealVars for each POI, set them constant if floatOtherPOIs is not set
keep track of number of floating and constant POIs

do an intial fit with the `doFit` routine, unless the option to skip it has been set

if there is an initial result from the preliminary fit, or a snapshot, load the values 
(KYLE NOTE: and store them in the tree? Not clear to me)

If robustHesse is used:
    create a RobustHesse object and run its hesse method




# HybridNew

HybridNew is a toy-based statistical evaluation routine, which can run a number of different statistical tests (e.g. limits or significance tests)

## run method

the main run method consists of a simple switch statement, which then runs one of the "limit, significance, pvalue or testStatistics` routines.

