from ..setup import *
import time
from urllib.parse import quote

class EpgWavve(object):
    total_epg_data = None

    @classmethod
    def get_total_epg_data(cls):
        if cls.total_epg_data is None:
            try:
                cls.total_epg_data = {}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
                }
                
                current_dt = datetime.now()
                start_dt = current_dt.replace(minute=0, second=0, microsecond=0)
                end_dt = current_dt + timedelta(hours=3)
                for i in range(24):
                    start_dt = start_dt + timedelta(hours=i*3)
                    end_dt = end_dt + timedelta(hours=i*3)
                    start_param = quote(f"{start_dt.strftime('%Y-%m-%d %H')}:00")
                    end_param = quote(f"{end_dt.strftime('%Y-%m-%d %H')}:00")
                    url = f"https://apis.wavve.com/live/epgs?startdatetime={start_param}&enddatetime={end_param}&genre=all&limit=500&offset=0&apikey=E5F3E0D30947AA5440556471321BB6D9&client_version=7.0.40&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=all"

                    logger.debug(f"EPG 웨이브 URL: {url}")
                    res =  requests.get(url, headers=headers)
                    data = res.json()

                    for channel_data in data['list']:
                        ch_data = cls.total_epg_data.get(channel_data['channelid'], None)
                        if ch_data is None:
                            cls.total_epg_data[channel_data['channelid']] = channel_data['list']
                        else:
                            ch_data.extend(channel_data['list'])
                    time.sleep(1)
            except Exception as e:
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())    
        return cls.total_epg_data
    

    @classmethod
    def make_epg(cls, channel):
        try:
            from support_site import SupportWavve
            logger.debug(channel)

            total_epg_data = cls.get_total_epg_data()
            for item in total_epg_data.get(channel.wavve_id, []):
                p = ModelEpgProgram()
                p.channel = channel
                p.start_time = datetime.strptime(item['starttime'], '%Y-%m-%d %H:%M')
                p.end_time = datetime.strptime(item['endtime'], '%Y-%m-%d %H:%M')
                p.title = item['title']
                #p.content_id = ModelEpgContent.append_by_wavve(item['title'])
                P.content_id = None
                p.episode_number = None
                p.part_number = None
                p.rate = None
                p.re = None
                p.is_movie = False
                #p.poster = 'https://' + item['channelimage']
                db.session.add(p)
            logger.info(f"EPG 웨이브 {channel.name} {len(total_epg_data.get(channel.wavve_id, []))} 저장")
            return True
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return False


        """
        def make_epg(cls, channel):
        try:
            from support_site import SupportWavve
            logger.debug(channel)
        
            current_dt = datetime.now()
            start_param = current_dt.strftime('%Y-%m-%d') + ' 00:00'
            end_dt = current_dt + timedelta(days=6)
            end_param = end_dt.strftime('%Y-%m-%d') + ' 24:00'
            data = SupportWavve.live_epgs_channels(channel.wavve_id, start_param, end_param)
            if data == None or data['list'] == False:
                logger.warning(f"wavve EPG 데이터 실패: {channel.name}")
                return False
                
            for item in data['list']:
                p = ModelEpgProgram()
                p.channel = channel
                p.start_time = datetime.strptime(item['starttime'], '%Y-%m-%d %H:%M')
                p.end_time = datetime.strptime(item['endtime'], '%Y-%m-%d %H:%M')
                p.title = item['title']
                p.content_id = ModelEpgContent.append_by_wavve(item['title'])
                p.episode_number = None
                p.part_number = None
                p.rate = None
                p.re = None
                p.is_movie = False
                #p.poster = 'https://' + item['channelimage']
                db.session.add(p)
            logger.info(f"EPG 웨이브 {channel.name} {len(data['list'])} 저장")
            return True
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return False
        """




"""
{
    "cpid": "C4",
    "channelid": "E07",
    "channelname": "EBS 2",
    "channelimage": "img.pooq.co.kr/BMS/Channelimage30/image/E07.jpg",
    "scheduleid": "E07_20220215234000",
    "programid": "",
    "title": "가만히 10분 멍TV [손칼국수]",
    "image": "wchimg.wavve.com/live/thumbnail/E07.jpg",
    "starttime": "2022-02-15 23:40",
    "endtime": "2022-02-15 23:50",
    "timemachine": "Y",
    "license": "y",
    "livemarks": [],
    "targetage": "0",
    "tvimage": "img.pooq.co.kr/BMS/ChannelImg/ebs2.png",
    "ispreorder": "n",
    "preorderlink": "n",
    "alarm": "n"
}
"""
