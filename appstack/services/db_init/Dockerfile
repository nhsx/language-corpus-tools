FROM alpine:3.12

RUN apk --no-cache add postgresql-client

COPY db-init.sh /
COPY scripts /scripts/
RUN chmod +x /db-init.sh

CMD ["/db-init.sh"]
