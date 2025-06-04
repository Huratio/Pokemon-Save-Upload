from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
import os, json
from datetime import datetime
import math

UPLOAD_FOLDER = 'uploads'
BACKUP_FOLDER = 'backup'
LOG_FILE = 'ip_log.txt'
FILES_JSON = 'files.json'
MAX_FILES = 50
FILES_PER_PAGE = 5

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

app = Flask(__name__)
files = []

def save_files_metadata():
    with open(FILES_JSON, 'w') as f:
        json.dump([
            {
                'name': file['name'],
                'date': file['date'].isoformat(),
                'path': file['path']
            } for file in files
        ], f)

def load_files_metadata():
    global files
    files.clear()
    if os.path.exists(FILES_JSON):
        with open(FILES_JSON, 'r') as f:
            try:
                data = json.load(f)
                for item in data:
                    files.append({
                        'name': item['name'],
                        'date': datetime.fromisoformat(item['date']),
                        'path': item['path']
                    })
            except Exception:
                pass  # fallback: leave files empty

load_files_metadata()

@app.route('/', methods=['GET', 'POST'])
def index():
    global files
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
            ua = request.headers.get('User-Agent', 'Unknown')

            filename = file.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            backup_path = os.path.join(BACKUP_FOLDER, filename)

            file.save(save_path)
            file.seek(0)
            with open(backup_path, 'wb') as f:
                f.write(file.read())

            with open(LOG_FILE, 'a') as log:
                now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                log.write(f"{filename} - {ip} - {now} - {ua}\n")

            files.insert(0, {
                'name': filename,
                'date': datetime.now(),
                'path': save_path
            })

            files[:] = files[:MAX_FILES]
            save_files_metadata()

            return redirect(url_for('index'))

    page = request.args.get('page', '1')
    try:
        page = max(int(page), 1)
    except:
        page = 1

    total_pages = math.ceil(len(files) / FILES_PER_PAGE)
    page = min(page, total_pages) if total_pages > 0 else 1

    start = (page - 1) * FILES_PER_PAGE
    end = start + FILES_PER_PAGE
    files_page = files[start:end]

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
    indexed_files = [(start + i + 1, f) for i, f in enumerate(files_page)]
    return render_template_string(html, files=indexed_files, page=page, total_pages=total_pages)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete_file(filename):
    global files
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    files = [f for f in files if f['name'] != filename]
    save_files_metadata()

    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
