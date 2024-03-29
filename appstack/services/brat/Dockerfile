# This Dockerfile is based on cassj's Dockerfile at https://github.com/cassj/brat-docker/Dockerfile

# start from a base debian image
FROM debian:buster

# Install pre-reqs
RUN apt-get update \
    && apt-get install -y curl apache2 python supervisor \
    && rm -rf /var/lib/apt/lists/*

# Fetch  brat
RUN mkdir /var/www/brat
RUN curl http://weaver.nlplab.org/~brat/releases/brat-v1.3_Crunchy_Frog.tar.gz > /var/www/brat/brat-v1.3_Crunchy_Frog.tar.gz 
RUN cd /var/www/brat && tar -xvzf brat-v1.3_Crunchy_Frog.tar.gz

# Create data and work directories - but link to the mount points for the local volumes
RUN mkdir /bratdata
RUN mkdir /bratconfig
RUN chown -R www-data /bratdata
RUN chown -R www-data /bratconfig
RUN chmod g+rwx /bratdata
RUN chmod g+rwx /bratconfig
RUN chmod o-rwx /bratdata
RUN chmod o-rwx /bratconfig
RUN ln -s /bratdata /var/www/brat/brat-v1.3_Crunchy_Frog/data
RUN ln -s /bratconfig  /var/www/brat/brat-v1.3_Crunchy_Frog/config


ADD brat_install_wrapper.sh /usr/bin/brat_install_wrapper.sh
RUN chmod +x /usr/bin/brat_install_wrapper.sh

# Make sure apache can access it
RUN chown -R www-data:www-data /var/www/brat/brat-v1.3_Crunchy_Frog/

ADD 000-default.conf /etc/apache2/sites-available/000-default.conf

# Enable cgi
RUN a2enmod cgi

EXPOSE 80

# We can't use apachectl as an entrypoint because it starts apache and then exits, taking your container with it. 
# Instead, use supervisor to monitor the apache process
RUN mkdir -p /var/log/supervisor

ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf 

CMD ["/usr/bin/supervisord"]
