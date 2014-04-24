import flask as f
import peewee
import models as md
import re
from functools import wraps
import hashlib

app = f.Flask(__name__)

### ----------------------------------------------------------------------------
### Helper functions
### ----------------------------------------------------------------------------

def requires_admin():
    def wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = get_user()
            if not user.is_admin():
                add_error("You're not authorized to do that")
                f.abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return wrapper

def requires_user(role=None):
    def wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = get_user()
            if not user:
                add_error('Please login first')
                return f.redirect('/login?out=%s'%(f.request.path))

            if user.is_admin:
                return fn(*args, **kwargs)

            if role and not user.has_project_role(get_project(), role):
                add_error('You need the project role %s to do that'%(role))
                f.abort(403)

            return fn(*args, **kwargs)
        return wrapped
    return wrapper

def add_message(msg):
    f.flash(msg, category='message')

def add_error(msg):
    f.flash(msg, category='error')

def get_user():
    if not f.session.get('user_id'):
        return None
    try:
        user = md.User.get(id=f.session.get('user_id'))
        f.g.user = user
    except:
        return None
    return f.g.user

def get_project():
    m = re.search(r'.*?/project/([0-9]+)/.*?', f.request.path)
    if m:
        return md.Project.get(id=m.groups(0))
    return None

def url_for(fn, **kwargs):
    path = app.config.get('URL_PREFIX','') + f.url_for(fn, **kwargs)
    return path

### ----------------------------------------------------------------------------
### Routes
### ----------------------------------------------------------------------------
@app.context_processor
def inject_user():
    return dict(user=get_user())

@app.context_processor
def injext_url_for():
    return dict(url_for=url_for)

@app.before_request
def before_request():
    print url_for('login')
    f.g.db = md.database
    f.g.db.connect()

@app.after_request
def after_request(response):
    f.g.db.close()
    return response

@app.route('/')
def index():
    return f.redirect(url_for('projects'))

@app.route('/account', methods=['GET','POST'])
@requires_user()
def account():

    """ Handles password, email, and name updates """

    user = get_user()
    if f.request.method == 'GET':
        return f.render_template('account.html')
    action = f.request.form.get('action')
    if not action:
        f.abort(400)

    if action == 'update_password':
        pw1 = f.request.form.get('password1','').strip()
        pw2 = f.request.form.get('password2','').strip()
        if len(pw1) < 6:
            add_error('Passwords must be at least 6 characters')
            return f.redirect(url_for('account'))
        if pw1 != pw2:
            add_error('Passwords do not match')
            return f.redirect(url_for('account'))
        user.password = hashlib.sha1(pw1).hexdigest()
        user.save()
        add_message('Passwords updated')
        return f.redirect(url_for('account'))

    if action == 'update_email':
        new_email = f.request.form.get('email','').strip()
        if not new_email or len(new_email) < 6:
            add_error('Invalid email address specified')
            return f.redirect(url_for('account'))
   
        try:
            # PeeWee weirdness
            ou = md.User.get(email=new_email)
            add_error('That email address is already in use')
            return f.redirect(url_for('account'))
        except:
            pass
        user.email = new_email
        user.save()
        add_message('Email address updated')
        return f.redirect(url_for('account'))

    if action == 'update_name':
        new_name = f.request.form.get('name','').strip()
        if len(new_name) < 3:
            add_error('Names must be at least 3 characters')
            return f.redirect(url_for('account'))
        user.name = new_name
        user.save()
        add_message('Name updated')
        return f.redirect(url_for('account'))

    add_error('Unknown action specified')
    return f.redirect(url_for('account'))

@app.route('/users', methods=['GET','POST'])
@requires_admin()
def users():
    pass

@app.route('/login', methods=['GET','POST'])
def login():

    """ Signs the user into GitGate and creates a session """    

    if f.request.method == 'GET':
        return f.render_template('login.html')
    email = f.request.form.get('email')
    password = f.request.form.get('password')
    try:
        pwhash = hashlib.sha1(password).hexdigest()
        user = md.User.get(email=email, password=pwhash)
    except:
        add_error('Invalid email or password')
        return f.redirect(url_for('login'))
    add_message('Welcome back %s'%(user.name))
    f.session['user_id'] = user.id
    return f.redirect(url_for('index'))

@app.route('/logout')
def logout():
    
    """ Destroys the user's session """
    
    if f.session.get('user_id'):
        f.session['user_id'] = None
        f.g.user = None
        add_message('You have been logged out')
    return f.redirect(url_for('login'))

@app.route('/project/<int:pid>/commit/<int:cid>')
@requires_user()
def commit(pid, cid):
    
    """ Returns information about a commit """

    try:
        project = md.Project.get(id=pid)
        commit = md.Commit.get(id=cid)
    except:
        abort(404)
    
    return f.render_template('commit.html', commit=commit, project=project)


@app.route('/project/<int:pid>/commit/<int:cid>/<action>', methods=['POST'])
@requires_user()
def commit_action(pid, cid, action):
    user = get_user()
    if action not in ['approve','review','reject','unreject','comment']:
        f.abort(404)
    try:
        project = md.Project.get(id=pid)
        commit = md.Commit.get(id=cid)
    except Exception as err:
        print "ERROR: %s"%(err)
        f.abort(404)

    def redirect_self():
        return f.redirect(url_for('commit', pid=pid, cid=cid))

    if action == 'approve':
        if commit.status not in ['reviewed','committed']:
            f.abort(400)
        if not user.has_project_role(project, 'approver'):
            f.abort(403)
        commit.status = 'approved'
        commit.save()
        md.CommitLog.create(user=user, commit=commit, message='Approved')
        add_message('Commit updated')
        return redirect_self()
    
    if action == 'review':
        if not user.has_project_role(project, 'reviewer'):
            f.abort(403)
        if commit.status not in ['committed']:
            f.abort(400)
        commit.status = 'reviewed'
        commit.save()
        md.CommitLog.create(user=user, commit=commit, message='Reviewed')
        add_message('Commit reviewed')
        return redirect_self()

    if action == 'reject':
        if commit.status not in ['committed','reviewed','approved']:
            add_error('Commit cannot be merged to reject')
            return redirect_self()
        commit.status = 'rejected'
        commit.save()
        md.CommitLog.create(user=user, commit=commit, message='Rejected')
        add_message('Commit rejected')
        return redirect_self()

    if action == 'unreject':
        if commit.status not in ['rejected']:
            add_error('Commit must be rejected to unreject')
            return redirect_self()
        commit.status = 'committed'
        commit.save()
        return redirect_self()

    if action == 'comment':
        comment = f.request.form.get('message')
        if not comment:
            add_error('Comment cannot be blank')
            return redirect_self()
        md.CommitLog.create(user=user, commit=commit, message=comment)
        add_message('Comment added')
        return redirect_self()

@app.route('/project/<int:pid>/commit/<int:cid>/file')
@requires_user()
def commit_file(pid, cid):
    try:
        fpath = f.request.args.get('fpath')
        project = md.Project.get(id=pid)
        commit = md.Commit.get(id=cid)
        commit_file = md.CommitFile.get(commit=commit, file_path=fpath)
    except:
        f.abort(404)
    full = f.request.args.get('full', False)
    
    #diff = commit.project.git_control.get_file_diff(
    #    commit.sha1, commit_file.file_path)
    diff = commit.project.git_control.get_stable_diff(
        commit.sha1, commit_file.file_path, full_diff=full)
    diff = diff.replace('<','&lt;')
    diff = diff.replace('>','&gt;')
    add_re = re.compile(r'^(\+.*?)$', flags=re.M)
    rm_re = re.compile(r'^(\-.*?)$', flags=re.M)
    diff = add_re.sub(r'<span class="code-line-added">\1</span>', diff)
    diff = rm_re.sub(r'<span class="code-line-removed">\1</span>', diff)
    return f.render_template('commit_file_diff.html', 
        commit_file=commit_file, diff=diff, commit=commit, full=full)

@app.route('/project/<int:pid>/commits')
@requires_user()
def commits(pid):
    try:
        project = md.Project.get(id=pid)
    except:
        f.abort(404)

    page = f.request.args.get('page',1)
    limit = f.request.args.get('limit',100)

    status_filter = f.request.args.get('status_filter','').strip()
    # Peewee queries are extra ugly - not sure why I chose it.
    statuses = [s[0] for s in md.Commit.STATUSES]
    if status_filter:
        statuses = status_filter.split(',')
    
    #print "Statuses: ", statuses
    commits = md.Commit.select().where(
        (md.Commit.project == project) &
        (md.Commit.status << statuses)
    ).order_by(md.Commit.author_date.desc()).paginate(int(page), int(limit))
    print "Page = %s, limit = %s, count = %s"%(page, limit, commits.count())
    for c in commits:
        print "\t", c.id
    
    return f.render_template('commits.html', project=project, 
        statuses=statuses, commits=commits)

@app.route('/project/<pid>/roles')
@requires_user()
def project_roles(pid): 
    try:
        project = md.Project.get(id=pid)
    except:
        f.abort(404)
    review_role = md.Role.get(name='reviewer')
    approve_role = md.Role.get(name='approver')
    reviewers = (md.ProjectRole.select()
        .where(
            (md.ProjectRole.project == project) &
            (md.ProjectRole.role == review_role))
        )
    approvers = (md.ProjectRole.select()
        .where(
            (md.ProjectRole.project == project) &
            (md.ProjectRole.role == approve_role))
        )

    roles = md.Role.select()
    return f.render_template('project_roles.html', reviewers=reviewers, 
        approvers=approvers, project=project, roles=roles)

@app.route('/project/<pid>/role/add', methods=['POST'])
def project_role_add(pid):
    try:
        project = md.Project.get(id=pid)
    except:
        f.abort(404)

    role_name = f.request.form.get('role_name')
    user_email = f.request.form.get('user_email','').strip()
    if not user_email or not role_name:
        add_error('You must specify a user email address and role')
        return f.redirect(url_for('project_roles', pid=project.id))
        
    try:
        user = md.User.get(email=user_email)
        role = md.Role.get(name=role_name)
    except:
        add_error('User or role not found')
        return f.redirect(url_for('project_roles', pid=project.id))
    try:
        ur = md.ProjectRole.get(project=project, user=user, role=role)
        add_error('User already exists for that role (%s)'%(role.name))
        return f.redirect(url_for('project_roles', pid=project.id))
    except:
        pass    
    pr = md.ProjectRole.create(user=user, role=role, project=project)
    add_message('User role created!')
    return f.redirect(url_for('project_roles', pid=project.id))

@app.route('/project/<pid>/role/delete', methods=['POST'])    
def project_role_delete(pid):
    try:
        project = md.Project.get(id=pid)
    except:
        f.abort(404)
    user_email = f.request.form.get('user_email')
    role_name = f.request.form.get('role_name')
    try:
        user = md.User.get(email=user_email)
        role = md.Role.get(name=role_name)
        pr = md.ProjectRole.get(role=role, user=user, project=project)
    except Exception as err:
        f.abort(404)
    
    pr.delete_instance()
    add_message('User removed from role: %s'%(role.name))
    return f.redirect(url_for('project_roles', pid=project.id))

@app.route('/projects')
def projects():
    projects = md.Project.select()
    return f.render_template('projects.html', projects=projects)

