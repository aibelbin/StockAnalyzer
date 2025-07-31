#!/bin/bash

# PDF Repair and Validation Tool for StockAnalyzer
# This script provides utilities to repair and validate PDF files

echo "PDF Repair and Validation Tool"
echo "==============================="

# Function to check if ghostscript is installed
check_ghostscript() {
    if command -v gs >/dev/null 2>&1; then
        echo "✅ Ghostscript is installed: $(gs --version)"
        return 0
    elif command -v ghostscript >/dev/null 2>&1; then
        echo "✅ Ghostscript is installed: $(ghostscript --version)"
        return 0
    else
        echo "❌ Ghostscript is not installed"
        echo "Installing Ghostscript..."
        
        # Detect OS and install accordingly
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get >/dev/null 2>&1; then
                sudo apt-get update && sudo apt-get install -y ghostscript
            elif command -v yum >/dev/null 2>&1; then
                sudo yum install -y ghostscript
            elif command -v pacman >/dev/null 2>&1; then
                sudo pacman -S ghostscript
            else
                echo "Please install Ghostscript manually for your Linux distribution"
                return 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew >/dev/null 2>&1; then
                brew install ghostscript
            else
                echo "Please install Homebrew first, then run: brew install ghostscript"
                return 1
            fi
        else
            echo "Please install Ghostscript manually for your operating system"
            return 1
        fi
        
        # Verify installation
        if command -v gs >/dev/null 2>&1; then
            echo "✅ Ghostscript successfully installed"
            return 0
        else
            echo "❌ Ghostscript installation failed"
            return 1
        fi
    fi
}

# Function to validate a PDF
validate_pdf() {
    local pdf_file="$1"
    
    if [[ ! -f "$pdf_file" ]]; then
        echo "❌ File not found: $pdf_file"
        return 1
    fi
    
    echo "🔍 Validating PDF: $pdf_file"
    
    # Try to get PDF info
    if command -v pdfinfo >/dev/null 2>&1; then
        echo "Using pdfinfo to validate..."
        if pdfinfo "$pdf_file" >/dev/null 2>&1; then
            echo "✅ PDF structure appears valid"
            pages=$(pdfinfo "$pdf_file" | grep "Pages:" | awk '{print $2}')
            echo "   Pages: $pages"
            return 0
        else
            echo "❌ PDF validation failed with pdfinfo"
        fi
    fi
    
    # Try with Ghostscript
    if command -v gs >/dev/null 2>&1; then
        echo "Using Ghostscript to validate..."
        if gs -dNOPAUSE -dBATCH -sDEVICE=nullpage "$pdf_file" >/dev/null 2>&1; then
            echo "✅ PDF can be processed by Ghostscript"
            return 0
        else
            echo "❌ PDF validation failed with Ghostscript"
        fi
    fi
    
    return 1
}

# Function to repair a PDF
repair_pdf() {
    local input_pdf="$1"
    local output_pdf="$2"
    
    if [[ ! -f "$input_pdf" ]]; then
        echo "❌ Input file not found: $input_pdf"
        return 1
    fi
    
    if [[ -z "$output_pdf" ]]; then
        output_pdf="${input_pdf%.*}_repaired.pdf"
    fi
    
    echo "🔧 Repairing PDF: $input_pdf -> $output_pdf"
    
    if ! command -v gs >/dev/null 2>&1; then
        echo "❌ Ghostscript is required for PDF repair"
        return 1
    fi
    
    # Attempt repair with Ghostscript
    if gs -o "$output_pdf" \
          -sDEVICE=pdfwrite \
          -dPDFSETTINGS=/prepress \
          -dNOPAUSE \
          -dBATCH \
          -dSAFER \
          -dCompatibilityLevel=1.4 \
          "$input_pdf" 2>/dev/null; then
        echo "✅ PDF repair successful: $output_pdf"
        
        # Validate the repaired PDF
        if validate_pdf "$output_pdf"; then
            echo "✅ Repaired PDF is valid"
            return 0
        else
            echo "⚠️  Repaired PDF may still have issues"
            return 1
        fi
    else
        echo "❌ PDF repair failed"
        return 1
    fi
}

# Main script logic
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <command> [arguments]"
    echo ""
    echo "Commands:"
    echo "  check              - Check if required tools are installed"
    echo "  validate <pdf>     - Validate a PDF file"
    echo "  repair <pdf> [out] - Repair a PDF file"
    echo ""
    echo "Examples:"
    echo "  $0 check"
    echo "  $0 validate document.pdf"
    echo "  $0 repair corrupted.pdf fixed.pdf"
    exit 1
fi

command="$1"

case "$command" in
    "check")
        check_ghostscript
        ;;
    "validate")
        if [[ $# -lt 2 ]]; then
            echo "Usage: $0 validate <pdf_file>"
            exit 1
        fi
        validate_pdf "$2"
        ;;
    "repair")
        if [[ $# -lt 2 ]]; then
            echo "Usage: $0 repair <input_pdf> [output_pdf]"
            exit 1
        fi
        repair_pdf "$2" "$3"
        ;;
    *)
        echo "Unknown command: $command"
        echo "Use '$0' without arguments to see usage information"
        exit 1
        ;;
esac
