from peewee import *
import util
import datetime
import ggconf

database = SqliteDatabase(ggconf.DATABASE)

def create_tables():
    User.create_table()
    Role.create_table()
    Project.create_table()
    ProjectRole.create_table()
    Commit.create_table()
    CommitFile.create_table()
    CommitLog.create_table()

def populate_data():
    Role.create(name='reviewer')
    Role.create(name='approver')

class DBModel(Model):
    class Meta:
        database = database

class User(DBModel):

    email = CharField(unique=True)
    name = CharField()
    password = CharField()
    is_admin = BooleanField(default=False)
    
    def has_project_role(self, project, role):
        if role == 'admin':
            return self.is_admin        
    
        if self.is_admin:
            return True

        if isinstance(role, str) or isinstance(role, unicode):
            role = Role.get(name=role)
        try:
            ProjectRole.get(user=self, role=role, project=project)
            return True
        except:
            return False

class Project(DBModel):

    name = CharField(unique=True)
    path = CharField(unique=True)
    devel_clone_url = CharField()
    stable_clone_url = CharField()
    last_merge_sha1 = CharField(default=None, null=True)
    _git_control = None
    
    @property
    def git_control(self):
        if self._git_control:
            return self._git_control
        self._git_control = util.GitProject(self)
        return self._git_control

class Role(DBModel):
    
    NAMES = (
        ('reviewer','Reviewer'),
        ('approver','Approver'),
    )

    name = CharField(unique=True)
    description = TextField(default=None, null=True)

class ProjectRole(DBModel):

    user = ForeignKeyField(User)
    project = ForeignKeyField(Project, related_name='roles')
    role = ForeignKeyField(Role)

class Commit(DBModel):

    STATUSES = (
        ('committed', 'Committed'),
        ('tested', 'Unit Tested'),
        ('reviewed', 'Code Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('outdated', 'Outdated'),
        ('merged','Merged'),
    )
    
    sha1 = CharField(unique=True)
    branch = CharField()
    project = ForeignKeyField(Project, related_name='commits')
    author_date = DateTimeField()
    author_name = CharField()
    author_email = CharField()
    message = TextField()
    status = CharField(choices=STATUSES)

    @property
    def can_merge(self):
        _merge = True
        older_commits = (self
            .select()
            .where((Commit.status != 'merged') 
                & (Commit.status != 'rejected')
                & (Commit.status != 'outdated')
                & (Commit.author_date < self.author_date))
        )
        this_files = [f.file_path for f in self.files]
        for cm in older_commits:
            for f in cm.files:
                if f.file_path in this_files:
                    _merge = False
                    break
        return _merge
    
class CommitFile(DBModel):
    
    commit = ForeignKeyField(Commit, related_name='files')
    file_path = CharField()
    change_type = CharField(choices=['A','M','D'])
    
    class Meta:
        primary_key = CompositeKey('commit', 'file_path')

class CommitLog(DBModel):
    
    commit = ForeignKeyField(Commit, related_name='logs')
    user = ForeignKeyField(User)
    created = DateTimeField(default=datetime.datetime.now)
    message = TextField()    
