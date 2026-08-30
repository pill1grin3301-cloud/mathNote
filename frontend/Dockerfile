FROM nginx:1.27-alpine

ARG NGINX_CONF=nginx.conf
COPY frontend/${NGINX_CONF} /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
