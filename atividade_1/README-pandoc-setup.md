# 🚀 Pandoc + File Watcher Setup

This setup provides automatic conversion of Markdown files to stylish PDFs using Pandoc with a custom LaTeX template based on your existing academic format.

## 📋 Prerequisites

### Required Dependencies

1. **Pandoc** - Document converter
2. **fswatch** - File system watcher
3. **LaTeX** - For PDF generation (MacTeX recommended)

## 🔧 Installation

### Automatic Installation (macOS)
```bash
make install-deps
```

### Manual Installation

#### Install Pandoc and fswatch
```bash
brew install pandoc fswatch
```

#### Install LaTeX (MacTeX)
```bash
brew install --cask mactex
```

**Note:** MacTeX is a large download (~4GB). After installation, you may need to restart your terminal or add `/usr/local/texlive/2024/bin/universal-darwin` to your PATH.

#### Alternative: Smaller LaTeX Installation
```bash
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install collection-fontsrecommended collection-latex collection-latexrecommended
```

## 🎯 Usage

### Method 1: Using the Watch Script (Recommended)

#### Start watching for automatic conversion:
```bash
./watch-markdown.sh
```

#### Watch a specific file:
```bash
./watch-markdown.sh my_document.md my_output
```

#### Convert once and exit:
```bash
./watch-markdown.sh --once atividade_1.md
```

### Method 2: Using Makefile

#### Convert to PDF:
```bash
make pdf
# or simply
make
```

#### Start file watching:
```bash
make watch
```

#### Convert to HTML (if LaTeX not available):
```bash
make html
make watch-html
```

#### Clean generated files:
```bash
make clean
```

#### Check dependencies:
```bash
make check-deps
```

### Method 3: Direct Pandoc Command

```bash
pandoc atividade_1.md -o atividade_1.pdf \
  --template=pandoc-template.tex \
  --bibliography=references.bib \
  --variable=lang:pt-BR \
  --variable=fontsize:12pt \
  --variable=geometry:margin=1in \
  --pdf-engine=xelatex
```

## 📁 File Structure

```
your-project/
├── atividade_1.md          # Your Markdown source
├── pandoc-template.tex     # Custom LaTeX template
├── references.bib          # Bibliography file
├── watch-markdown.sh       # File watcher script
├── Makefile               # Build automation
├── style.css              # CSS for HTML output
└── README-pandoc-setup.md # This file
```

## ⚙️ Configuration

### Template Customization

The `pandoc-template.tex` file is based on your existing LaTeX template and includes:

- ABNT citation style support
- Portuguese language support
- Academic formatting
- Code syntax highlighting
- Custom headers and footers
- Professional styling

### Markdown Metadata

Add metadata to your Markdown files:

```yaml
---
title: "Your Document Title"
author: "Your Name"
date: "2025-01-27"
short-title: "Short Title for Headers"
toc: true
bibliography: references.bib
---
```

### Watch Script Options

The watch script (`watch-markdown.sh`) supports:

- `--help` - Show help message
- `--once` - Convert once and exit
- `--watch` - Start file watching (default)

## 🎨 Output Formats

### PDF Output
- Uses XeLaTeX engine for better font support
- Professional academic formatting
- Proper Portuguese language support
- ABNT citation style

### HTML Output (Fallback)
- Uses custom CSS styling
- Responsive design
- Print-friendly
- Syntax highlighting

## 🔍 Troubleshooting

### LaTeX Not Found
If you get LaTeX errors:
1. Install MacTeX: `brew install --cask mactex`
2. Restart terminal or update PATH
3. Use HTML output as fallback: `make html`

### File Not Found Errors
- Ensure your Markdown file exists
- Check file paths in configuration
- Verify template and bibliography files are present

### Permission Denied
Make the script executable:
```bash
chmod +x watch-markdown.sh
```

### Bibliography Issues
- Ensure `references.bib` exists
- Check BibTeX syntax
- Remove bibliography option if not needed

## 🚀 Advanced Usage

### Custom Templates
Modify `pandoc-template.tex` to customize:
- Page layout
- Fonts
- Colors
- Headers/footers
- Citation style

### Multiple Files
Watch multiple files by running separate instances:
```bash
./watch-markdown.sh file1.md output1 &
./watch-markdown.sh file2.md output2 &
```

### Batch Conversion
Use the Makefile with different parameters:
```bash
make MARKDOWN_FILE=chapter1.md OUTPUT_NAME=chapter1 pdf
make MARKDOWN_FILE=chapter2.md OUTPUT_NAME=chapter2 pdf
```

## 📚 Tips

1. **File Organization**: Keep all related files in the same directory
2. **Version Control**: Add `*.pdf` and `*.html` to `.gitignore`
3. **Backup**: Keep backups of your custom templates
4. **Testing**: Test with small files first
5. **Performance**: Large bibliographies may slow conversion

## 🆘 Help

For help with specific components:
- **Pandoc**: `pandoc --help` or [Pandoc Manual](https://pandoc.org/MANUAL.html)
- **LaTeX**: Check LaTeX logs for detailed error messages
- **fswatch**: `man fswatch` for file watching options

## 📝 Example Workflow

1. Edit your `atividade_1.md` file
2. Run `./watch-markdown.sh` in terminal
3. Save your Markdown file
4. PDF is automatically generated
5. Continue editing - PDF updates automatically

This setup gives you a professional, automated workflow for academic document creation! 🎓
