---
layout: post
title: Force Velocity Profiling and Prem Round 5 Predictions
comments: true
categories: [Stats, Rugby, Sports Science]
---

Welcome to my latest post. There are two topics for this one, a double whammy if you will - Prem predictions and Force Velocity Profiling. 

### Elo Ratings Round 5
Some close results in the Prem last week. The Elo ratings system correctly predicted 4/6 fixtures. The two fixtures predicted incorrectly were Gloucester vs Sale and Wasps vs Northampton which happened to be the two fixtures with the closest odds for each team.

| Team   | After Round 3  | After Round 4  | 
| -------|------------------------|----------------------------|
Harlequins | 1674 | 1697 | 
Leicester | 1640 | 1649 | 
Exeter | 1632 | 1643 | 
Saracens | 1602 | 1632 | 
Sale | 1583 | 1566 | 
Wasps | 1480 | 1522 |
Northampton | 1541 | 1500 | 
Newcastle Falcons | 1500 | 1469 | 
Gloucester | 1466 | 1483 | 
Bristol | 1465 | 1442 | 
Bath | 1374 | 1374 | 
London Irish | 1291 | 1282 | 
Worcester | 1284 | 1272 | 

And the predictions for this week are:

```python  
elo.predict_fixture('SALE', 'HARLEQUINS', teams)
>>> Sale win = 39%
>>> Harlequins win = 61%  

elo.predict_fixture('NEWCASTLE FALCONS', 'BRISTOL', teams)
>>> Newcastle Falcons win = 61%
>>> Bristol win = 39%

elo.predict_fixture('WASPS', 'EXETER', teams)
>>> Wasps win = 40%
>>> Exeter win = 60%

elo.predict_fixture('WORCESTER', 'LEICESTER', teams)
>>> Worcester win = 13%
>>> Leicester win = 87%

elo.predict_fixture('BATH', 'SARACENS', teams)
Bath win = 23%
Saracens win = 77% 

elo.predict_fixture('LONDON IRISH', 'GLOUCESTER', teams)
>>> London Irish win = 29%
>>> Gloucester win = 71%
```  

Looking at these predictions I'm not sure how many I'd disagree with. Wasps vs Exeter would be a tough one to call given Exeter's recent form. London Irish vs Gloucester could be a bit closer than what the odds are suggesting.  

## Force Velocity Profiling Dashboard  

Sometime last year I was reading a [blog post](https://www.mathlacome.com/blog/fvp-easy)  by Mathieu Lacome on force velocity profiling using GPS. The post led me to creating an interactive force velocity dashboard to be used with GPS exports and calculates many of the various parameters from the work of JB Morin and also allows easy visualization of each sprint to allow comparisons either within or between players. The whole idea with the dashboard was to allow anyone with a csv file to be able to use it without having to touch any code. For those interested, the web app is available [here](http://force-velocity-profile.herokuapp.com/). If you drag and drop one or both of the files [here]({{ site.baseurl }}{% link /assets/john_smith-103-20201106.csv %}) or [here]({{ site.baseurl }}{% link /assets/john_smith-103-20201107.csv %}) then you should be able to see the dashboard in action. It would be great to hear any thoughts or feedback and for more details on it's usage then have a little goosey [here](https://github.com/Grant592/force-velocity-app). It can be modified fairly easily if anyone has any specific use cases so please feel free to drop me a message on Twitter or email if you're interested in using it.  




