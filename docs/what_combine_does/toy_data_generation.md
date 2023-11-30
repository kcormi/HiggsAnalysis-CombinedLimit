# Toy Data Generation

For many purposes it is often helpful to generate "toy" datasets, or pseudodata, which represent possible observations. 
For example, these toy datasets can be used for optimizing an analysis without looking at any real data, for debugging and validating fits, for evaluating counterfactuals about what might happen under other assumptions or models, and for estimating the expected distributions of test-statistics when they are not known analytically.

There are different ways of generating such pseudodata, each with different use cases. The methods for generating, storing, and using these toys in combine are described [in other parts of the online documentation.](../../part3/runningthetool/#toy-data-generation) Here, we discuss some basic concepts related to toy datasets and what they represent.

## Asimov Data

One particularly useful toy dataset is referred to as the ["Asimov dataset"](https://ar5iv.labs.arxiv.org/html/1007.1727#S3.SS2).  

The asimov dataset for a given model is defined as the set of observations that give the true parameter values as the estimates of the model values. 
Note that typically, this is not a physically observable dataset, as it may include non-integer observed values. 

This type of toy dataset is typically useful for debugging and for providing a single representative fit. 
Prior to looking at the real data, the asimov dataset is often used for computing expected outcomes of the analysis.

## Frequentist Toys

In a frequentist framework, probability statements are statements about the frequency of observations given a large number of trials.
Within this framework, toy datasets can be used to estimate the frequencies of observations for a given model, which translate directly into probability statements for that model.

Importantly, in the frequentist framework, model parameters have a single well-defined true value; however, the constraints on the parameters in the model are themselves random observables.
This is because the constraints on a given parameter are taken to be the results of some previous experiment, which itself is a random outcome subject to statistical fluctuations.

Performing frequentist tests with toy data involves a generation step and a fitting step.
The generation step generates not only alternative data, but alternative constraint terms which define the alternative models with which the fit will be done. 
i.e. we consider redoing not only the experiment which provides the primary data for the analysis at hand, but also redoing each of the experiments which defined the prefit parameter value estimates used in our model.

Consider, for example a simple counting experiment, with an expected rate $\mu$ and a single nuisance parameter $\theta$, with a gaussian constraint of width one. 
The likelihood for this model is:

$$ \mathcal{L} \propto \mathrm{Poiss}(n | n_\mathrm{exp}(\mu,\theta) ) \cdot e^{(\theta - \tilde{\theta})^2} $$

The frequentist generation step generates a value of $n$ (call it $n_{g}$) and $\tilde{\theta}$ (call it $\tilde{\theta}_g$) for each toy. 
The values of $n_g$ are sample from the Poisson probability mass function with $\mu$ and $\theta$ fixed to their assumed true values. 
The value of $\tilde{\theta}$ is generated from the gaussian probability density function with $\theta$ fixed to its assumed true value.

Then, when fitting these frequentist toys in the new framework each toy will be fit using the generated values $n_{g}$ and $\tilde{\theta}_g$. i.e. using:

$$ \mathcal{L} \propto \mathrm{Poiss}(n_g | n_\mathrm{exp}(\mu,\theta) ) \cdot e^{(\theta - \tilde{\theta}_g)^2} $$

where now $\mu$ an $\theta$ are no longer fixed, but are the parameters of the fit.

## Hybrid Bayes-frequentist Toys

While in frequentist frameworks, the true parameter values are fixed, and are not random variables, it is sometimes useful to consider cases where the parameter values used to generate the data may themselves vary.
These toys can be used to inspect distributions of fit results under ensembles of reasonable true parameter values.

In this form of toy generation, the parameter values are first randomized before generating the toy observations; the constraint terms however, are never changed.

Considering again the example above of a single counting experiment with one parameter of interest, $\mu$, and one nuisance parameter, $\theta$, whose constraint term is a gaussian of width 1, the likelihood is:

$$ \mathcal{L} \propto \mathrm{Poiss}(n | n_{exp}(\mu,\theta) ) \cdot e^{(\theta - \tilde{\theta})^2}. $$

For each hybrid Bayes-frequentist toy, a random value of $\theta$ is first drawn from the gaussian probability distribution defining its constraint term, lets call that value $\theta_g$. 
Then a value for the observation $n$ is drawn using the Poisson term with $n_\mathrm{exp} = n_\mathrm{exp}(\mu, \theta_g)$, called $n_{g}$.

When the fit is performed it is performed using the likelihood: 

$$ \mathcal{L} \propto \mathrm{Poiss}(n_g | n_\mathrm{exp}(\mu,\theta) ) \cdot  e^{(\theta - \tilde{\theta})^2}. $$

Where $\mu$ and $\theta$ are the parameters of the fit and $\tilde{\theta}$ is the original value as used in the nominal analysis.

## Other possibilities

While these are common methods for generating and fitting toys, they are not the only methods, nor the only useful ones.
It can be useful, for example, to generate a set of toys in one given model and fit them with another model. 
