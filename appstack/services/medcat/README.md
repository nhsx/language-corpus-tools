This folder contains a custom Docker image configuration for the [MedCATTrainer](https://github.com/CogStack/MedCATtrainer).

This build significantly reduces the image size and makes teh database connection parameters and the admin username and password configurable.

It also bundles an instance of nginx that serves static content eliminating the need to have a separate container and a volume.
