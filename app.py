import os
from datetime import datetime
import math


BACKUP_FOLDER = 'backup'
LOG_FILE = 'ip_log.txt'

os.makedirs(BACKUP_FOLDER, exist_ok=True)


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

files = []

MAX_FILES = 50
FILES_PER_PAGE = 5


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
          ip = request.remote_addr
          ip = request.headers.get('X-Forwarded-For', request.remote_addr)
          user_agent = request.headers.get('User-Agent', 'Unknown')
          filename = file.filename


@@ -62,7 +63,8 @@
          # Log IP address and file name
          with open(LOG_FILE, 'a') as log:
              now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
              log.write(f"{filename} - {ip} - {now}\n")
              log.write(f"{filename} - {ip} - {now} - {user_agent}\n")


          # Add to in-memory list
          files.insert(0, {
@@ -173,51 +175,51 @@
    return redirect(url_for('index'))

# Secret admin page
ADMIN_PASSWORD = "p@ss123"  # Change this to your secret password
ADMIN_PASSWORD = "suck"  # Change this to your secret password

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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # use port from environment if available
    app.run(host='0.0.0.0', port=port)