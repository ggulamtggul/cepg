import argparse
import json
import os
import platform
import re
import sys
import time
import traceback
import urllib.parse
from collections import OrderedDict
from datetime import datetime
from urllib.parse import quote, unquote, urlencode

import flaskfarm
import requests
import yaml
from lxml import html
from support import d, default_headers, get_logger
from support.expand.gsheet_base import GoogleSheetBase

logger = get_logger()





class CliMakeSheet:

    def __init__(self):
        self.sheet = EPG_Sheet()

    def daum(self):
        daum_map = [
            {
                'name': '지상파',
                'flag_sub_category': False,
                'flag_all_channel': False,
            },
            {
                'name': '종합편성',
                'flag_sub_category': False,
                'flag_all_channel': False,
            },
            {
                'name': '케이블',
                'flag_sub_category': True,
                'flag_all_channel': True,
            },
            {
                'name': '지상파',
                'flag_sub_category': True,
                'flag_all_channel': True,
            },
            {
                'name': '스카이라이프',
                'flag_sub_category': True,
                'flag_all_channel': True,
                'is_skylife': True
            },
            {
                'name': '해외위성',
                'flag_sub_category': False,
                'flag_all_channel': True,
            },
            {
                'name': '라디오',
                'flag_sub_category': False,
                'flag_all_channel': True,
            },
        ]

        try:
            compare_sheet_data = self.sheet.get_sheet_data()
            for cate in daum_map:
                sheet_data = self.sheet.get_sheet_data()
                url = f"https://search.daum.net/search?DA=B3T&w=tot&rtmaxcoll=B3T&q={cate['name']} 편성표"
                text = requests.get(url, headers=default_headers).text
                root = html.fromstring(text)
                if cate['flag_sub_category'] == False and cate['flag_all_channel'] == False:
                    tags = root.xpath('//*[@id="channelNaviLayer"]/div[1]/span')
                    for tag in tags:
                        a_tag = tag.xpath('a')[0]
                        ch = {
                            '이름': a_tag.text, 
                            'DAUM 이름': a_tag.text, 
                            'DAUM ID' :unquote(re.search(r'q=(?P<id>.*?)$', a_tag.attrib['href']).group('id')),
                            '카테고리1': cate['name'],
                            '카테고리': cate['name'],
                            'FROM': 'DAUM',
                        }
                        self.sheet.write_data(compare_sheet_data, ch)
                elif cate['flag_sub_category'] == True:
                    top_cate_tags = root.xpath('//*[@id="channelNaviLayer"]/div[1]/span')
                    cate_order = OrderedDict()
                    if cate['name'] != '지상파':
                        for top_cate in top_cate_tags:
                            cate_order[top_cate.xpath('a')[0].text] = -1
                        # 연예/오락 뉴스/경제 드라마 여성/패션 스포츠 영화 음악 만화 어린이 교양 다큐 교육 레저 공공 종교 홈쇼핑
                        

                        all_cate_tags = root.xpath('//*[@id="channelNaviLayer"]/div[2]/div')
                        for idx, all_cate in enumerate(all_cate_tags):
                            cate_order[all_cate.xpath('strong')[0].text] = idx
                    else:
                        all_cate_tags = root.xpath('//*[@id="channelNaviLayer"]/div[2]/div')
                        for idx, all_cate in enumerate(all_cate_tags):
                            cate_order[all_cate.xpath('strong')[0].text] = idx
                    
                    if cate.get('is_skylife') == False:
                        for sub_cate, idx in cate_order.items():
                            tags = root.xpath(f'//*[@id="channelNaviLayer"]/div[2]/div[{idx+1}]/ul/li')
                            for tag in tags:
                                a_tag = tag.xpath('a')[0]
                                ch = {
                                    '이름': a_tag.text, 
                                    'DAUM 이름': a_tag.text, 
                                    'DAUM ID' :unquote(re.search(r'q=(?P<id>.*?)$', a_tag.attrib['href']).group('id')),
                                    '카테고리1': cate['name'],
                                    '카테고리': sub_cate,
                                    'FROM': 'DAUM',
                                }
                                self.sheet.write_data(compare_sheet_data, ch)
                    else:
                        for sub_cate, idx in cate_order.items():
                            tags = root.xpath(f'//*[@id="channelNaviLayer"]/div[2]/div[{idx+1}]/ul/li')
                            for tag in tags:
                                a_tag = tag.xpath('a')[0]
                                name = name2 = a_tag.text
                                if name.startswith('HD'):
                                    name2 = name.replace('HD', '').strip()
                                #if name.endswith('UHD'):
                                #    name2 = name.replace('UHD', '').strip()
                                skylife_ch = {
                                    'Asia': 'Asia N',
                                    'Asia N2': 'Asia N',
                                    'FTV2': 'FTV',
                                    'CJ온스타일2': 'CJ온스타일',
                                }
                                name2 = skylife_ch.get(name2, name2)
                                find = False
                                for sheet_item in sheet_data:
                                    if self.util_get_search_name(name2) in self.util_get_search_name(sheet_item['DAUM 이름']) or self.util_get_search_name(name2) in self.util_get_search_name(sheet_item['AKA']):
                                        logger.warning(name2)
                                        find = True
                                        break
                                if find:
                                    continue
                                ch = {
                                    '이름': name2, 
                                    'DAUM 이름': name2, 
                                    'DAUM ID' :unquote(re.search(r'q=(?P<id>.*?)$', a_tag.attrib['href']).group('id')),
                                    '카테고리1': '케이블',
                                    '카테고리': sub_cate,
                                    'FROM': 'DAUM',
                                }
                                self.sheet.write_data(compare_sheet_data, ch)
                elif cate['flag_sub_category'] == False and cate['flag_all_channel'] == True:
                    tags = root.xpath('//*[@id="channelNaviLayer"]/div[2]/ul/li')
                    for tag in tags:
                        a_tag = tag.xpath('a')[0]
                        ch = {
                            '이름': a_tag.text, 
                            'DAUM 이름': a_tag.text, 
                            'DAUM ID' :unquote(re.search(r'q=(?P<id>.*?)$', a_tag.attrib['href']).group('id')),
                            '카테고리1': cate['name'],
                            '카테고리': cate['name'],
                            'FROM': 'DAUM',
                        }
                        self.sheet.write_data(compare_sheet_data, ch)
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc()) 



    def wavve(self):
        def live_all_channels(genre='all'):
            try:
                param = {
                    'apikey' : 'E5F3E0D30947AA5440556471321BB6D9',
                    'credential' : 'none',
                    'device' : 'pc',
                    'partner' : 'pooq',
                    'pooqzone' : 'none',
                    'region' : 'kor',
                    'drm' : 'wm',
                    'targetage' : 'auto',
                    'genre' : genre,
                    'type' : 'all',
                    'offset' : 0,
                    'limit' : 999,
                }
                url = f"https://apis.wavve.com/live/all-channels?{urlencode(param)}"
                response = requests.get(url, headers=default_headers)
                data = response.json()
                if response.status_code == 200:
                    return data
                else:
                    if 'resultcode' in data:
                        logger.debug(data['resultmessage'])
            except Exception as e:
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc()) 
        try:
            sheet_data = self.sheet.get_sheet_data()
            compare_sheet_data = self.sheet.get_sheet_data()
            # 지상파 종편/보도 홈쇼핑 드라마/예능 시사/교양 영화/스포츠 키즈/애니 라디오/음악
            cates = ['01', '02', '03', '04', '12', '05', '06', '10']
            for cate in cates:
                live_data = live_all_channels(cate)

                ch_list = []
                for item in live_data['list']:
                    img = 'https://' + item['tvimage'].replace(' ', '%20') if item['tvimage'] != '' else ''
                    ch_list.append({'name':item['channelname'], 'id':item['channelid'], 'img':img})
                
                logger.warning(f"웨이브 채널 : {len(ch_list)}")
                now = datetime.now()
                date = now.strftime('%Y-%m-%d')
                logger.debug(date)
                url = f"https://apis.wavve.com/live/epgs?enddatetime={date}%2022%3A00&genre=all&limit=200&offset=0&startdatetime={date}%2019%3A00&apikey=E5F3E0D30947AA5440556471321BB6D9&credential=none&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=all"
                epg_data = requests.get(url, headers=default_headers).json()
                #logger.debug(epg_data)

                for item in epg_data['list']:
                    for ch in ch_list:
                        if ch['name'] == item['channelname'] and ch['id'] == item['channelid']:
                            logger.debug(ch['name'])
                            ch['img2'] = 'https://' + item['channelimage']
                            break
                    else:
                        logger.warning("없음")
                        logger.warning(item['channelname'])

                for ch in ch_list:
                    if 'img2' not in ch:
                        logger.error(ch['name'])
                        ch['img2'] = ch['img']
                    
                    data = self.find_in_sheet(sheet_data, ch['name'])
                    if data == None:
                        data = {
                            '이름': ch['name'],
                            'FROM': '웨이브',
                            '로고': '',
                            '웨이브 로고2': '',
                        }
                    if data['로고'] == '':
                        data['로고'] = ch['img2']
                    data['웨이브 ID'] = ch['id']
                    data['웨이브 이름'] = ch['name']
                    data['웨이브 로고1'] = ch['img']
                    if data['웨이브 로고2'] == '':
                        data['웨이브 로고2'] = ch['img2']
                    self.sheet.write_data(compare_sheet_data, data)
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc()) 
        #logger.warning(len(live_data['list']))    

    def tving(self):
        def api_get(cls, url, token=None):
            try:
                if token == None:
                    token = cls.__token
                cls.__headers['Cookie'] = f"_tving_token={token}"
                data = requests.get(url, headers=cls.__headers, proxies=cls.__proxies).json()
                try:
                    if type(data['body']['result']) == type({}) and data['body']['result']['message'] != None:
                        logger.debug(f"tving api message : {data['body']['result']['message']}")
                except:
                    pass
                if data['header']['status'] == 200:
                    return data['body']
            except Exception as e:
                logger.error(f'url: {url}')
                logger.error(f"Exception:{str(e)}")
                logger.error(traceback.format_exc())


        def get_live_list(list_type='live', order='rating', include_drm=False):
            def func(param, page, order='rating', include_drm=True):
                has_more = 'N'
                try:
                    __default_param = f'&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey=1e7952d0917d6aab1f0293a063697610'
                    __headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Referer' : '',
                    }

                    result = []
                    url = f'https://api.tving.com/v2/media/lives?cacheType=main&pageNo={page}&pageSize=20&order={order}&adult=all&free=all&guest=all&scope=all{param}{__default_param}'
                    data = requests.get(url, headers=__headers).json()['body']
                    for item in data["result"]:
                        try:
                            info = {}
                            info['id'] = item["live_code"]
                            info['title'] = item['schedule']['channel']['name']['ko']
                            info['episode_title'] = ' '
                            info['img'] = 'http://image.tving.com/upload/cms/caic/CAIC1900/%s.png' % item["live_code"]
                            if item['schedule']['episode'] is not None:
                                info['episode_title'] = item['schedule']['episode']['name']['ko']
                                if info['title'].startswith('CH.') and len(item['schedule']['episode']['image']) > 0:
                                    info['img'] = 'http://image.tving.com' + item['schedule']['episode']['image'][0]['url']
                            info['summary'] = info['episode_title']
                            result.append(info)
                        except Exception as e:
                            logger.error(f"Exception:{str(e)}")
                            logger.error(traceback.format_exc())
                    has_more = data["has_more"]
                except Exception as e:
                    logger.error(f"Exception:{str(e)}")
                    logger.error(traceback.format_exc())
                return has_more, result

            ret = []
            if list_type == 'live':
                params = ['&channelType=CPCS0100,CPCS0400']
            elif list_type == 'vod':
                params = ['&channelType=CPCS0300']
            elif list_type == 'all':
                params = ['&channelType=CPCS0100,CPCS0400', '&channelType=CPCS0300']
            else:
                params = ['&channelType=CPCS0100,CPCS0400']

            for param in params:
                page = 1
                while True:
                    hasMore, data = func(param, page, order=order, include_drm=include_drm)
                    ret += data
                    if hasMore == 'N':
                        break
                    page += 1
            return ret
        data = get_live_list(include_drm=True)
        #logger.debug(d(data))
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in data:
            data = self.find_in_sheet(sheet_data, item['title'])
            if data == None:
                data = {}
                data['이름'] = item['title']
                data['FROM'] = '티빙'
            if '로고' not in data or data['로고'] == '':
                data['로고'] = item['img']
            data['티빙 ID'] = item['id']
            data['티빙 이름'] = item['title']
            data['티빙 로고'] = item['img']
            self.sheet.write_data(compare_sheet_data, data)



    def skb(self):
        def get_skb_list():
            #cate_list = [5100, 7800, 6600, 5600, 5800, 6300, 6700, 7200, 6000, 6400, 5900, 5300, 5700, 7400, 7600, 6900, 7300, 7700, 6501]
            cate_list = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] 
            #
            ret = []
            for cate in cate_list:
                #date = datetime.now().strftime('%Y%m%d')
                #url = f"https://www.bworld.co.kr/myb/core-prod/product/btv-channel/day-frmt-list?gubun=day&stdDt={date}&idSvc={cate}"

                #url = 'http://m.skbroadband.com/content/realtime/Channel_List.do?key_depth1=%s&key_depth2=&key_depth3=' % cate
                url = f"https://www.bworld.co.kr/myb/core-prod/product/btv-channel/chnl-dtl-list?cdMenu={cate}"
                headers = default_headers.copy()
                headers['Referer'] = "https://www.bworld.co.kr/myb/product/btv-chnl/chnl-frmt-list.do"
                headers['Host'] = "www.bworld.co.kr"

                logger.debug(url)
                data = requests.get(url, headers=headers).json()
            
                for item in data['result']:
                    ret.append({
                        'SKB ID': item['idSvc'],
                        'SKB 이름': item['nmCh'],
                    })
            return ret

        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in get_skb_list():
            data = self.find_in_sheet(sheet_data, item['SKB 이름'])
            if data == None:
                data = {}
                data['이름'] = item['SKB 이름']
                data['FROM'] = 'SKB'
            data['SKB ID'] = item['SKB ID']
            data['SKB 이름'] = item['SKB 이름']
            self.sheet.write_data(compare_sheet_data, data)


    def cmb(self):
        url = 'https://www.cmb.co.kr/kwa-kj_ch2'
        text = requests.get(url, headers=default_headers).text
        root = html.fromstring(text)
        

        #//*[@id="AB_contents"]/div[2]/div[1]/div/div/table/tbody/tr[1]
        #//*[@id="AB_contents"]/div[2]/div[1]/div/div/table/tbody/tr[4]
        ret = []
        xpaths = [
            ['//*[@id="AB_contents"]/div[2]/div[1]/div/div/table/tbody/tr', 3],
            ['//*[@id="AB_contents"]/div[2]/div[2]/div[1]/div/table/tbody/tr',3],
            ['//*[@id="AB_contents"]/div[2]/div[2]/div[2]/div[1]/table/tbody/tr',2],
        ]
        for idx, xx in enumerate(xpaths):
            tags = root.xpath(xx[0])
            for tag in tags[xx[1]:]:
                if idx == 2:
                    tds = tag.xpath('td/p')
                else:
                    tds = tag.xpath('td')
                for td in tds:
                    if td.text != None:
                        tmp = re.sub('\d+', '', td.text)
                        if tmp == '':
                            continue
                        logger.error(td.text)
                        if td.text.startswith('HD '):
                            ch_name = td.text.replace('HD ', '').strip()
                        ret.append(ch_name)

        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for name in ret:
            data = self.find_in_sheet(sheet_data, name)
            if data == None:
                data = {
                    '이름': name,
                    'FROM': 'CMB',
                    '케이블 이름': name
                }
                logger.warning(f"NOT FIND : {name}")
            else:
                if data['케이블 이름'] == '':
                    data['케이블 이름'] = name
                else:
                    tmp = data['케이블 이름'].split('\n')
                    if name not in tmp:
                        data['케이블 이름'] = data['케이블 이름'] + '\n' + name
            self.sheet.write_data(compare_sheet_data, data)


    def kt(self):
        def py_unicode(v):
            return str(v)
        def get_kt_list():
            ret = []
            url = 'https://tv.kt.com/tv/channel/pChInfo.asp'
            res = requests.get(url, headers=default_headers)
            res.encoding = res.apparent_encoding
            html = res.text
            tmp = re.compile(r'^\s+(?P<id>\d+)\&nbsp\;(?P<name>.*?)($|\&nbsp;\<)', re.MULTILINE).finditer(html)
            for t in tmp:
                ret.append([t.group('name').strip().replace('&amp;', '&') , t.group('id')])
            return ret

        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in get_kt_list():
            data = self.find_in_sheet(sheet_data, item[0])
            if data == None:
                data = {}
                data['이름'] = item[0]
                data['FROM'] = 'KT'
            data['KT ID'] = item[1]
            data['KT 이름'] = item[0]
            self.sheet.write_data(compare_sheet_data, data)

    def kt_logo(self):
        url = 'https://tv.kt.com/tv/channel/pSchedule.asp'
        data = {'ch_type': '3', 'view_type': '1'}
        #service_ch_no: 155
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()

        for item in sheet_data:
            if item['KT ID'] == '':
                continue
            if item['KT 로고'] != '':
                continue
            data['service_ch_no'] = item['KT ID']
            res = requests.post(url, headers=default_headers, data=data)
            text = res.text
            #logger.debug(res.text)
            match = re.search(r'<h5 class="b_logo"><img src=\'(?P<logo>[^\']+)\' alt=\'(?P<name>[^\']+)\'', text)
            if match and match.group('name').strip() == item['KT 이름']:
                item['KT 로고'] = 'https://tv.kt.com' + match.group('logo')
                item['로고'] = item['KT 로고']
                self.sheet.write_data(compare_sheet_data, item)
            else:
                logger.error(item['이름'])




    def lgu(self):
        try:
            url = "https://www.lguplus.com/uhdc/fo/prdv/chnlgid/v1/tv-schedule-list?brdCntrTvChnlBrdDt=20240621&urcBrdCntrTvChnlId=&urcBrdCntrTvChnlGnreCd="
            ret = requests.get(url, headers=default_headers, verify=False).json()
            sheet_data = self.sheet.get_sheet_data()
            compare_sheet_data = self.sheet.get_sheet_data()
            for item in ret['brdCntrTvChnlIDtoList']:
                data = self.find_in_sheet(sheet_data, item['urcBrdCntrTvChnlDscr'])
                if data == None:
                    data = {}
                    data['이름'] = item['urcBrdCntrTvChnlDscr']
                    data['FROM'] = 'LGU'
                data['LGU ID'] = item['urcBrdCntrTvChnlId']
                data['LGU 이름'] = item['urcBrdCntrTvChnlDscr']
                self.sheet.write_data(compare_sheet_data, data)

        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())



    def hcn(self):
        try:
            url = 'https://www.hcn.co.kr/user/channel/BD_ChannelInfoList.do'
            res = requests.get(url, headers=default_headers)
            root = html.fromstring(res.text)
            sheet_data = self.sheet.get_sheet_data()
            compare_sheet_data = self.sheet.get_sheet_data()
            for i in range(17):
                tr_tags = root.xpath(f'//*[@id="firstBody_{i}"]/tr')
                for tr in tr_tags:
                    td = tr.xpath('td')[1]
                    tmp = td.attrib['onclick']
                    match = re.search(r'goProgramInfo\(.*?,(\d+)\)', tmp.strip())
                    ch_name = td.text.strip()
                    data = self.find_in_sheet(sheet_data, ch_name)
                    if data == None:
                        data = {}
                        data['이름'] = ch_name
                        data['FROM'] = 'HCN'
                    data['HCN ID'] = match.group(1)
                    data['HCN 이름'] = ch_name
                    self.sheet.write_data(compare_sheet_data, data)

        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
    


    def kctv(self):
        url = 'https://www.kctv.co.kr/channel/digital_channel.php'
        res = requests.get(url, headers=default_headers, verify=False)
        res.encoding = res.apparent_encoding
        text = res.text
        match = re.finditer(r'class="txt_lf">(?P<ch>[^<]+)<\/td>', text)
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for m in match:
            name = m.group('ch').strip()
            data = self.find_in_sheet(sheet_data, name)
            if data == None:
                data = {
                    '이름': name,
                    'FROM': 'KCTV',
                    '케이블 이름': name
                }
            else:
                if data['케이블 이름'] == '':
                    data['케이블 이름'] = name
                else:
                    tmp = data['케이블 이름'].split('\n')
                    if name not in tmp:
                        data['케이블 이름'] = data['케이블 이름'] + '\n' + name
                self.sheet.write_data(compare_sheet_data, data)


    def last_logo(self):
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in sheet_data:
            if item['최종 로고'] != '' or item['카테고리'] in ['', '미사용'] or item['로고'] == '':
                continue
            # URL이 김
            # https://images-ext-1.discordapp.net/external/grWjdO6f-ted630snPcSGawPt45dvjxv_pJm-luBQLU/https/tv.kt.com/relatedmaterial/ch_logo/live/5.png
            #item['최종 로고'] = SupportDiscord.discord_proxy_image(item['로고'])
            tmp = requests.get(item['로고'], headers=default_headers).content
            item['최종 로고'] = SupportDiscord.discord_proxy_image_bytes(tmp)

            self.sheet.write_data(compare_sheet_data, item)
            #return
    


    def util_get_search_name(self, s):
        return s.strip().replace('-', '').replace(' ', '').upper()

    def find_in_sheet(self, sheet_data, name):
        for sheet_item in sheet_data:
            if self.util_get_search_name(sheet_item['이름']) == self.util_get_search_name(name):
                return sheet_item
            #logger.debug(sheet_item['이름'])
            if 'AKA' in sheet_item:
                akas = [self.util_get_search_name(x.strip()) for x in self.util_get_search_name(sheet_item['AKA']).splitlines()]
                if self.util_get_search_name(name) in akas:
                    return sheet_item

            #logger.debug(akas)
            

    def all(self):
        self.daum()
        self.wavve()
        self.tving()
        self.skb()
        self.kt()
        self.lgu()
        self.cmb()
        self.kctv()
        self.hcn()
        self.kt_logo()
        return
        
        self.last_logo()
        logger.debug("종료")


    def log(self):
        data = [
            ['티빙', 0, 0],
            ['SPOTV', 0, 0],
            ['DAUM', 0, 0],
            ['웨이브', 0, 0],
            ['HCN', 0, 0],
            ['LGU', 0, 0],
            ['KT', 0, 0],
            ['SKB', 0, 0],
        ]
        count = 0
        sheet_data = self.sheet.get_sheet_data()
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] in ['', '미사용']:
                continue
            #if sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['시즌 ID'] == '' and sheet_item['케이블 이름'] != '':
            #    continue

            count += 1
            for tmp in data:
                if sheet_item[f"{tmp[0]} ID"] != '':
                    tmp[1] += 1
            for tmp in data:
                if sheet_item[f"{tmp[0]} ID"] != '':
                    tmp[2] += 1
                    break
        
        for tmp in data:
            print(tmp)
            #logger.debug(d(data))

        count = 0
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] == '미사용':
                continue
            if sheet_item['DAUM ID'] == '' and sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['SKB ID'] == '' and sheet_item['KT ID'] == '' and sheet_item['LGU ID'] == '' and sheet_item['HCN ID'] == '' and sheet_item['SPOTV ID'] == '':
                count += 1
        #logger.debug(f"시즌 : {count}")

        count = 0
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] == '미사용':
                continue
            if sheet_item['SKB ID'] != '' and sheet_item['DAUM ID'] == '' and sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['KT ID'] == '' and sheet_item['LGU ID'] == '' and sheet_item['HCN ID'] == '' and sheet_item['SPOTV ID'] == '':
                count += 1
        logger.debug(f"SKB : {count}")

        count = 0
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] == '미사용':
                continue
            if sheet_item['KT ID'] != '' and sheet_item['DAUM ID'] == '' and sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['SKB ID'] == '' and sheet_item['LGU ID'] == '' and sheet_item['HCN ID'] == '' and sheet_item['SPOTV ID'] == '':
                count += 1
        logger.debug(f"KT : {count}")

        count = 0
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] == '미사용':
                continue
            if sheet_item['LGU ID'] != '' and sheet_item['DAUM ID'] == '' and sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['KT ID'] == '' and sheet_item['SKB ID'] == '' and sheet_item['HCN ID'] == '' and sheet_item['SPOTV ID'] == '':
                logger.debug(sheet_item['이름'])
                count += 1
        logger.debug(f"LGU : {count}")
        logger.warning(count)



class EPG_Sheet(GoogleSheetBase):
    def __init__(self):
        super(EPG_Sheet, self).__init__('17Uq1cOokrZ4Ci0eQxs5_v6Ea8jKx3IPgTR1JudLR6tM', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files', 'credential.json'), 0, '이름')
        #super(EPG_Sheet, self).__init__('1jLE8xDmrxhcMLmXuD1ShCFIK63-DorCg-KOe1PjBPZc', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files', 'credential.json'), 0, '이름')

        # 원본 17Uq1cOokrZ4Ci0eQxs5_v6Ea8jKx3IPgTR1JudLR6tM
        # 테스트용: 1jLE8xDmrxhcMLmXuD1ShCFIK63-DorCg-KOe1PjBPZc



if __name__ == '__main__':
    ins = CliMakeSheet()
    ins.all()
    ins.log()
