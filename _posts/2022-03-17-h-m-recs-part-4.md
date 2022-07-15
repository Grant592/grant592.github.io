---
layout: post
title: H&M Recommendations Challenge - Part 4 - Bringing it all together
comments: true
categories: [ Data Science, Neo4j ]
---

### UPDATE 15th July 2022

I recently presented this project at the Neo4j meetup on 12th July. I've uploaded the slides to the github repository [here](https://github.com/Grant592/H-M_recs/blob/main/recommendations.pdf).

### Intro

For anyone still reading, well done for making it this far. We'll try to tie all the previous posts together in this one and create the recommendations we'll use for the Kaggle entry.
* Part 1 - [loading the data and EDA]({% post_url 2022-02-17-h-m-recs-part-1 %})  
* Part 2 - [image based recommendations]({% post_url 2022-02-23-h-m-recs-part-2 %})
* Part 3 - [collaborative filtering and with implicit datasets]({% post_url 2022-03-05-h-m-recs-part-3 %})

### The Recommendation Process  

So just to recap the data we have available for making our recommendations:
* A graph model of all users and purchases including product metadata.
* Image embeddings of almost all of the products and along with this we previously calculated the 10 most similar items for each of these images which we wrote back to our Neo4j database.
* A matrix factorization based recommendation system built with implicit feedback using Alternating Least Squares courtesy of the python package `implicit`.

The task now is to combine these recommendations to create the most insightful and useful recommendations. Some of the challenges with each of these pieces of data are:
* Image embeddings are powerful however often we may end up selecting items that are almost exactly the same as an item someone has previously purchased or and item that looks similar but is actually not suitable for the customer (e.g. a mens shirt when somebody is looking for a blouse)
* The ALS method is also very useful however one of the challenges when training the model is we try to decrease the sparsity of the dataset by filtering customers and items that fall below a certain threshold, so not every customer or item is included in the model.

So the here are the steps we'll go through when creating the recommendations with the features we've created, each of which I'll go into in more detail in the following sections:
1. For each customer, find all of their purchases and then retrieve the most similar products based on their images.
2. Use a Cypher query to filter this list of similar items to only include products from a department and index that the customer had previously purchased from - this solves the problem of not recommending men's jeans to women and vice versa although reduces the number of items
3. Now we have a list of potential items for each customer, use the ALS model to rank this list and take the top 12 items from the ranked list.
4. For those who have less than 12 recommended items (at this point it's most likely because the items were filtered out during the training of the ALS model), take a random sample of those items returned in step 2.
5. Finally, for those who have no recommendations through the above process, use a cypher query to return the 12 most popular products purchased by other users who also purchased the same product as the customer.  

So let's get started...

### Getting the process started

Let's begin with some of the groundwork.

First we need to create an empty sparse matrix of **all** users and products, and mappings from the `customer_id` and `product_id` to their relevant indices in the sparse matrix.

```python
import pandas as pd
import numpy as np
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from scipy import sparse
import datetime as dt
import logging
import sys

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))

# Get all customer ID's and all products ID's to create sparse matrix

with driver.session() as session:
    query = """
    MATCH (c:Customer)
    RETURN c.id as id
    """

    results = session.run(query)
    customers = [record['id'] for record in results]


    query = """
    MATCH (p:Product)
    RETURN p.code as id
    """

    results = session.run(query)
    products = [record['id'] for record in results]

# Create mappings for sparse matrix
all_product_to_idx = {}
all_idx_to_product = {}
for (idx, prod_id) in enumerate(products):
    all_product_to_idx[prod_id] = idx
    all_idx_to_product[idx] = prod_id

all_customer_to_idx = {}
all_idx_to_customer = {}
for (idx, cust_id) in enumerate(customers):
    all_customer_to_idx[cust_id] = idx
    all_idx_to_customer[idx] = cust_id

# Create lil matrix to incrementally build sparse matrix of recs
n_users = len(customers)
n_products = len(products)

rec_matrix = sparse.lil_matrix((n_users, n_products))
```  

I've found `sparse.lil_matrix` incredibly useful in this process for assigning values to a sparse matrix incrementally, It can then be converted to a `csr` matrix later in the process for more efficient operations.  

### Creating a Neo4j Class  

Next we need to create a `class` to connect to our Neo4j database and retrieve our recommendations.  

```python  
class NeoUserRecommender:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    @staticmethod
    def enable_log(level, output_stream):
        handler = logging.StreamHandler(output_stream)
        handler.setLevel(level)
        logging.getLogger("neo4j").addHandler(handler)
        logging.getLogger("neo4j").setLevel(level)

    def get_recommended_items_for_user(self, customer_id):
        with self.driver.session(database='fabric') as session:
            result = session.read_transaction(
                self._get_recommended_items_for_user, customer_id)
            return result[0]

    @staticmethod
    def _get_recommended_items_for_user(tx, customer_id):

        query = ("""
        CALL {
        // Return all purchases for a single customer
        USE fabric.neo4j
        MATCH (c:Customer)-[pur:PURCHASED]->(p:Product)
        WHERE  c.id = $customer_id
        RETURN p.code as prod_code
        }
        CALL {
        // For each of those purchases, return the 10 most similar
        // by image embedding
        USE fabric.products
        WITH prod_code
        MATCH (p1:Product)-[:SIMILAR]->(rec:Product)
        WHERE p1.code = prod_code
        RETURN rec.code as rec_code
        }
        CALL {
        // For each of these recommendations, filter out the ones
        // that don't come from a department or index previously
        // purchases from by the customer
        USE fabric.neo4j
        with rec_code
        MATCH (c:Customer)
        WHERE c.id = $customer_id
        MATCH (ind:Index)<-[:HAS_INDEX]-(rec:Product)-[:FROM_DEPARTMENT]->(d:Department)
        WHERE rec.code = rec_code
        AND EXISTS ((c)-[:PURCHASED]->(:Product)-[:FROM_DEPARTMENT]->(d))
        AND EXISTS ((c)-[:PURCHASED]->(:Product)-[:HAS_INDEX]->(ind))
        RETURN rec.code AS recommended_item
        }

        RETURN collect(recommended_item) as recommended_items
        """
        )
        result = tx.run(query, customer_id=customer_id)
        try:
            return [row['recommended_items'] for row in result]
        # Capture any errors along with the query and data for traceability
        except ServiceUnavailable as exception:
            logging.error(f"{query} raised an error: \n {exception}")
            raise


    def get_cypher_recs_for_user(self, customer_id):
        with self.driver.session(database='neo4j') as session:
            result = session.read_transaction(
                self._get_cypher_recs_for_user, customer_id)
            return result[0]

    @staticmethod
    def _get_cypher_recs_for_user(tx, customer_id):

        query = """
        MATCH (c:Customer {id: $customer_id})-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(:Customer)-[:PURCHASED]->(rec:Product)
        WHERE id(p) <> id(rec)
        AND NOT EXISTS ((c)-[:PURCHASED]->(rec))
        WITH c.id as customer_id, rec, COUNT(rec) as score ORDER BY COUNT(rec) DESC LIMIT 12
        RETURN collect(rec.code) as recommended_items
        """

        result = tx.run(query, customer_id=customer_id)
        try:
            return [row['recommended_items'] for row in result]
        # Capture any errors along with the query and data for traceability
        except ServiceUnavailable as exception:
            logging.error(f"{query} raised an error: \n {exception}")
            raise
```


The first transaction function in the class `_get_recommended_items_for_user` is finding all similar items for a user based off their purchases, filtering items which aren't from departments or product indexes the customer has purchased from previously and returning a list of these items. `_get_cypher_recs_for_user` is the function which will be used when we have no similar items for a user based on the above criteria and finds the most popular purchases of other users who purchased a product that our original customer purchased.

Now we've done some of the groundwork, we'll write all these items to our currently empty user/item sparse matrix. This took a while...

```python  

neo_recs = NeoUserRecommender(uri, 'neo4j', 'password')

# For each customer, get recommendations and map them to the sparse matrix
for i, cust in enumerate(customers):

    customer_index = customer_to_idx[cust]

    recs = neo_recs.get_recommended_items_for_user(cust)
    rec_indices = [product_to_idx[rec] for rec in recs]

    rec_matrix[customer_index, rec_indices] = 1

    if i%10000 == 0:
        print(f'{i} customers processed')

rec_matrix = rec_matrix.tocsr()
sparse.save_npz('rec_matrix.npz', rec_matrix)
```  

### Train the ALS model  

[We'll train the ALS model exactly as we did in the previous post]({% post_url 2022-03-05-h-m-recs-part-3 %}) using the parameters that scored best on the test set i.e. giving more weight to more recent purchases.  

So we now have two sets of mappings from a `customer_id` and `product_id` to an index in a sparse matrix:
* Mappings starting with `all_` reference those for the overall user/item matrix
* Mappings starting with `als_` references those for the ALS user/item matrix which doesn't contain all of the customers and products.  

### Generating The Recommendations  

The code below begins to go over the customers one by one and follows the process outlined above, most of the steps are explained in the code below.

```python  

# Create a matrix to hold the recommendations
final_recommendations = sparse.lil_matrix((n_users, n_products))

for i, cust in enumerate(customers):

    # Convert the customer_id to the index of all user/items
    all_user_id = all_customer_to_idx[cust]

    # Get all the purchases identified by image similarity and previously written to the user/item matrix
    neo_user_recs = rec_matrix[all_user_id].indices

    # Convert all these product_ids to their respective indicies in the user/item matrix
    neo_recs_product_id = [all_idx_to_product[rec] for rec in neo_user_recs]

    # the dataset used to train the ALS model was filtered by num of purchases and sales
    # so first check that the customer was part of the training set
    if cust in als_customer_to_idx and len(neo_recs_product_id) > 0:

        # Identify the customers index in the als user/item matrix
        als_user_id = als_customer_to_idx[cust]

        # Identify the product index in the als user/item matrix
        als_prod_ids = [als_product_to_idx[int(rec)] for rec in \
         neo_recs_product_id if int(rec) in als_product_to_idx.keys()]

        # Providing at least one of the items was part of the als training data - rank the items and take the top 12
        if len(als_prod_ids) > 0:
            ranked_recs = als.rank_items(als_user_id, purchases_with_confidence, selected_items=als_prod_ids)
            ranked_recs = [x[0] for x in ranked_recs[:12]]
            ranked_recs_prod_ids = [als_idx_to_product[x] for x in ranked_recs]

            # Slight issue with str/int conversion and losing the leading 0
            ranked_recs_all_prod_ids = [all_product_to_idx[f'0{x}'] for x in ranked_recs_prod_ids]

            final_recommendations[all_user_id, ranked_recs] = 1


    # If we didn't find at least 12 recs, find the extra recs to add
    if final_recommendations.getrow(all_user_id).count_nonzero() < 12:


        num_to_insert = 12 - final_recommendations.getrow(all_user_id).count_nonzero()

        if len(rec_matrix[all_user_id].indices) == 0:
            continue

        extra_recs = np.random.choice(rec_matrix[all_user_id].indices, size=num_to_insert)

        final_recommendations[all_user_id, extra_recs] = 1

    if i % 10000 == 0:
        print(f'{i} customers processed')
        print(f'{n_users - i} customers remaining')

```  

For those who didn't have 12 recommendations from the ALS method, I think taking a random sample of the recommendations based on image similarity is a reasonable way to create the extra recommendations based on the fact that these recs have already been filtered down to be more suitable through the use of the cypher query we set up earlier. So although it's not perfect, it's reasonable mechanism in this instance.  

Finally, for any customers who had no recommendations at all after the previous steps, out last method is to use a pure cypher query to get the recs.  

First though we need to find out which customers these were. The best way I could find when dealing with a sparse matrix was following [this explanation](https://mike.place/2015/sparse/). Essentially we need to find any rows where there are no entries for the `indptr` (check out the scipy.sparse docs for a deeper explanation).

```python  
final_recommendations = final_recommendations.tocsr()
still_to_recommend = np.where(np.diff(final_recommendations.indptr) == 0)[0]
```

To break it down, if we look at `final_recommendations.indptr`, we'll see something like `[0,12,24,36,36,48...]`. If we then us `np.diff`, we'll get the difference between consecutive points in this array. Where this difference equals zero is where the row has no entries in our recommendation matrix, therefore these are the users for which we still need to create some recommendations. And this was done as follows:

```python  
final_recommendations = final_recommendations.tolil()

for i, cust in enumerate(still_to_recommend):

    cust_id = all_idx_to_customer[cust]

    cypher_recs = neo_recs.get_cypher_recs_for_user(cust_id)
    recs = [all_product_to_idx[x] for x in cypher_recs]

    final_recommendations[cust ,recs] = 1
```  

### Conclusion  

So there we have it - recommendations based on image embeddings, Cypher queries and collaborative filtering. I'll be munging the recommendations into a format that can be entered into the Kaggle competition and will be waiting patiently for the cheque for the prize money to come through the door...

![](https://media.giphy.com/media/1sIV2B9i1UpjO/giphy.gif)
