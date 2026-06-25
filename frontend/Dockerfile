# 多阶段：node 构建静态产物 -> nginx 托管 + 反代后端
FROM node:20-alpine AS build
WORKDIR /app
# controller 可用内存有限，Node 会自调出很小的堆 → vite build 生成阶段 OOM。
# 显式抬高堆上限（仅 docker 构建生效，不影响本地 Windows 构建）。
ENV NODE_OPTIONS=--max-old-space-size=4096
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
