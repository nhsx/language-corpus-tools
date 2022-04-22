# NHS Language Corpus Discovery Tools
## Analytics Unit - Discovery Project

### Warning to Users

**This codebase is a proof of concept and should only be used for demonstration purposes within a controlled environment. The components are not a live product and should not be deployed in a live or production environment.**

We further recommend looking for the most recent versions of the individual components in their original repositories.

### About the Project

This discovery project seeks to investigate possible approaches to building a data set of NHS focussed text sources for the purposes of training and benchmarking NLP models in the NHS. You can read more about it in the blog [here](https://nhsx.github.io/AnalyticsUnit/languagecorpusdiscovery.html).

The aim was to test thinking and feasibility of such a solution by exploring aspects of:
- infrastructure, scalability and maintenance
- possible data sources, appropriate metadata, clinical input and required governance
- possible use cases of the outputs for training, benchmarking, validating and testing

This repository contains aspects of the tooling used during the discovery phase.

**Note:** No data, public or private are shared in this repository.

### Project Stucture

- `appstack` folder contains scripts and configuration files to deploy the stack either on AWS Elastic Container Service or to deploy on a local system running Docker.  Please refer to the folder [README](./appstack/README.md) for further details.

- `doccano_autolabelling` folder contains a script to implement an trial autolabelling approach into the `doccano` deployment.

- `scrapers` folder contains a scraper framework as well as a number of implemented scrapers. Please refer to the folder [README](./scrapers/README.md) for further details.

- `user_stories` folder contains a copy of the user stories which were identified as part of this discovery work.

### Limitations of Use

This repository is exploratory, pre-alpha code that has been developed for demonstration and evaluation purposes only. It is not to be used as a live service. No testing has been performed apart from ad-hoc trials and tests by its developers. No guarantees are made as to its performance. 

Although containing code to deploy as a cloud app, no auto-scaling or redundancy mechanisms have been built. No security reviews have been performed and therefore no guarantees are made as to the security of this release.

### Built using

- [Doccano v1.2.2](https://github.com/doccano/doccano/tree/v1.2.2)
- [MedCATTrainer v1.0.4](https://github.com/CogStack/MedCATtrainer/tree/1.0.4)
- [BRAT v1.3](https://github.com/nlplab/brat/tree/refs/tags/v1.3p1)

### Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

_See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidance._

### License

Distributed under the MIT License. _See [LICENSE](./LICENSE) for more information._

### Contact

To find out more about the [Analytics Unit](https://www.nhsx.nhs.uk/key-tools-and-info/nhsx-analytics-unit/) visit our [project website](https://nhsx.github.io/AnalyticsUnit/projects.html) or get in touch at [analytics-unit@nhsx.nhs.uk](mailto:analytics-unit@nhsx.nhs.uk).
