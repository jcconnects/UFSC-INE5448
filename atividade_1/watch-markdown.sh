#!/bin/bash

# Pandoc + File Watcher Script for Automatic Markdown to PDF Conversion
# Usage: ./watch-markdown.sh [markdown-file] [output-name]

# Configuration
MARKDOWN_FILE=${1:-"atividade_1.md"}
OUTPUT_NAME=${2:-"atividade_1"}
TEMPLATE="pandoc-template.tex"
BIBLIOGRAPHY="references.bib"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠${NC} $1"
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v pandoc &> /dev/null; then
        print_error "Pandoc is not installed. Install with: brew install pandoc"
        exit 1
    fi
    
    if ! command -v fswatch &> /dev/null; then
        print_error "fswatch is not installed. Install with: brew install fswatch"
        exit 1
    fi
    
    if ! command -v xelatex &> /dev/null && ! command -v pdflatex &> /dev/null; then
        print_warning "LaTeX engine not found. Install with: brew install --cask mactex"
        print_warning "Falling back to HTML output..."
        USE_HTML=true
    fi
    
    print_success "Dependencies check completed"
}

# Function to convert markdown to PDF
convert_to_pdf() {
    print_status "Converting $MARKDOWN_FILE to PDF..."
    
    # Check if markdown file exists
    if [[ ! -f "$MARKDOWN_FILE" ]]; then
        print_error "Markdown file '$MARKDOWN_FILE' not found!"
        return 1
    fi
    
    # Pandoc command with all the options
    PANDOC_CMD="pandoc '$MARKDOWN_FILE'"
    
    # Add template if it exists
    if [[ -f "$TEMPLATE" ]]; then
        PANDOC_CMD="$PANDOC_CMD --template='$TEMPLATE'"
    fi
    
    # Add bibliography if it exists
    if [[ -f "$BIBLIOGRAPHY" ]]; then
        PANDOC_CMD="$PANDOC_CMD --bibliography='$BIBLIOGRAPHY'"
    fi
    
    # Choose output format and engine
    if [[ "$USE_HTML" == "true" ]]; then
        PANDOC_CMD="$PANDOC_CMD -o '${OUTPUT_NAME}.html' --standalone --css=style.css"
    else
        PANDOC_CMD="$PANDOC_CMD -o '${OUTPUT_NAME}.pdf' --pdf-engine=xelatex"
    fi
    
    # Add common options
    PANDOC_CMD="$PANDOC_CMD --variable=lang:pt-BR --variable=fontsize:12pt --variable=geometry:margin=1in --highlight-style=pygments"
    
    # Execute the command
    if eval $PANDOC_CMD; then
        if [[ "$USE_HTML" == "true" ]]; then
            print_success "Successfully converted to ${OUTPUT_NAME}.html"
        else
            print_success "Successfully converted to ${OUTPUT_NAME}.pdf"
        fi
    else
        print_error "Conversion failed!"
        return 1
    fi
}

# Function to start file watching
start_watching() {
    print_status "Starting file watcher for $MARKDOWN_FILE..."
    print_status "Press Ctrl+C to stop watching"
    
    # Initial conversion
    convert_to_pdf
    
    # Watch for changes
    fswatch -o "$MARKDOWN_FILE" | while read f; do
        print_status "File changed, reconverting..."
        convert_to_pdf
    done
}

# Function to show help
show_help() {
    echo "Pandoc + File Watcher for Automatic Markdown to PDF Conversion"
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS] [markdown-file] [output-name]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -o, --once     Convert once and exit (no watching)"
    echo "  -w, --watch    Start file watching (default)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Watch atividade_1.md, output to atividade_1.pdf"
    echo "  $0 my_file.md my_output      # Watch my_file.md, output to my_output.pdf"
    echo "  $0 -o atividade_1.md         # Convert once and exit"
    echo ""
    echo "Files used:"
    echo "  Template: $TEMPLATE"
    echo "  Bibliography: $BIBLIOGRAPHY"
}

# Parse command line arguments
WATCH_MODE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--once)
            WATCH_MODE=false
            shift
            ;;
        -w|--watch)
            WATCH_MODE=true
            shift
            ;;
        *)
            if [[ -z "$MARKDOWN_FILE_SET" ]]; then
                MARKDOWN_FILE="$1"
                MARKDOWN_FILE_SET=true
            elif [[ -z "$OUTPUT_NAME_SET" ]]; then
                OUTPUT_NAME="$1"
                OUTPUT_NAME_SET=true
            fi
            shift
            ;;
    esac
done

# Main execution
print_status "Pandoc Markdown to PDF Converter"
print_status "Markdown file: $MARKDOWN_FILE"
print_status "Output name: $OUTPUT_NAME"

check_dependencies

if [[ "$WATCH_MODE" == "true" ]]; then
    start_watching
else
    convert_to_pdf
fi
