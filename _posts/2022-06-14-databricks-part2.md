---
layout: post
title: The Grooviest Prog Band with PySpark and Spotify - Part 2
comments: true
categories: [  Music, Data Science ]
---

In [last week's post]({% post_url 2022-05-31-databricks-part1 %}), we looked at how we can access the Spotify API and subsequently create a Spark Dataframe from the data and query the data. This week we'll have a look at how we can use MLflow to manage the machine learning tasks that we'll run on the data. 

## MLflow  

So what is MLflow? According to their docs it is:
> MLflow is an open source platform to manage the ML lifecycle, including experimentation, reproducibility, deployment, and a central model registry  
MLflow tracks the whole machine learning training process from each experiment and run, the parameters used, the metrics from various models, where the models and artifacts are stored all the way through to the productionization of the final model. In this example we'll look at how we can use MLflow with a simple clustering algorithm on the data that was collected from Spotify.  

It turns out there aren't many clustering related gif's so you'll have to do with this one...If anyone knows what 'Cluster Face' means then please drop me a message.  

![](https://media.giphy.com/media/f0LPcE2CZkOKLG3EL0/giphy.gif)  


## Assembling the Data 

One of the differences between sklearn and PySpark ML packages is that PySpark models usually require feature vectors as inputs so it's not good enough to just pass the dataframe to the model without doing a bit of preprocessing.  

Let's import the libraries we need first.  

```python  
import mlflow
import mlflow.spark
from pyspark.ml.feature import VectorAssembler
from pyspark.ml import Pipeline
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.ml.feature import StandardScaler
```  

And then we'll use a few PySpark classes to get the data into the appropriate shape:  
* Firstly we'll need `VectorAssembler`. This will create the feature vectors from the columns we need to feed our model.  
* We also need to scale our data for K-means clustering so one feature doesn't dominate the feature space. For this we can use the `StandardScaler` class and pass in our feature vector.  
* Finally we need our `KMeans` model and the `Pipeline` class to create a pipeline so that all data is processed in the same manner and with the same scaling parameters when passed to the model.  

```python  
# List comp to get our input columns - only using numeric columns
input_cols = [col for (col,dtype) in df.dtypes if (dtype == 'double')]

vecAssembler = VectorAssembler(inputCols=input_cols, outputCol='features')
scaler = StandardScaler(inputCol='features', outputCol='scaled_features', withMean=True, withStd=True)
model = KMeans(featuresCol='scaled_features', seed=42)
pipeline = Pipeline(stages=[vecAssembler, scaler, model])

# Use the clustering evaluator to evaluate our clustering model
evaluator = ClusteringEvaluator()
```  

## Hyperopt - Creating an Objective Function

We'll also want to optimize our clustering algorithm by tuning the hyperparameters. Fortunately the Hyperopt library has us covered for doing this in a distrubuted fashion on Databricks.
> Hyperopt is a Python library for serial and parallel optimization over awkward search spaces, which may include real-valued, discrete, and conditional dimensions.  

To use Hyperopt, one of the first things we need to do is create an objective function which hyperopt will try to minimize during the training process. In our instance, we'll be measuring the quality of or KMeans classifier with PySpark's `ClusteringEvaluator` which computes the Silouhette measure for our models predictions. This returns scores between -1 and 1 where a value close to 1 means all the points in a cluster are close to points in the same cluster and far away from points in the other clusters.  

Because we're looking to maximize this value, we'll want our objective function to minimize the negative value of the score. Our objective function will be given our parameters that we're trying to optimize as an argument (in this case, the value for k in KMeans)  

```python   
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
import mlflow

def objective_function(params):
    
    # Set hypterparameters for tuning
    k_value = params['k_value']
    
    # Create grid (only one feature, more like a line...)
    grid = (ParamGridBuilder()
           .addGrid(model.k, [k_value])
           .build())
    # Not sure we need CV with unsupervised model, can't find example of paramGridMap for unsupervised
    cv = CrossValidator(estimator=pipeline, estimatorParamMaps=grid, evaluator=evaluator, numFolds=3)
    cvModel = cv.fit(df)
    
    score = cvModel.avgMetrics[0]

    # We want to maximize silouhette therefore we take the negative of the score
    return {'loss': -score, 'status':STATUS_OK}
```  

And we also need to define a search space for Hyperopt to work with. For more complex models we could pass many more hyperparameters for a proper grid/random search but for our relatively simple model we'll just look at optimizing `k`. 

```python  
from hyperopt import hp

search_space = {
  'k_value': hp.randint('k_value',3,20)
}
```  

## Training the Model with MLflow and Hyperopt  

Now we've managed to navigate getting this far without breaking too much of a sweat (hopefully) ![](https://media.giphy.com/media/3oKHWspJ9dRB1DSQIE/giphy.gif) we'll use the objective function and setup an MLflow experiment. The things to note here:
* We run our Hyperopt evaluation within our MLflow loop
* Specify the number of trials for Hyperopt to run, in this case it'll be 10. This means Hyperopt will use our search space and in this instance randomly sample 10 integers between 3 and 20 as we defined above.  
* We then use Hyperopt's `fmin` function to sample from our search space and minimize our objective function to return our best hyperparameters.
* We can then subsequently run our model with the best hyperparameters and MLflow will automatically store the model so it can be retrieved whenever it's needed. Lovely stuff.  


```python  
from hyperopt import fmin, tpe, STATUS_OK, Trials
import numpy as np

with mlflow.start_run(run_name='k_means') as run:
  
    num_evals = 10
    
    trials = Trials()
    
    best_hyperparams = fmin(
        fn = objective_function,
        space = search_space,
        max_evals = num_evals,
        trials = trials,
        algo = tpe.suggest,
        rstate = np.random.RandomState(42)
    )
  
    best_k = best_hyperparams['k_value']
    ## Turns out 3 was the best value for K
    
    model.setK(best_k)
    
    # Retrain pipeline using best k-value
    pipelineModel = pipeline.fit(df)
    predDF = pipelineModel.transform(df)
    silouhette = evaluator.evaluate(predDF)
    
    # Log param and metric for the final model
    mlflow.log_param("k_value", best_k)
    mlflow.log_metric("silouhette", silouhette)
```  

### Brucey Bonus  

And a little Brucey Bonus for all the fellow prog rock fans out there. Here's the top 3 tracks for each of the bands for which we retrieved data ranked by Spotify's 'Danceability' metric, not something traditionally associated with the genre. Not only due to the odd time signatures but the levels of energy needed to make it through all 4 sides of Yes' [Tales from Topographic Oceans](https://en.wikipedia.org/wiki/Tales_from_Topographic_Oceans) album. 

![](/images/prog_chart.png)  

And rather ironically, Genesis' most danceable song is...'I Can't Dance'.  











