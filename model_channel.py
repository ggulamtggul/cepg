from .setup import *


class ModelEpgChannel(ModelBase):
    P = P
    __tablename__ = f'{P.package_name}_channel'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = EPG_DATA_DB_BIND_KEY

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################
    name = db.Column(db.String)
    category = db.Column(db.String)
    aka = db.Column(db.String)
    epg_from = db.Column(db.String)
    icon = db.Column(db.String)

    daum_name = db.Column(db.String)
    daum_id = db.Column(db.String)
    wavve_name = db.Column(db.String)
    wavve_id = db.Column(db.String)
    tving_name = db.Column(db.String)
    tving_id = db.Column(db.String)
    skb_name = db.Column(db.String)
    skb_id = db.Column(db.String)
    kt_name = db.Column(db.String)
    kt_id = db.Column(db.String)
    lgu_name = db.Column(db.String)
    lgu_id = db.Column(db.String)
    hcn_name = db.Column(db.String)
    hcn_id = db.Column(db.String)
    spotv_id = db.Column(db.String)
    cable_name = db.Column(db.String)
    memo = db.Column(db.String)
    programs = db.relationship('ModelEpgProgram', backref='channel', lazy='joined')

    def __init__(self):
        self.created_time = datetime.now()
    
    def update(self, sheet_item):
        self.name = sheet_item['이름']
        self.category = sheet_item['카테고리']
        self.aka = sheet_item['이름'] + '\n' + sheet_item['AKA']
        #self.icon = sheet_item['최종 로고']
        self.icon = sheet_item['로고']

        self.daum_name = sheet_item['DAUM 이름']
        self.daum_id = sheet_item['DAUM ID']
        self.wavve_name = sheet_item['웨이브 이름']
        self.wavve_id = sheet_item['웨이브 ID']
        self.tving_name = sheet_item['티빙 이름']
        self.tving_id = sheet_item['티빙 ID']
        self.skb_name = sheet_item['SKB 이름']
        self.skb_id = sheet_item['SKB ID']
        self.kt_name = sheet_item['KT 이름']
        self.kt_id = sheet_item['KT ID']
        self.lgu_name = sheet_item['LGU 이름']
        self.lgu_id = sheet_item['LGU ID']
        self.hcn_name = sheet_item['HCN 이름']
        self.hcn_id = sheet_item['HCN ID']
        self.spotv_id = sheet_item['SPOTV ID']
        self.cable_name = sheet_item['케이블 이름']
        self.memo = sheet_item['메모']
        #self.json = sheet_item
        F.db.session.add(self)
        F.db.session.commit()


    @classmethod
    def get_by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()


    @classmethod
    def get_by_source_id(cls, source, source_id):
        if source == 'spotv':
            return db.session.query(cls).filter_by(spotv_id=str(source_id)).first()
        elif source == 'tving':
            return db.session.query(cls).filter_by(tving_id=str(source_id)).first()


    @classmethod
    def get_channel_list_by_source(cls, source):
        if source == 'tving':
            return db.session.query(cls).filter(cls.tving_id != '').all()


    @classmethod
    def util_get_search_name(cls, s):
        return s.lower().strip().replace('-', '').replace(' ', '').upper()


    @classmethod
    def get_by_prefer(cls, name):
        channel_list = cls.get_list()
        for ch in channel_list:
            aka = [cls.util_get_search_name(x) for x in ch.aka.splitlines()]
            if cls.util_get_search_name(name) in aka:
                return ch


    @classmethod
    def get_instance_by_name(cls, name):
        try:
            return db.session.query(cls).filter_by(name=name).first()
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())


    @classmethod
    def get_channel_list(cls):
        try:
            channel_list = db.session.query(cls).all()
            #ret = [x.as_dict() for x in channel_list]
            return channel_list
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())

 