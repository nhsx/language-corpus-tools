NOTE: Nginx has been replaced by caddy. See ../caddy for more details.


This Nginx instance is used as the entry point to the application stack. Its only purpose currently is to route the requests to the appropriate
internal endpoints.

Note, in AWS it could be done by configuring Load Balancer forwarding rules, but the goal was to make the configuration as vendor-agnostic as possible.

In the future this instance could also handle access control, federated authentication, etc.
