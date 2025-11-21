FROM node:18-alpine AS build
WORKDIR /app
COPY package.json ./
COPY pnpm-lock.yaml ./
COPY package-lock.json ./
RUN [ -f pnpm-lock.yaml ] && npm i -g pnpm || true
RUN if [ -f pnpm-lock.yaml ]; then pnpm install; elif [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]