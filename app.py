from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
import os
from datetime import datetime
import math

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Store file metadata in memory (for demo); in real use, save to DB or JSON file.
files = []

MAX_FILES = 50
FILES_PER_PAGE = 5

# Load existing files on startup
def load_files():
    global files
    files = []
    for fname in os.listdir(UPLOAD_FOLDER):
        fpath = os.path.join(UPLOAD_FOLDER, fname)
        if os.path.isfile(fpath):
            created = datetime.fromtimestamp(os.path.getctime(fpath))
            files.append({
                'name': fname,
                'date': created,
                'path': fpath
            })
    # Sort newest first
    files.sort(key=lambda x: x['date'], reverse=True)

load_files()

@app.route('/', methods=['GET', 'POST'])
def index():
    global files
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            save_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(save_path)

            # Add new file to list
            files.insert(0, {
                'name': file.filename,
                'date': datetime.now(),
                'path': save_path
            })

            # Keep max 50 files, delete oldest
            while len(files) > MAX_FILES:
                old_file = files.pop()
                try:
                    os.remove(old_file['path'])
                except:
                    pass

            return redirect(url_for('index'))

    # Pagination handling
    page = request.args.get('page', '1')
    try:
        page = int(page)
        if page < 1:
            page = 1
    except:
        page = 1

    total_pages = math.ceil(len(files) / FILES_PER_PAGE)
    if page > total_pages and total_pages > 0:
        page = total_pages

    start = (page - 1) * FILES_PER_PAGE
    end = start + FILES_PER_PAGE
    files_page = files[start:end]

    # Render basic HTML with inline template
    html = '''
    <html>
    <head>
      <title>Pokemon Red Chapter Save Files</title>
      <style>
        table, th, td { border: 1px solid black; border-collapse: collapse; padding: 5px; }
        th { background-color: #eee; }
        nav a { margin: 0 5px; text-decoration: none; }
        nav a.current { font-weight: bold; }
      </style>
    </head>
    <body>
      <h2>Upload Pokemon Red Chapter Save File</h2>
      <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" required />
        <input type="submit" value="Upload" />
      </form>

      <h3>Save Files</h3>
      <table>
        <tr>
          <th>Serial No</th>
          <th>Name</th>
          <th>Date</th>
          <th>Download</th>
          <th>Delete</th>
          
        </tr>
        {% for idx, f in files %}
        <tr>
          <td>{{ idx }}</td>
          <td>{{ f.name }}</td>
          <td>{{ f.date.strftime("%d/%m/%Y %H:%M:%S") }}</td>
          <td><a href="/download/{{ f.name }}">Download</a></td>
          <td><a href="/delete/{{ f.name }}" onclick="return confirm('Delete this file?')">Delete</a></td>
        </tr>
        {% endfor %}
      </table>

      <nav>
        {% if page > 1 %}
          <a href="/?page={{ page-1 }}">Prev</a>
        {% endif %}
        {% for p in range(1, total_pages + 1) %}
          {% if p == page %}
            <a href="/?page={{ p }}" class="current">{{ p }}</a>
          {% else %}
            <a href="/?page={{ p }}">{{ p }}</a>
          {% endif %}
        {% endfor %}
        {% if page < total_pages %}
          <a href="/?page={{ page+1 }}">Next</a>
        {% endif %}
      </nav>
    </body>
    </html>
    '''
    # Add serial numbers starting from 1 + offset of page
    indexed_files = [(start + i + 1, f) for i, f in enumerate(files_page)]

    return render_template_string(html, files=indexed_files, page=page, total_pages=total_pages)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete_file(filename):
    global files
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Remove file from disk
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove from metadata list
    files = [f for f in files if f['name'] != filename]

    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(debug=True)