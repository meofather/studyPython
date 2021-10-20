import json
import random
import time
import os
from typing import Dict, Optional, Any

import redis
from telegram.client import Telegram

dir = '/home/milo/pythonCache/'

'''
    添加用户到通讯薄
'''


def addUserToContact(tg: Telegram, members: Optional[Dict[Any, Any]]):
    userMap = {}
    user_ids = []
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
    sleep_time = random.randint(0, 9)
    redis_exc = redis.Redis(connection_pool=pool)
    for member in members:
        member_key_in_redis = f'member_{member["user_id"]}'
        if redis_exc.exists(member_key_in_redis) == 1:
            print(f'{member["user_id"]} 已调用过')
            continue
        else:
            redis_exc.set(member_key_in_redis,json.dumps(member))
        # print(f'user_id:{member["user_id"]}')
        r = tg.call_method('getUser', {'user_id': member["user_id"]})
        r.wait()
        # print(f'MemberInfo:{r.update}')
        if r.update["username"] != '':
            print(f'MemberInfo: {r.update["id"]}  ,  {r.update["username"]}')
            userMap[member["user_id"]] = r.update
            contactParam = {
                'user_id': member["user_id"],
                'first_name': ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 5)),
                'last_name': ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 5))
            }
            r = tg.call_method('addContact', {'contact': contactParam})
            r.wait()
            if r.error:
                if r.error_info['code'] == 429:
                    redis_exc.delete(member_key_in_redis)
                    sleep_time += (60 + random.randint(0, 9))
                print(f'{r.error_info}')
            else:
                print(f' 调用正常>>>{json.dumps(contactParam)}')
            time.sleep(sleep_time)
            user_ids.append(member["user_id"])
            pass
        pass

    return userMap, user_ids


'''
    获取用户信息
'''


def getMembers(tg: Telegram, group_id, current_page=1, page_size=20) -> object:
    param = {
        'supergroup_id': group_id,
        'limit': page_size,
        'offset': page_size * (current_page - 1)
    }
    if exists(group_id, current_page, param['offset']):
        print(f' getting from cache')
        members = readMembersFromFile(group_id, current_page, param['offset'])
    else:
        print(f'get from remote')
        r = tg.call_method('getSupergroupMembers', param)
        r.wait()
        members = r.update['members']
        saveMembersAsFile(group_id, current_page, param['offset'], members)

    print(f' Members: {members}')
    return members, current_page
    pass


def getMembersCount(tg: Telegram, group_id, page_size):
    param = {
        'supergroup_id': group_id,
        'limit': 20
    }
    r = tg.call_method('getSupergroupMembers', param)
    r.wait()
    page = int((r.update['total_count'] - 1) / page_size + 1);
    print(f">> total :{r.update['total_count']} totalPage: {page}")
    return page


def exists(group_id, limit, offset):
    global dir
    return os.path.exists(f"{dir}member_{group_id}_{limit}_{offset}.json")


def saveMembersAsFile(group_id, limit, offset, data):
    global dir
    with open(f"{dir}member_{group_id}_{limit}_{offset}.json", 'w+') as f:
        json.dump(data, f)
        print("complete writing...")


def readMembersFromFile(group_id, limit, offset):
    global dir
    with open(f"{dir}member_{group_id}_{limit}_{offset}.json", "r") as f:
        members = json.load(f)
        return members


def removeMutis(old_list):
    for i in old_list:
        for j in old_list:
            if i['user_id'] == j['user_id'] and i != j:
                print(f"重复的ID》》{j['user_id']}")
                old_list.remove(j)
