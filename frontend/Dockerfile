FROM nginx:1.27-alpine

ARG NGINX_CONF=nginx.conf
COPY frontend/${NGINX_CONF} /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY guide.html /usr/share/nginx/html/guide.html
COPY shortcuts.html /usr/share/nginx/html/shortcuts.html
COPY SHORTCUTS.md /usr/share/nginx/html/SHORTCUTS.md
