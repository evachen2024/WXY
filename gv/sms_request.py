import time
import requests

from utils import get_date_time, get_log_header


def request_phone_num(sms_api_key, logFile):
    try:
        session = requests.Session()
        req_params = {
            "api_key": sms_api_key,
            "action": "getNumber",
            "service": "gf",
            "max_price": "5.5"
        }
        resp = session.get("https://daisysms.com/stubs/handler_api.php", params=req_params)
        print(
            f'{get_log_header()}: url:https://daisysms.com/stubs/handler_api.php,params:{req_params} , resp:{resp.text}',
            file=logFile)
        if resp.text:
            if 'ACCESS_NUMBER' in resp.text:
                return resp.text.split(':')
    except Exception as e:
        print(f'{get_log_header()}:  Exception occurred while getting phone number from the platform:{e}', file=logFile)


def request_google_phone_number(sms_api_key, logFile):
    try:
        session = requests.Session()
        req_params = {
            "api_key": sms_api_key,
            "action": "getNumber",
            "service": "go",
            "max_price": "5.5"
        }
        resp = session.get("https://daisysms.com/stubs/handler_api.php", params=req_params)
        print(
            f'{get_log_header()}: url:https://daisysms.com/stubs/handler_api.php, params:{req_params}, resp:{resp.text}',
            file=logFile)
        if resp.text:
            if 'ACCESS_NUMBER' in resp.text:
                return resp.text.split(':')
    except Exception as e:
        print(f'{get_log_header()}:  Exception occurred while getting phone number from the platform:{e}', file=logFile)


def get_code(id, start_time, sms_api_key, logFile):
    session = requests.Session()
    req_params = {
        "api_key": sms_api_key,
        "action": "getStatus",
        "id": id
    }
    resp = session.get("https://daisysms.com/stubs/handler_api.php", params=req_params)
    print(
        f'{get_log_header()}: url:https://daisysms.com/stubs/handler_api.php,  params:{req_params}, resp:{resp.text}',
        file=logFile)
    if resp.text:
        if 'STATUS_OK' in resp.text:
            return resp.text.split(':')[1]
        else:
            cur_time = time.time() * 1000
            if cur_time - start_time > 30000:
                return -1
            else:
                print(
                    f'{get_log_header()}:  SMS not received yet, retrying in 5 seconds', file=logFile)
                time.sleep(5)
                return get_code(id, start_time, sms_api_key, logFile)


def login(username, pwd, logFile):
    try:
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json"
        })
        data = {
            "userName": username,
            "password": pwd
        }
        response = session.request(
            "post", "http://154.23.179.49:18888/tally/user/loginByPWD", json=data)
        user_info = response.json()
        print(f"user_info:{user_info},resp:{response},data:{data}")
        return user_info
    except Exception as e:
        print(f'{get_log_header()}:  Exception occurred while getting phone number from the platform:{e}', file=logFile)
        return None


def checkInfo(token):
    try:
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "platform": "App",
            "token": token
        })
        response = session.request(
            "get", "http://154.23.179.49:18888/tally/user/info")
        user_info = response.json()
        return user_info is not None and 'code' in user_info and user_info['code'] == 200
    except Exception as e:
        return False
