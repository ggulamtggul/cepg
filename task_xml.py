import urllib

import requests
from lxml import etree as ET
from support import default_headers

from .setup import *


class Task(object):
    @staticmethod
    def updated_time():
        return P.ModelSettingDATA.get('updated_time')

    @staticmethod
    def get_updated_time():
        url = 'https://raw.githubusercontent.com/flaskfarm/.epg.db/main/UPDATED_TIME'
        return requests.get(url, headers=default_headers).text

    @staticmethod 
    def get_output_filepath(plugin):
        if plugin == 'all':
            filename = os.path.join(os.path.dirname(__file__), 'files', f'xmltv.xml')
        else:
            filename = os.path.join(F.config['path_data'], 'xmltv', f'xmltv_{plugin}.xml')
        return filename


    @staticmethod 
    def update_epg_data_db():
        try:
            time1 = P.ModelSetting.get('epg_data_updated_time')
            time2 = Task.get_updated_time()
            if time1 == None or time1 != time2:
                data_db_file = os.path.join(os.path.dirname(__file__), 'files', 'epg_data.db')
                if os.path.exists(data_db_file):
                    os.remove(data_db_file)
                
                logger.info(f"{time1} {time2} epg_data.db 다운로드")
                urllib.request.urlretrieve("https://github.com/flaskfarm/.epg.db/raw/main/epg_data.db", data_db_file) 
                logger.info(f"{time1} {time2} epg_data.db 다운로드 완료")
                P.ModelSetting.set('epg_data_updated_time', time2)
            else:
                logger.info(f"{time1} {time2} epg_data.db 다운로드 필요없음")
        except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())


    @staticmethod
    @celery.task
    def start(*args, **kwargs):
        logger.info(f"args:{args}")
        logger.info(f"kargs:{kwargs}")
        need_make = 0
        plugin = args[0]
        mode = args[1]
        
        if plugin.startswith('alive'):
            try:
                import alive
                with F.app.app_context():
                    Task.make_xml(plugin)
            except Exception as e: 
                logger.error('alive not installed')
        elif plugin == 'hdhomerun':
            try:
                import hdhomerun
                with F.app.app_context():
                    Task.make_xml('hdhomerun')
            except Exception as e: 
                logger.error('hdhomerun not installed')
        elif plugin == 'tvheadend':
            try:
                import tvheadend
                with F.app.app_context():
                    Task.make_xml('tvheadend')
            except Exception as e: 
                logger.error('tvheadend not installed')
        logger.debug(f'EPG {plugin} epg make start..')

    @staticmethod
    def make_xml(call_from):
        Task.update_epg_data_db()
        logger.warning(f"make_xml_task : {call_from}")
        if call_from == 'tvheadend':
            try:
                import tvheadend
                tvh_list = tvheadend.LogicNormal.channel_list()
                if tvh_list is None:
                    return 'not setting tvheadend'
                for tvh_ch in tvh_list['lineup']:
                    epg_entity = ModelEpgChannel.get_by_prefer(tvh_ch['GuideName'])
                    tvh_ch['channel_instance'] = epg_entity
            except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())

            try:
                generated_on = str(datetime.now())
                root = ET.Element('tv')
                root.set('generator-info-name', F.SystemModelSetting.get('ddns'))
                for tvh in tvh_list['lineup']:
                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', '%s' % tvh['uuid'])
                    icon_tag = ET.SubElement(channel_tag, 'icon')
                    if tvh['channel_instance'] != None:
                        icon_tag.set('src', tvh['channel_instance'].icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = tvh['GuideName']
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = str(tvh['GuideNumber'])

                for tvh in tvh_list['lineup']:
                    if tvh['channel_instance'] == None:
                        logger.debug('no channel_instance :%s', tvh)
                        continue
                    Task.make_channel(root, tvh['channel_instance'], tvh['uuid'])
            except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())
                return traceback.format_exc()

        elif call_from == 'alive':
            root = Task.process_alive()
        elif call_from == 'alive_all':
            root = Task.process_alive(is_all=True)

        elif call_from == 'hdhomerun':
            try:
                import hdhomerun
                from hdhomerun.model import ModelHDHomerunChannel
                channel_list = ModelHDHomerunChannel.channel_list(only_use=True)

                root = ET.Element('tv')
                root.set('generator-info-name', F.SystemModelSetting.get('ddns'))
                
                for channel in channel_list:
                    if channel.match_epg_name == '':
                        continue
                    epg_entity = ModelEpgChannel.get_by_name(channel.match_epg_name)
                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', '%s' % channel.id)
                    
                    if epg_entity is not None:
                        icon_tag = ET.SubElement(channel_tag, 'icon')
                        icon_tag.set('src', epg_entity.icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = channel.scan_name
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = str(channel.ch_number)
                    display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                    display_name_tag.text = str(channel.ch_number)

                for channel in channel_list:
                    epg_entity = ModelEpgChannel.get_by_name(channel.match_epg_name)
                    if epg_entity is None:
                        epg_entity = ModelEpgChannel.get_by_prefer(channel.scan_name)
                    if epg_entity is None:
                        continue
                    Task.make_channel(root, epg_entity, '%s' % channel.id)
                   
            except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())
                return traceback.format_exc()
        
        elif call_from == 'all':
            try:
                channel_list = ModelEpgChannel.get_list()
                root = ET.Element('tv')
                root.set('generator-info-name', F.SystemModelSetting.get('ddns'))
                for idx, channel in enumerate(channel_list):
                    if channel.category == '지상파' and channel.name not in ['KBS1', 'KBS2', 'MBC', 'SBS', 'EBS1', 'EBS2', 'OBS 경인TV']:
                        continue

                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', channel.name)
                    icon_tag = ET.SubElement(channel_tag, 'icon')
                    icon_tag.set('src', channel.icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = channel.name
                    display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                    display_name_tag.text = str(idx+1)
                for channel in channel_list:
                    Task.make_channel(root, channel, channel.name)
            except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())
                return traceback.format_exc()
       
        try:
            tree = ET.ElementTree(root)
            if call_from == 'all':
                filename = os.path.join(os.path.dirname(__file__), 'files', f'xmltv.xml')
            else:
                _ = os.path.join(F.config['path_data'], 'xmltv')
                os.makedirs(_, exist_ok=True)
                filename = os.path.join(_, f'xmltv_{call_from}.xml')
            if os.path.exists(filename):
                os.remove(filename)
            tree.write(filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
            #ret = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")
            P.ModelSetting.set(f'xml_updated_{call_from}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            #db.session.commit()
            logger.info('EPG2XML end....')
            return True
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())

    
    @staticmethod
    def process_alive(is_all=False):
        regex1 = r'tvg-id="(?P<name>[^"]*?)"\stvg-name="([^"]*?)"\stvg-logo="(?P<logo>[^"]*?)"\sgroup-title="(?P<group>[^"]*?)"\s(radio="true"\s)?tvg-chno="(?P<no>[^"]*?)"\stvh-chnum="([^"]*?)",([^$]*?)$'

        try:
            import alive
            from alive.logic_alive import LogicAlive, LogicKlive

            #PP = F.PluginManager.get_plugin_instance('alive')
            #m3u = PP.module_list[0].process_m3u('m3u' if normal else 'm3uall', {})
            if is_all == False:
                m3u = LogicAlive.get_m3u()
            else:
                m3u = LogicKlive.get_m3uall()
            alive_channel_list = []   
            for ch in re.finditer(regex1, m3u, re.MULTILINE):
                alive_channel_list.append({
                    'cate': ch.group('group'),
                    'name': ch.group('name'),
                    'number': ch.group('no'),
                })
            root = ET.Element('tv')
            root.set('generator-info-name', F.SystemModelSetting.get('ddns'))
            for idx, alive_channel in enumerate(alive_channel_list):
                epg_entity = ModelEpgChannel.get_by_name(alive_channel['name'])
                if epg_entity is None:
                    # 2020-06-14
                    epg_entity = ModelEpgChannel.get_by_prefer(alive_channel['name'])
                if epg_entity:
                    logger.debug(f"{idx+1} / {len(alive_channel_list)} ALive - {alive_channel['name']} / DB - {epg_entity.name} ")
                else:
                    logger.info(f"{idx+1} / {len(alive_channel_list)}  ALive - {alive_channel['name']} / DB 없음.")
                channel_tag = ET.SubElement(root, 'channel') 
                #channel_tag.set('id', '%s|%s' % (alive_channel.source, alive_channel.source_id))
                channel_tag.set('id', alive_channel['name'])
                if epg_entity is not None:
                    icon_tag = ET.SubElement(channel_tag, 'icon')
                    icon_tag.set('src', epg_entity.icon)
                display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                display_name_tag.text = alive_channel['name']
                display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                display_name_tag.text = alive_channel['number']
                display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                display_name_tag.text = alive_channel['number']

            for idx, alive_channel in enumerate(alive_channel_list):
                epg_entity = ModelEpgChannel.get_by_name(alive_channel['name'])
                if epg_entity is None:
                    epg_entity = ModelEpgChannel.get_by_prefer(alive_channel['name'])
                if epg_entity is None:
                    logger.debug('no channel_instance :%s', alive_channel['name'])
                    continue
                                    
                #Task.make_channel(root, epg_entity, '%s|%s' % (alive_channel.source, alive_channel.source_id), category=alive_channel.group)
                Task.make_channel(root, epg_entity, alive_channel['name'], category=alive_channel['cate'])
            return root
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return traceback.format_exc()
        


    @staticmethod
    def make_channel(root, channel_instance, channel_id, category=None):
        try:
            logger.debug('CH : %s', channel_instance.name)
            for program in channel_instance.programs:
                program_tag = ET.SubElement(root, 'programme')
                program_tag.set('start', program.start_time.strftime('%Y%m%d%H%M%S') + ' +0900')
                program_tag.set('stop', program.end_time.strftime('%Y%m%d%H%M%S') + ' +0900')
                program_tag.set('channel', '%s' % channel_id)
                title_tag = ET.SubElement(program_tag, 'title')
                title_tag.set('lang', 'ko')
                if program.re is not None and program.re:
                    title_tag.text = program.title + ' (재)'
                else:
                    title_tag.text = program.title

                if program.rate != None:
                    rating_tag = ET.SubElement(program_tag, 'rating')
                    rating_tag.set('system', 'MPAA')
                    value_tag = ET.SubElement(rating_tag, 'value')
                    value_tag.text = program.rate
                # desc
                if program.desc is not None:
                    desc_tag = ET.SubElement(program_tag, 'desc')
                    desc_tag.set('lang', 'ko')
                    desc_tag.text = program.desc
                elif program.content_info is not None and program.content_info.desc is not None:
                    desc_tag = ET.SubElement(program_tag, 'desc')
                    desc_tag.set('lang', 'ko')
                    desc_tag.text = program.content_info.desc
                # poster
                if program.poster is not None:
                    icon_tag = ET.SubElement(program_tag, 'icon')
                    icon_tag.set('src', program.poster)
                elif program.content_info is not None and program.content_info.poster is not None:
                    icon_tag = ET.SubElement(program_tag, 'icon')
                    icon_tag.set('src', program.content_info.poster)
                # actor
                if program.actor is not None:
                    credits_tag = ET.SubElement(program_tag, 'credits')
                    for actor in program.actor.split('|'):
                        try:
                            actor_tag = ET.SubElement(credits_tag, 'actor')
                            #logger.debug(actor)
                            #name, role = actor.split(',')
                            #actor_tag.set('role', role.strip())
                            actor_tag.text = actor.strip()
                        except:
                            pass
                elif program.content_info is not None and program.content_info.actor is not None:
                    credits_tag = ET.SubElement(program_tag, 'credits')
                    for actor in program.content_info.actor.split('|'):
                        try:
                            actor_tag = ET.SubElement(credits_tag, 'actor')
                            #logger.debug(actor)
                            #name, role = actor.split(',')
                            #actor_tag.set('role', role.strip())
                            actor_tag.text = actor.strip()
                        except:
                            pass

                category_tag = ET.SubElement(program_tag, 'category')
                category_tag.set('lang', 'ko')
                category_tag.text = category if category is not None else channel_instance.category
                # TODO 영화부터 분기, 영화가 아니라면 모두 에피소드 처리해야함
                if program.is_movie == False:
                    if program.episode_number is not None:
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'onscreen')
                        episode_num_tag.text = program.episode_number
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'xmltv_ns')
                        episode_num_tag.text = '0.%s.' % (int(program.episode_number.split('-')[0]) - 1)
                    else:
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'onscreen')
                        tmp = program.start_time.strftime('%Y%m%d')
                        episode_num_tag.text = tmp
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'xmltv_ns')
                        episode_num_tag.text = '%s.%s.' % (int(tmp[:4])-1, int(tmp[4:]) - 1)
                
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())

