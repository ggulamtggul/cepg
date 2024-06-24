from .setup import *


class ModelEpgProgram(ModelBase):
    P = P
    __tablename__ = f'{P.package_name}_program'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = EPG_DATA_DB_BIND_KEY

    def __init__(self, **kwargs):
        self.bind_key = self.__bind_key__
        P.db.Model.metadata.tables[self.__tablename__].info['bind_key'] = self.__bind_key__
        super(ModelBase, self).__init__(**kwargs)


    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################

    channel_name = db.Column(db.Integer, db.ForeignKey(f'{P.package_name}_channel.name'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    title = db.Column(db.String)
    episode_number = db.Column(db.String)
    part_number = db.Column(db.String)
    rate = db.Column(db.String)
    #tv_mpaa_map = {'CPTG0100' : u'모든 연령 시청가', 'CPTG0200' : u'7세 이상 시청가', 'CPTG0300' : u'12세 이상 시청가', 'CPTG0400' : u'15세 이상 시청가', 'CPTG0500' : u'19세 이상 시청가'}

    re = db.Column(db.Boolean)

    is_movie = db.Column(db.Boolean)
    content_id = db.Column(db.String, db.ForeignKey(f'{P.package_name}_content.content_id' ))
    content_info = db.relationship('ModelEpgContent', backref='program', lazy='joined')

    # 다음과 티빙은 ModelEpgContent 사용
    # 티빙 episode_plot 사용
    is_movie = db.Column(db.Boolean)
    poster = db.Column(db.String)
    desc = db.Column(db.String)
    genre = db.Column(db.String)
    actor = db.Column(db.String)
    director = db.Column(db.String)
    producer = db.Column(db.String)
    writer = db.Column(db.String)


    def __init__(self):
        self.created_time = datetime.now()
        self.is_movie = False
        self.re = False


    @classmethod
    def delete_by_channel_name(cls, channel_name):
        with F.app.app_context():
            db.session.query(cls).filter(cls.channel_name == channel_name).delete()
            db.session.commit()

