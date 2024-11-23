import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

from utils import get_date, get_window_json, get_log_header, get_account_json, get_date_time, get_logs_file, \
    get_json_file_info, \
    write_json_to_file, get_json_from_excel, get_json_obj_file_info
from register import login_to_gv
from request import open_browser, close_browser, create_browser, get_group_list, add_group
import contextlib
import sys
import asyncio


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
    print(f'get_driver:{debuggerAddress},driver_path:{driver_path}')
    # selenium 连接代码
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

    service = Service(driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


async def main(group_name, f_path, stop_event, is_business_account, max_failed_count, sms_api_key, core_version,
               logFile):
    # for i in range(30):
    #     time.sleep(10)
    #     print(f"{get_date_time()}:  注册账号分组:{group_name} 运行中", file=file)

    # print(
    #     f"{get_date_time()}:  注册账号分组:{group_name} 运行中,is_business_account:{is_business_account},内核版本号:{core_version}",
    #     file=logFile)
    # return

    if stop_event.is_set():
        print(f"{get_log_header()}:  用户手动停止程序,分组名称为: {group_name}", file=logFile)
        return

    group_id = get_group_id_by_name(group_name, logFile)
    if not group_id:
        print(f"{get_log_header()}:  分组名称{group_name}不存在，请检查分组输入是否正确", file=logFile)
        return

    cur_group_account_list_file = get_account_json(group_name)
    cur_group_account_list = get_json_file_info(
        cur_group_account_list_file, logFile)

    new_account_excel_file = f_path
    new_account_list = get_json_from_excel(new_account_excel_file, logFile)
    for account in new_account_list:
        if not any(item['userName'] == account['userName'] for item in cur_group_account_list):
            cur_group_account_list.append(account)
    write_json_to_file(cur_group_account_list_file,
                       cur_group_account_list, logFile)
    cur_window_list_file = get_window_json(group_name)
    cur_window_info_list = get_json_file_info(cur_window_list_file, logFile)
    if new_account_list:
        for i, account_info in enumerate(new_account_list):
            print(f'{get_log_header()}:  index:{i}', file=logFile)
            if not any(item['userName'] == account_info['userName'] and item['password'] == account_info['password'] for
                       item in cur_window_info_list):
                window_info_params = generate_window_info(group_id, "https://accounts.google.com/", "gmail",
                                                          f"{group_name}-{i}",
                                                          account_info['userName'], account_info['password'],
                                                          account_info.get('remark'),
                                                          2, "socks5", account_info['host'], account_info['port'],
                                                          account_info['proxyUserName'],
                                                          account_info['proxyPassword'],
                                                          core_version)
                res = create_browser(window_info_params)
                if res['success']:
                    print(
                        f"{get_log_header()}:  添加窗口成功！{window_info_params['userName']}", file=logFile)
                    window_info = {
                        'id': res['data']['id'],
                        'seq': res['data']['seq'],
                        'code': res['data']['code'],
                        'groupId': res['data']['groupId'],
                        'platform': res['data']['platform'],
                        'platformIcon': res['data']['platformIcon'],
                        'name': res['data']['name'],
                        'userName': res['data']['userName'],
                        'password': res['data']['password'],
                        'proxyMethod': res['data']['proxyMethod'],
                        'proxyType': res['data']['proxyType'],
                        'host': res['data']['host'],
                        'port': res['data']['port'],
                        'proxyUserName': res['data']['proxyUserName'],
                        'proxyPassword': res['data']['proxyPassword'],
                        'remark': res['data'].get('remark') or '',
                        'isBusinessAccount': is_business_account
                    }
                    cur_window_info_list.append(window_info)
                else:
                    print(
                        f"{get_log_header()}:  添加窗口失败！{window_info_params['userName']},res:{res}", file=logFile)

        write_json_to_file(cur_window_list_file, cur_window_info_list, logFile)

    date = get_date()

    for current_window in cur_window_info_list:

        if stop_event.is_set():
            print(f"{get_log_header()}:  用户停止程序", file=logFile)
            return

        if current_window.get('isRegisterSuccess'):
            print(f"窗口{current_window['seq']}已注册成功，跳过")
            continue

        if 'registerFailedInfo' not in current_window:
            current_window['registerFailedInfo'] = []

        today_failed_info = next(
            (item for item in current_window['registerFailedInfo'] if item['date'] == date), None)
        if today_failed_info and today_failed_info['count'] > max_failed_count:
            print(
                f"{get_log_header()}:  今日注册失败次数超过{max_failed_count}次,不再操作窗口{current_window['seq']}",
                file=logFile)
            continue

        print(
            f"{get_log_header()}:  开始操作窗口{current_window['seq']},{current_window}", file=logFile)
        open_res = open_window(current_window['id'])
        date_time_str = get_date_time()
        current_window['registerActionTime'] = date_time_str
        driver = None
        if open_res['success']:
            print(f'{get_log_header()}:  打开窗口成功:{open_res}', file=logFile)
            current_window['isOpenSuccess'] = True
            try:
                if open_res.get('data'):
                    if open_res.get('data').get('driver') in ["", None]:
                        print(f'{get_log_header()}:  chromedriver路径不存在，请检查内核版本号配置是否正确！！！',
                              file=logFile)
                    else:
                        driver = get_driver(open_res)
                        driver.get('https://voice.google.com/')
                        is_success, gv_number = login_to_gv(
                            driver, current_window['userName'], current_window['password'],
                            current_window['isBusinessAccount'],
                            current_window['remark'], sms_api_key, logFile)
                        if is_success:
                            print(
                                f"{get_log_header()}:  gv注册成功,窗口id: {current_window['seq']}", file=logFile)
                            current_window['isRegisterSuccess'] = True
                            current_window['gvNumber'] = gv_number
                        else:
                            print(
                                f"{get_log_header()}:  gv注册失败,窗口id: {current_window['seq']}", file=logFile)
                            current_window['isRegisterSuccess'] = False
                            if today_failed_info:
                                today_failed_info['count'] += 1
                            else:
                                current_window['registerFailedInfo'].append(
                                    {'date': date, 'count': 1})
                        close_all_tabs(driver)
            except Exception as e:
                print(f'{get_log_header()}:  打开gv页面失败，检查代理是否配置正确:{e}', file=logFile)
                if today_failed_info:
                    today_failed_info['count'] += 1
                else:
                    current_window['registerFailedInfo'].append(
                        {'date': date, 'count': 1})
        else:
            print(f'{get_log_header()}:  打开窗口失败', file=logFile)
            current_window['isOpenSuccess'] = False
            if today_failed_info:
                today_failed_info['count'] += 1
            else:
                current_window['registerFailedInfo'].append(
                    {'date': date, 'count': 1})

        write_json_to_file(cur_window_list_file, cur_window_info_list, logFile)
        time.sleep(2)

        try:
            if driver:
                driver.quit()
            time.sleep(2)
            if not current_window.get('hasUnreadMsg'):
                close_browser(current_window['id'])
        except Exception as e:
            print(f'{get_log_header()}:  关闭窗口失败,exception:{e}', file=logFile)

        if stop_event.is_set():
            print(f"{get_log_header()}:  用户停止程序", file=logFile)
            return


def close_all_tabs(driver):
    all_handles = driver.window_handles
    for handle in all_handles:
        driver.switch_to.window(handle)
        time.sleep(1)
        driver.close()


def get_group_id_by_name(group_name, file):
    group_list_resp = get_group_list(0, 100)
    if group_list_resp['success']:
        group_item = next(
            (item for item in group_list_resp['data']['list'] if item['groupName'] == group_name), None)
        if group_item:
            print(f"{get_log_header()}:  已存在分组", file=file)
            return group_item['id']
        else:
            print(f'{get_log_header()}:  开始添加分组,分组名称为: {group_name}', file=file)
            add_group_resp = add_group(group_name, 0)
            if add_group_resp['success']:
                print(f"{get_log_header()}:  添加分组成功", file=file)
                return add_group_resp['data']['id']
            else:
                print(f"{get_log_header()}:  添加分组失败,resp:{add_group_resp}", file=file)
    else:
        print(f"{get_log_header()}:  获取分组列表失败,resp:{group_list_resp}", file=file)


def generate_window_info(group_id, platform, platform_icon, name, user_name, password, remark, proxy_method, proxy_type,
                         host, port, proxy_user_name, proxy_password, core_version):
    return {
        'groupId': group_id,
        'platform': platform,
        'platformIcon': platform_icon,
        'name': name,
        'userName': user_name,
        'password': password,
        'remark': remark,
        'proxyMethod': proxy_method,
        'proxyType': proxy_type,
        'host': host,
        'port': port,
        'proxyUserName': proxy_user_name,
        'proxyPassword': proxy_password,
        'browserFingerPrint': {
            'coreVersion': core_version
        },
    }


if __name__ == "__main__":
    main()
