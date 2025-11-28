FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY ui/frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY ui/frontend/. .

EXPOSE 5173

# Run dev server with host binding for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
