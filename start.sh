#!/bin/bash

# Modern sese-engine startup script
# This script starts all components of the search engine

set -e

# Configuration
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export SESE_STORAGE_PATH=${SESE_STORAGE_PATH:-"./savedata"}
export SESE_PORT=${SESE_PORT:-8080}
export SESE_HOST=${SESE_HOST:-"0.0.0.0"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_success "Python version $PYTHON_VERSION is compatible"
else
    print_error "Python 3.8 or higher is required. Found version $PYTHON_VERSION"
    exit 1
fi

# Check if dependencies are installed
print_status "Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn, jieba, lxml, brotli" 2>/dev/null; then
    print_warning "Dependencies not found. Installing..."
    pip install -e .
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies. Please run: pip install -e ."
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p "$SESE_STORAGE_PATH"
mkdir -p ./data
mkdir -p ./logs

# Check if tmux is available
if command -v tmux &> /dev/null; then
    USE_TMUX=true
    print_success "tmux found - will use multi-pane layout"
else
    USE_TMUX=false
    print_warning "tmux not found - will use simple layout"
fi

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down sese-engine..."
    
    if [ "$USE_TMUX" = true ]; then
        tmux kill-session -t sese_engine 2>/dev/null || true
    else
        # Kill background processes
        pkill -f "python.*src.api.main" 2>/dev/null || true
        pkill -f "python.*src.crawler" 2>/dev/null || true
        pkill -f "python.*src.indexer" 2>/dev/null || true
    fi
    
    print_success "sese-engine stopped"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

print_success "Starting sese-engine..."

if [ "$USE_TMUX" = true ]; then
    # Start with tmux multi-pane layout
    TMUX_SESSION_NAME="sese_engine"
    
    # Check if session already exists
    if tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
        print_warning "Session $TMUX_SESSION_NAME already exists. Killing it..."
        tmux kill-session -t "$TMUX_SESSION_NAME"
    fi
    
    # Create new session
    tmux new-session -d -s "$TMUX_SESSION_NAME"
    
    # Split into panes
    tmux split-window -h -t "$TMUX_SESSION_NAME"
    tmux split-window -v -t "$TMUX_SESSION_NAME:0.0"
    tmux split-window -v -t "$TMUX_SESSION_NAME:0.1"
    
    # Start API server in pane 0
    tmux send-keys -t "$TMUX_SESSION_NAME:0.0" "cd $(pwd)" Enter
    tmux send-keys -t "$TMUX_SESSION_NAME:0.0" "python -m src.api.main" Enter
    
    # Start crawler in pane 1
    tmux send-keys -t "$TMUX_SESSION_NAME:0.1" "cd $(pwd)" Enter
    tmux send-keys -t "$TMUX_SESSION_NAME:0.1" "echo 'Starting crawler...' && while true; do python -m src.crawler.main; sleep 1; done" Enter
    
    # Start indexer in pane 2
    tmux send-keys -t "$TMUX_SESSION_NAME:0.2" "cd $(pwd)" Enter
    tmux send-keys -t "$TMUX_SESSION_NAME:0.2" "echo 'Starting indexer...' && while true; do python -m src.indexer.main; sleep 1; done" Enter
    
    # Start metrics in pane 3
    tmux send-keys -t "$TMUX_SESSION_NAME:0.3" "cd $(pwd)" Enter
    tmux send-keys -t "$TMUX_SESSION_NAME:0.3" "echo 'Starting metrics...' && python -m src.metrics.main" Enter
    
    # Attach to the session
    print_success "sese-engine started with tmux multi-pane layout"
    print_status "API server: http://$SESE_HOST:$SESE_PORT"
    print_status "Press Ctrl+B, D to detach from tmux session"
    print_status "To reattach: tmux attach -t $TMUX_SESSION_NAME"
    
    tmux attach -t "$TMUX_SESSION_NAME"
    
else
    # Start without tmux
    print_status "Starting API server..."
    python -m src.api.main &
    API_PID=$!
    
    print_status "Starting crawler..."
    (while true; do python -m src.crawler.main; sleep 1; done) &
    CRAWLER_PID=$!
    
    print_status "Starting indexer..."
    (while true; do python -m src.indexer.main; sleep 1; done) &
    INDEXER_PID=$!
    
    print_success "sese-engine started in background"
    print_status "API server: http://$SESE_HOST:$SESE_PORT"
    print_status "API PID: $API_PID"
    print_status "Crawler PID: $CRAWLER_PID"
    print_status "Indexer PID: $INDEXER_PID"
    print_status "Press Ctrl+C to stop"
    
    # Wait for interrupt
    wait
fi