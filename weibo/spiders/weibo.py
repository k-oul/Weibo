# -*- coding: utf-8 -*-
from scrapy import Spider, Request
import json
from ..items import *

class WeiboSpider(Spider):
    name = 'weibo'
    allowed_domains = ['m.weibo.cn']
    user_url = 'https://m.weibo.cn/api/container/getIndex?uid={uid}&type=uid&value={uid}&containerid=100505{uid}'
    follow_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_{uid}&page={page}'
    fan_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{uid}&since_id={page}'
    weibo_url = 'https://m.weibo.cn/api/container/getIndex?uid={uid}&type=uid&value={uid}&containerid=107603{uid}'
    start_users = ['3217179555', '1742566624']


    def start_requests(self):
        for uid in self.start_users:
            yield Request(self.user_url.format(uid=uid),callback=self.parse_user)


    def parse_user(self, response):
        self.logger.debug(response)
        result = json.loads(response.text)
        if result.get('data').get('userInfo'):
            user_Info = result.get('data').get('userInfo')
            user_item = UserItem
            field_map = {
                'id':'id', 'name': 'screen_name', 'avatar': 'profile_image_url', 'cover': 'cover_image_phone',
                'gender': 'gender', 'description': 'description', 'fans_count': 'followers_count',
                'follows_count': 'follow_count', 'weibos_count': 'statuses_count', 'verified': 'verified',
                'verified_reason': 'verified_reason', 'verified_type': 'verified_type'
            }
        for field, attr in field_map.items():
            user_item[field] = user_Info.get(attr)
        yield user_item

        # 关注
        uid = user_Info.get('id')
        yield Request(self.follow_url.format(uid=uid, page=1), callback=self.parse_follows,
                      meta={'page':1, 'uid': uid})
        # 粉丝
        yield Request(self.fan_url.format(uid=uid, page=1), callback=self.parse_fans,
                      meta={'page': 1, 'uid': uid})
        # 微博
        yield Request(self.weibo_url.format(uid=uid, page=1), callback=self.parse_weibos,
                      meta={'page': 1, 'uid': uid})

    def parse_follows(self, response):
        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards') and len(result.get('data').get('cards')) \
                and result.get('data').get('cards')[-1].get('card_group'):
            follows = result.get('data').get('cards')[-1].get('card_group')
            for follow in follows:
                if follow.get('user'):
                    uid = follow.get('user').get('id')
                    yield Request(self.user_url.format(uid=uid), callback=self.parse_user)
            uid = response.meta.get('uid')
            user_relation_item = UserRelationItem()
            follows = [{'id': follow.get('user').get('id'), 'name': follow.get('screen_name')}
                       for follow in follows]
            user_relation_item['id'] = uid
            user_relation_item['follows'] = follows
            user_relation_item['fans'] = []
            yield user_relation_item
            # 下一页关注
            page = response.meta.get('page') + 1
            yield Request(self. follow_url.format(uid=uid, page=page),
                          callback=self.parse_follows, meta={'page': page, 'uid': uid})

    def parse_weibos(self, response):
        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('card'):
            weibos = result.get('data').get('cards')
            for weibo in weibos:
                mblog = weibo.get('mblog')
                if mblog:
                    weibo_item = WeiboItem()
                    field_map ={
                        'id': 'id','attitudes_count': 'attitudes_count', 'comments_count': 'comments_count',
                        'created_at': 'created_at', 'reposts_count': 'resposts_count', 'picture': 'oroginal_pic',
                        'pictures': 'pic', 'source': 'source', 'text': 'text', 'raw_text': 'raw_text',
                        'thumbnail': 'thumbnail_pic'
                    }
                    for field, attr in field_map.items():
                        weibo_item[field] = mblog.get(attr)

                    weibo_item['user'] = response.meta.get('uid')
                    yield weibo_item

            uid = response.meta.get('uid')
            page = response.meta.get('page') + 1
            yield Request(self.weibo_url.format(uid=uid, page=page), callback=self.parse_weibos,
                          meta={'uid': uid, 'page': page})


