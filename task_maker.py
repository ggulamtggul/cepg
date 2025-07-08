from support.base.file import SupportFile
from support.base.sub_process import SupportSubprocess

from .setup import *
from .site.cli_make_sheet import EPG_Sheet
from .site.epg_daum import EpgDaum
from .site.epg_hcn import EpgHcn
from .site.epg_kt import EpgKt
from .site.epg_lgu import EpgLgu
from .site.epg_skb import EpgSkb
from .site.epg_spotv import EpgSpotv
from .site.epg_tving import EpgTving
from .site.epg_wavve import EpgWavve
import sqlite3
#       API채널전체 API채널별  방송정보  연령  장르   회차  파트  재방송  
# lgu : X           X          X        O     O     O    O     O  
# skb : X           X          X        O     X     O    O     O  
# kt  : X           X          X        O     O     X    X     X

class Task(object):

    @staticmethod
    @celery.task
    def start(*args, **kargs):
        from .site.cli_make_sheet import EPG_Sheet
        sheet = EPG_Sheet()
        with F.app.app_context():
            logger.debug("EPG MAKER start..")
            Task.make_channel_list(sheet)
            logger.debug("EPG MAKER channel list created.")

        with F.app.app_context():
            # spotv 
            logger.info("스포티비 EPG 생성 시작")
            db_item = ModelEpgChannel.get_by_name('SPOTV')
            if db_item:
                if Task.is_need_epg_make(db_item):
                    logger.info("스포티비 EPG 생성")
                    EpgSpotv.make_epg()
                else:
                    logger.debug('스포티비 1일 미만이라 패스 : %s', (datetime.now()-db_item.update_time))

            # tving 
            logger.info("티빙 EPG 생성 시작")
            db_item = ModelEpgChannel.get_by_name('tvN')
            if db_item:
                if db_item and Task.is_need_epg_make(db_item):
                    logger.info("티빙 EPG 생성")
                    EpgTving.make_epg()
                else:
                    logger.debug('티빙-tvN 1일 미만이라 패스 : %s', (datetime.now()-db_item.update_time))

            epg_map = [
                {'name':'daum', 'ins' : EpgDaum, 'count':0},
                {'name':'wavve', 'ins': EpgWavve, 'count':0},
                #{"name" : 'hcn', 'ins' : EpgHcn, 'count':0}, 
                #{"name" : 'lgu', 'ins' : EpgLgu, 'count':0}, 
                #{"name" : 'skb', 'ins' : EpgSkb, 'count':0}, 
                #{"name" : 'kt', 'ins' : EpgKt, 'count':0}, 
            ]
            now = datetime.now()

            make_title = []
            make_count = 0
            
            channel_list = ModelEpgChannel.get_list() 
            #channel_list = []
            for index, channel in enumerate(channel_list):
                logger.info(f">>>> {index} / {len(channel_list)} : {channel.name} UPDATED TIME:[{channel.update_time}]")
                if channel.epg_from in ['spotv', 'tving']:
                    logger.info(f"{channel.epg_from} continue..")
                    continue
                #if Task.is_need_epg_make(channel) == False and len(channel.programs) > 0 and channel.epg_from != 'seezn' and channel.name not in ['VIKI']:
                if Task.is_need_epg_make(channel) == False and len(channel.programs) > 0:
                        #logger.debug(u'만든지 1일 미만이라 패스 : %s', (now-channel.update_time))
                    continue
                try:
                    make_title.append(channel.name)
                    ModelEpgProgram.delete_by_channel_name(channel.name)
                except Exception as e: 
                    logger.error(f'Exception:{str(e)}')
                    logger.error(traceback.format_exc())
                try:    
                    for epg_source in epg_map:
                        ret = getattr(channel, f"{epg_source['name']}_id")
                        if ret == '':
                            continue
                        if epg_source['ins'] == None:
                            continue
                        ret = epg_source['ins'].make_epg(channel)
                        if ret:
                            make_count += 1
                            channel.epg_from = epg_source['name']
                            epg_source['count'] += 1
                            channel.update_time = datetime.now()
                            break
                except Exception as e: 
                    logger.error(f'Exception:{str(e)}')
                    logger.error(traceback.format_exc())
                    logger.debug('XX :%s', channel)
                finally:
                    db.session.add(channel)
                    db.session.commit()

        #logger.debug(d(make_title))
        #logger.debug(len(make_title))
        try:
            conn = sqlite3.connect(EPG_DATA_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('VACUUM;')
            conn.commit()
            conn.close()
            logger.info("VACUUM done.")
            logger.info("VACUUM done.")
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())


        logger.info(make_count)
        if make_count > -1:
            P.ModelSettingDATA.set('updated_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            from .task_xml import Task as TaskXml
            TaskXml.make_xml('all', no_update=True)
            Task.upload()
        logger.info("EPG MAKER end..")

    @staticmethod
    def make_channel_list(sheet):
        sheet_data = sheet.get_sheet_data()
        # 없어진 채널을 삭제한다.
        db_data = ModelEpgChannel.get_list()
        for db_item in db_data:
            ret = Task.find_in_sheet(sheet_data, db_item.name)
            if ret == None:
                ModelEpgProgram.delete_by_channel_name(db_item.name)
                ModelEpgChannel.delete_by_id(db_item.id)

        for sheet_item in sheet_data:
            if sheet_item['카테고리'] in ['', '미사용']:
                continue
            db_item = ModelEpgChannel.get_by_name(sheet_item['이름'])    
            if db_item == None:
                db_item = ModelEpgChannel()
            db_item.update(sheet_item)

    
    @staticmethod
    def find_in_sheet(sheet_data, name):
        for item in sheet_data:
            if item['이름'] == name and item['카테고리'] != '미사용':
                return item


    @staticmethod
    @celery.task
    def upload():
        try:
            import platform
            import shutil
            git_home = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.epg.db')
            upload_sh = os.path.join(git_home, 'epg_upload.sh')

            time_file = os.path.join(os.path.dirname(__file__), 'files', 'UPDATED_TIME')
            SupportFile.write_file(time_file, P.ModelSettingDATA.get('updated_time'))
            names = ['epg_data.db', 'xmltv.xml', 'UPDATED_TIME']
            for name in names:
                file1 = os.path.join(os.path.dirname(__file__), 'files', name)
                file2 = os.path.join(git_home, name)
                if os.path.exists(file2):
                    os.remove(file2)
                #shutil.move(file1, file2)
                shutil.copyfile(file1, file2)

            if platform.system() == 'Windows':
                git_bash  = "C:\\Program Files\\Git\\bin\\bash.exe"
                cmd = [git_bash, 'chmod', '777', upload_sh]
                ret = SupportSubprocess.execute_command_return(cmd, timeout=60)
                logger.info(ret)
                cmd = [git_bash, upload_sh, git_home]
                ret = SupportSubprocess.execute_command_return(cmd, timeout=60)
                logger.info(ret)
            else:
                os.system(f"chmod 777 {upload_sh}")
                cmd = [upload_sh, git_home]
                logger.info(f"upload command: {' '.join(cmd)}")
                ret = SupportSubprocess.execute_command_return(cmd, timeout=60)
                logger.info(ret)
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())

    @staticmethod
    def is_need_epg_make(db_item):
        #return True
        #if db_item.update_time + timedelta(days=1) > datetime.now():
        if db_item.update_time == None or db_item.update_time + timedelta(hours=12) < datetime.now():
            return True
        if P.ModelSetting.get('maker_force_update'):
            return True
        return False

 
if __name__ == '__main__':
    Task.start()
    