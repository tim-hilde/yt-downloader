# Multi-stage build for smaller image size and better Pi performance
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (production only for smaller size)
RUN npm ci --only=production --silent

# Copy source code
COPY public/ ./public/
COPY src/ ./src/

# Build the React app
RUN npm run build

# Production stage - smaller final image
FROM node:18-alpine AS production

WORKDIR /app

# Install serve globally
RUN npm install -g serve@14.2.1 --silent

# Copy built app from builder stage
COPY --from=builder /app/build ./build

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S reactuser -u 1001

# Switch to non-root user
USER reactuser

# Expose port
EXPOSE 3000

# Health check - less frequent for Pi
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start the application
CMD ["serve", "-s", "build", "-l", "3000"]
