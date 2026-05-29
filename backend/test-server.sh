#!/bin/bash

# Test script for the backend server

echo "🧪 Testing Ereader Backend Server"
echo "================================"

# Check if server is running
if ! curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "❌ Server is not running!"
    echo ""
    echo "Please start the server first:"
    echo "  export BOOKS_DIR=\"/path/to/your/books\""
    echo "  ./run.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Test health endpoint
echo "📡 Testing /api/health endpoint..."
health_response=$(curl -s http://localhost:5000/api/health)
echo "$health_response" | python3 -m json.tool
echo ""

# Test books endpoint
echo "📚 Testing /api/books endpoint..."
books_response=$(curl -s http://localhost:5000/api/books)
book_count=$(echo "$books_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")
echo "Found $book_count books"
echo ""

if [ "$book_count" -eq 0 ]; then
    echo "⚠️  No books found!"
    echo "Make sure your Calibre Content Server is running and has books in the library."
else
    echo "Sample books:"
    echo "$books_response" | python3 -c "import sys, json; books = json.load(sys.stdin)['books'][:5]; [print(f\"  - {b['title']} by {b['author']} ({b['format']})\") for b in books]"
fi

echo ""
echo "🎉 Backend server is working!"
echo ""
echo "Your server URL for the app:"
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "  http://$SERVER_IP:5000"
