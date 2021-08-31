import os
from flask import Flask, render_template, request, redirect, url_for, abort, send_file, after_this_request
from werkzeug.utils import secure_filename
import subprocess
import os.path
import flask_sqlalchemy
import hashlib
import time
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler

db = flask_sqlalchemy.SQLAlchemy()

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), unique=False, nullable=False)
    filehash = db.Column(db.String(80), unique=False, nullable=False)
    filehash_c = db.Column(db.String(80), unique=False, nullable=True)
    file_size = db.Column(db.Float, unique=False, nullable=False)
    file_size_c = db.Column(db.Float, unique=False, nullable=True)
    upload_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"File('{self.id}', '{self.filename}', '{self.filehash}', '{self.file_size}', '{self.upload_time}')"


def scheduledTask():
    expiration_time=datetime.utcnow() - timedelta(hours=0, minutes=15) 
    with app.app_context():
        expired_files=File.query.filter(File.upload_time <= expiration_time).all()

        for file in expired_files:
            os.remove(os.path.join(app.config['UPLOAD_PATH'], file.filehash))
            if file.filehash_c is not None:
                os.remove(os.path.join(app.config['UPLOAD_PATH'], file.filehash_c))
            db.session.delete(file)

        db.session.commit()

def create_app():
    flaskapp = Flask(__name__)

    flaskapp.config['MAX_CONTENT_LENGTH'] = 500000000
    flaskapp.config['UPLOAD_EXTENSIONS'] = ['PDF']
    flaskapp.config['UPLOAD_PATH'] = 'static/uploads'
    flaskapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    flaskapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    db.init_app(flaskapp)

    with flaskapp.app_context():
        db.create_all()


    scheduler = APScheduler()
    scheduler.add_job(id ='Scheduled task', func = scheduledTask, trigger = 'interval', seconds=5)
    scheduler.start()

    return flaskapp

app=create_app()



def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def compress_ghostscript(input_file_path, output_file_path, power=0):
    """Function to compress PDF via Ghostscript command line interface"""
    quality = {
        0: '/default',
        1: '/prepress',
        2: '/printer',
        3: '/ebook',
        4: '/screen'
    }

    print("Compress PDF...")
    initial_size = os.path.getsize(input_file_path)
    subprocess.call(['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                    '-dPDFSETTINGS={}'.format(quality[power]),
                    '-dNOPAUSE', '-dQUIET', '-dBATCH',
                    '-sOutputFile={}'.format(output_file_path),
                     input_file_path]
    )



if not os.path.exists(app.config['UPLOAD_PATH']):
    os.makedirs(app.config['UPLOAD_PATH'])


def allowed_file(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["UPLOAD_EXTENSIONS"]:
        return True
    else:
        return False


@app.route('/')
def index():
    return render_template('index.html')

 
@app.route('/', methods=['GET','POST'])
def upload_files():
    if request.method == "POST":

        if request.files:

            uploaded_file = request.files['file']

            if uploaded_file.filename == "":
                print("No filename")
                return redirect(url_for('index'))

            if allowed_file(uploaded_file.filename):

                filename = secure_filename(uploaded_file.filename)
                
                filehash = hashlib.sha224((filename+str(time.time())).encode()).hexdigest()
                
                uploaded_file.save(os.path.join(app.config["UPLOAD_PATH"], filehash))

                size = os.path.getsize(os.path.join(app.config["UPLOAD_PATH"], filehash))

                filetable=File(filename=filename,filehash=filehash,file_size=size)

                db.session.add(filetable)
                db.session.commit()
                
                return redirect(url_for('compress', filehash=filehash))
            else:
                print("That file extension is not allowed")
                return redirect(url_for('index'))

    return redirect(url_for('index')) 

    

@app.route('/compress/<filehash>', methods=['GET', 'POST'])
def compress(filehash):
    if os.path.isfile(os.path.join(app.config['UPLOAD_PATH'], filehash)):

        found_file=File.query.filter_by(filehash=filehash).first()

        if request.method == 'POST':
            if request.form['submit_button'] == 'Compress':        

                filehash_c=filehash+'c'
                file_path=os.path.join(app.config['UPLOAD_PATH'], filehash)
                file_reduc=os.path.join(app.config['UPLOAD_PATH'], filehash_c)
                compress_ghostscript(file_path, file_reduc, power=0)
                final_size = os.path.getsize(file_reduc)
                found_file.file_size_c=final_size
                found_file.filehash_c=filehash_c
                db.session.commit()

                return redirect(url_for('download', filehash=filehash))
            else:
                return render_template('compress.html', file=filehash)
        elif request.method == 'GET':
            print("No Post Back Call")

        filename=found_file.filename
        file_size=sizeof_fmt(found_file.file_size, suffix='B')

    else:
        abort(404)
    return render_template('compress.html', file=filename, file_size=file_size)



@app.route('/download/<filehash>')
def download(filehash):
    if os.path.isfile(os.path.join(app.config['UPLOAD_PATH'], filehash)):
        found_file=File.query.filter_by(filehash=filehash).first()
        filename=found_file.filename[:-4]+'_compressed.pdf'

        file_size=sizeof_fmt(found_file.file_size_c, suffix='B')
    else:
        abort(404)
    return render_template('download.html', file=filename, file_size=file_size, filehash=filehash)


@app.route('/download_file/<filehash>')
def download_file(filehash):
    if os.path.isfile(os.path.join(app.config['UPLOAD_PATH'], filehash)):
        found_file=File.query.filter_by(filehash=filehash).first()
        file_path=os.path.join(app.config['UPLOAD_PATH'], found_file.filehash_c)
        filename=found_file.filename[:-4]+'_compressed.pdf'
    else:
        abort(404)
    return send_file(file_path, as_attachment=True, download_name=filename)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


 
