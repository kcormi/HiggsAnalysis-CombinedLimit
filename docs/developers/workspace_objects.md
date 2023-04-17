# CMSHistFunc

This is a dervied class of `RooAbsReal`, it gets passed a TH1 object, which is then stored as a `FastHisto`.

It also contains an vector of `FastTemplates` which can are stored, using the `setShape` function.

IT appears to be an alternative to the RooHistPdf, which seems to be used if barlow-beeston parameters are required

# FastHisto

This is a derived class of `FastTemplate`. As well as the vector of values, it stores std::vectors of bin edges and bin widths.
It also implements some convenience methods (`findBin`,`GetAt`,`GetbinContent`) (Likely for compatibility with ROOT calls?)


# FastTemplate

Template class for storing Histograms. Histogram values are copied into an std::vector.
It implements function likes `Log`, `Exp`, `Subtract`, `LogRatio`, `SumDiff`, which do loops over the values and call `std::<math_func>`. Presumably this is part of the 'fast' part?

# FastVerticalInterpHistPdf2

Derived class from `FastVerticalInterpHistPdf2Base`, which is derived from `RooAbsPdf`

Appears to be another alternative to the RooHistPdf, but for cases when barlow-beeston parameters are not required.

it stores its morphs as FastHisto or RooAbsPdf objects


# AsymPow

Class derived from RooRealVar. Represents overall morphing from Asymmetric log-normal uncertainties.

# ProcessNormalization

Contains lists of logNormal, AsymmLogNormal and OtherNormalization functions


# CMSHistSum

derived class from RooAbsReal

used for BarlowBeeston

# CMSHistErrorPropagator

has a barlowBeeston struct with vectors of  a bunch of different values

# CMSHistFuncWrapper


# CombDatasetFactory

just a c++ helper class for making combined datasets because PyROOT apparently cant call some constructors of  RooDataHist
