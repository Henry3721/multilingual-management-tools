# Multilingual Management Tools

This is a comprehensive toolkit designed for managing multilingual content, focusing on seamless conversion between multilingual JSON, JS files, and Excel. It is ideal for startups and web projects that require efficient translation updates.

## Features

### 1. APP JSON to Excel Converter
Location: `/json_to_excel`
- Converts multiple JSON language files into a single Excel file
- Maintains hierarchical structure of language keys
- Preserves original key order
- Supports multiple language files processing
- Automatic error handling and logging
- Validates JSON structure during import

### 2. Excel to APP JSON Updater
Location: `/update_excel_to_json`
- Updates multiple JSON language files from Excel content
- Supports incremental updates (only changes modified content)
- Preserves existing translations
- Maintains JSON file structure
- Provides detailed update logs
- Error handling for file operations

### 3. H5 JS to Excel Converter
Location: `/js_to_excel`
- Converts multiple JS language files into a single Excel file
- Handles nested object structures
- Supports complex JS file parsing
- Maintains class and key hierarchies
- Preserves original order of translations
- Handles comments and special characters
- Supports multiple language processing

### 4. Excel to H5 JS Generator
Location: `/excel_to_js`
- Creates or updates multiple JS language files from Excel
- Maintains proper JS file structure
- Supports export default format
- Preserves class hierarchy
- Handles special characters and formatting
- Provides detailed conversion logs

## Installation

```bash
# Install required packages
pip install -r requirements.txt
