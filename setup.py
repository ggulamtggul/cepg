from plugin import *

setting = {
    'filepath' : __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': None,
    'menu': {
        'uri': __package__,
        'name': 'EPG',
        'list': [
            {
                'uri': 'xml',
                'name': 'xml 생성',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                ]
            },
            {
                'uri': 'maker',
                'name': '서버전용 - epg.db 생성',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                ]
            },
            {
                'uri': 'manual',
                'name': '매뉴얼',
                'list': [
                    {'uri':'README.md', 'name':'ChangeLog'},
                    {'uri':'files/manual.md', 'name':'매뉴얼'}
                ]
            },
            {
                'uri': 'log',
                'name': '로그',
            },
        ]
    },
    'default_route': 'normal',
}
EPG_DATA_DB_BIND_KEY = 'epg_data'

from plugin import *

P = create_plugin_instance(setting)


try:
    EPG_DATA_DB_PATH = os.path.join(os.path.dirname(__file__), 'files', f'{EPG_DATA_DB_BIND_KEY}.db')
    F.app.config['SQLALCHEMY_BINDS'][EPG_DATA_DB_BIND_KEY] = f"sqlite:///{EPG_DATA_DB_PATH}?check_same_thread=False"
    P.ModelSettingDATA = get_model_setting(EPG_DATA_DB_BIND_KEY, P.logger)
    from sqlalchemy import MetaData, create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    from .model_channel import ModelEpgChannel
    from .model_content import ModelEpgContent
    from .model_program import ModelEpgProgram
    
    pass # 순서 좀 바꾸지 마라
    from .mod_xml import ModuleXml
    
    
    P.db = create_engine(F.app.config['SQLALCHEMY_BINDS'][EPG_DATA_DB_BIND_KEY])
    metadata = MetaData()
    P.db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=P.db))
    with F.app.app_context():
        F.db.engines[EPG_DATA_DB_BIND_KEY] = P.db
   
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'files', 'credential.json')) == False:
        P.set_module_list([ModuleXml])
    else:
        from .mod_maker import ModuleMaker
        P.set_module_list([ModuleXml, ModuleMaker])
except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())

logger = P.logger