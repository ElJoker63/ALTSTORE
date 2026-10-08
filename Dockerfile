FROM nginx:alpine

# Copia todo el repo (menos lo excluido en .dockerignore):
# cualquier carpeta nueva (apps/, img/, etc.) se sirve sola tras cada deploy.
COPY . /usr/share/nginx/html/

EXPOSE 80
