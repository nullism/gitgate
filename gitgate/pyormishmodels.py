from pyormish import Model

def create_tables():
    sql = '''
CREATE TABLE project(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    path TEXT,
    devel_clone_url TEXT,
    stable_clone_url TEXT
);
CREATE TABLE commit(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    '''

class Project(Model):

    _TABLE_NAME = 'project'
    _PRIMARY_FIELD = 'id'
    _SELECT_FIELDS = ('id','name','path','devel_clone_url','stable_clone_url')
    _COMMIT_FIELDS = ('name','path','devel_clone_url','stable_clone_url')


class Commit(Model):
    _TABLE_NAME = 'commit'
    _PRIMARY_FIELD = 'id'
    _SELECT_FIELDS = ('id','sha1','branch','project_id',
        'author_date','author_name','author_email',
        'status')
    _COMMIT_FIELDS = ('sha1','branch','project_id',
        'author_date','author_name','author_email',
        'status')

