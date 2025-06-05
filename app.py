import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string
import math

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
BACKUP_FOLDER = 'backup'
LOG_FILE = 'ip_log.txt'

# Ensure necessary folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# Constants
MAX_FILES = 50
FILES_PER_PAGE = 5

# In-memory file list
files = []

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
    files.sort(key=lambda x: x['date'], reverse=True)

load_files()

@app.route('/', methods=['GET', 'POST'])
def index():
    global files
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            user_agent = request.headers.get('User-Agent', 'Unknown')
            filename = file.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            with open(LOG_FILE, 'a') as log:
                log.write(f"{filename} - {ip} - {now}\n")
                log.write(f"{filename} - {ip} - {now} - {user_agent}\n")

            files.insert(0, {
                'name': filename,
                'date': datetime.now(),
                'path': save_path
            })

            if len(files) > MAX_FILES:
                old = files.pop()
                os.remove(old['path'])

            return redirect(url_for('index'))

    page = int(request.args.get('page', 1))
    start = (page - 1) * FILES_PER_PAGE
    end = start + FILES_PER_PAGE
    paginated_files = files[start:end]
    total_pages = math.ceil(len(files) / FILES_PER_PAGE)

    html = '''
    <html>
    <head><title>File Upload</title></head>
    <body>
      <h1>Upload File</h1>
      <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
      </form>

      <h2>Uploaded Files</h2>
      <ul>
        {% for file in files %}
          <li>{{ file.name }} ({{ file.date.strftime('%Y-%m-%d %H:%M:%S') }})</li>
        {% endfor %}
      </ul>

      <div>
        {% for i in range(1, total_pages + 1) %}
          <a href="/?page={{ i }}">{{ i }}</a>
        {% endfor %}
      </div>
    </body>
    </html>
    '''
    return render_template_string(html, files=paginated_files, total_pages=total_pages)

# Secret admin page
ADMIN_PASSWORD = "suck"  # WARNING: Don't use weak passwords in production!

@app.route('/admin')
def admin_page():
    key = request.args.get('key', '')
    if key != ADMIN_PASSWORD:
        return "Unauthorized", 403

    try:
        with open(LOG_FILE, 'r') as log_file:
            log_content = log_file.read()
    except FileNotFoundError:
        log_content = "No IP log available."

    upload_list = os.listdir(UPLOAD_FOLDER)

    admin_html = '''
    <html>
    <head>
      <title>Admin Panel</title>
      <style>
        body { font-family: sans-serif; padding: 20px; }
        h2 { margin-top: 30px; }
        pre { background: #f4f4f4; padding: 10px; border: 1px solid #ccc; overflow-x: auto; }
      </style>
    </head>
    <body>
      <h1>Admin Panel</h1>

      <h2>Uploaded Files</h2>
      <ul>
        {% for fname in uploads %}
          <li><a href="/download/{{ fname }}">{{ fname }}</a></li>
        {% endfor %}
      </ul>

      <h2>IP Log</h2>
      <pre>{{ log }}</pre>
    </body>
    </html>
    '''
    return render_template_string(admin_html, uploads=upload_list, log=log_content)

@app.route('/download/<filename>')
def download_file(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
