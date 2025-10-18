from functools import wraps
import os
import requests
import psycopg2
import shutil
from PIL import Image, ImageDraw, ImageFont

from flask import Flask, redirect, session, url_for, render_template, request, make_response, send_file


app = Flask(__name__)
app.secret_key = 'g8y348f3h4f34jf93ij4g3hrthsrthrsth213u49gh3487fh34fj8347hfg3487fh348jf34hf837fg'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

image_counter = 1

def set_flag(text, output_path='uploads/admin/1.jpg', font_size=20, image_size=(150, 150), text_color=(0, 0, 0), background_color=(255, 255, 255), font_path=None):
    image = Image.new('RGB', image_size, background_color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default() if font_path is None else ImageFont.truetype(font_path, font_size)

    lines = text.split('\n')

    x, y = 0, 75

    for line in lines:
        draw.text((x, y), line, font=font, fill=text_color)
        y += font.getsize(line)[1]

    image.save(output_path)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_images(username):
    try:
        return list(filter(lambda x: "avatar" not in x, os.listdir(f"{UPLOAD_FOLDER}/{username}")))
    except:
        return "no"


def dbConnect():
    mydb = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        user="student",
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    return mydb


def signin(username, password):
    mydb = dbConnect()
    cursor = mydb.cursor()

    cursor.execute(
        "SELECT id FROM users_info WHERE username = %s and password = %s", (username, password))
    user = cursor.fetchall()
    mydb.close()

    if user:
        session['user'] = username
        session['user_id'] = user[0][0]
        session['userpic'] = ''
        return redirect(url_for('account'))
    else:
        return render_template('index.html', info="login or password is invalid")


def signup(username, password):
    mydb = dbConnect()
    cursor = mydb.cursor()

    cursor.execute(
        "SELECT id FROM users_info WHERE username = %s", (username,))
    user = cursor.fetchall()

    if user:
        mydb.close()
        return render_template('index.html', info="This user is already exist")
    else:
        cursor.execute(
            "INSERT INTO users_info (username, password) VALUES (%s, %s)", (username, password))
        mydb.commit()
        mydb.close()
        return render_template('index.html', info="User has been registered")


def auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            session['user'] = False
        return f(*args, **kwargs)
    return decorated_function


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        action = request.form['action']
        username = request.form['login']
        password = request.form['password']

        if username.isalnum() and password:
            if action == 'signin':
                return signin(username, password)
            elif action == 'signup':
                return signup(username, password)
        else:
            return render_template("index.html", info="invalid input")
    return render_template('index.html')


@auth
@app.route("/account", methods=['GET', 'POST'])
def account():
    is_user = session.get('user', False)
    if not (is_user):
        return redirect(url_for('index'))

    return render_template("account.html", username=session['user'], user_id=session['user_id'])


@auth
@app.route("/gallery", methods=['GET', 'POST'])
def gallery():
    is_user = session.get('user', False)
    if not (is_user):
        return redirect(url_for('index'))

    images = get_user_images(session['user'])
    if images == 'no':
        return render_template('gallery.html')
    return render_template('gallery.html', images=images, username=session['user'], user_id=session['user_id'])


@auth
@app.route('/upload', methods=['POST'])
def upload():
    is_user = session.get('user', False)
    if not (is_user):
        return redirect(url_for('index'))

    file = request.files['file']
    if 'file' not in request.files or file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        global image_counter
        image_counter += 1
        file.filename = str(image_counter) + '.jpg'

        upload_folder = os.path.join(UPLOAD_FOLDER, session['user'])
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file.save(os.path.join(upload_folder, file.filename))
        return redirect(url_for('account'))
    return "the file was not uploaded or is not an image"


@auth
@app.route('/uploads/<pic>')
def get_image(pic):
    is_user = session.get('user', False)
    if not (is_user):
        return redirect(url_for('index'))
    
    try:
        filepath = os.path.join(UPLOAD_FOLDER, session['user'], pic)
        send_file(filepath, mimetype='image/jpg')
        return send_file(filepath, mimetype='image/jpg')
    except FileNotFoundError as e:
        return render_template('403pic.html')


@auth
@app.route('/picture/<pic>', methods=['GET', 'POST'])
def picture(pic):
    is_user = session.get('user', False)
    if not (is_user):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        picid = request.form['imageid']
        account = request.form['account']
        resource = request.form['resource']
        action = request.form['action']
        
        if account != session['user'] or picid != pic:
            return render_template('403pic.html')
        print(session)
        requests.get(f'http://{resource}/{action}?imageid={picid}&account={account}', cookies={'user': session['user']})

        return redirect(url_for('account'))

    try:
        filepath = os.path.join(UPLOAD_FOLDER, session['user'], pic)
        send_file(filepath, mimetype='image/jpg')
        return render_template('pic.html', filepath=filepath, imageid=pic, user=session['user'])
    except FileNotFoundError as e:
        return render_template('403pic.html')


@auth
@app.route('/getImage', methods=['GET'])
def getImage():
    pic = request.args.get('imageid')
    folder = request.args.get('account')
    user = request.cookies.get('user')
    gallery_image = os.path.join(UPLOAD_FOLDER, folder, pic)
    avatar = os.path.join(UPLOAD_FOLDER, user, 'avatar')
    shutil.copy2(gallery_image, avatar)
    return "ok"


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


@app.route("/logout", methods=["GET", "POST"])
def logout():
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('session', '')
    return resp


if __name__ == "__main__":
    set_flag(os.getenv('FLAG'), font_size=25)
    app.run(host='0.0.0.0', port='80', debug=False)
