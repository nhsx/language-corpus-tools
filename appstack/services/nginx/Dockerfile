FROM nginx
# Add configuration
RUN rm /etc/nginx/conf.d/default.conf
ADD nginx.conf /etc/nginx/nginx.conf
# Add site
ADD templates/ /etc/nginx/templates
