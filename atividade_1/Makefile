# Makefile for Pandoc Markdown to PDF Conversion
# Usage: make [target]

# Configuration
MARKDOWN_FILE = atividade_1.md
OUTPUT_NAME = atividade_1
TEMPLATE = pandoc-template.tex
BIBLIOGRAPHY = references.bib
PDF_ENGINE = xelatex

# Pandoc flags
PANDOC_FLAGS = --template=$(TEMPLATE) \
               --bibliography=$(BIBLIOGRAPHY) \
               --variable=lang:pt-BR \
               --variable=fontsize:12pt \
               --variable=geometry:margin=1in \
               --pdf-engine=$(PDF_ENGINE) \
               --highlight-style=pygments \
               --standalone

# Default target
.PHONY: all
all: pdf

# Convert to PDF
.PHONY: pdf
pdf: $(OUTPUT_NAME).pdf

$(OUTPUT_NAME).pdf: $(MARKDOWN_FILE) $(TEMPLATE) $(BIBLIOGRAPHY)
	@echo "Converting $(MARKDOWN_FILE) to PDF..."
	pandoc $(MARKDOWN_FILE) -o $(OUTPUT_NAME).pdf $(PANDOC_FLAGS)
	@echo "✓ Successfully created $(OUTPUT_NAME).pdf"

# Convert to HTML (fallback if LaTeX not available)
.PHONY: html
html: $(OUTPUT_NAME).html

$(OUTPUT_NAME).html: $(MARKDOWN_FILE)
	@echo "Converting $(MARKDOWN_FILE) to HTML..."
	pandoc $(MARKDOWN_FILE) -o $(OUTPUT_NAME).html --standalone --css=style.css --variable=lang:pt-BR
	@echo "✓ Successfully created $(OUTPUT_NAME).html"

# Watch for changes and auto-convert
.PHONY: watch
watch:
	@echo "Starting file watcher..."
	./watch-markdown.sh $(MARKDOWN_FILE) $(OUTPUT_NAME)

# Watch with HTML output
.PHONY: watch-html
watch-html:
	@echo "Starting file watcher (HTML mode)..."
	USE_HTML=true ./watch-markdown.sh $(MARKDOWN_FILE) $(OUTPUT_NAME)

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	rm -f $(OUTPUT_NAME).pdf $(OUTPUT_NAME).html
	rm -f *.aux *.log *.out *.toc *.nav *.snm *.vrb
	@echo "✓ Cleaned"

# Install dependencies (macOS)
.PHONY: install-deps
install-deps:
	@echo "Installing dependencies..."
	@if ! command -v brew >/dev/null 2>&1; then \
		echo "❌ Homebrew not found. Please install Homebrew first."; \
		exit 1; \
	fi
	brew install pandoc fswatch
	@if ! command -v xelatex >/dev/null 2>&1; then \
		echo "Installing MacTeX (this may take a while)..."; \
		brew install --cask mactex; \
	fi
	@echo "✓ Dependencies installed"

# Check if all dependencies are available
.PHONY: check-deps
check-deps:
	@echo "Checking dependencies..."
	@command -v pandoc >/dev/null 2>&1 || (echo "❌ pandoc not found" && exit 1)
	@command -v fswatch >/dev/null 2>&1 || (echo "❌ fswatch not found" && exit 1)
	@command -v xelatex >/dev/null 2>&1 || echo "⚠️  xelatex not found (will use HTML output)"
	@echo "✓ Dependencies check completed"

# Show help
.PHONY: help
help:
	@echo "Pandoc Markdown to PDF Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  pdf          Convert markdown to PDF (default)"
	@echo "  html         Convert markdown to HTML"
	@echo "  watch        Watch for changes and auto-convert to PDF"
	@echo "  watch-html   Watch for changes and auto-convert to HTML"
	@echo "  clean        Remove generated files"
	@echo "  install-deps Install required dependencies (macOS)"
	@echo "  check-deps   Check if dependencies are installed"
	@echo "  help         Show this help message"
	@echo ""
	@echo "Configuration:"
	@echo "  MARKDOWN_FILE = $(MARKDOWN_FILE)"
	@echo "  OUTPUT_NAME   = $(OUTPUT_NAME)"
	@echo "  TEMPLATE      = $(TEMPLATE)"
	@echo "  BIBLIOGRAPHY  = $(BIBLIOGRAPHY)"
	@echo "  PDF_ENGINE    = $(PDF_ENGINE)"
	@echo ""
	@echo "Examples:"
	@echo "  make                    # Convert to PDF"
	@echo "  make watch              # Start watching for changes"
	@echo "  make MARKDOWN_FILE=test.md OUTPUT_NAME=test pdf"
	@echo "  make clean              # Clean generated files"

# Set default goal
.DEFAULT_GOAL := pdf
