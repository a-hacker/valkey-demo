# Valkey Demo

This repo is intended to demo the basic functionality of [valkey](https://valkey.io/), an in-memory data store forked from redis. The demo can be run via docker-compose which will do the following:

- Spin up valkey in a container. This container does not mount a data volume so no data is persisted in between runs.
- Run two writer jobs. These writers will both write randomized, structured data to valkey in parallel. The data is correspond to two tables, users and orders and both writers write rows for both tables.
- Run a reader to consume the data written by the writers. This only runs after the writers have completed and will read all rows for both tables, one at a time. The data will be written row by row into a csv file that is mounted to the output directory in this repo.