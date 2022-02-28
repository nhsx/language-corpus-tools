This spider scrapes the Health A-Z section of the nhs.uk website using the API (https://developer.api.nhs.uk/nhs-api#<YOUR-API-KEY\>).

Note that the basic access to the API has a rather restrictive rate limits (10 requests/min). The framework handles it by honouring the Retry-After header in 429 responses,
however it means much longer running time.
