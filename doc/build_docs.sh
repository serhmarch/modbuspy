#!/bin/bash
# Build script for libmodbuspy documentation

echo "Building libmodbuspy documentation..."

# Check if doxygen is installed
if ! command -v doxygen &> /dev/null; then
    echo "Error: Doxygen is not installed or not in PATH"
    echo "Please install Doxygen from https://www.doxygen.nl/download.html"
    exit 1
fi

# Navigate to doc directory
cd "$(dirname "$0")"

# Generate documentation
echo "Running Doxygen..."
doxygen Doxyfile

# Check if generation was successful
if [ $? -eq 0 ]; then
    echo "Documentation generated successfully!"
    echo "Open output/libmodbuspy/html/index.html in your web browser to view the documentation"
else
    echo "Error: Documentation generation failed"
    exit 1
fi