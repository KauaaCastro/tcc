FROM nginx:alpine

# Copia os arquivos estáticos do frontend para a pasta padrão do Nginx
COPY ./index.html /usr/share/nginx/html/index.html
COPY ./css/ /usr/share/nginx/html/css/
COPY ./js/ /usr/share/nginx/html/js/

# Copia a configuração personalizada do Nginx para habilitar o proxy reverso
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
