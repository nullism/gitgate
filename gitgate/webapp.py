import flask as f
import peewee
import models as md
import re
from functools import wraps

app = f.Flask(__name__)

### ----------------------------------------------------------------------------
### Helper functions
### ----------------------------------------------------------------------------

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
    try:
        user = md.User.get(id=1)
        f.g.user = user
    except:
        return None
    return f.g.user

def get_project():
    m = re.search(r'.*?/project/([0-9]+)/.*?', f.request.path)
    if m:
        return md.Project.get(id=m.groups(0))
    return None

### ----------------------------------------------------------------------------
### Routes
### ----------------------------------------------------------------------------
@app.context_processor
def inject_user():
    return dict(user=get_user())

@app.before_request
def before_request():
    f.g.db = md.database
    f.g.db.connect()

@app.after_request
def after_request(response):
    f.g.db.close()
    return response

@app.route('/')
def index():
    return f.redirect(f.url_for('projects'))

@app.route('/login', methods=['GET','POST'])
def login():
    if f.request.method == 'GET':
        return f.render_template('login.html')
    email = f.request.form.get('email')
    password = f.request.form.get('password')
    try:
        user = md.User.get(email=email, password=password)
    except:
        add_error('Invalid email or password')
        return f.redirect(url_for('login'))
    add_message('Welcome back %s'%(user.name))
    return f.redirect(url_for('index'))

@app.route('/project/<int:pid>/commit/<int:cid>')
@requires_user()
def commit(pid, cid):
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
        return f.redirect(f.url_for('commit', pid=pid, cid=cid))

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
        abort(404)
    diff = commit.project.git_control.get_file_diff(
        commit.sha1, commit_file.file_path)
    diff = diff.replace('<','&lt;')
    diff = diff.replace('>','&gt;')
    diff = re.sub(r'^(\+.*?)$',r'<span class="code-line-added">\1</span>', diff, flags=re.M) 
    diff = re.sub(r'^(\-.*?)$',r'<span class="code-line-removed">\1</span>', diff, flags=re.M) 
    return f.render_template('commit_file_diff.html', 
        commit_file=commit_file, diff=diff, commit=commit)

@app.route('/project/<int:pid>/commits')
@requires_user()
def commits(pid):
    try:
        project = md.Project.get(id=pid)
    except:
        abort(404)

    status_filter = f.request.args.get('status_filter','').strip()
    # Peewee queries are extra ugly - not sure why I chose it.
    statuses = [s[0] for s in md.Commit.STATUSES]
    if status_filter:
        statuses = status_filter.split(',')
    
    print "Statuses: ", statuses
    commits = md.Commit.select().where(
        (md.Commit.project == project) &
        (md.Commit.status << statuses)
    )
    return f.render_template('commits.html', project=project, commits=commits)
 

@app.route('/projects')
def projects():
    projects = md.Project.select()
    return f.render_template('projects.html', projects=projects)

   
