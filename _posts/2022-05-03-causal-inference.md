---
layout: post
title: Causal Inference and the dreaded OVB
comments: true
categories: [ Stats ]
---

I've recently been working through an excellent resource on [causal inference](https://matheusfacure.github.io/python-causality-handbook/landing-page.html#)
from Matheus Facure. Machine learning models are great at predicting things (well, in some cases...\*cough\* [Zillow](https://insidebigdata.com/2021/12/13/the-500mm-debacle-at-zillow-offers-what-went-wrong-with-the-ai-models/) \*cough\*). You throw some data at them, make some predictions and try to find a model which gives you the best accuracy (or whatever measure it is you're trying to optimize). Some models may be explainable as to why they make their predictions and some are black box models which can be incredibly difficult to interpret which in turn runs the risk of a lack of trust in the predictions. However, consider a machine learning model trained on airline prices...it would see that ticket sales a relatively low when the prices are low (during term time for example) and ticket sales go up as prices go up (during school holidays). A naive model may suggest increasing prices to increase sales...

![](https://media.giphy.com/media/4Ya8UtZz4PEuk/giphy.gif)

ML models aren't so great at answering the 'what if' questions..."what would happen if I changed the price of X?", "How do socio-economic factors affect Y?". Although it's relatively easy to spot association patterns in data, what we really want to examine are the causal patterns. How can we figure out when an association is actually a causation?  

For a more in depth analysis, I'd suggest having a look at:  
* Matheus Facure's [resource](https://matheusfacure.github.io/python-causality-handbook/01-Introduction-To-Causality.html)  
* [Mastering Metrics](www.masteringmetrics.com)  

In this post I'm going to explore the omitted variable bias - how biased are the parameters we estimate from our model and how are these affected by the inclusion and exclusion of selected variables.  

### Omitted Variable Bias  

I'll use a very simple example to work through this. Estimating points scored by a rugby team from number of tries, conversions and penalties. But wait, eagle eyed readers will realise this is completely deterministic so we'll add some randomness to the data as if it were a stochastic process - let's assume that depending on the amount or lack of 'jouer' involved in a try, the ref can award +/- a normally distributed variable with zero mean and a standard deviation of 5.  

```python  
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

df = pd.read_csv('rugby_regression.csv', index_col=0)
df.columns = ['tries', 'conversions', 'penalty_goals', 'points']
# Add some randomness to the data
df['points'] = df['points'] + np.random.normal(loc=0, scale=5, size=df.shape[0])
# Remove any scores below zero
df.loc[df['points'] < 0, 'points'] = 0
```  

And we end up with a dataset looking something like this...

![](/images/2022-05-03-causal-inference-9180d284.png)

Our long model for this would be:  

$$
\hat {Points}_i = \beta_0 + \beta_1 \cdot {Tries}_i + \beta_2 \cdot {Conversions}_i + \beta_3 \cdot {Penalty Goals}_i
$$

That is, our predicted points are a linear combination of tries, conversions and penalties. Now if we run a linear regression of points on tries, conversions and penalties, it should be fairly easy to figure out what each of the coefficients will be...  

![](https://media.giphy.com/media/AiqLB6AdhDVESBSCLc/giphy.gif)

If you said 5, 2 and 3 then give yourself a pat on the back. So let's double check this:

```python  
long_model = smf.ols('points ~ tries + conversions + penalty_goals', data=df).fit()  
long_model.summary()  

=================================================================================
                    coef    std err          t      P>|t|      [0.025      0.975]
---------------------------------------------------------------------------------
Intercept         0.7626      0.861      0.886      0.377      -0.934       2.459
tries             4.9804      0.352     14.141      0.000       4.287       5.674
conversions       1.8559      0.393      4.720      0.000       1.081       2.630
penalty_goals     2.9084      0.257     11.295      0.000       2.401       3.416
=================================================================================

```  

Our model has estimated these parameters fairly well. If we hadn't added our ref's try bonus to our data then these values would be exactly 5, 2 and 3 as expected.  

### The Short Model  

So now imagine we're in a situation whereby we only have the number of tries available to us, in this case our model looks more like:  

$$
\hat {Points}_i = \beta_0 + \beta_1 \cdot {Tries}_i + u_i  
$$

What happens if we run this regression now?  
```python  
really_short_model = smf.ols('points ~ tries', data=df).fit()
print(really_short_model.summary().tables[1])

==============================================================================
                 coef    std err          t      P>|t|      [0.025      0.975]
------------------------------------------------------------------------------
Intercept      7.0832      0.840      8.429      0.000       5.428       8.738
tries          5.5807      0.225     24.760      0.000       5.137       6.025
==============================================================================

```  

If we don't include anything other than the number of tries scored in our model, the best fit for the model estimates a baseline score of 7.08 and that a try is worth 5.6 points +/- ~0.5. We now have a biased estimator - essentially the coefficient of the tries variable is trying to account for the other missing variables.  

Another way of estimating this coefficient is:  
$$
\beta_1^{*} = \frac{Cov(Y_i, x_{1i})}{Var(x_{1i})}
$$  

```python  
beta_1_biased = df['points'].cov(df['tries']) / df['tries'].var()
print(beta_1_biased)

>>> 5.580725846785696  
```  

Another sanity check is to confirm that:
> "Short equals long 
> plus the effect of omitted
> times the regression of omitted on included"  

Which means the parameters from our short model should be equal to the coefficients for our long model + the effect of omitted variable in the long model multiplied by the regression of each omitted variable on the included variable.
