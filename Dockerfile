FROM nginx:alpine

COPY index.html altstore.json /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/

EXPOSE 80
