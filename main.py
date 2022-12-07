import argparse
import json
import logging
import time

import redis
from telegram.client import Telegram

import utils
from datasFunction import addUserToContact, getMembers, removeMutis, getMembersCount

logger = logging.getLogger(__name__)


def confirm(message):
    sure = input(message + ' yes ')
    if sure.lower() not in ['y', 'yes']:
        exit(0)


def getSubList(parent_list, start=0, end=0):
    temp = []
    if end >= len(parent_list):
        end = len(parent_list)-1
    for i in range(start, end):
        temp.append(parent_list[i])
    return temp


if __name__ == '__main__':
    utils.setup_logging()

    parser = argparse.ArgumentParser()
    utils.add_api_args(parser)
    utils.add_proxy_args(parser)
    args = parser.parse_args()

    tg = Telegram(
        api_id=args.api_id,
        api_hash=args.api_hash,
        phone=args.phone,
        database_encryption_key='changeme1234',
        proxy_server=args.proxy_server,
        proxy_port=args.proxy_port,
        proxy_type=utils.parse_proxy_type(args)
    )
    # you must call login method before others
    tg.login()

    # get me
    result = tg.get_me()
    result.wait()
    me = result.update['id']
    print(result.update)

    # get chats
    result = tg.get_chats(9223372036854775807)  # const 2^62-1: from the first
    result.wait()
    chats = result.update['chat_ids']
    # get each chat
    print('Chat List')
    chat_map = {}
    index = 0
    for chat_id in chats:
        r = tg.get_chat(chat_id)
        r.wait()
        title = r.update['title']
        if r.update['type']['@type'] == 'chatTypeSupergroup' and not r.update['type']['is_channel']:
            print(f'{index} {chat_id} >> {title}')
            chat_map[index] = r.update
            index += 1

    resource_index = int(input('选择要转移的群: ').strip())
    target_index = int(input('选择目标群: ').strip())
    resource_chat_info = chat_map[resource_index]
    target_chat_info = chat_map[target_index]

    print(f'Chat: {resource_chat_info["title"]} >>即将转移到>> {target_chat_info["title"]}')

    confirm('确认开始？? Y/N')

    # 获取用户信息
    resource_members = []
    target_members = []
    page_size = 100
    group_id = resource_chat_info['type']['supergroup_id']

    page = getMembersCount(tg, group_id, page_size)

    resource_members, current_page = getMembers(tg, group_id, page_size=page_size)
    current_page += 1
    while current_page <= page:
        print(f'resource 总页数为：{page} 当前页为：{current_page}')
        temp1, current_page = getMembers(tg, group_id, current_page, page_size)
        if len(temp1) == 0:
            break
        resource_members.extend(temp1)
        current_page += 1
        time.sleep(2)

    group_id = target_chat_info['type']['supergroup_id']

    page = getMembersCount(tg, group_id, page_size)

    target_members, current_page = getMembers(tg, group_id, page_size=page_size)
    current_page += 1
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
    redis_exc = redis.Redis(connection_pool=pool)
    while current_page <= page:
        print(f'target 总页数为：{page} 当前页为：{current_page}')
        temp2, current_page = getMembers(tg, group_id, current_page, page_size)
        if len(temp2) == 0:
            break

        for tem in temp2:
            member_key_in_redis = f'member_{tem["user_id"]}'
            redis_exc.set(member_key_in_redis,json.dumps(tem))

        current_page += 1
        time.sleep(2)

    count = 0
    user_ids_five = []
    resource_members_temp = []
    total = len(resource_members)
    current_page = 1;
    page_size = 20
    page = int((total - 1) / page_size + 1)
    while current_page <= page:
        sleep_time = 3
        # 添加到目标群成员到通讯录
        print(f"正在添加：一共:{total},当前页:{current_page}")
        temp3 = getSubList(resource_members, page_size * (current_page - 1), page_size * current_page);
        userMap, user_ids_five = addUserToContact(tg, temp3)
        if len(user_ids_five) == 0:
            current_page += 1
            continue

        for user_id in user_ids_five:
            r = tg.call_method('addChatMembers', {'chat_id': target_chat_info['id'], 'user_ids': [user_id]})
            r.wait()
            time.sleep(sleep_time)
            if r.error:
                print(f'{r.error_info}')
                if r.error_info['code'] == 429:
                    sleep_time = 30
            member_key_in_redis = f'member_{user_id}'
            redis_exc.set(member_key_in_redis,json.dumps(userMap[user_id]))
        # 添加后删除联系人
        r = tg.call_method('removeContacts', {'user_ids': user_ids_five})
        r.wait()
        print(f'>>>> {r.update}')
        current_page += 1
        time.sleep(3)

    print('Done')
    tg.stop()
