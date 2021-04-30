NHS Language Corpus Tools
===

This project seeks to build the first steps towards having a data set of UK focussed medical text sources for the purposes of training and benchmarking
NLP models for NHSX. The aim was to test thinking around feasibility of such a solution; infrastructure, scalability and maintenance; possible data
sources, appropriate metadata, clinical input and required governance; as well as possible use cases of the outputs for training, benchmarking, validating
and testing.

The `appstack` folder contains scripts and configuration files to deploy the stack either on AWS Elastic Container Service or on a locally running Docker.
Please refer to the [README](./appstack/README.md) for further details.

The `scrapers` folder contains a scraper framework as well as a number of scrapers implemented on top of the framework. Please refer to the
[README](./scrapers/README.md) for further details.
