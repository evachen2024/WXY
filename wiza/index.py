import asyncio
import json
import os
import time
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# You'll need to implement these functions or replace them with appropriate Python equivalents
from request import open_browser, get_group_list, close_browser, get_browser_list
from request import open_browser, get_group_list, close_browser, get_browser_list
from utils import get_date, get_window_json, get_date_time, get_message_json, get_logs_file, get_json_file_info, \
    write_json_to_file, get_json_from_excel, get_json_obj_file_info, get_log_header, get_message_record
from register import login_to_gv
from sendmsg import send_message


def open_window(window_id):
    open_res = open_browser({
        'id': window_id,
        'args': [],
        'loadExtensions': False,
        'extractIp': False
    })
    return open_res


def get_driver(window_info):
    driver_path = window_info['data']['driver']
    debuggerAddress = window_info['data']['http']
    # selenium 连接代码
    # selenium 连接代码
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

    service = Service(driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def update_local_info(cur_group_window_info_list, cur_group_window_list_file, logFile):
    write_json_to_file(cur_group_window_list_file,
                       cur_group_window_info_list, logFile)


async def main1(group_name, f_path, stop_event, is_continuous_send, max_success_count, max_failed_count, sms_api_key,
                logFile):
    # for i in range(30):
    #     time.sleep(10)
    #     print(f"{get_date_time()}:  发送短信分组:{group_name} 运行中",file=file)

    # print(f"{get_date_time()}:  发送短信分组:{group_name} 运行中,是否是连发:{is_continuous_send}", file=logFile)
    # return

    if stop_event.is_set():
        print(f"{get_log_header()}:  用户手动停止程序,分组名称为: {group_name}", file=logFile)
        return

    message_file_name = f_path
    print(f"{get_log_header()}:  文件名{message_file_name}", file=logFile)
    group_id = check_group_exist(group_name, logFile)
    if not group_id:
        print(f"{get_log_header()}:  分组{group_name}不存在，请检查分组输入是否正确", file=logFile)
        return

    cur_group_window_list_file = get_window_json(group_name)
    cur_group_message_list_file = get_message_record(group_name)

    browser_list_resp = get_browser_list(
        {"page": 0, "pageSize": 100, "groupId": group_id})
    if browser_list_resp and browser_list_resp['success']:
        print(
            f"{get_log_header()}:  成功获取 {group_name} 分组窗口信息，共有 {browser_list_resp['data']['totalNum']} 个窗口",
            file=logFile)
        window_list = browser_list_resp['data']['list']
        if window_list and len(window_list) > 0:
            cur_group_window_info_list = get_json_file_info(
                cur_group_window_list_file, logFile)
            for cur_window in window_list:
                if not any(item['id'] == cur_window['id'] for item in cur_group_window_info_list):
                    print(
                        f"{get_log_header()}:  Window {cur_window['seq']} does not exist in the local file record (this situation occurs when adding directly in the bit browser rather than through the script), adding this window to the local file record",
                        file=logFile)
                    cur_group_window_info_list.append(cur_window)

            write_json_to_file(cur_group_window_list_file,
                               cur_group_window_info_list, logFile)

            message_list = get_json_from_excel(message_file_name, logFile)
            if len(message_list) > 0:
                message_index = 0
                send_times = 1
                message_record = read_message_record(group_name, logFile)
                if message_record.get('messageIndex', None) and message_record.get('messageFile',
                                                                                   None) == message_file_name:
                    message_index = message_record['messageIndex']

                print(
                    f"{get_log_header()}:  开始第 {send_times} 轮发送，从第 {message_index} 条消息开始", file=logFile)
                send_result = start_send_message(stop_event, group_name, message_file_name, is_continuous_send,
                                                 cur_group_window_info_list,
                                                 message_index,
                                                 message_list, max_success_count, max_failed_count, sms_api_key,
                                                 logFile)
                update_local_info(cur_group_window_info_list,
                                  cur_group_window_list_file, logFile)
                print(
                    f"{get_log_header()}:  第 {send_times} 轮发送完成，共操作 {len(cur_group_window_info_list)} 个窗口，其中{send_result['openFailedWindowId']}等{send_result['openFailedCount']} 个窗口打开失败 ，{send_result['loginFailedWindowId']}等{send_result['loginFailedCount']} 个窗口登录失败，{send_result['sendMsgFailedWindowId']}等{send_result['sendMsgFailedCount']} 个窗口发送失败 ",
                    file=logFile)
                if len(send_result['unreadMsgWindowId']) > 0:
                    print(
                        f"{get_log_header()}:  窗口 {send_result['unreadMsgWindowId']} 有未读消息，请及时处理！",
                        file=logFile)

                while send_result['status'] != 'hasNoMoreMsg':
                    if stop_event.is_set():
                        print(f"{get_log_header()}:  用户停止程序", file=logFile)
                        break

                    time.sleep(300)

                    if stop_event.is_set():
                        print(f"{get_log_header()}:  用户停止程序", file=logFile)
                        break
                    send_times += 1
                    message_index = send_result['messageIndex'] + 1
                    print(
                        f"{get_log_header()}:  开始第 {send_times} 轮发送，从第 {message_index} 条消息开始",
                        file=logFile)
                    send_result = start_send_message(stop_event, group_name, message_file_name, is_continuous_send,
                                                     cur_group_window_info_list, message_index,
                                                     message_list, max_success_count, max_failed_count, sms_api_key,
                                                     logFile)
                    print(
                        f"{get_log_header()}:  第 {send_times} 轮发送完成，共操作 {len(cur_group_window_info_list)} 个窗口，其中{send_result['openFailedWindowId']}等{send_result['openFailedCount']} 个窗口打开失败 ，{send_result['loginFailedWindowId']}等{send_result['loginFailedCount']} 个窗口登录失败，{send_result['sendMsgFailedWindowId']}等{send_result['sendMsgFailedCount']} 个窗口发送失败 ",
                        file=logFile)
                    # print(
                    #     f"{get_log_header()}:  第 {send_times} 轮发送完成，共操作 {len(cur_group_window_info_list)} 个窗口，其中打开失败 {send_result['openFailedCount']} 个，登录失败 {send_result['loginFailedCount']} 个，发送失败 {send_result['sendMsgFailedCount']} 个",
                    #     file=logFile)
                    if len(send_result['unreadMsgWindowId']) > 0:
                        print(
                            f"{get_log_header()}:  窗口 {send_result['unreadMsgWindowId']} 有未读消息，请及时处理！",
                            file=logFile)

                update_local_info(cur_group_window_info_list,
                                  cur_group_window_list_file, logFile)
                write_json_to_file(cur_group_message_list_file, message_list, logFile)
            else:
                print(f'{get_log_header()}:  未获取到消息列表数据', file=logFile)
        else:
            print(
                f"{get_log_header()}:  {group_name} 分组下未添加任何窗口，请先添加窗口并注册", file=logFile)
    else:
        print(f"{get_log_header()}:  获取 {group_name} 分组窗口信息失败，退出！", file=logFile)
        return


def close_service():
    try:
        # In Python, we don't need to explicitly close the ChromeDriver service
        pass
    except Exception as e:
        print(e)


def start_send_message(stop_event, group_name, message_file_name, is_continuous_send, windows_list, message_index,
                       message_list,
                       max_success_count,
                       max_failed_count, sms_api_key, logFile):
    send_result = {
        'message': {},
        'messageIndex': message_index,
        'status': '',
        'window': {},
        'openFailedCount': 0,
        'openFailedWindowId': [],
        'loginFailedCount': 0,
        'loginFailedWindowId': [],
        'sendMsgFailedCount': 0,
        'sendMsgFailedWindowId': [],
        'unreadMsgWindowId': []
    }
    date_str = get_date()
    for current_window in windows_list:
        if stop_event.is_set():
            print(f"{get_log_header()}:  用户停止程序", file=logFile)
            return send_result

        if 'failedInfo' not in current_window:
            current_window['failedInfo'] = []

        seq = current_window.get('seq')

        today_failed_info = next(
            (item for item in current_window['failedInfo'] if item['date'] == date_str), None)
        if today_failed_info and today_failed_info['count'] > max_failed_count:
            print(
                f"{get_log_header()}:{seq}:  今日失败超过 {max_failed_count} 次，不再操作窗口 {seq}",
                file=logFile)
            continue

        if current_window.get('isRegisterSuccess') == False:
            print(f'{get_log_header()}:{seq}:  该窗口注册 GV 失败，跳过发送消息', file=logFile)
            continue

        if current_window.get('unreadMsgInfo'):
            unreadMsgInfo = current_window.get('unreadMsgInfo')
            if unreadMsgInfo['date'] == date_str:
                print(f"窗口{seq}在今日有过未读消息,不再进行发送")
                continue

        if current_window.get('sendSuccessInfo'):
            if current_window.get('sendSuccessInfo').get('count') >= max_success_count:
                print(
                    f"窗口{seq}在今日发送消息已达到上限{max_success_count}条,不再进行发送")
                continue
        print(
            f"{get_log_header()}:  开始操作窗口{seq}", file=logFile)
        open_res = open_window(current_window['id'])
        date_time_str = get_date_time()
        current_window['sendActionTime'] = date_time_str
        if open_res['success']:
            print(f'{get_log_header()}:{seq}:  成功打开窗口', file=logFile)
            current_window['isOpenSuccess'] = True
            driver = get_driver(open_res)

            is_success = False
            gv_num = None
            try:
                if current_window.get('isRegisterSuccess') == True:
                    print(f'{get_log_header()}:{seq}:  该窗口已成功注册 GV，直接发送消息', file=logFile)
                    driver.get('https://voice.google.com/')
                    is_success = True
                else:
                    print(
                        f'{get_log_header()}:{seq}:  该窗口尚未注册 GV，正在注册 GV 并发送消息', file=logFile)
                    driver.get('https://voice.google.com/')
                    is_success, gv_number = login_to_gv(driver, current_window.get('userName'),
                                                        current_window.get('password'),
                                                        current_window.get('isBusinessAccount'),
                                                        current_window.get('remark'),
                                                        sms_api_key,
                                                        logFile)
                    gv_num = gv_number
            except Exception as e:
                stack_trace = traceback.format_exc()
                print(f'{get_log_header()}:{seq}:  打开 GV 页面失败! strack_trace:{stack_trace}', file=logFile)
            if is_success:
                print(
                    f"{get_log_header()}:{seq}:  GV 注册成功，窗口 id: {seq}", file=logFile)
                current_window['isRegisterSuccess'] = True
                current_window['gvNumber'] = gv_num
                continuous_send = 0
                today_failed_count = 0
                today_success_count = 0
                while True:
                    if is_continuous_send:
                        if stop_event.is_set():
                            print(f"{get_log_header()}:{seq}:  用户停止程序", file=logFile)
                            return send_result
                    if len(message_list) > message_index:
                        cur_message = message_list[message_index]
                        print(f'{get_log_header()}:{seq}:  开始发送消息:{cur_message}',
                              file=logFile)
                        record_msg = {
                            'messageIndex': message_index,
                            'message': cur_message,
                            'messageFile': message_file_name
                        }
                        record_message_info(group_name, record_msg, logFile)
                        send_status = send_message(driver, seq, cur_message, logFile)
                        if send_status == 'hadUnreadMsg':
                            current_window['hasUnreadMsg'] = True
                            current_window['sendSuccess'] = False
                            current_window['unreadMsgInfo'] = {
                                'date': date_str,
                                'hasUnreadMsg': True
                            }
                            send_result['unreadMsgWindowId'].append(
                                current_window['seq'])
                        elif send_status == 'sendSuccess':
                            current_window['sendSuccess'] = True
                            current_window['hasUnreadMsg'] = False
                            cur_message['sendSuccess'] = True
                            successInfo = current_window.get('sendSuccessInfo')
                            if successInfo:
                                if successInfo.get('date') == date_str:
                                    count = successInfo.get('count')
                                    successInfo['count'] = count + 1
                                    today_success_count = count + 1
                                else:
                                    current_window['sendSuccessInfo'] = {
                                        'date': date_str,
                                        'count': 1
                                    }
                                    today_success_count = 1
                            else:
                                current_window['sendSuccessInfo'] = {
                                    'date': date_str,
                                    'count': 1
                                }
                                today_success_count = 1
                            send_result['message'] = cur_message
                            send_result['messageIndex'] = message_index
                            message_index += 1
                            if len(message_list) > message_index:
                                record_msg = {
                                    'messageIndex': message_index,
                                    'message': message_list[message_index],
                                    'messageFile': message_file_name
                                }
                            else:
                                record_msg = {
                                    'messageIndex': 0,
                                    'message': message_list[0],
                                    'messageFile': message_file_name
                                }
                            record_message_info(group_name, record_msg, logFile)
                        else:
                            current_window['sendSuccess'] = False
                            current_window['hasUnreadMsg'] = False
                            cur_message['sendSuccess'] = False
                            today_failed_info = next(
                                (item for item in current_window['failedInfo'] if item['date'] == date_str), None)
                            if today_failed_info:
                                failed_count = today_failed_info['count']
                                today_failed_info['count'] = failed_count + 1
                                today_failed_count = failed_count + 1
                            else:
                                current_window['failedInfo'].append({
                                    'date': date_str,
                                    'count': 1
                                })
                                today_failed_count = 1
                            send_result['sendMsgFailedCount'] += 1
                            send_result['sendMsgFailedWindowId'].append(seq)
                            if is_continuous_send:
                                message_index += 1
                        continuous_send = continuous_send + 1
                    else:
                        print(f'{get_log_header()}:{seq}:  所有消息已发送完毕！', file=logFile)
                        send_result['status'] = 'hasNoMoreMsg'
                        break

                    if is_continuous_send:
                        print(f"{get_log_header()}:{seq}:  当前模式为连发模式，开始第{continuous_send}条消息的发送",
                              file=logFile)
                        if current_window['hasUnreadMsg']:
                            print(f"{get_log_header()}:{seq}:  当前窗口有未读消息，退出当前账号发送", file=logFile)
                            break
                        else:
                            if current_window['sendSuccess']:
                                if today_success_count >= max_success_count:
                                    print(
                                        f"{get_log_header()}:{seq}:  当前账号连发模式发送成功消息数量{today_success_count}超出限制{max_success_count},退出当前账号的连发",
                                        file=logFile)
                                    break
                            else:
                                if today_failed_count >= max_failed_count:
                                    print(
                                        f"{get_log_header()}:{seq}:  当前账号连发模式发送失败消息数量{today_failed_count}超出限制{max_failed_count},退出当前账号的连发",
                                        file=logFile)
                                    break
                    else:
                        break
            else:
                print(
                    f"{get_log_header()}:{seq}:  GV 注册失败，窗口 id: {seq}", file=logFile)
                current_window['isRegisterSuccess'] = False
                send_result['loginFailedCount'] += 1
                send_result['loginFailedWindowId'].append(seq)

            if not current_window.get('hasUnreadMsg'):
                time.sleep(2)
                close_all_tab(driver, logFile)
                close_browser(current_window['id'])
        else:
            print(f'{get_log_header()}:{seq}:  打开窗口失败', file=logFile)
            current_window['isOpenSuccess'] = False
            send_result['openFailedCount'] += 1
            send_result['openFailedWindowId'].append(seq)

        send_result['window'] = current_window
        close_service()
        if stop_event.is_set():
            print(f'{get_log_header()}:{seq}:  用户停止程序', file=logFile)
            return send_result

    return send_result


def close_all_tab(driver, logFile):
    print(f'{get_log_header()}:  关闭所有标签页', file=logFile)
    all_handles = driver.window_handles
    for handle in reversed(all_handles[1:]):
        driver.switch_to.window(handle)
        time.sleep(1)
        driver.close()
    driver.switch_to.window(all_handles[0])


def check_group_exist(group_name, logFile):
    group_list_resp = get_group_list(0, 1000)
    if group_list_resp['success']:
        group_item = next(
            (item for item in group_list_resp['data']['list'] if item['groupName'] == group_name), None)
        if group_item:
            print(f"{get_log_header()}:  分组已存在", file=logFile)
            return group_item['id']
        else:
            print(f"{get_log_header()}:  分组不存在", file=logFile)
    else:
        print(f"{get_log_header()}:  获取分组列表失败,resp:{group_list_resp}", file=logFile)
    return None


def record_message_info(date_str, message_info, logFile):
    message_record_file_path = get_message_json(date_str)
    write_json_to_file(message_record_file_path, message_info, logFile)


def read_message_record(group_name, logFile):
    message_record_file_path = get_message_json(group_name)
    return get_json_obj_file_info(message_record_file_path, logFile)


if __name__ == "__main__":
    asyncio.run(main1())
