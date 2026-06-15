#!/bin/bash

# GreatReads Docker Deployment Script
# Usage: ./scripts/docker-deploy.sh [local|deploy] [--no-cache]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [MODE] [OPTIONS]

MODES:
    dev         Build and run development (foreground with logs, uses data-dev)
    local       Build and run locally (foreground with logs)
    deploy      Build and deploy in production (background/detached)
    restart     Restart the container without rebuilding
    stop        Stop the container
    logs        Show container logs
    status      Show container status

OPTIONS:
    --no-cache  Force a clean rebuild (no Docker cache)

EXAMPLES:
    $0 dev                      # Build and run development with logs
    $0 dev --no-cache           # Clean rebuild and run development
    $0 local                    # Build and run locally with logs
    $0 local --no-cache         # Clean rebuild and run locally
    $0 deploy                   # Build and deploy in production
    $0 deploy --no-cache        # Clean rebuild and deploy
    $0 restart                  # Restart without rebuilding
    $0 logs                     # Show logs
    $0 status                   # Show container status

EOF
}

# Parse arguments
MODE="${1:-}"
NO_CACHE=""

if [[ "$2" == "--no-cache" ]] || [[ "$1" == "--no-cache" && -z "$MODE" ]]; then
    NO_CACHE="--no-cache"
    print_warning "Clean rebuild requested (no cache)"
fi

# Validate mode
case "$MODE" in
    dev|local|deploy|restart|stop|logs|status)
        ;;
    "")
        print_error "No mode specified"
        show_usage
        exit 1
        ;;
    *)
        print_error "Invalid mode: $MODE"
        show_usage
        exit 1
        ;;
esac

# Main script
print_info "GreatReads Docker Deployment - Mode: $MODE"
echo ""

case "$MODE" in
    dev)
        print_info "Building for development (using data-dev)..."
        docker-compose -f docker-compose.dev.yml down
        docker-compose -f docker-compose.dev.yml build $NO_CACHE
        print_success "Build complete"
        echo ""
        print_info "Starting development container in foreground (Ctrl+C to stop)..."
        print_info "Access at: http://localhost:8010"
        print_info "Health check: http://localhost:8010/health"
        echo ""
        docker-compose -f docker-compose.dev.yml up
        ;;

    local)
        print_info "Building for local development..."
        docker-compose down
        docker-compose build $NO_CACHE
        print_success "Build complete"
        echo ""
        print_info "Starting container in foreground (Ctrl+C to stop)..."
        print_info "Access at: http://localhost:8007"
        print_info "Health check: http://localhost:8007/health"
        echo ""
        docker-compose up
        ;;

    deploy)
        print_info "Building for production deployment..."
        docker-compose down
        docker-compose build $NO_CACHE
        print_success "Build complete"
        echo ""
        print_info "Starting container in detached mode..."
        docker-compose up -d
        print_success "Container started"
        echo ""
        print_info "Waiting for health check..."
        sleep 3

        # Check health endpoint
        if curl -s http://localhost:8007/health | grep -q "ok"; then
            print_success "Health check passed!"
            print_success "Application deployed successfully"
            echo ""
            print_info "From dockerhost: http://localhost:8007"
            print_info "From local network: http://192.168.0.158:8007"
            echo ""
            print_info "View logs with: $0 logs"
        else
            print_error "Health check failed!"
            print_warning "Check logs with: $0 logs"
            exit 1
        fi
        ;;

    restart)
        print_info "Restarting container (no rebuild)..."
        docker-compose restart
        print_success "Container restarted"
        echo ""
        print_info "View logs with: $0 logs"
        ;;

    stop)
        print_info "Stopping container..."
        docker-compose down
        print_success "Container stopped"
        ;;

    logs)
        print_info "Showing container logs (Ctrl+C to exit)..."
        echo ""
        docker-compose logs -f
        ;;

    status)
        print_info "Container status:"
        echo ""
        docker-compose ps
        echo ""
        print_info "Health check:"
        if curl -s http://localhost:8007/health 2>/dev/null | grep -q "ok"; then
            print_success "Application is healthy"
            curl -s http://localhost:8007/health | jq . 2>/dev/null || curl -s http://localhost:8007/health
        else
            print_error "Application is not responding"
        fi
        ;;
esac

