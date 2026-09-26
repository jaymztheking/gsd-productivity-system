# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Placed in templates/ rather than conf.d/ so the nginx:alpine entrypoint
# renders it with envsubst at startup, injecting API_TOKEN from the
# environment. The filter limits substitution to our own variable so that
# nginx directives like $uri and $host are left alone.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
ENV NGINX_ENVSUBST_FILTER='API_TOKEN'

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
