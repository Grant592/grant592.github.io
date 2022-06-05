---
layout: post
title: The Grooviest Prog Band with PySpark and Spotify - Part 1
comments: true
categories: [  Music, Data Science ]
---

I've recently started working with Databricks and PySpark and it's been quite an interesting journey familiarising myself with some of the benefits and challenges of working with distributed data. To get acquainted with the syntax and some of the idiosyncrasies let's dive in and start working with the Spotify API...

### Accessing the Spotify API  

The first thing we need to do is get some data from Spotify. Fortunately, there's an excellent [blog post](https://stmorse.github.io/journal/spotify-api.html) which helps us get set up.  

First things first, get our `client_id` and `client_secret` and get an access token  

```python  

import requests

CLIENT_ID = '<insert client id>'
CLIENT_SECRET = '<insert client secret>'

AUTH_URL = 'https://accounts.spotify.com/api/token'

# POST
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})

# convert the response to JSON
auth_response_data = auth_response.json()

# save the access token
access_token = auth_response_data['access_token']
```  

And subsequently we can create the header that will be used to authorize all of our API calls.  

```python 
headers = {
    'Authorization': f'Bearer {access_token}'
}
```  

And now getting some data is a simple GET call and passing in whatever parameters we might want to pass in (see [Spotify](https://developer.spotify.com/documentation/web-api/reference/#/) for more details on what data is available).  


```python  
BASE_URL = 'https://api.spotify.com/v1/'  

# Track ID from the URI
track_id = '1nmZ8yqKkfooOuYvtFctDp'

# actual GET request with proper header
r = requests.get(BASE_URL + 'audio-features/' + track_id, headers=headers)
r.json()

Out[4]: {'danceability': 0.323,
 'energy': 0.839,
 'key': 1,
 'loudness': -7.35,
 'mode': 1,
 'speechiness': 0.0503,
 'acousticness': 0.315,
 'instrumentalness': 0.000313,
 'liveness': 0.348,
 'valence': 0.543,
 'tempo': 136.232,
 'type': 'audio_features',
 'id': '1nmZ8yqKkfooOuYvtFctDp',
 'uri': 'spotify:track:1nmZ8yqKkfooOuYvtFctDp',
 'track_href': 'https://api.spotify.com/v1/tracks/1nmZ8yqKkfooOuYvtFctDp',
 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/1nmZ8yqKkfooOuYvtFctDp',
 'duration_ms': 227627,
 'time_signature': 4}
```  

So now we know how to access the data we want, let's use the API to create a dataset and then have a play around with MLflow and hyperopt to see how they work.  

### Creating the Dataset  

In order to run an experiment with PySpark, we need to create a dataset first and convert it to a Spark DataFrame. The dataset will be roughly 10000 rows so clearly doesn't neccesitate the being distributed but for the sake of this blogpost let's forget that part...  

![](https://y.yarn.co/099c968b-a3f6-4687-96e3-bd4bb669f1f3_text.gif)  

We'll start by creating a dictionary of bands and their Spotify ID's which we can pass to our GET requests and get the required data.  

```python  
artists = {
  'Yes':{'id': '7AC976RDJzL2asmZuz7qil'},
  'Genesis': {'id': '3CkvROUTQ6nRi9yQOcsB50'},
  'Jethro Tull': {'id': '6w6z8m4WXX7Tub4Rb6Lu7R'},
  'Pink Floyd': {'id': '0k17h0D3J5VfsdmQ1iZtE9'},
  'King Crimson':{'id': '7M1FPw29m5FbicYzS2xdpi'},
  'Camel': {'id': '3Uz6jx81OY2J5K8Z4wmy2P'},
  'PFM': {'id': '1MD5pgVzlusqGyuSTcTxvu'},
  'Rush': {'id': '2Hkut4rAAyrQxRdof7FVJq'},
  'Frank Zappa': {'id': '6ra4GIOgCZQZMOaUECftGN'},
  'Asia': {'id': '1bdytLV3FPjyhfrb6BhMej'}
}  
```  

A fine selection of bands if I do say so (although I've never been a Pink Floyd fan for some reason)...  

Anyway, we'll also create a few helper functions to format the parameters needed for the API call and process the requests. The function names should be rather self-explanatory.  

```python  
def get_album_ids_for_artist(artist: str, limit: int = 50, offset: int = 0) -> list:
  
  albums_response = requests.get(
      BASE_URL + 'artists/' + artist + '/albums',
      headers=headers,
      params={
        'include_groups':'album',
        # Max limit of 50 per call
        'limit': limit,
        # Provide an offset value so we can get the next 50 values each call
        'offset': offset
      }
    )
  
  album_list = [album['id'] for album in albums_response.json()['items']]
  
  return album_list


def get_songs_from_albums(albums: str) -> list:
    """
    albums - a string of album ids in the format 'abcde,qwert,poiuy'
    """
    albums_response = requests.get(
      BASE_URL + 'albums/',
      headers=headers,
      params={
        'ids':albums
      }
    )
    
    all_tracks = []
    for album in albums_response.json()['albums']:
        for track in album['tracks']['items']:
            all_tracks.append(track['id'])
  
    return all_tracks
  
def get_tracks_audio_features(tracks: str) -> list:
    """
    tracks - a string of track ids in the format 'abcde,qwert,poiuy'
    """
    
    track_response =  requests.get(
      BASE_URL + 'audio-features/', 
      headers=headers, 
      params={'ids':tracks}
    )
    
    track_features = track_response.json()['audio_features']
    
    return track_features  
  ```  

  Now using the functions above, we need to go through a few stages. To avoid hitting the Spotify API rate limit (although they don't seem to make this public anywhere) we'll try to use requests which can take strings of multiple id's in one call. The stages are:
  * Get list of artists (already stored in dict) - for each artist
    * Get list of albums - for each album
      * Get all tracks - join tracks into string of 100 song ids max
        * Get audio features for all of these tracks  


For the first task we'll get a list of albums for each artist.  

```python  
# Max number of albums that can be returned in one request
album_limit=50

for artist_name, artist_data in artists.items():
    # Keep track of the total number of albums
    total_albums = 0
    # Get first max 50 albums
    album_list = get_album_ids_for_artist(artist_data['id'], offset=total_albums)
    
    total_albums += len(album_list)
    
    # Keep adding albums until none left
    while total_albums % album_limit == 0:
        print(total_albums)
        more_albums = get_album_ids_for_artist(artist_data['id'], offset=total_albums)
        if more_albums[-1] == album_list[-1]:
            break
        total_albums += len(more_albums)
        album_list.extend(more_albums)
        
    # Store albums in the dict
    artists[artist_name]['albums'] = album_list

```  

And now we have the albums we can iterate through these for each artist and retrieve the track data  

```python  

for artist_name, artist_data in artists.items():
  
    artist_data['tracks'] = []
    
    num_albums = len(artist_data['albums'])
    chunk_size = 20
    
    for idx in range(0, num_albums, chunk_size):
        # Joins up to 20 track ids into one string to pass as a param to the request
        query_string = ','.join(artist_data['albums'][idx:min(idx + chunk_size, num_albums)])
        tracks = get_songs_from_albums(query_string)
        artist_data['tracks'].extend(tracks)
```  

And finally we can retrieve the audio features for each track in a similar fashion. We can pass up to 100 tracks per API call for this request.

```python  
output = []

for artist_name, artist_data in artists.items():
    
    num_songs = len(artists[artist_name]['tracks'])
    chunk_size = 100
    
    for idx in range(0, num_songs, chunk_size):
        query_string = ','.join(artist_data['tracks'][idx:min(idx + chunk_size, num_songs)])
        tracks = get_tracks_audio_features(query_string)
        for track in tracks:
            # Catch a Nonetype error that kept popping up
            try:
                track['artist'] = artist_name
                output.append(track)
            except(TypeError) as e:
                print(e)
                continue       
```  

### Distributing the Data  

The data is now sat in a nice little python dictionary but in order to use MLflow and other packages we need to convert it to a Spark Dataframe. There's a few steps to this but all we're doing is parallelizing it so it can be read as a spark DF.  

```python  
import json

jsonData = json.dumps(output)
jsonDataList = []
jsonDataList.append(jsonData)
jsonRDD = sc.parallelize(jsonDataList)
df = spark.read.json(jsonRDD)  
```      

### Basic PySpark Syntax  

We can run a few queries on our new dataframe to see what the basic PySpark syntax is like for querying a dataframe. Essentially it's like some weird offspring of SQL and Python, but not too bad to actually pick up.  

```python  
# Basic filtering and ordering
from pyspark.sql.functions import col
(df
  .select('*')
  .filter(col('artist') == 'King Crimson')
  .orderBy(col('acousticness'), ascending=False)
  .show()
)
```  

|acousticness|        analysis_url|      artist|danceability|duration_ms| energy|                  id|instrumentalness|key|liveness|loudness|mode|speechiness|  tempo|time_signature|          track_href|          type|                 uri|valence|
|------------|--------------------|------------|-----------|-----------|-------|--------------------|----------------|---|--------|--------|----|-----------|-------|--------------|--------------------|--------------|--------------------|-------|
|       0.979|https://api.spoti...|King Crimson|       0.214|     141813| 0.0419|5vr2AS7J48VTzx0GB...|            0.56|  0|  0.0675| -22.746|   0|     0.0422| 63.455|             4|https://api.spoti...|audio_features|spotify:track:5vr...| 0.0386|
|       0.978|https://api.spoti...|King Crimson|       0.231|     148680| 0.0326|6QdcPRbpM3XgAP2WJ...|           0.397|  0|    0.12| -23.945|   0|     0.0438| 63.729|             4|https://api.spoti...|audio_features|spotify:track:6Qd...| 0.0377|
|       0.976|https://api.spoti...|King Crimson|        0.45|     173573|  0.287|2qUmkuMWCP78D6CBn...|             0.7|  0|    0.11| -15.755|   0|      0.053| 97.511|             3|https://api.spoti...|audio_features|spotify:track:2qU...|  0.794|
|       0.976|https://api.spoti...|King Crimson|       0.515|      96746|  0.194|0VigqrWmeQu02PQ7V...|           0.889|  2|   0.373| -25.197|   0|     0.0381|107.021|             1|https://api.spoti...|audio_features|spotify:track:0Vi...|  0.817|
|        0.97|https://api.spoti...|King Crimson|       0.239|      50060|0.00157|4oKl6de5N3O6zJBLR...|             0.0|  7|   0.124| -42.488|   0|     0.0514|  94.32|             3|https://api.spoti...|audio_features|spotify:track:4oK...| 0.0638|


```python  
# Aggregate functions  
from pyspark.sql.functions import *

# Basic groupby functions
display(df
       .groupby('artist')
       .agg(avg('acousticness').alias('avg_acousticness'),
            avg('danceability').alias('avg_danceability'),
           (avg('duration_ms') / 60 / 1000).alias('avg_duration_min'),
            avg('energy').alias('avg_energy'),
            avg('instrumentalness').alias('avg_instrumentalness'),
            avg('liveness').alias('avg_liveness'),
            avg('loudness').alias('avg_loudness'),
            avg('speechiness').alias('avg_speechiness'),
            avg('tempo').alias('avg_tempo'),
            avg('valence').alias('avg_valence')
           ))
```  

|      artist|   avg_acousticness|   avg_danceability|  avg_duration_min|         avg_energy|avg_instrumentalness|       avg_liveness|       avg_loudness|    avg_speechiness|         avg_tempo|        avg_valence|
|------------|-------------------|-------------------|------------------|-------------------|--------------------|-------------------|-------------------|-------------------|------------------|-------------------|
|         PFM| 0.3721898909252667| 0.4022918149466193| 5.497503529062871| 0.6347435943060499| 0.24537355122775806| 0.3863923487544484| -10.40714056939501|0.06466672597864766|118.21350355871887| 0.3575676156583629|
| Frank Zappa| 0.3791181434430153|0.44998950044869873| 4.722723895702463| 0.5784439575231828| 0.17566577603051156| 0.4034937182171701|  -12.7904932695184|0.14676706551002094|117.23569368830393|0.49328629973078053|
|King Crimson|0.21413095111517375|  0.367053747714808| 6.029358592321755| 0.5406411151736749|  0.3986181844424132| 0.4802530164533821|-13.721378427787934|0.07530420475319925|118.68908957952465| 0.2947462522851919|
|       Camel|0.44131067716535455|0.35251259842519705| 4.825228280839895|0.45385437007874013|  0.4931887993700787| 0.3571830708661418|-14.443846456692913|0.04657952755905513|119.41430314960633| 0.3594440944881891|
|     Genesis| 0.2688770427364866|  0.438260135135135| 5.772080940315315| 0.5987576013513513| 0.09644313038851351|0.33425219594594596|-10.725427364864862|0.06685033783783785|117.09421283783782| 0.3842393581081083|
| Jethro Tull|0.42836510390848437| 0.4967559580552907| 4.401592373689228| 0.5071039084842709| 0.09515943808388941|0.29735967588179235| -12.59948522402288|0.10503155386081986| 121.6670133460438| 0.6003044804575787|
|         Yes|0.23045781883660138| 0.3752308496732027| 7.413914901960785| 0.6147684967320266| 0.11815227339869287| 0.4683524183006538|-10.360205228758176|0.05776379084967318|119.96347450980389| 0.3830351633986928|
|  Pink Floyd|0.32437635558958655|0.36935604900459396|5.3182710311383365|0.42457889739663085| 0.28464265220520674| 0.4193330781010722|-15.466632465543647|0.05452771822358344|115.67404441041347|0.24251163859111793|
|        Rush|0.07189137062986556|0.36448478414720475| 5.700721325784383|  0.815637296532201| 0.16446113754423214| 0.5545845718329792|  -8.06344939844303|0.06928683651804671| 128.3137940552018| 0.4109498938428876|
|        Asia|0.25772684318766065| 0.3954010282776349|5.0995668808911745| 0.7205347043701799| 0.04524703089974293| 0.4367948586118253| -7.924539845758358|0.06118123393316195|126.95846529562988|0.37722210796915173|  

And we can see that Rush come out as the most 'energetic' of the 10 prog bands in the sample which shouldn't come as too much of a suprise, even if my friend Luc would like to argue otherwise.  

Window functions are a little bit different but work exactly the same as their SQL equivalents. Let's have a look at the most 'danceable' prog tracks for each of our bands  

```python  
# Window functions
from pyspark.sql import Window

window = Window.partitionBy('artist').orderBy(col('danceability').desc())

df_top_dance = (df
               .withColumn('ranked_danceability', rank().over(window))
               .select('artist', 'id', 'ranked_danceability')
               .filter(col('ranked_danceability') <= 3)
               )

df_top_dance.show()
```  

|      artist|                  id|ranked_danceability|
|------------|--------------------|-------------------|
|         PFM|2CHCp64gMJ2ao9SLe...|                  1|
|         PFM|6rdPleYVkJIiGYTqr...|                  2|
|         PFM|0GvvI645ZcjQxHi8d...|                  3|
| Frank Zappa|0N0BlSPOE2fghPO3Q...|                  1|
| Frank Zappa|3dN1Kp5m80vbmSCPP...|                  2|
| Frank Zappa|1mCAlJGdnDcZ3MULP...|                  3|
|King Crimson|5zrgm2vquJE8niTe4...|                  1|
|King Crimson|5upQw0fEqb8DKn8jD...|                  2|
|King Crimson|5DDYqGNNKOWwxfSsE...|                  3|  


### Stay Tuned  

For part 1 we've looked at accessing the Spotify API, creating a Spark Dataframe from the data and then some of the basic syntax for querying the dataframe. For part two next week we'll look at running experiments with MLflow and hyperparameter tuning with Hyperopt.  
