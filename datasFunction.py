import json
import random
import time
from typing import Dict, Optional, Any

from telegram.client import Telegram

chat = {}

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


def getMembers(tg: Telegram, group_id, current_page=1) -> object:
    param = {
        'supergroup_id': group_id,
        'limit': 20,
        'offset': 20 * current_page
    }
    r = tg.call_method('getSupergroupMembers', param)
    r.wait()
    print(f' Members: {r.update}')
    return r.update['members'], current_page, int((r.update['total_count'] - 1) / 20 + 1)
    pass


def removeMutis(old_list):
    for i in old_list:
        for j in old_list:
            if i['user_id'] == j['user_id'] and i != j:
                print(f"重复的ID》》{j['user_id']}")
                old_list.remove(j)
