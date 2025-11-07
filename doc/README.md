# modbuspy Documentation

This directory contains the Doxygen documentation setup for the modbuspy project.

## Structure

- `Doxyfile` - Main Doxygen configuration file
- `pages/` - Custom documentation pages
  - `mainpage.md` - Main documentation page with project overview
- `output/` - Generated documentation output (created after running Doxygen)

## Generating Documentation

### Prerequisites

1. Install Doxygen:
   - **Windows**: Download from https://www.doxygen.nl/download.html
   - **Linux**: `sudo apt-get install doxygen`
   - **macOS**: `brew install doxygen`

2. Optional: Install Graphviz for generating diagrams:
   - **Windows**: Download from https://graphviz.org/download/
   - **Linux**: `sudo apt-get install graphviz`
   - **macOS**: `brew install graphviz`

### Building Documentation

1. Navigate to the `doc` directory:
   ```console
   cd doc
   ```

2. Run Doxygen:
   ```console
   doxygen Doxyfile
   ```

3. Open the generated documentation:
   - HTML: Open `output/modbuspy/html/index.html` in your web browser
   - The documentation will include:
     - API reference for all modules and classes
     - Code examples and usage patterns
     - Cross-referenced source code
     - Class hierarchies and collaboration diagrams

## Configuration

The `Doxyfile` is configured for Python projects with the following key settings:

- **Language Support**: Optimized for Python with `OPTIMIZE_OUTPUT_JAVA = YES`
- **Python Docstrings**: Enabled with `PYTHON_DOCSTRING = YES`
- **File Patterns**: Configured to process `*.py` and `*.md` files
- **Source Browser**: Enabled for code browsing
- **HTML Output**: Modern responsive design with search functionality
- **Main Page**: Uses `pages/mainpage.md` as the project overview

## Customization

To customize the documentation:

1. **Add new pages**: Create `.md` files in the `pages/` directory
2. **Modify styling**: Add custom CSS files and reference them in `HTML_EXTRA_STYLESHEET`
3. **Add examples**: Place example files in the `../examples/` directory
4. **Configure diagrams**: Enable `HAVE_DOT = YES` if Graphviz is installed

## Output Formats

The current configuration generates:
- **HTML**: Interactive web documentation (default)
- **LaTeX/PDF**: Disabled (can be enabled by setting `GENERATE_LATEX = YES`)
- **XML**: Disabled (can be enabled for tool integration)

## Maintenance

- Update `PROJECT_NUMBER` in `Doxyfile` when releasing new versions
- Add new modules to documentation by ensuring they have proper docstrings
- Review and update `mainpage.md` when adding major features

## Troubleshooting

Common issues:

1. **Doxygen not found**: Ensure Doxygen is installed and in your PATH
2. **Empty documentation**: Check that Python files have proper docstrings
3. **Missing diagrams**: Install Graphviz and set `HAVE_DOT = YES`
4. **Encoding issues**: Ensure all files are UTF-8 encoded

For more information, see the [Doxygen Manual](https://www.doxygen.nl/manual/).