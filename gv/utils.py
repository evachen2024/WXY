import os
import json
import threading
import traceback
from datetime import datetime
import openpyxl
import pandas as pd


def get_data_file(parent, group_name):
    app_name = "selenium_gui"
    # 获取系统家目录
    if os.name == 'nt':  # Windows
        home_dir = os.environ['USERPROFILE']
    else:  # macOS/Linux
        home_dir = os.environ['HOME']

    # 构造应用的数据或缓存目录
    app_data_dir = os.path.join(home_dir, "." + app_name, "data")

    # 确保目录存在
    os.makedirs(app_data_dir, exist_ok=True)
    file_path = os.path.join(app_data_dir, parent, group_name)
    return file_path


def get_window_json(group_name):
    return get_data_file('window_info', f'{group_name}.json')


def get_message_json(group_name):
    return get_data_file('message_info', f'{group_name}.json')


def get_message_record(group_name):
    return get_data_file('message_record', f'{group_name}.json')


def get_account_json(group_name):
    return get_data_file('account_info', f'{group_name}.json')


def get_logs_file(group_name):
    return get_data_file('logs', f'{group_name}.log')


def get_config_file():
    return get_data_file('config', 'config.json')


def get_date():
    now = datetime.now()
    return now.strftime("%Y-%m-%d")


def get_date_time():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def get_log_header():
    return f'{get_date_time()}:{threading.current_thread().name}'


def get_json_file_info(file_name, logFile):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    print(f'{get_log_header()}:  get_json_file_info:{file_path}')
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"{get_log_header()}:  Error parsing JSON in {file_name}: {e}", file=logFile)
            return None
    else:
        print(f"{get_log_header()}:  File {file_name} does not exist, creating it", file=logFile)
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump([], file)
            return []
        except IOError as e:
            print(f"{get_log_header()}:  Failed to create file {file_name}: {e}", file=logFile)
            return None


def get_json_obj_file_info(file_name, logFile):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    print(f'{get_log_header()}:  get_json_obj_file_info:{file_path}')
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"{get_log_header()}:  Error parsing JSON in {file_name}: {e}", file=logFile)
            return None
    else:
        print(f"{get_log_header()}:  File {file_name} does not exist, creating it", file=logFile)
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump({}, file)
            return {}
        except IOError as e:
            print(f"{get_log_header()}:  Failed to create file {file_name}: {e}", file=logFile)
            return None


def write_json_to_file(file_name, json_data, logFile):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    print(f'{get_log_header()}:  write_json_to_file:{file_path}')
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(json_data, file, ensure_ascii=False, indent=2)
        return print(f"{get_log_header()}:  File {file_name} written successfully", file=logFile)
    except IOError as e:
        return print(f"{get_log_header()}:  Failed to write to file {file_name}: {e}", file=logFile)


def get_json_from_excel(file_name, logFile):
    try:
        full_path = os.path.join(os.path.dirname(__file__), file_name)
        print(f'{get_log_header()}:  get_json_from_excel:{full_path}')
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File does not exist: {full_path}")

        workbook = openpyxl.load_workbook(full_path)
        worksheet = workbook.active
        json_data = list(worksheet.values)
        new_json_data = []
        for row in json_data:
            if not all(str(cell) == '' or cell is None for cell in row):
                new_json_data.append(row)
            # for cell in row:
            #     print(str(cell), cell is None)
        json_data = new_json_data
        if json_data and len(json_data) > 0:
            title_list = json_data[0]
            title_count = len(title_list)
            data_list = json_data[1:]
            new_json_data = []

            for element in data_list:
                if element:
                    new_json_obj = {}
                    for index in range(title_count):
                        value = element[index] if index < len(
                            element) else None
                        key = title_list[index]
                        new_key = get_key(key)
                        if new_key:
                            if new_key == "address" and value:
                                address_list = value.split(":")
                                if len(address_list) == 4:
                                    new_json_obj["host"] = address_list[0]
                                    new_json_obj["port"] = address_list[1]
                                    new_json_obj["proxyUserName"] = address_list[2]
                                    new_json_obj["proxyPassword"] = address_list[3]
                                else:
                                    new_json_obj[new_key] = value
                            else:
                                new_json_obj[new_key] = value
                    new_json_data.append(new_json_obj)
            return new_json_data
        else:
            return []
    except Exception as e:
        print(f"{get_log_header()}:  File reading failed:{e}", file=logFile)
        return []


def get_key(key_text):
    key_mapping = {
        "账号": "userName",
        "密码": "password",
        "辅助邮箱": "remark",
        "socks5": "address",
        "号码": "phone",
        "内容": "message"
    }
    return key_mapping.get(key_text, None)


def export_excel_file(group_name, log_file):
    try:
        cur_group_window_list_file = get_window_json(group_name)
        cur_group_window_info_list = get_json_file_info(
            cur_group_window_list_file, log_file)
        # 创建两个空的 DataFrame 分别用于存储成功和失败的数据
        success_df = pd.DataFrame(columns=['账号', '密码', 'socks5', '辅助邮箱', '窗口ID', 'GV号码'])
        failure_df = pd.DataFrame(columns=['账号', '密码', 'socks5', '辅助邮箱', '窗口ID', 'GV号码'])

        for item in cur_group_window_info_list:
            socks5_value = f"{item['host']}:{item['port']}:{item['proxyUserName']}:{item['proxyPassword']}"
            row_data = {
                '账号': item.get('userName', None),
                '密码': item.get('password', None),
                'socks5': socks5_value,
                '辅助邮箱': item.get('remark', None),
                '窗口ID': item.get('seq', None),
                'GV号码': item.get('gvNumber', None)
            }
            if item.get('isRegisterSuccess'):
                # 使用 concat 将新数据行添加到成功的 DataFrame
                success_df = pd.concat([success_df, pd.DataFrame([row_data])], ignore_index=True)
            else:
                # 使用 concat 将新数据行添加到失败的 DataFrame
                failure_df = pd.concat([failure_df, pd.DataFrame([row_data])], ignore_index=True)

        # 使用 openpyxl 引擎将数据写入 Excel 文件
        with pd.ExcelWriter(f'{group_name}.xlsx', engine='openpyxl') as writer:
            success_df.to_excel(writer, sheet_name='成功账号', index=False)
            failure_df.to_excel(writer, sheet_name='失败账号', index=False)

        current_directory = os.getcwd()
        output_file_path = os.path.join(current_directory, f'{group_name}.xlsx')
        print(f"{group_name}分组excel成功，请去{output_file_path}路径下查看")
    except Exception as e:
        trace = traceback.format_exc()
        print(f"{group_name}分组excel导出异常:{trace}")


def export_message_excel_file(group_name, log_file):
    try:
        cur_group_message_list_file = get_message_record(group_name)
        cur_group_message_record_list = get_json_file_info(
            cur_group_message_list_file, log_file)
        print("export_message_excel_file", cur_group_message_record_list)
        # 创建两个空的 DataFrame 分别用于存储成功和失败的数据
        # "号码", "内容"
        success_df = pd.DataFrame(columns=['号码', '内容'])
        failure_df = pd.DataFrame(columns=['号码', '内容'])
        unsend_df = pd.DataFrame(columns=['号码', '内容'])

        for item in cur_group_message_record_list:
            # socks5_value = f"{item['host']}:{item['port']}:{item['proxyUserName']}:{item['proxyPassword']}"
            row_data = {
                '号码': item.get('phone'),
                '内容': item.get('message')
            }
            if item.get('sendSuccess') == True:
                # 使用 concat 将新数据行添加到成功的 DataFrame
                success_df = pd.concat([success_df, pd.DataFrame([row_data])], ignore_index=True)
            elif item.get('sendSuccess') == False:
                # 使用 concat 将新数据行添加到失败的 DataFrame
                failure_df = pd.concat([failure_df, pd.DataFrame([row_data])], ignore_index=True)
            else:
                unsend_df = pd.concat([unsend_df, pd.DataFrame([row_data])], ignore_index=True)

        # 使用 openpyxl 引擎将数据写入 Excel 文件
        with pd.ExcelWriter(f'{group_name}.xlsx', engine='openpyxl') as writer:
            success_df.to_excel(writer, sheet_name='成功账号', index=False)
            failure_df.to_excel(writer, sheet_name='失败账号', index=False)
            unsend_df.to_excel(writer, sheet_name='未发送账号', index=False)

        current_directory = os.getcwd()
        output_file_path = os.path.join(current_directory, f'{group_name}_message.xlsx')
        print(f"{group_name}分组消息发送excel导出成功，请去{output_file_path}路径下查看")
    except Exception as e:
        print(f"{group_name}分组消息发送excel导出异常:{e}")
