import argparse
import logging
import time

from telegram.client import Telegram

import utils
from datasFunction import addUserToContact, getMembers, removeMutis, getMembersCount

logger = logging.getLogger(__name__)


def confirm(message):
    sure = input(message + ' ')
    if sure.lower() not in ['y', 'yes']:
        exit(0)


def getSubList(list, start, end):
    temp = []
    for i in range(start, end):
        temp.append(list[i])
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
        if r.update['type']['@type'] == 'chatTypeSupergroup':
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
    page_size = 50
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
        time.sleep(5)

    group_id = target_chat_info['type']['supergroup_id']
    page = getMembersCount(group_id, page_size)
    target_members, current_page = getMembers(tg, group_id, page_size=page_size)
    current_page += 1
    while current_page <= page:
        print(f'target 总页数为：{page} 当前页为：{current_page}')
        temp2, current_page = getMembers(tg, group_id, current_page, page_size)
        if len(temp2) == 0:
            break
        target_members.extend(temp2)
        current_page += 1
        time.sleep(5)
    # 去重
    resource_members.extend(target_members)
    removeMutis(resource_members)

    count = 0
    user_ids_five = []
    resource_members_temp = []
    total = len(resource_members)
    current_page = 1;
    page_size = 5
    page = int((total - 1) / page_size + 1)
    while current_page <= page:
        # 添加到目标群成员到通讯录
        userMap, user_ids = addUserToContact(tg, getSubList(resource_members, page_size * current_page,
                                                            (page_size + 1) * current_page))
        print(f"正在添加：{user_ids_five}")
        r = tg.call_method('addChatMembers', {'chat_id': target_chat_info['id'], 'user_ids': user_ids_five})
        r.wait()
        if r.error:
            print(f'{r.error_info}')
        else:
            print(f' 调用正常>>>{user_ids_five}')
        # 添加后删除联系人
        r = tg.call_method('removeContacts', {'user_ids': user_ids_five})
        r.wait()
        print(f'>>>> {r.update}')
        time.sleep(5)
    print('Done')
    tg.stop()
