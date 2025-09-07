FROM node:20-bullseye
WORKDIR /app
COPY package*.json ./
RUN npm ci || npm i
COPY . .
RUN npm run build || npx tsc -p .
CMD ["node", "dist/index.js"]
