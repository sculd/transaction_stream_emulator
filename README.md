# How to run

![ui](https://preview.ibb.co/j2cYqz/Screen_Shot_2018_08_21_at_8_18_45_PM.png)

## requirements
+ python (python3 was tested, python2 probably should work but not tested)
+ Google Cloud Platform account
    + The account should have Bigtable activated
    + The account should have the Bigtable instance named `demo-ti` created.

install the required python modules
> pip install -r requirements.txt

run the simulation backend
> jupyter notebook

open `main.ipynb` and run the notebook.

copy `config.sample.json` to `config.json` and fill in the `project_id` with the GCP project id.
start the webserver to load the dashboard. It is set up to run on the port 5000
> ./run_server.sh

`config.json` file specifies the number of generated users, and the spending period of each user.
The spending period is sampled from the exponential distribution.
I found exponential distribution a good choice as [it describes](https://en.wikipedia.org/wiki/Exponential_distribution) the time between events in a Poisson point process, i.e., a process in which events occur continuously and independently at a constant average rate.
The amount of each transaction is sampled from uniform distribution between 20 and 100. 

# Stack choice
## Language
I chose to implement all the components in python. 

Pros:
As I was specifically asked to use PySpark, keeping the backend in the same language helps.
* In production components with different languages should be put into separate packages, thus more operational cost.
* Also keeping the stack in single language generally helps with the deployment process.
* In this demo the interaction to PySpark is done via a file, but keeping the stack in the same language allows to in-memory process.

Cons:
* Not really a con, but if it were in production, the choice of stack should be firstly based on the usage and performance requirement not on the operational cost. If performance is the top priority, python might not be a good choice. 


## Emitter
I designed the emitter to run as a batch job, which publishes the signals to a Pubsub topic. The configuration on the number of user and each user's transaction interval is given in the config file. The batch job is also given the time range of the simulation.

## Pubsub
I designed a simple Pubsub that queues the published messages to a topic in order of arrival to a subscription queue. A queue is maintained for each subscription of a topic. Consumer of the queue provides a callback function that is to be called on each message. The message is free-format encoded as a byte list .

## Aggregator
As suggested explicitly in the problem, I chose PySpark. 
PySpark can run in both batch mode and streaming mode. 
According to PySpark's document, the streaming module supports kafka, kinesis, flume only, which adds another layer, e.g. flume should be subscriber of the Pubsub, and PySpark reads from flume. As I wanted to avoid introducing another layer of dependency, I chose the batch mode.

To feed the signals into PySpark, the aggregator first consumes the Pubsub messages into a temporary csv file PySpark batch job reads. The PySpark job aggregates the sum grouped by timestamp truncated at hour level and user id, then writes the values to the database.

## Database
Firstly I chose NoSQL database as the use case does not involve heavy relational logic, also I wanted avoid running SQL query for each API call.
NoSQL is horizontally scalable so considering the production, I prefered NoSQL database to make API from.
I also avoided using toy databases like TinyDB, as otherwise in production I am likely to redesign the database layer.

I chose Google Cloud Platform (GCP) Bigtable.

Pros
* It is production level NoSQL database, which satisfies both my requirements.
* It is hosted on cloud, thus I can save the configuration and management effort.
    * Minimal configuration (enter number of nodes and type of hard disk)
    * Scalling up and down is easy as just setting the number of nodes.
    * It is easy to set up of the region, fail-over replication.

Cons 
* As it is hosted on cloud, the call to database has to be made remotely, which adds to the response time. 
    * This can be mitigated by placing the web server to the same region/datacenter to the database.
* If the use case requirement changes, the schema mihght need to be redesigned.
* Not as broad user base. 

As alternatives, MongoDb or dynamoDb could be used with similar regards as well. 

## Web server
I chose python flask, as it is a lightweight web server suitable for a demo that I could grab quickly.


# How the components interact
## Simulation flow
Emitter -> Pubsub -> csv file -> PySpark -> BigtableDB

* Emitter: as a batch job, publish signals to a Pubsub topic.
* Pubsub: keeps the published signals in memory for each subscription (in the demo we have just one subscription).
* Aggregator: consume the Pubsub subscription queue, dump the messages to a temp csv. file.
* PySpark:  read the csv file to calculate the list and sum.
* BigtableDB: stores the calculation.

Above processes run as a batch, the main Jupyter notebook can initiate the process specifying the from and to time range. 
The number of users and the spending interval can be set up using the config file.

## API
webserver <-(request, response)-> BigtableDB

# Database Schema
A Bigtable table can be divided into separate column family, which can be queried independently.
In this demo, two column families `dcflist` and `dcfbhour` are used.
`dcflist` is used to store each transaction.
`dcfbhour` is used to store the sum of transactions per hour. The sum over a time range is based on this.

Each column family maintains key-value pair. The row key is the only index in the Bigtable, which is formatted as following.
`<user_id>#<timestamp>`

Bigtable can perform a range query between two given row keys.
Placing the user id before the timestamp allows to query only the entries for a particular user, which saves the lookup time. 
For instance, a query for a user `u1` for `t1` and `t2` can be done by a range query of between `u1#t1` and `u1#t2`.

# Moving to the production
Generally monitoring probe and alerting set up should be configured for each component.

## Emitter
Emitter in production can be designed to be a live process instead of a batch job, to generate the synthetic signal for monitoring/functional test.
In can be deployed to kubernetes as a docker image.

Emitter can be configured to produce larger volume of signal to imitate the production environment.


## Pub/sub
* The message queue will have size limit, after which it will start dropping the new published messages until the queue is consumed.
    * The drop count should be monitored.
* The message queue will store the messages in the permanent disk rather than memory only if the volume gets large.
* Due to overhead of implementing / managing in-house Pubsub, public service like GCP Pubsub can be considered as well.


## Aggregator
The aggregator can be run as a streaming job, if the real-timeless is important.
* The real time job tends to be costly in operation cost.
* The timestamp of the stream should sync to the event timestamp, if the event delivery is delayed, the stream itself will be delayed accordingly.
* For PySpark, the streaming module supports kafka, kinesis, flume only, so the PubSub subscriber should redirect the stream to one of them or the emitter itself should publish the signal directly to them.

Batch process can be run frequently to provide near-real-timeness as well. 
In this case, one should make sure to aggregate the data that belongs to the same bucket but run in separate batch jobs.
Some aggregation such percentile values can not be correctly combined accross the batches. It needs to run from streaming job or an estimation (e.g. weighted average) should be made. 


## Database
If the service is multi-regional, the web server should be pointed to database server in the nearby region.
The node number should be optimized to handle the production volume.


