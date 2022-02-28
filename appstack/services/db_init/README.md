This Docker image provides a mechanism to initialise the database after an instance has been created.

This includes creating the necessary users and schemas.

If more scripts are added they need to be idempotent as this container may run on an already created database. It must not drop any existing objects.
