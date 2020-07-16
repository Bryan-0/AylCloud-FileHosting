from app import size, datetime, app, render_template, Response, request, redirect, url_for, send_from_directory, session, g, mongo

@app.route("/")
def index():
    return render_template('index.html')

''' Start Login Section '''

@app.route("/login")
def loginpage():
    if 'account' in session:
        return redirect(url_for('homepage'))

    return render_template('login.html', invalid = request.args.get('invalid'))

@app.route('/home', methods=['POST', 'GET'])
def homepage():

    if request.method == 'GET':
        if 'account' in session:
            account = mongo.db.Accounts.find_one({'Email': session['account'][1]})
            userFiles = orderFilesInfo(account['Files'])
            userSpaceUsed = '0M'
            if 'M' in size(account['SpaceUsed']):
                userSpaceUsed = size(account['SpaceUsed'])
            
            if request.args.get('nospaceleft') is None:
                nospace = 0
            else:
                nospace = 1
            return render_template('logged/home.html', nospace = nospace, userName = session['account'][0], userEmail = session['account'][1], userFiles = enumerate(userFiles), userSpaceUsed = userSpaceUsed, userSpaceLimit = size(account['SpaceLimit']))
        else:
            return redirect(url_for('loginpage'))

    account = mongo.db.Accounts.find_one({'Email': request.form['userEmail']})

    if account is not None:
        if (account['Password'] == request.form['userPassword']):
            userFiles = orderFilesInfo(account['Files'])
            session['account'] = [account['FirstName'], account['Email'], userFiles, account['SpaceUsed'], account['SpaceLimit']]
            userSpaceUsed = '0M'
            if 'M' in size(account['SpaceUsed']):
                userSpaceUsed = size(account['SpaceUsed'])
            return render_template('logged/home.html', nospace=0, userName = account['FirstName'], userEmail = session['account'][1], userFiles = enumerate(userFiles), userSpaceUsed = userSpaceUsed, userSpaceLimit = size(account['SpaceLimit']))

    return redirect(url_for('loginpage', invalid=1))

''' End Login Section '''

''' Start Register Section '''

@app.route("/register")
def registerpage():
    if 'account' in session:
        return redirect(url_for('homepage'))
    return render_template('register.html')

@app.route("/registersuccess", methods=['POST'])
def registered():
    fields = ['userFirstName', 'userLastName', 'userEmail', 'userPassword']

    for field in fields:
        if len(request.form[field]) == 0:
            return redirect(url_for('registerpage'))
        
    newAccount = {
        'FirstName': request.form['userFirstName'],
        'LastName': request.form['userLastName'],
        'Email': request.form['userEmail'],
        'Password': request.form['userPassword'],
        'Files': [],
        'SpaceUsed': 0.0,
        'SpaceLimit': 21000000.0
    }

    mongo.db.Accounts.insert_one(newAccount)

    return redirect(url_for('loginpage'))

''' End of Register Section'''

''' Start Logout Section '''

@app.route('/logout')
def logoutpage():
    session.pop('account', None)
    return redirect(url_for('loginpage'))

''' End Logout Section '''


''' Start Upload File Section '''

@app.route('/upload')
def uploadpage():
    if 'account' in session:
        return render_template('logged/upload.html')
    
    return redirect(url_for('loginpage'))

@app.route("/uploaded", methods=["POST"])
def uploaded():
    f = request.files['userFile']
    fileSize = request.form['fileSize']

    account = mongo.db.Accounts.find_one({'Email': session['account'][1]})
    newSize = account['SpaceUsed'] + int(fileSize)

    if newSize >= session['account'][4]:
        return redirect(url_for('homepage', nospaceleft=1))

    mongo.save_file(f.filename, f)

    file_length = size(int(fileSize))

    today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    mongo.db.Accounts.update_one({'Email': session['account'][1]}, {'$push': {'Files': "{}>{}>{}".format(f.filename, file_length, today)} })
    mongo.db.Accounts.update_one({'Email': session['account'][1]}, {'$set': {'SpaceUsed': newSize} })
    session['account'][2].append("{}>{}>{}".format(f.filename, file_length, today))
    print(session)
    return redirect(url_for("homepage"))

@app.route('/<user>/file/<filename>')
def file(user, filename):
    if 'account' in session:
        user = session['account'][1]
        return mongo.send_file(filename)
    return redirect(url_for('loginpage'))

@app.route('/deletefile', methods=['POST'])
def deletefile():
    filename = request.form['fileToDelete']
    fileInfo = mongo.db.fs.files.find_one({'filename': filename})
    fileID = fileInfo['_id']

    account = mongo.db.Accounts.find_one({'Email': session['account'][1]})
    newSize = account['SpaceUsed'] - int(fileInfo['length'])

    mongo.db.fs.files.delete_one({'filename': filename})
    mongo.db.fs.chunks.delete_many({'files_id': fileID})

    account = mongo.db.Accounts.find_one({'Email': session['account'][1]})
    files = account['Files']
    for cfile in files:
        if filename in cfile:
            files.remove(cfile)
            continue

    mongo.db.Accounts.update_one({'Email': session['account'][1]}, {'$set': {'Files': files, 'SpaceUsed': newSize}})
    return redirect(url_for('homepage'))

''' End Upload File Section '''


''' Start Utilities function '''

def orderFilesInfo(userFiles):
    return list(userf.split('>') for userf in userFiles)

''' End Utilities function '''