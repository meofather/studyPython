import json
import random
import time
import os
from typing import Dict, Optional, Any

from telegram.client import Telegram

dir = '/home/milo/pythonCache/'

'''
    添加用户到通讯薄
'''


def addUserToContact(tg: Telegram, members: Optional[Dict[Any, Any]]):
    userMap = {}
    user_ids = []
    for member in members:
        # print(f'user_id:{member["user_id"]}')
        r = tg.call_method('getUser', {'user_id': member["user_id"]})
        r.wait()
        print(f'MemberInfo:{r.update}')
        if r.update["username"] != '':
            print(f'MemberInfo: {r.update["id"]}  ,  {r.update["username"]}')
            userMap[member["user_id"]] = r.update
            contactParam = {
                'user_id': member["user_id"],
                'first_name': ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 5)),
                'last_name': ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 5))
            }
            r = tg.call_method('addContact', {'contact': contactParam})
            if r.error:
                print(f'{r.error_info}')
            else:
                print(f' 调用正常>>>{json.dumps(contactParam)}')
            time.sleep(3);
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
        'offset': page_size * current_page
    }
    if exists(group_id, current_page, page_size * current_page):
        print(f' getting from cache')
        members = readMembersFromFile(group_id, current_page, page_size * current_page)
    else:
        print(f'get from remote')
        r = tg.call_method('getSupergroupMembers', param)
        r.wait()
        members = r.update['members']
        saveMembersAsFile(group_id, current_page, page_size * current_page, members)

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
