from ..setup import *


class EpgWavve(object):
    @classmethod
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
