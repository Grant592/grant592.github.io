---
layout: post
title: We Have To Go Deeper...
comments: true
categories: [ Neo4J, Graph Databases, GraphQL, Rugby ]
---

Welcome back and happy new year to all four (at last count) of my regular readers. We'll continue where we left off; creating a GraphQL endpoint with Neo4j . This week we'll go deeper and look at how we can call an API from within the GraphQL endpoint to enrich our data.

![](https://media.giphy.com/media/lQ1AkXFktuJsnoqO3A/giphy.gif)  

### Enriching the Data  

One part of the context that is lost when examining historical fixture data is historical weather data. In this post we'll look at how we can use GraphQL Schema directives to apply custom logic on the server, which will allow us to use Cypher directly in the GraphQL schema file. Before all the exciting stuff though, we need to figure out how we'll get the weather data in the first place. The best weather API I could find that was both free and had historical weather data was [Meteostat](https://dev.meteostat.net/api/) and the process of getting a rapidapi key to access it was fairly straightforward. Once that was done, the first hurdle was finding the nearest weather station to each Stadium in the Neo4j database.

The query below uses `apoc.load.jsonParams` to pass the API key to the meteostat API and uses the latitude and longitude of the stadium to find the nearest weather station.  


```sql
WITH {`Accept`: 'application/json',
    `Content-Type`:'application/json',
    `x-rapidapi-key`: <RAPID_API_KEY>
} as header
MATCH (f:Fixture)-[:VENUE]->(s:Stadium) WHERE f.fxid = 118011
WITH f,s,header
CALL apoc.load.jsonParams(
  'https://meteostat.p.rapidapi.com/stations/nearby?lat='+ s.latitude+
  '&lon='+s.longitude + '&limit5',
    header,
    null)
YIELD value WITH value as station
RETURN station


{
  "data": [
    {
      "name": {
"en": "Gloucestershire / Staverton"
      },
      "id": "EGBJ0",
      "distance": 6132.6
    },
    ...
```  

Now we know how to access the data for the closest weather station, we can match all stadia and save the weather station ID to the graph for use in the GraphQL API.  


```sql  
WITH {`Accept`: 'application/json',
    `Content-Type`:'application/json',
    `x-rapidapi-key`: <RAPID_API_KEY>
} as header
MATCH (s:Stadium)
WITH s,header
CALL apoc.load.jsonParams(
      'https://meteostat.p.rapidapi.com/stations/nearby?lat='+
      s.latitude+'&lon='+s.longitude + '&limit5',
    header,
    null)
YIELD value WITH value as station,s
SET s.closestWeatherStation = station.data[0].id
```

### Finding Historical Weather Data  

We have the nearest station for each stadium so now we're able to query the Meteostat API to find the weather for a given station on a given date/dates. The query below uses a similar query as above but adds some dates to the url in order to see what the output looks like.  

```sql   
WITH {`Accept`: 'application/json',
    `Content-Type`:'application/json',
    `x-rapidapi-key`: <RAPID_API_KEY>
} as header
MATCH (s:Stadium {name: 'Twickenham Stoop'})
WITH s,header
CALL apoc.load.jsonParams(
  'https://meteostat.p.rapidapi.com/stations/daily?station=' +
  s.closestWeatherStation + '&start=2020-01-01&end=2020-01-02',
    header,
    null)
YIELD value
RETURN value

{
  "data": [
    {
      "date": "2020-01-01",
      "wdir": 127.2,
      "wpgt": 20.4,
      "pres": 1029.3,
      "tmax": 6.8,
      "snow": null,
      "wspd": 7.0,
      "tavg": 5.3,
      "tmin": 1.7,
      "prcp": 0.0,
      "tsun": null
    },
    {
      "date": "2020-01-02",
      "wdir": 188.6,
      "wpgt": 40.8,
      "pres": 1020.4,
      "tmax": 10.8,
      "snow": null,
      "wspd": 18.4,
      "tavg": 8.7,
      "tmin": 6.2,
      "prcp": 0.0,
      "tsun": null
    }
  ],
  "meta": {
"generated": "2022-01-05 21:33:12"
  }
}

```  
As we can see above, the API call returns a list of maps, each containing various measurements of the weather on a given date.

![](https://media.giphy.com/media/rSaQxzxmPAGpW/giphy.gif)  

### `@cypher` Directives and Type Definitions

We can apply custom logic on the server to return scalar values, nodes, objects and in this case maps. Scalar values and nodes are relatively simple as the type definitions have already been defined in the schema file. In our example, we're returning a map of weather conditions, a type that hasn't yet been defined in the GraphQL schema file.  

The first step then is to create a type in our schema.graphql file that maps the the output of our weather values to some type definitions.  


```js

// Step 1 - create a Weather type to store
// the weather map

type Weather {
        windDirection: BigInt
        wpgt: BigInt
        pressure: BigInt
        maxTemp: BigInt
        snow: BigInt
        windSpeed: BigInt
        avgTemp: BigInt
        minTemp: BigInt
        precipitation: BigInt
        tsun: BigInt
}

```  

Now the exciting stuff, calling an API from within an API, all very Inception like if you ask me.

![](https://c.tenor.com/EYPJjOVJOHYAAAAC/inception-deeper.gif)    

We can use the `@cypher` directive to apply the custom logic that extends the `Fixture` type and returns a `Weather` type for a given fixture. The custom logic takes the date of a fixture, the weather station nearest to the fixture's venue, passes this to the Meteostat API and finally returns a representation of a `Weather` object.

```js
extend type Fixture {
        fixtureConditions: Weather @cypher(statement:"""
        WITH {
            `Accept`: 'application/json',
            `Content-Type`:'application/json',
            `x-rapidapi-key`: <RAPID_API_KEY>
         } as header, this
        MATCH (this)-[:VENUE]->(s:Stadium)
        WITH this, s, header
        CALL apoc.load.jsonParams(
          'https://meteostat.p.rapidapi.com/stations/daily?station=' +
           s.closestWeatherStation + '&start=' + this.fixtureDate + '
           &end=' + this.fixtureDate,
        header,
        null)
        YIELD value WITH value.data[0] as weather
        RETURN {
            windDirection: weather.wdir,
            wpgt: weather.wpgt,
            pressure: weather.pres,
            maxTemp: weather.tmax,
            snow: weather.snow,
            windSpeed: weather.wspd,
            avgTemp: weather.tavg,
            minTemp: weather.tmin,
            precipitation: weather.prcp,
            tsun: weather.tsun
        } as conditions""")
}

```  

And just to prove that this thing actually works, here's an example of a GraphQL query for a fixture which contains fixture teams, scores and weather details. Voila!


```js

query fixtureQ {
  fixtures(where: {fxid: 120081}) {
    HTFTSC
    ATFTSC
    fixtureConditions {
      windSpeed
      windDirection
      avgTemp
      maxTemp
      minTemp
      precipitation
      pressure
      snow
      tsun
      wpgt
    }
    teamsTeamPlayedInConnection {
      edges {
        node {
          name
        }
        home_away
      }
    }
  }
}


{
  "data": {
    "fixtures": [
      {
        "HTFTSC": "48",
        "ATFTSC": "10",
        "fixtureConditions": {
          "windSpeed": "16.5",
          "windDirection": "268.4",
          "avgTemp": "6.7",
          "maxTemp": "10",
          "minTemp": "4",
          "precipitation": "1.4",
          "pressure": "1020.4",
          "snow": null,
          "tsun": null,
          "wpgt": "33.3"
        },
        "teamsTeamPlayedInConnection": {
          "edges": [
            {
              "node": {
                "name": "Sale"
              },
              "home_away": "home"
            },
            {
              "node": {
                "name": "Harlequins"
              },
              "home_away": "away"
            }
          ]
        }
      }
    ]
  }
}

```  
