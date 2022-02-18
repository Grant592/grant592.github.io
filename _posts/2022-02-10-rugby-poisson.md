---
layout: post
title: Can tries scored be modelled as a Poisson process?
comments: true
categories: [ Rugby, Stats ]
---

So I thought I'd do a post for those interested in rugby this week and look at how we can model the number of tries scored per team per game. I'll look at fetching the data from a database, processing the data and finally what sort of distribution we can use to best model the data. Let's start with accessing the database.

```python
import mysql.connector
import pandas as pd
import numpy as np
```


```python
conn = mysql.connector.connect(
    user='user',
    password='password',
    database='db'
)

cur = conn.cursor()
```

## Querying the Database

The aim of the query is to return all of the tries scored and the time in the match that they were scored so we could then calculate the average time period between tries. This sounded simple at first, however I realised I also needed to find a way to return an entry for a team in a fixture even if they didn't score a try so we could consider the additional 80 minutes between tries scored.


```sql

// Select any fixtures between premiership teams
WITH fixtures AS (
  SELECT 
    f.fxid,
    f.FxDate
  FROM
    fix_data f 
  WHERE 
    f.FxHTID IN ( 84,1000,1050,1100,1150,1250,1300,1350,1400,1450,1500,1550,3300) 
  AND
    f.FxATID IN ( 84,1000,1050,1100,1150,1250,1300,1350,1400,1450,1500,1550,3300)
)

// Select only tries and the match time they were scored
SELECT 
  m.fxid as fxid, 
  team_id,
  fixtures.`FxDate`, 
  PLID, 
  MatchTime, 
  `ID`,
  1 as counter
FROM 
  match_data m 
INNER JOIN
  fixtures
ON
  fixtures.fxid = m.fxid
WHERE EXISTS
  (SELECT
    1
   FROM
    fixtures f
   WHERE
     f.fxid = m.fxid
   )
AND
  action = 9 

/* We then need to check for games whereby there wasn't a try scored by a team
and return a dummy entry for this match. We can query with a NOT EXISTS to check
that a try didnt occur in a fixture for a team */

UNION

SELECT DISTINCT
  m.fxid as fxid, 
  team_id, 
  fixtures.`FxDate`, 
  -1 AS PLID, 
  9959 AS MatchTime, 
  -1 AS `ID` ,
  0 as counter
FROM 
  match_data m 
INNER JOIN
  fixtures
ON
  fixtures.fxid = m.fxid
WHERE NOT EXISTS (
  SELECT
    fxid,
    team_id
  FROM
    match_data m2
  WHERE
    m2.fxid = fixtures.fxid
  AND
    m2.team_id = m.team_id
  AND
    action = 9
  )

"""
```


```python
cur.execute(query)
data = cur.fetchall()
df = pd.DataFrame.from_records(data, columns=[x[0] for x in cur.description])
df.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>fxid</th>
      <th>team_id</th>
      <th>FxDate</th>
      <th>PLID</th>
      <th>MatchTime</th>
      <th>ID</th>
      <th>counter</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>23312</td>
      <td>1150</td>
      <td>2019-03-30</td>
      <td>28736</td>
      <td>1601</td>
      <td>20100663</td>
      <td>1</td>
    </tr>
    <tr>
      <th>1</th>
      <td>23312</td>
      <td>3300</td>
      <td>2019-03-30</td>
      <td>11627</td>
      <td>2318</td>
      <td>20100751</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>23312</td>
      <td>3300</td>
      <td>2019-03-30</td>
      <td>20444</td>
      <td>4559</td>
      <td>20102079</td>
      <td>1</td>
    </tr>
    <tr>
      <th>3</th>
      <td>23312</td>
      <td>1150</td>
      <td>2019-03-30</td>
      <td>10304</td>
      <td>6907</td>
      <td>20102962</td>
      <td>1</td>
    </tr>
    <tr>
      <th>4</th>
      <td>23638</td>
      <td>1250</td>
      <td>2021-04-10</td>
      <td>30387</td>
      <td>412</td>
      <td>25585378</td>
      <td>1</td>
    </tr>
  </tbody>
</table>
</div>




```python
df.fillna(0, inplace=True)

# Sort values by fxid and match time so we have an ordered dataframe
df = df.sort_values(['fxid', 'MatchTime'])
# Calculate the cumulative sum of tries during the game so we have
# tries for at each point during the game
df['try_for'] = df.groupby(['fxid', 'team_id']).cumsum()['counter']
```


```python
# We can also see an example of when a try wasn't scored
df[df['fxid'] == 118052]
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>fxid</th>
      <th>team_id</th>
      <th>FxDate</th>
      <th>PLID</th>
      <th>MatchTime</th>
      <th>ID</th>
      <th>counter</th>
      <th>try_for</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>153</th>
      <td>118052</td>
      <td>1500</td>
      <td>2017-09-29</td>
      <td>8442</td>
      <td>539</td>
      <td>14684544</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>154</th>
      <td>118052</td>
      <td>1500</td>
      <td>2017-09-29</td>
      <td>9486</td>
      <td>5124</td>
      <td>14685365</td>
      <td>1</td>
      <td>2</td>
    </tr>
    <tr>
      <th>155</th>
      <td>118052</td>
      <td>1500</td>
      <td>2017-09-29</td>
      <td>8442</td>
      <td>7723</td>
      <td>14686006</td>
      <td>1</td>
      <td>3</td>
    </tr>
    <tr>
      <th>2213</th>
      <td>118052</td>
      <td>3300</td>
      <td>2017-09-29</td>
      <td>-1</td>
      <td>9959</td>
      <td>-1</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# The next function calculate the total number of tries at each point in the game
# by grouping by fxid and using the cumsum function again
df['cum_try_total'] = df.groupby('fxid').cumsum()['counter']


# Subsequently, we can calculate the tries against at any point in the match as well
df['try_against'] = df['cum_try_total'] - df['try_for']

df[df['fxid'] == 118052]
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>fxid</th>
      <th>team_id</th>
      <th>FxDate</th>
      <th>PLID</th>
      <th>MatchTime</th>
      <th>ID</th>
      <th>counter</th>
      <th>try_for</th>
      <th>cum_try_total</th>
      <th>try_against</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>153</th>
      <td>118052</td>
      <td>1500</td>
      <td>2017-09-29</td>
      <td>8442</td>
      <td>539</td>
      <td>14684544</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
    </tr>
    <tr>
      <th>154</th>
      <td>118052</td>
      <td>1500</td>
      <td>2017-09-29</td>
      <td>9486</td>
      <td>5124</td>
      <td>14685365</td>
      <td>1</td>
      <td>2</td>
      <td>2</td>
      <td>0</td>
    </tr>
    <tr>
      <th>155</th>
      <td>118052</td>
      <td>1500</td>
      <td>2017-09-29</td>
      <td>8442</td>
      <td>7723</td>
      <td>14686006</td>
      <td>1</td>
      <td>3</td>
      <td>3</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2213</th>
      <td>118052</td>
      <td>3300</td>
      <td>2017-09-29</td>
      <td>-1</td>
      <td>9959</td>
      <td>-1</td>
      <td>0</td>
      <td>0</td>
      <td>3</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>




```python
## Matchtime in format mmss but leading zeros missing. Pad with zeros the then convert to TimeDelta
df['MatchTime'] = df['MatchTime'].astype('str').str.pad(width=4, side='left', fillchar='0')

# Add a colon to the match time value
df['MatchTime'] = df['MatchTime'].apply(lambda x: x[:2] + ':' + x[2:])

df['MatchTime']
```




    0       16:01
    1       23:18
    2       45:59
    3       69:07
    4       04:12
            ...  
    2206    36:06
    2207    41:32
    2208    53:48
    2209    56:25
    2210    76:50
    Name: MatchTime, Length: 2254, dtype: object  



The following function converts all the MatchTime strings to a proper datetime, also taking into account the dummy entries for the matches where there was no try for a team.


```python
import datetime
def convert_to_delta(time_string):
    
    if time_string == '.0':
        delta = datetime.timedelta(hours=1, minutes=20, seconds=0)
        return delta
    
    if int(time_string[:2]) > 59:
        new_min = int(time_string[:2]) - 60
        new_time = f'01:{new_min}:{time_string[3:]}'
        t = datetime.datetime.strptime(new_time, '%H:%M:%S')
        delta = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        
        return delta
    else:
    
        t = datetime.datetime.strptime(time_string, '%M:%S')
        delta = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        
        return delta
```


```python
# Run the funtion and also convert to seconds
df['MatchTimeDelta'] = df['MatchTime'].apply(convert_to_delta)
df['MatchTimeSeconds'] = df['MatchTimeDelta'] /  np.timedelta64(1, 's')
```

The next cell applies some if/else logic to calculate the amount of time between tries but also spans the time across multiple games including games whereby there was no try.


```python
all_df = []

for row_num, rows in df.sort_values(['team_id','fxid', 'MatchTime']).groupby(['team_id']):
    match_time_seconds_delta = []
    n_rows = rows.shape[0]
    
    for idx in range(n_rows):
        if idx == 0 or idx == n_rows:
            match_time_seconds_delta.append(rows.iloc[idx]['MatchTimeSeconds'])
            continue
            
        elif rows.iloc[idx]['MatchTimeSeconds'] < rows.iloc[idx - 1]['MatchTimeSeconds']:
            seconds =  4800 - rows.iloc[idx - 1]['MatchTimeSeconds'] + rows.iloc[idx]['MatchTimeSeconds']
            match_time_seconds_delta.append(seconds)
            
        elif rows.iloc[idx]['MatchTimeSeconds'] == 5999.0:
            seconds =  4800 - rows.iloc[idx - 1]['MatchTimeSeconds'] + 4800
            match_time_seconds_delta.append(seconds)
            
        elif rows.iloc[idx - 1]['MatchTimeSeconds'] == 5999.0:
            seconds = rows.iloc[idx]['MatchTimeSeconds']
            match_time_seconds_delta.append(seconds)
            
        else:
            seconds =  rows.iloc[idx]['MatchTimeSeconds'] - rows.iloc[idx - 1]['MatchTimeSeconds']
            match_time_seconds_delta.append(seconds)
    
    
            
    rows['MatchSecondsDelta2'] = match_time_seconds_delta
    all_df.append(rows)
    
```


```python
# We know the data is sorted, so reset the index and for any fixture/team without a try, 
# roll the 80 minutes over into the next try scoring period
for d in all_df:
    d.reset_index(inplace=True)
    no_scores_idx = d[d['ID'] == -1].index
    for idx in no_scores_idx:
        d.loc[idx + 1, 'MatchSecondsDelta2'] += d.loc[idx, 'MatchTimeSeconds']
    
df = pd.concat(all_df)

df.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>level_0</th>
      <th>index</th>
      <th>fxid</th>
      <th>team_id</th>
      <th>FxDate</th>
      <th>PLID</th>
      <th>MatchTime</th>
      <th>ID</th>
      <th>counter</th>
      <th>try_for</th>
      <th>cum_try_total</th>
      <th>try_against</th>
      <th>MatchTimeDelta</th>
      <th>MatchTimeSeconds</th>
      <th>MatchSecondsDelta2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>11</td>
      <td>118011</td>
      <td>84</td>
      <td>2017-09-01</td>
      <td>20339</td>
      <td>03:52</td>
      <td>14394797</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0 days 00:03:52</td>
      <td>232.0</td>
      <td>232.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>13</td>
      <td>118011</td>
      <td>84</td>
      <td>2017-09-01</td>
      <td>20339</td>
      <td>27:55</td>
      <td>14395376</td>
      <td>1</td>
      <td>2</td>
      <td>3</td>
      <td>1</td>
      <td>0 days 00:27:55</td>
      <td>1675.0</td>
      <td>1443.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2</td>
      <td>16</td>
      <td>118011</td>
      <td>84</td>
      <td>2017-09-01</td>
      <td>19218</td>
      <td>70:10</td>
      <td>14400577</td>
      <td>1</td>
      <td>3</td>
      <td>6</td>
      <td>3</td>
      <td>0 days 01:10:10</td>
      <td>4210.0</td>
      <td>2535.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>3</td>
      <td>67</td>
      <td>118023</td>
      <td>84</td>
      <td>2017-09-09</td>
      <td>19087</td>
      <td>10:58</td>
      <td>14491379</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0 days 00:10:58</td>
      <td>658.0</td>
      <td>1248.0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>4</td>
      <td>68</td>
      <td>118023</td>
      <td>84</td>
      <td>2017-09-09</td>
      <td>84</td>
      <td>24:20</td>
      <td>14491595</td>
      <td>1</td>
      <td>2</td>
      <td>2</td>
      <td>0</td>
      <td>0 days 00:24:20</td>
      <td>1460.0</td>
      <td>802.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Convert the times to minutes
df['MatchTimeMinDelta'] = df['MatchSecondsDelta2'] / 60


intervals = [0,10,20,30,40,50,60,70,80,90,float('inf')]

pd.cut(df['MatchTimeMinDelta'], bins=intervals).value_counts().plot(kind='bar')
```




    <AxesSubplot:>




    
![png](/images/rugby_poisson_27_1.png)
    


At a brief glance, it appears the timing of tries being scored fits an exponential (geometric if we look at it in discrete bins) distribution. So in reality, the most likely time for a try to be scored after a previous try is within the next 10 minutes. Simple.

### Are these tries poisson distributed?

A Poisson distribution models the count of events in a given time period - i.e. $\lambda$ per unit time. In our instance we will look at number of tries per game (80 minutes)

$$
p_{X}(x) = \frac{e^{-\lambda}\lambda^x}{x!}
$$

If Poisson events take place on average at the rate of $\lambda$ per unit of time, then the sequence of time between events are independent and identically distributed exponential random variables, having mean $\beta = \frac{1}{\lambda}$

Which in a much simpler way means that if a team scores on average 4 tries per game ($\lambda = 4$), then the average time between tries is $1/\lambda = 1/4$. 1/4 is relative to the unit of time, so essentially 1/4 of a game or 1/4 of 80 minutes which is 20 minutes.

The mean and variance of a Poisson random variable $X$ which we can denote as $\mu_X$ and $\sigma_X^2$ are:

$$
\mu_X = \lambda
$$

and

$$
\sigma_X^2 = \lambda
$$

Therefore we can examine the average number of tries scored by each team over all these matches and check whether these two values match as the first indicator that the data may match a poisson distribution. 




```python
team_mean = df.groupby(['fxid', 'team_id']).max()['try_for'].mean()
team_std = df.groupby(['fxid', 'team_id']).max()['try_for'].std()

print(f'Team Mean = {team_mean:.3f}')
print(f'Team Variance = {team_std**2:.3f}')
```

    Team Mean = 2.902
    Team Variance = 3.482


So it appears that the variance is greater than the mean which suggests that this is an over dispersed Poisson distribution. In this instance, we can use a negative binomial distribution to model the number of tries scored. A negative binomial distribution is a way of modelling [" the number of successes in a sequence of independent and identically distributed Bernoulli trials before a specified (non-random) number of failures (denoted n) occurs."](https://en.wikipedia.org/wiki/Negative_binomial_distribution). Fortunately, we can use the mean and variance of our tries scored to calculate the parameters to use when modelling the data. 

The [scipy docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.nbinom.html) shows that the probability mass function (PMF) of the negative binomial distribution is:

$$
f(k) = \binom{k + n -1}{n - 1} p^n (1-p)^k
$$

And we can use the mean and variance to calculate the parameters n and p where:

$$
p = \frac{\mu}{\sigma^2}
$$
$$
n = \frac{\mu^2}{\sigma^2 - \mu}
$$

First, let's plot the distribution of tries per team per game


```python
import scipy.stats as stats


tries_per_game = df.groupby(['fxid', 'team_id']).max()['try_for']
fig, axes = plt.subplots(figsize=(10,15),nrows=5, ncols=3, sharex=True)

axes = axes.flatten()
for i,team in enumerate(tries_per_game.index.get_level_values(1).unique()):
    axes[i].set_title(team)
    axes[i].bar(
        tries_per_game.loc[:,team].value_counts().index, 
        tries_per_game.loc[:,team].value_counts()/tries_per_game.loc[:,team].sum(), 
        color='blue', alpha=0.5
    )



```


    
![png](/images/rugby_poisson_33_0.png)
    



```python
# Next let's calculate some parameters
mean = df.groupby(['fxid', 'team_id']).max()['try_for'].mean() 
var = df.groupby(['fxid', 'team_id']).max()['try_for'].var()
p = mean / var
n = mean**2 / (var - mean)
```


```python
# Create some samples from a negative binomial distribution
samples = stats.nbinom.rvs(n,p,size=10000)
sample_x, sample_y = np.unique(samples,return_counts=True)
```

Finally, let's plot what our true try scoring distribution looks like (the blue bars) and overlay what our negative binomial distribution looks like (the red line).


```python
import scipy.stats as stats


tries_per_game = df.groupby(['fxid', 'team_id']).max()['try_for']
fig, axes = plt.subplots(figsize=(10,15),nrows=5, ncols=3, sharex=True)

axes = axes.flatten()
for i,team in enumerate(tries_per_game.index.get_level_values(1).unique()):
    axes[i].set_title(team)
    axes[i].bar(
        tries_per_game.loc[:,team].value_counts().index, 
        tries_per_game.loc[:,team].value_counts()/tries_per_game.loc[:,team].sum(), 
        color='blue', alpha=0.5
    )
    
    ax2 = axes[i].twinx()
    ax2.set_yticks([])
    ax2.grid(False)
    ax2.plot(sample_x, sample_y/sample_y.sum())

```


    
![png](/images/rugby_poisson_37_0.png)
    


### Conclusion
And there we have it, we can see that try scoring in Premiership rugby can be fairly accurately modelled by a negative binomial distribution and not a Poisson distibution which is used quite often in football.

Stay tuned for next week when I'll be starting a mini series on recommendations combining graphs and image recognition...

