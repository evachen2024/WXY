import http.client
import json
import time
import pandas as pd

# import pandas as pd

api_key = "db2e139a8670a05f3e4ca2c7c54014812d80abf118064c7a32be1920443430e9"  # update with your api_key

# 查询参数
# 定义搜索信息字典
search_info = {
    # 行业
    # "major": ["Manufacturing"],

    # 姓氏列表
    "last_name": [
        "Cao", "Tsao", "Chou", "Yan", "Yen", "Hua", "Va", "Jin", "Chin", "Kam", "Kam", "Tao", "To", "Tou", "Jiang",
        "Chiang", "Keong", "Qi", "Chi", "Chik", "Chek", "Xie", "Hsieh", "Tse", "Che", "Zou", "Tsou", "Chao", "Yu",
        "Bai", "Po", "Pak", "Shui", "Shui", "Sui", "Dou", "Tou", "Tao", "Zhang", "Chang", "Cheong", "Yun", "Wan", "Van",
        "Pan", "Poon", "Pun", "Ge", "Ko", "Kot", "Xi", "Hsi", "Hai", "Hai", "Fan", "Fan", "Peng", "Pang", "Lang", "Lu",
        "Lo", "Lou", "Ma", "Ma", "Miao", "Miao", "Mio"
    ],

    # 地点信息
    "location": [
        {"v": "Los Angeles,california,united states", "b": "city"}
    ]
}

# 最大提取数量
max_profiles = 2500

# 列表名称
list_name = "陈多多_百家姓+城市"

# 是否连续查找
continue_search = True


def search():
    conn = http.client.HTTPSConnection("wiza.co")

    payload = json.dumps({
        "filters": search_info
    })
    authorization = ("Bearer {api_key}").format(api_key=api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': authorization
    }
    conn.request("POST", "/api/prospects/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    data_str = data.decode("utf-8")
    print(f"api: /api/prospects/search")
    print(f"payload: {payload}")
    print(f"headers: {headers}")
    print(f"response: {data_str}")
    # print(f"查询结果: {data_str}")
    data_json = json.loads(data_str)
    total_account_number = data_json['data']['total']
    print(f"共查询到{total_account_number}个人")
    print(f"要创建的列表名称为: {list_name}, 每次创建列表大小为: {max_profiles}, 参数为: {search_info}")
    print(f"是否连续创建列表直至查询到所有数据: {continue_search}")
    run_script = input("请确认是否执行(输入y回车后执行)?")
    if run_script == 'y':
        if total_account_number > 0:
            print(f"共搜索到{total_account_number}个用户")
            create_list(total_account_number)
        else:
            print("未搜索到用户！！")


def create_list(total_account_number):
    print("开始创建列表")
    conn = http.client.HTTPSConnection("wiza.co")
    payload = json.dumps({
        "filters": search_info,
        "list": {
            "name": list_name,
            "max_profiles": max_profiles,
            "enrichment_level": "full"
        }
    })
    authorization = ("Bearer {api_key}").format(api_key=api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': authorization
    }
    conn.request("POST", "/api/prospects/create_prospect_list", payload, headers)
    res = conn.getresponse()
    data = res.read()
    data_str = data.decode("utf-8")
    print(f"api: /api/prospects/create_prospect_list")
    print(f"payload: {payload}")
    print(f"headers: {headers}")
    print(f"response: {data_str}")
    data_json = json.loads(data_str)
    print(f"the list id is ：{data_json['data']['id']}")
    search_account_number = max_profiles
    if total_account_number > search_account_number:
        list_id = data_json['data']['id']
        is_list_finish(list_id)
        continueSearch(list_id, total_account_number, search_account_number)


def is_list_finish(list_id):
    while True:
        try:
            conn = http.client.HTTPSConnection('wiza.co')
            authorization = ("Bearer {api_key}").format(api_key=api_key)
            payload = ''
            headers = {'Authorization': authorization}
            url = ("/api/lists/{list_id}").format(list_id=list_id)
            conn.request('GET', url, payload, headers)
            res = conn.getresponse()
            data = res.read()
            data_str = data.decode('utf-8')
            print(data_str)
            data_json = json.loads(data_str)
            list_status = data_json['data']['status']
            if list_status == 'finished':
                print(f"当前列表{list_id}已完成查找, 开始进行下次查找")
                break
            else:
                print(f"当前列表{list_id}还未查找完成，10分钟后再次检查列表状态")
                time.sleep(600)
        except Exception as e:
            print(f"请求发生异常: {e}")


#
# def get_list_contracts(list_id):
#     conn = http.client.HTTPSConnection("wiza.co")
#     authorization = ("Bearer {api_key}").format(api_key=api_key)
#     payload = ''
#     headers = {'Authorization': authorization}
#     url = ("/api/lists/{list_id}/contacts?segment=people").format(list_id=list_id)
#     conn.request("GET", url, payload, headers)
#     res = conn.getresponse()
#     data = res.read()
#     data_str = data.decode("utf-8")
#     print(f"api: {url}")
#     print(f"payload: {payload}")
#     print(f"headers: {headers}")
#     # print(f"response: {data_str}")
#     data_json = json.loads(data_str)
#     print(f"共{len(data_json['data'])}条数据")
#     df = pd.json_normalize(data_json["data"])
#     df.to_excel("contract.xlsx", index=False)


def continueSearch(list_id, total_account_number, search_account_number):
    conn = http.client.HTTPSConnection('wiza.co')
    payload = json.dumps({
        'id': list_id,
        'max_profiles': max_profiles
    })
    authorization = ("Bearer {api_key}").format(api_key=api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': authorization
    }
    conn.request('POST', '/api/prospects/continue_search', payload, headers)
    res = conn.getresponse()
    data = res.read()
    data_str = data.decode('utf-8')
    data_json = json.loads(data_str)
    print(f"api: /api/prospects/continue_search")
    print(f"payload: {payload}")
    print(f"headers: {headers}")
    print(f"response: {data_str}")
    search_account_number = search_account_number + max_profiles
    if total_account_number > search_account_number:
        list_id = data_json['data']['id']
        print(f"开始在列表{list_id}的基础上开始下一轮的查找")
        is_list_finish(list_id)
        continueSearch(list_id, total_account_number, search_account_number)
    else:
        print("查找完毕！")


# 创建列表,注意列表max_profiles为最大提取数量，
# create_list("10_28_li")
#
# 开始提取数据，需要传递上一步列表id，调用此方法才会真正消耗点数，查询与创建列表不消耗点数
# get_list_contracts("1780434")
#
# 进一步搜索
# continueSearch("1780439")

# 查询这个筛选条件的用户数量
# search()


import requests


def download_valid_contacts(api_key, list_id):
    """
    下载指定联系人列表的有效联系人数据并以列表ID命名保存到本地文件。
    
    参数:
    - api_key: API密钥，授权访问API。
    - list_id: 列表的ID，系统生成。
    """

    conn = http.client.HTTPSConnection("wiza.co")
    authorization = ("Bearer {api_key}").format(api_key=api_key)
    payload = ''
    headers = {'Authorization': authorization}
    url = ("/api/lists/{list_id}/contacts?segment=people").format(list_id=list_id)
    conn.request("GET", url, payload, headers)
    res = conn.getresponse()
    data = res.read()
    data_str = data.decode("utf-8")
    # print(data_str)
    json_data = json.loads(data_str)
    data_array = json_data["data"]
    if len(data_array) > 0:
        first_item = data_array[0]
        list_name = first_item['list_name']
        print(f"第一条内容为:" + first_item['list_name'])
        df = pd.DataFrame(data_array)
        # 将DataFrame导出为Excel文件
        df.to_excel(f"{list_name}.xlsx", index=False)
    # 使用pandas将数据转换为DataFrame
    # df = pd.DataFrame(data_array)
    # # 将DataFrame导出为Excel文件
    # df.to_excel("output.xlsx", index=False)
    # output_file = f'valid_contacts_{list_id}.csv'
    # url = f"https://wiza.co/api/lists/{list_id}/contacts.csv?segment=valid"
    # headers = {
    #     "Authorization": f"Bearer {api_key}"
    # }
    #
    # try:
    #     # 发送请求，获取CSV格式的有效联系人
    #     response = requests.get(url, headers=headers)
    #     response.raise_for_status()  # 自动抛出HTTP错误
    #
    #     # 将CSV内容写入指定文件
    #     with open(output_file, 'wb') as file:
    #         file.write(response.content)
    #     print(f"有效联系人数据已成功保存到 {output_file}")
    #
    # except requests.exceptions.HTTPError as http_err:
    #     print(f"HTTP错误: {http_err}")
    # except Exception as err:
    #     print(f"出现错误: {err}")


def is_list_finish(list_id):
    """
    检查列表状态，确保每次查找完成时触发下载操作。
    """
    while True:
        try:
            conn = http.client.HTTPSConnection('wiza.co')
            authorization = ("Bearer {api_key}").format(api_key=api_key)
            headers = {'Authorization': authorization}
            url = ("/api/lists/{list_id}").format(list_id=list_id)
            conn.request('GET', url, headers=headers)
            res = conn.getresponse()
            data = res.read()
            data_str = data.decode('utf-8')
            data_json = json.loads(data_str)
            print(f"请求结果: {data_str}")
            list_status = data_json['data']['status']

            # 当列表状态为 "finished" 时，立即调用下载功能并继续下一个搜索
            if list_status == 'finished':
                print(f"当前列表{list_id}已完成查找，开始下载有效联系人数据。")
                download_valid_contacts(api_key, list_id)  # 立即下载数据
                break  # 退出循环，避免重复检查
            else:
                print(f"当前列表{list_id}还未查找完成，10分钟后再次检查列表状态")
                time.sleep(600)
        except Exception as e:
            print(f"请求发生异常: {e}")


is_list_finish(1780439)
