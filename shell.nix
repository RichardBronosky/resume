{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "resume-builder-env";
  
  buildInputs = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
    pkgs.libreoffice
  ];

  shellHook = ''
    echo "=========================================="
    echo "🦞 Resume Builder Environment"
    echo "=========================================="
    echo "Python and LibreOffice are ready."
    echo ""
    
    # Auto-setup the virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "Creating python virtual environment..."
        python -m venv .venv
    fi
    
    source .venv/bin/activate
    
    # Install the local docx-generator package in editable mode
    if ! command -v resume-docx &> /dev/null; then
        echo "Installing docx-generator..."
        pip install -e src/docx-generator -q
    fi
    
    echo "You can now run: make docx"
    echo "              or make pdf"
  '';
}
