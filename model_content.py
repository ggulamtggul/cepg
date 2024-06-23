from .setup import *


class ModelEpgContent(ModelBase):
    P = P
    __tablename__ = f'{P.package_name}_content'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = EPG_DATA_DB_BIND_KEY

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################
    
    is_movie = db.Column(db.Boolean)
    content_title = db.Column(db.String)
    content_id = db.Column(db.String)

    poster = db.Column(db.String)
    desc = db.Column(db.String)
    genre = db.Column(db.String)

    actor = db.Column(db.String)
    director = db.Column(db.String)
    producer = db.Column(db.String)
    writer = db.Column(db.String)

    def __init__(self):
        self.created_time = datetime.now()


    @classmethod
    def person_to_line(cls, data, attr):
        if attr in data:
            persons = []
            for tmp in data[attr]:
                if tmp['name'] == '' or tmp['role'] in ['작가', '극본', '각본', '감독', '연출', '제작', '기획']:
                    continue
                persons.append(tmp['name'])
            return '|'.join(persons)

    @classmethod
    def append_by_daum(cls, title, code, is_movie=False):
        try:
                entity = db.session.query(cls).filter(cls.content_id == code).first()
                if entity is not None:
                    #logger.debug(f"{title} exists..")
                    return code
                PP = F.PluginManager.get_plugin_instance('metadata')
                meta_ktv = PP.logic.get_module('ktv')
                meta_movie = PP.logic.get_module('movie')
                m = ModelEpgContent()
                
                m.content_id = code
                m.is_movie = is_movie
                if is_movie:
                    data = meta_movie.info(code)
                    posters = sorted(data['art'], key=lambda k: k['score'], reverse=True) 
                    m.actor = cls.person_to_line(data, 'actor')
                    m.director = '|'.join(data['director'])
                    m.writer = '|'.join(data['credits'])
                    m.producer = '|'.join(data['producers'])
                else:
                    from support_site import SiteDaumTv
                    ret = SiteDaumTv.info(code, title)
                    if ret['ret'] != 'success':
                        return code
                    data = ret['data']
                    posters = sorted(data['thumb'], key=lambda k: k['score'], reverse=True) 
                    m.actor = cls.person_to_line(data, 'actor')
                    m.director = cls.person_to_line(data, 'director')
                    m.writer = cls.person_to_line(data, 'credits')
            
                for tmp in posters:
                    if tmp['aspect'] == 'poster':
                        m.poster = tmp['value']
                        break
                m.content_title = data['title']
                m.desc = data['plot']
                m.genre = '|'.join(data['genre'])
                F.db.session.add(m)
                F.db.session.commit()
                return code
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())


    @classmethod
    def append_by_tving(cls, data):
        try:
                entity = db.session.query(cls).filter(cls.content_id == data['code']).first()
                if entity is not None:
                    return data['code']

                m = ModelEpgContent()
                m.content_id = data['code']
                m.content_title = data['name']['ko']
                m.desc = data['synopsis']['ko']
                m.genre = data['category1_name']['ko']
                m.actor = '|'.join(data['actor'])
                m.director = '|'.join(data['director'])

                for idx, img in enumerate(data['image']):
                    if img['code'] in ['CAIP0900', 'CAIP2300', 'CAIP2400']: #poster
                        m.poster = 'https://image.tving.com' + img['url']
                        break
                F.db.session.add(m)
                F.db.session.commit()
                return data['code']
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
    
    @classmethod
    def append_by_wavve(cls, title):
        try:
                entity = db.session.query(cls).filter(cls.content_title == title).first()
                if entity is not None:
                    return entity.content_id
                
                from support_site import SiteWavveTv, SupportWavve
                show_ret = SiteWavveTv.search(title)
                if show_ret['ret'] != 'success' or len(show_ret['data']) == 0:
                    return
                show = show_ret['data'][0]
                info = SiteWavveTv.info(show['code'], all_episode=False)

                entity = db.session.query(cls).filter(cls.content_id == show['code'][2:]).first()
                if entity is not None:
                    return entity.content_id

                if info and info['ret'] == 'success':
                    m = ModelEpgContent()
                    m.content_id = info['data']['code'][2:]
                    m.content_title = info['data']['title']
                    m.desc = info['data']['plot']
                    if len(info['data']['genre'])>0:
                        m.genre = info['data']['genre'][0]
                    tmps = [x['name'] for x in info['data']['actor']]
                    m.actor = '|'.join(tmps)
                    tmps = [x['name'] for x in info['data']['director']]
                    m.director = '|'.join(tmps)
                    for img in info['data']['thumb']:
                        if img['aspect'] == 'poster':
                            m.poster = img['value']
                    F.db.session.add(m)
                    F.db.session.commit()
                    return info['data']['code'][2:]
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            