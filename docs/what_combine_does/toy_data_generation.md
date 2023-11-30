# Toy Data Generation

For many purposes it is often helpful to generate "toy" datasets, or pseudodata. 
For example, these toy datasets can be used for optimizing an analysis without looking at any real data, for debugging and validating fits, for evaluating counterfactuals about what might happen under other assumptions or models, and for estimating the expected distributions of test-statistics when they are not known analytically.

There are different ways of generating such pseudodata, each with different use cases.

# Asimov Data

One particularly useful toy dataset is typically referred to as "Asimov toy" generation, and the dataset is referred to as the "Asimov dataset".  
The asimov dataset is defined as the set of observations that give the true parameter values as the estimates of the model values. 
Note that typically, this is not a physically observable dataset, as it may include non-integer observed values, however it can be mathematically well-defined due to cancellations in the likelihood ratio which remove undefined terms. 

This type of toy dataset is typically useful for debugging and for providing a single representative fit. 

# Frequentist Toys

In a frequentist framework, probability statements are statements about the probability of observations given a large number of independent variations.
Within this framework, toy datasets can be used to evaluate the frequencies of occurences for a given model.
They answer questions of the form "what distribution of resulsts should I expect if this experiment were repeated a large number of times?"

Importantly, in the frequentist framework, model parameters have a single well-defined true value; however, the constraints on parameters are themselves random observables.
This is because the constraints on a given parameter are taken to be the results of some previous experiment or experience, which itself is a random outcome subject to statistical fluctuations.

Given these above points, running an ensemble of frequentist tests with toy data is performed as a two step process.
The generation step generates not only alternative data, but alternative constraint terms. 
i.e. we consider redoing not only the experiment which provides the primary data for the analysis at hand, but also redoing each of the experiments which defined the parameter value estimates used in our model.

Consider, for example a simple counting experiment, with an expected rate $\mu$ and a single nuisance parameter $\theta$, with a gaussian constraint of width one. 
The likelihood for this model is:

$$ \mathcal{L} \propto \mathrm{Poiss}(n | n_\mathrm{exp}(\mu,\theta) ) e^{(\theta - \tilde{\theta})^2} $$

Then the generation step generates values of $n$ from the poisson probability mass function with $\mu$ and $\theta$ fixed to their assumed true values, *and* also generating a new value of $\tilde{\theta}$.
Just as the value of $n$ is generated from the Poisson pmf, the value of $\tilde{\theta}$ is generated from the gaussian probability density function with $\theta$ fixed to its assumed true value.
Lets call these generated values $n_{g}$ and $\tilde{\theta}_{g}$, where for each toy, different values of $n$ and $\tilde{\theta}$ will be generated, so $g$ can be seen as indexing the toy.

Then, when fitting these frequentist toys in the new framework the fit will be done to the data using the generated values $n_{g}$ and $\tilde{\theta}_g$. i.e. using:


$$ \mathcal{L} \propto \mathrm{Poiss}(n_g | n_\mathrm{exp}(\mu,\theta) ) e^{(\theta - \tilde{\theta}_g)^2} $$

where now $\mu$ an $\theta$ are no longer fixed, but are the parameters of the fit.

# Hybrid Bayes-frequentist Toys

While in frequentist frameworks, the true parameter values are fixed, and are not random variables, it is sometimes useful to consider cases where the parameter values used to generate the data may themselves vary.
These toys can be used to answer questions of the form "considering an ensemble of universes with different true parameter values, what distribution of results would expect for this experiment I am doing."

In this form of toy generation, the parameter values are first randomized before generating the toy observations. The constraint terms however, are never changed.

Considering again the example above of a single counting experiment with one POI $\mu$ and one nuisance parameter $\theta$ whose constraint term is a gaussian of width 1, the likelihood is:


$$ \mathcal{L} \propto \mathrm{Poiss}(n | n_{exp}(\mu,\theta) ) e^{(\theta - \tilde{\theta})^2}. $$

To generate the hybrid Bayes-frequentist toys, a random value of $\theta$ is first drawn from the gaussian probability distribution defining its constraint term, lets call that value $\theta_g$. 
Then a value for the observation $n$ is drawn using the Poisson term with $n_\mathrm{exp} = n_\mathrm{exp}(\mu, \theta_g)$, called $n_{g}$.

When the fit is performed it is performed using the likelihood: 

$$ \mathcal{L} \propto \mathrm{Poiss}(n_g | n_\mathrm{exp}(\mu,\theta) ) e^{(\theta - \tilde{\theta})^2}. $$

Where $\mu$ and $\theta$ are the parameters of the fit and $\tilde{\theta}$ is the original value as used in the nominal analysis.

# Other possibilities

While these are common methods for generating and fitting toys, they are not the only methods, nor the only useful ones.
It can be useful, for example, to generate a set of toys in one given model and fit them with another model. 
