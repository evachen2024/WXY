import http.client
import json
import time

# import pandas as pd

api_key = "db2e139a8670a05f3e4ca2c7c54014812d80abf118064c7a32be1920443430e9"  # update with your api_key

# 查询参数
search_info = {

    # "first_name": [
    #     "jack"
    # ],
    "last_name": [
        "Chun", "Joen", "Tiền", "Chen", "Chien", "Chee", "Zee", "Chin", "Qian"
    ],
    "job_title_level": ["Director", "Manager", "Owner", "Partner", "Senior", "Training", "Unpaid",
                        "VP"],
    "location": [
        {
            "v": "united states",
            "b": "country"
        }
    ]
}

# 最大提取数量
max_profiles = 2500

# 列表名称
list_name = "11_01_Chun,Joen,Tiền,Chen,Chien,Chee,Zee,Chin,Qian"

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
                print(f"当前列表{list_id}还未查找完成，5分钟后再次检查列表状态")
                time.sleep(300)
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
search()

# is_list_finish(1780439)
