import os
from pathlib import Path

TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Presse</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        
        h2 {
            color: #1a3c5e;
            border-bottom: 2px solid #1a3c5e;
            padding-bottom: 8px;
            margin-top: 30px;
            font-weight: 600;
        }
        
        ul {
            list-style-type: none;
            padding-left: 15px;
        }
        
        .newspaper-section {
            background-color: white;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 25px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .folder {
            margin: 10px 0;
            font-weight: 500;
            color: #2c3e50;
        }
        
        .folder-icon {
            margin-right: 8px;
            color: #e67e22;
        }
        
        .file {
            margin: 5px 0 5px 25px;
            transition: transform 0.2s;
        }
        
        .file:hover {
            transform: translateX(5px);
        }
        
        .pdf-icon {
            margin-right: 8px;
            color: #e74c3c;
        }
        
        a {
            text-decoration: none;
            color: #3498db;
            transition: color 0.2s;
        }
        
        a:hover {
            color: #2980b9;
            text-decoration: underline;
        }
        
        .date-label {
            background-color: #f0f7ff;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 0.9em;
            color: #1a3c5e;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .header-desc {
            color: #7f8c8d;
            font-style: italic;
        }
    </style>
</head>
<body>
    <header>
        <h1>Presse</h1>
        <p class="header-desc">BNF - Europresse</p>
    </header>
"""

TEMPLATE_END = """
</body>
</html>
"""

def generate_index(all_editions):

    current_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "Journaux"
    print("Current ", current_dir)

    li_template = '<li class="folder"><span class="folder-icon">📁</span>{name}\n{content}</li>\n'
    pdf_template = '<li class="file pdf"><a href="{pdf_path}" target="_blank"><span class="pdf-icon">📄</span>{pdf_name}</a></li>\n'

    html = ""
    for journal_name, dates_dict in all_editions.items():
        html += f"<h2>{journal_name}</h2>\n"
        dates_str = ""
        for date, pdf_paths in dates_dict.items():
            pdfs_str = ""
            for pdf_path in pdf_paths:
                pdfs_str += pdf_template.format(pdf_path=pdf_path, pdf_name=pdf_path.split("/")[-1])
            pdfs_str = f"<ul>\n{pdfs_str}</ul>\n"
            dates_str += li_template.format(name=date, content=pdfs_str)

        html += f'\n<div class="newspaper-section">{dates_str}</div>\n'

    rendered_html = TEMPLATE + html + TEMPLATE_END

    output_path = os.path.join(current_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
