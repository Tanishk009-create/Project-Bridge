FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG BACKEND_URL=http://api:8000
ENV BACKEND_URL=$BACKEND_URL
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0"]
