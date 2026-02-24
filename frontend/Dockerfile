# Встановлюємо Node.js для збірки
FROM node:22-alpine as build

WORKDIR /app

# Копіюємо package.json та встановлюємо залежності
COPY package.json package-lock.json ./
RUN npm ci

# Копіюємо весь код та збираємо застосунок
COPY . .
RUN npm run build

# Використовуємо легкий Nginx для роздачі статики
FROM nginx:alpine

# Копіюємо зібрані файли React у стандартну папку Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Копіюємо наш конфіг Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
