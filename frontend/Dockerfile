# Build Stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Vite incrusta VITE_API_BASE_URL y VITE_TELEGRAM_BOT_URL en el build;
# Railway las pasa como build arg si están declaradas aquí.
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ARG VITE_TELEGRAM_BOT_URL
ENV VITE_TELEGRAM_BOT_URL=$VITE_TELEGRAM_BOT_URL
RUN npm run build

# Production Stage
FROM nginx:alpine

# Copiar build de Vite al directorio de Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar plantilla Nginx con soporte de variable $PORT (Railway compatible)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

ENV PORT=80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
