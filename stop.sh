#!/bin/bash

# Digiskills IT Helpdesk - Stop Script

echo "Stopping Digiskills IT Helpdesk..."
docker-compose down

echo ""
echo "Digiskills has been stopped."
echo ""
echo "To start again, run: ./start.sh"
echo "To remove all data, run: docker-compose down -v"
