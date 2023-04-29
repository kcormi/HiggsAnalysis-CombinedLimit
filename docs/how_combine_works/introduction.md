# Introduction

Combine is a tool for making statistical analysis based on a model of expected observations and a dataset.
Statistical analyses can include things like, claiming discovery of a new particle or process, setting limits on the existence of new physics, or measuring physics parameters, among other things.
The package is has no physics-specific knowledge, and is completely agnostic to the actual meaning of the analysis being performed, but its usage and development is based around common cases in High Energy Physics.

In order to run the statistical tests, combine must be supplied with a model of expected observations. 
This could be, for example, a model of how many evens are expected to be observed in several bins of a histogram.
It can also be a continuous distribution, codifying the probability density function for observing events with a given set of features.

In general, the model will actually be a set of models which depend on one or more parameters. 
Some of these parameters will be the parameters of interest, such as the cross section for some hypothesized new physics process.
Other parameters will be nuisance parameters, which are not necessarily of interest in and of themselves, but will effect the observation; for example the total luminosity recorded by the detector or the cross section of some background physics process.

The model is a function of the parameters of interest, $\vec{mu}$, and the nuisance parameters, $\theta$, and defines the expected observations.
We will denote the full model as $\mathcal{M}(\vec{\mu},\vec{\theta}$. 

Combine can be divided into several primary functionalities.

1. Giving the user a convenient interface for specifying their model, and from the physics model building a full likelihood function -- the primary object used for the statistical analyses.
2. Performing statistical tests -- the primary measurement outcome
3. Investigating the model, and the statistical tests to spot errors or issues, make improvements, run cross checks and so forth.

The last point is particularly important as model building and statistical tests can go wrong in many places. 
Especially with the large complex models that are used in modern High Energy Physics analyses, many things can go wrong.
While combine automates many pieces of work that you would otherwise have to implement yourself, being able to inspect every step and check that assumptions hold, the results are robust, and everything is working.

### The Model and the Likelihood

The model specifies the expected observations, on a statistical basis. 
Combine provides simple interfaces for defining the model.
For example, the user can provide a set of histograms which define the expected observation; they can also provide a set of histograms defining how the expected distribution changes as a function of some parameter.
The interface is relatively simple.

However, combine then does a lot of *behind the scenes* work to go from the inputs provided by the user to a full statistical model. 
This behind the scenes work comes in essentially two forms.

Firstly, the information provided by the user typically undertermines the model, in that the full model gives the expected observation for any value of the parameter $\vec{\mu}$ and $\vec{\theta}$.
On the other hand, the user typically only supplies the expected values for a small discrete set of points; combine defines and implements the interpolations.

Secondly, the model $\matchcal{M}(\vec{\mu},\vec{\theta})$, defines the expected number of events. 
But the likelihood $\mathcal{L}$, which is used for the statistical tests additionally defines a numerical value for each model determining how $a priori$ likely that model is considered based on the parameter values that define it.
That is to say, a model in which a background has a five times higher cross section than expected is a valid model, but is considered unlikely, and this value is quantified by the likelihood.
The likelihood also defines the probability of observing any actual set of observed events given the expected observation from the model.

The full likelihood $\mathcal{L}(\vec{\mu},\vec{\theta}, \mathrm{data})$, is a mathematical function defined by the model, its parametrs and the observed data.
Combine does the work of defining the full likelihood function based on the model provided by the user. 
With the full model and likelihood, combine is then able to run many types of statistical analyses.

The full likelihood model is implemented within the ROOT framework, based on RooFit/RooStats.

**TODO** reference to section(s) where the model and likelihood definitions are covered in detail.

### Statistical Tests

Once the likelihood has been defined it is useful for running many statistical tests, because it defines how probable any observation is for a given set of parameters, and how a priori likely a given set of parameters are considered.

The likelihood is a typically high-dimensional function of the model parameters $\vec{\mu}$, and $\vec{\theta}$. 
Statistical questions such as "how unlikely is it that my hypothesized new physics cross section is larger than X" can be translated into questions about the likelihood function, such as "What is the largest value of the likelihood function for the observed data if I fix my cross section to X and how does that value compare to the largest value of the likelihood for any possible value of X?".

In general, these questions are quite difficult to answer as they require asking complicated questions about an extremely high-dimensional dimensional and non-trivial function. 
A typical physics model will be a function of one or several parameters of interest, tens or sometimes hundreds of observed and expected values, and tens, hundreds, or sometimes even thousands of nuisance parameters.

One of the key things that combine does is to stop the user from having to implement every statistical physics question, such as "What region of this parameter should be considered unlikely" and precise mathematical questions about the likelihood function. 
However, combine cannot guess the question that a user is trying to ask, and in order for the question to be mathematically well formulated it must first be conceptually well formulated.
Combine cannot remove the burden of understanding what statisitcal tests a user would like to perform, and it is always the users job to understand what they are doing.

A second key task that combine does is to actually perform the necessary evaluations of the likelihood function. 
In general the questions asked of the likelihood function (e.g. "what are the values of the parameters which maximize the likelihood function") cannot be answered analytically.
Typically numerical methods must be used, and combine both implements some of its own tools for performing some of the necessary tasks, as well as making use of external programs such as the MINUIT optimization program.

**TODO** reference to section(s) where the statistical tests are covered in detail

### Inspection and Validation

Given the complexity of the models under consideration, both from a statistical and physics perspective, it is important that the user is able to inspect the model and check it carefully.
There are many things which can easily go wrong; just to name a couple of easy examples, the optimization may get stuck in a local minimum, or the inputs to the model may have large statistical fluctuations leading to untrustworthy results.

To this end, combine provides a suite of tools for inspecting the model and carefully checking that the results of the statistical analysis can be trusted.
These tools are things like: 
- Validation tools which check for common problems in the input model. 
- Visualization tools which show the shape of the likelihood in one or two dimensions
- Tools which plot the post-fit model expectation and uncertainties
- Tools which show you correlations between parameters and changes in which parameters will have the largest effect on the parameters of interest
- Tools which provide numerical values for how well the model matches the data
- Tools which allow you to produce pseudo-data and test the models behaviour against these fake datasets
and many more

It is imperative that the user actually makes use of these tools and endeavours to careful test and validate the model and statistical analysis which they perform.
In any complicated analysis, many things can go wrong, and it can virtually be guaranteed that until checking many elements carefully, some things will go wrong.

**TODO** reference to sections where details are given on validation and other tools for inspection


