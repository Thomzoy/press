import os
import jinja2
from pathlib import Path

def scan_directory(root_dir, base_dir):
    """
    Scans the directory structure starting from root_dir
    Returns a dictionary representing the structure
    """
    structure = {}
    
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        
        # Skip the index.html file itself
        if item == "index.html":
            continue
            
        if os.path.isdir(item_path):
            # If it's a directory, recursively scan it
            structure[item] = {
                'type': 'directory',
                'content': scan_directory(item_path, base_dir),
                'path': os.path.relpath(item_path, root_dir)
            }
        elif item.lower().endswith('.pdf'):
            print("ITEM", item_path)
            # If it's a PDF file, add it to the structure with its relative path
            structure[item] = {
                'type': 'pdf',
                'path': os.path.relpath(item_path, base_dir)
            }
    
    return structure

def generate_html_structure(structure, indent=0):
    """
    Recursively generates HTML to represent the directory structure
    """
    html = ""
    indent_str = "  " * indent
    
    for name, info in sorted(structure.items()):
        if info['type'] == 'pdf':  # It's a PDF file
            # Make the PDF file clickable with its relative path
            html += f'{indent_str}<li class="file pdf"><a href="{info["path"]}" target="_blank"><span class="pdf-icon">📄</span> {name}</a></li>\n'
        elif name.strip() != "images":  # It's a directory
            html += f'{indent_str}<li class="folder"><span class="folder-icon">📁</span> {name}\n'
            html += f'{indent_str}  <ul>\n'
            html += generate_html_structure(info['content'], indent + 2)
            html += f'{indent_str}  </ul>\n'
            html += f'{indent_str}</li>\n'
    
    return html

def create_index_html():
    """
    Creates the index.html file displaying the directory structure
    """
    # Get the directory where the script is running
    current_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "Journaux"
    print("Current ", current_dir)
    if not current_dir:  # If empty, use current directory
        current_dir = os.getcwd()
    
    # Scan the directory structure
    structure = scan_directory(current_dir, base_dir=current_dir)
    
    # Create HTML structure
    html_structure = generate_html_structure(structure)
    
    # Jinja2 template
    template_str = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BNF Press</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        ul {
            list-style-type: none;
            padding-left: 20px;
        }
        li {
            margin: 5px 0;
        }
        .folder {
            font-weight: bold;
            cursor: pointer;
        }
        .file {
            font-weight: normal;
        }
        .pdf {
            color: #C00;
        }
        .pdf a {
            color: #C00;
            text-decoration: none;
        }
        .pdf a:hover {
            text-decoration: underline;
        }
        .folder-icon, .pdf-icon {
            margin-right: 5px;
        }
        /* Add JavaScript to make folders collapsible */
        .folder > ul {
            display: block;
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Add click event to all folder elements
            document.querySelectorAll('.folder').forEach(folder => {
                folder.addEventListener('click', function(event) {
                    // Only toggle if the click was directly on this element or its folder icon/text
                    if (event.target === this || 
                        event.target.classList.contains('folder-icon') || 
                        (event.target.parentNode === this && event.target.nodeName !== 'A')) {
                        
                        // Toggle visibility of the child ul element
                        const ul = this.querySelector('ul');
                        if (ul) {
                            ul.style.display = ul.style.display === 'none' ? 'block' : 'none';
                        }
                        
                        // Stop event propagation to prevent parent folders from collapsing
                        event.stopPropagation();
                    }
                });
            });
            
            // Prevent clicks on PDF links from toggling parent folders
            document.querySelectorAll('.pdf a').forEach(link => {
                link.addEventListener('click', function(event) {
                    event.stopPropagation();
                });
            });
        });
    </script>
</head>
<body>
    <h1>Presse</h1>
    <div class="directory-tree">
        <ul>
            {{ structure|safe }}
        </ul>
    </div>
</body>
</html>
"""
    
    # Create template and render
    template = jinja2.Template(template_str)
    rendered_html = template.render(structure=html_structure, current_dir=current_dir)
    
    # Write the HTML to index.html
    output_path = os.path.join(current_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    
    print(f"Created index.html successfully at {output_path}")

if __name__ == "__main__":
    create_index_html()
