# Overview

Combine is a tool for statistical inference. It can essentially be divided into two major parts.

Firstly, combine builds a statistical model, in the form of a likelihood. 
This defines the probability of observing any given set of data given the model (this implicitly or explicitly includes the physics model, but also the detector model, systematics etc).

Secondly combine provides a suite of tools and routines for fitting the model to data, running statistical tests, inspecting the fits, plotting their results and so on.

## The Likelihood Model

Combine builds a likelihood model through the `text2workspace.py` script.
This script takes as an input a `Datacard` which defines the observables being considered, the observations, the processes which contribute, the uncertainties, and various relationships between each of these.
The `text2workspace.py` script takes this datacard and any other input files it references (for example root files which may contain histograms) and builds a `RooWorkspace` which defines the likelihood model.

The likelihood takes the general form:

$ \mathcal{L} =  \mathcal{L}_\mathrm{data} \cdot \mathcal{L}_\mathrm{constraint}$

Where $ \mathcal{L}_\mathrm{data} $ is the likelihood of observing the data given your model, and $\mathcal{L}_\mathrm{constraint}$ represent some external constraints.
The data term determine how probable any set of data is given the model (which may depend on many parameters). 
The constraint term does not depend on the observed data, but rather encodes other constraints which may be constraints from previous measurements (such as Jet Energy Scales) or prior beliefs about the value some parameter in the model should have.

In general each is, in turn, composed of many sublikelihoods. 
For example in a binned shape analysis every bin has its own term representing the probability of observing the actual observed number of events given the expected number of events.
Similarly, for every systematic uncertainty there will be some constraint term associated with the uncertainty.

This model is extremely general. Without yet specifying any function forms for these likelihoods, this model can represent anything at all.
However, there are typical forms that the likelihoods take which will cover most use cases, and for which combine is primarily designed.

Combine is designed for constructing data likelihoods which refer to observation of some count of events, though they can be binned or unbinned.
The constraint terms also often take on common forms, such as that of a gaussian distribution.

For conceptual clarity, it is often also useful to introduce the concept of the underlying "Model".

This model defines the probability of observing certain data, given some parameters; i.e. it tells you what the expected observations are for any set of parameters.

In this way of thinking we can rewrite our likelihood terms above. The likelihood of the data depends on the model $\mathcal{L}_\mathrm{data} = P(\mathrm{data} | \mathrm{Model} )$.
and the likelihood of the contraints tells us the likelihood of the model given other external information we have. $\mathcal{L}_\mathrm{contraints} = L(\mathrm{Model} | \mathrm{contraints )$.

The model itself encodes how the expected observations change as a function of the model parameters. e.g. how many more or less events I expect to see given some change in the jet energy scale or the ttbar cross section.


### Binned Likelihood Models

For a binned likelihood, the probability of observing a certain number of counts, given a model takes on a simple form.
It is given just by  $\mathrm{Poiss}(\mathrm{obs}; n_\mathrm{exp})$, i.e. it is a poisson distribution with the mean given by the expected number of events in the model.
This is the underlying likelihood model used for every binned analysis. 
All of the differences between different analyses are encoded in how $n_\mathrm{exp}$ depends on the model parameters.

### Unbinned Likelihood Models


### Constraint Likelihoods

In principle, the constraint terms in the likelihood can be arbitrary. 
They simply encode the probability of model parameters taking on a certain value.
This might represent the probability that a cross section has a certain value, or that the true luminosity is shifted by some amount as compared to the nominal value.
In practice, most constraint terms are gaussian, of the form $\mathcal{N}(0,1)$ where the model parameter, often denoted $\theta$, has been defined such that 0 is its nominal value and $\pm1$ represent its value shifted to the edges of the 68\% confidence range; i.e. these two values define the bounds of the region in which you expect to find the parameter 68\% of the time.

It is not *necessary* that these constraint terms take on such a gaussian form. They can be arbitrary functions.
However, it is very convenient to use gaussian constraints for a number of reasons\*. 
Furthermore, any co-ordinate transformation of the parameter values can be absorbed into the definition of the parameter; i.e. the likelihood model is independent of how it is parameterized.
A reparameterization would change the mathematical form of the constraint term, but would also simultaneously change how the model depends on the parameter in such a way that the total likelihood is unchanged.
e.g. if you define  $\theta = \sigma(tt)$ or $\theta = \sigma(tt) - \sigma_0$ you will change the form of the constraint term, but the you will not change the overall likelihood.

### Models

Most of the magic and variability of the different likelihoods is encoded in what I have refered to as the "model"; i.e. the relationship between $n_\mathrm{exp}$ and the model parameters.

Although combine is very flexible in letting you construct different models, there are a number of components which are in every model, or are most commonly used.

**Channels**: The model is a set of models for multiple channels. $\mathcal{M} = \{ \mathcal{m}_{c1}, \mathcal{m}_{c2}, .... \mathcal{m}_{cN}\}a$ .
    and the combined data likehood for all of the channels is the product of the data likelihoods for each channel. \mathcal{L}_{\matrhm{data}}(\mathcal{M}) = \Prod_\mathcal{i} \mathcal{L}_\mathrm{data}(\mathcal{m}_i)$

**Processes**: The model consists of a sum over different processes, each processes having its own model defining it. $\mathcal{m}_c =  \Sum_p \mathcal{m}_{c,p}$

The processes are typically correlated across multiple channels (the same process may appear in multiple channels and its expectation in different channels will depend on common parameters).
Different processes may also depend on the same parameters (e.g. the number of expected ttbar events and ttH events will both depend on the luminosity).
However, different channels are assumed to be independent observations. i.e. if you repeated the observation many times the observations in different channels would be uncorrelated.

**Modifiers**: A number of parameters can modify the model expectation. These include the parameters of interest (those being measured) as well as nuisance parameters, which may not be of interest but still affect the model expectation.

There is a lot of flexibility in defining custom modifiers both for parameters of interest and nuisance parameters, such that they may alter the model in almost arbitrary ways.
However, there are typical modifiers which cover most use cases.

**Parameter of interest**: By default, the parameter of interest simply scales the overall expectation from any signal processes. $m_{c,\mathrm{sig}(\mu) = \mu * m_{c,\mathrm{sig}}^0

**Multiplicative Modifiers**: Generally speaking, there are many modifiers which modify the model in a multiplicative fashion. $m_{c,p}(\theta) = f(\theta) m_{c,p}^0$
    note that this is still quite general, as $f$ can take on arbitrary function forms.
    However, the most common forms are:
        - $f = \theta$
        - $f = \kappa^{\theta} $

**Additive Modifiers**: We also often use modifiers which modify the model in an additive way. $m_{c,p}(\theta) = m_{c,p}^0 + f(\theta)$
    where again, $f$ can take o arbitrary functional forms, leaving this quite general.
    The most common forms are:
        

The resolution order of these parameters is important, since $ f\cdot m + g \neq f\cdot(m+g)$. 




