import hashlib
import contextlib
import sys
import time

from request import close_browser  # 导入 close_browser 函数
from sms_request import login, checkInfo
from index import main1 as index_main1
from register_gv import main as register_main
from utils import get_date_time, get_log_header, get_window_json, get_config_file, get_message_json, get_logs_file, \
    get_json_obj_file_info, write_json_to_file, export_excel_file, export_message_excel_file
import pandas as pd
import asyncio
import traceback
import queue
import threading
from tkinter import ttk
from tkinter import filedialog, scrolledtext, messagebox
import tkinter as tk
import json
import os
import warnings
import webbrowser
from version import version_code
import http.client

warnings.filterwarnings("ignore", category=UserWarning, module='PIL')


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(stored_password_hash, provided_password):
    return stored_password_hash == hash_password(provided_password)


def openBrowse(arg1):
    webbrowser.open_new("http://154.23.179.49/#/guide")


class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.root.title("登录")

        self.on_login_success = on_login_success

        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=10, pady=160)

        self.username_label = tk.Label(self.frame, text="用户名:")
        self.username_label.grid(row=0, column=0, pady=5)
        self.username_entry = tk.Entry(self.frame)
        self.username_entry.grid(row=0, column=1, pady=5)

        self.password_label = tk.Label(self.frame, text="密码:")
        self.password_label.grid(row=1, column=0, pady=5)
        self.password_entry = tk.Entry(self.frame, show='*')
        self.password_entry.grid(row=1, column=1, pady=5)

        self.login_button = tk.Button(
            self.frame, text="登录", command=self.login)
        self.login_button.grid(row=2, columnspan=2, pady=5)

        self.message_label = tk.Label(self.frame, text="", fg="red")
        self.message_label.grid(row=3, columnspan=2, pady=5)

        # self.contract_label = tk.Label(
        #     self.frame, text="Telegram: @NIHONG666", fg="red")
        # self.contract_label.grid(row=4, columnspan=2, pady=5)

        # self.use_label = tk.Label(
        #     self.frame, text="使用说明: http://154.23.179.49/#/guide", cursor="hand2", fg="blue")
        # self.use_label.grid(row=5, columnspan=2, column=0, pady=5)
        # self.use_label.bind("<Button-1>", openBrowse)

        # self.link_button = tk.Button(
        #     self.frame, text="查看", fg="blue", command=self.openBrowse)
        # self.link_button.grid(row=5, columnspan=1, column=3,
        #                       pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user_info = login(username, password, None)
        if user_info:
            if user_info.get('code') == 200:
                user_data = user_info.get('data', None)
                if user_data is not None:
                    if 'appVersion' in user_data and user_data['appVersion'] is not None:
                        if user_data['appVersion'] > version_code:
                            result = messagebox.showerror(
                                "警告", "当前应用程序版本过低,请升级新版本")
                            if result:
                                webbrowser.open_new(user_data['appUrl'])
                                return
                    if 'token' in user_data and user_data['token'] is not None:
                        on_login_success(user_data['token'])
                else:
                    self.message_label.config(text="未知异常")
            else:
                self.message_label.config(text=user_info.get('msg'))
        else:
            self.message_label.config(text="登录异常")


# 更新后的 MainApp 类

# 更新后的 App 类


class App:
    running_groups = set()  # 存储正在运行的分组名

    def __init__(self, parent, title, main_app, group_name="", type=1):
        self.parent = parent
        self.main_app = main_app
        self.frame = tk.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.current_action = None  # 功能选择
        self.file_path = tk.StringVar()
        self.is_business_account = tk.BooleanVar(value=False)
        self.is_continuous_send = tk.BooleanVar(value=False)

        self.group_name = tk.StringVar(value=group_name)
        self.group_id = None
        self.queue = queue.Queue()
        self.title = title
        self.create_widgets(title, type)
        self.parent.after(100, self.process_queue)
        self.stop_event = threading.Event()  # 添加停止事件
        self.window_type = type

        # 为每个实例创建独立的输出重定向
        self.stop_event = threading.Event()  # 添加停止事件
        self.stdout = StdRedirector(self.log)
        self.stderr = StdRedirector(self.log)
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def create_widgets(self, title, type):
        self.frame.grid(row=0, column=0, sticky="nsew")

        self.input_label = tk.Label(self.frame, text=f"分组名:")
        self.input_label.grid(row=0, column=0, pady=5, sticky='e')

        self.input_entry = tk.Entry(
            self.frame, textvariable=self.group_name, width=50)
        self.input_entry.grid(row=0, column=1, pady=5, sticky='ew')

        if type != 3:
            self.file_label = tk.Label(self.frame, text=f"选择一个 Excel 文件:")
            self.file_label.grid(row=1, column=0, pady=5, sticky='e')

            self.file_entry = tk.Entry(
                self.frame, textvariable=self.file_path, width=50)
            self.file_entry.grid(row=1, column=1, pady=5, sticky='ew')

            self.browse_button = tk.Button(
                self.frame, text="浏览", command=self.browse_file)
            self.browse_button.grid(row=1, column=2, pady=5, sticky='w')

        if type == 1:
            self.business_account_check = tk.Checkbutton(
                self.frame, text="企业GV账户", variable=self.is_business_account)
            self.business_account_check.grid(
                row=2, columnspan=2, pady=5, sticky='ew')

        if type == 2:
            self.continuous_send_check = tk.Checkbutton(
                self.frame, text="连发模式", variable=self.is_continuous_send)
            self.continuous_send_check.grid(
                row=2, columnspan=2, pady=5, sticky='ew')

        # 控制按钮Frame
        self.control_frame = tk.Frame(self.frame)
        self.control_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.add_app_button = tk.Button(
            self.control_frame, text="新建窗口", command=self.main_app.add_app)
        self.add_app_button.pack(side=tk.LEFT, padx=5)

        if type != 3:
            self.start_button = tk.Button(
                self.control_frame, text="开始", command=self.start)
            self.start_button.pack(side=tk.LEFT, padx=5)
        else:
            self.start_button = tk.Button(
                self.control_frame, text="查看", command=self.start)
            self.start_button.pack(side=tk.LEFT, padx=5)

        if type != 3:
            self.stop_button = tk.Button(
                self.control_frame, text="结束", command=self.end)
            self.stop_button.pack(side=tk.LEFT, padx=5)

        if type != 2:
            self.export_button = tk.Button(
                self.control_frame, text="导出", command=self.export)
            self.export_button.pack(side=tk.LEFT, padx=5)
        else:
            self.export_button = tk.Button(
                self.control_frame, text="导出", command=self.export_message)
            self.export_button.pack(side=tk.LEFT, padx=5)

        self.tab_control = ttk.Notebook(self.frame)
        if type != 3:
            self.log_tab = tk.Frame(self.tab_control)
        self.file_content_tab = tk.Frame(self.tab_control)

        if type != 3:
            self.tab_control.add(self.log_tab, text='日志')
        self.tab_control.add(self.file_content_tab, text='信息')

        self.tab_control.grid(row=4, column=0, columnspan=3, sticky="nsew")

        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        if type != 3:
            self.log_tab.grid_rowconfigure(0, weight=1)
            self.log_tab.grid_columnconfigure(0, weight=1)

        self.file_content_tab.grid_rowconfigure(0, weight=1)
        self.file_content_tab.grid_columnconfigure(0, weight=1)
        if type != 3:
            self.log_text = scrolledtext.ScrolledText(
                self.log_tab, wrap=tk.WORD, width=70, height=20)
            self.log_text.grid(row=0, column=0, sticky="nsew")

        self.tree = ttk.Treeview(self.file_content_tab)
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree["columns"] = ("窗口ID", "用户名", "GV号码", "成功打开",
                                "成功注册", "最近注册时间", "成功发送", "是否有未读消息", "最近发送时间")
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("窗口ID", anchor=tk.CENTER, width=80)
        self.tree.column("用户名", anchor=tk.CENTER, width=120)
        self.tree.column("GV号码", anchor=tk.CENTER, width=120)
        self.tree.column("成功打开", anchor=tk.CENTER, width=80)
        self.tree.column("成功注册", anchor=tk.CENTER, width=80)
        self.tree.column("最近注册时间", anchor=tk.CENTER, width=120)
        self.tree.column("成功发送", anchor=tk.CENTER, width=80)
        self.tree.column("是否有未读消息", anchor=tk.CENTER, width=80)
        self.tree.column("最近发送时间", anchor=tk.CENTER, width=120)
        self.tree.heading("#0", text="", anchor=tk.CENTER)
        self.tree.heading("窗口ID", text="窗口ID", anchor=tk.CENTER)
        self.tree.heading("用户名", text="用户名", anchor=tk.CENTER)
        self.tree.heading("GV号码", text="GV号码", anchor=tk.CENTER)
        self.tree.heading("成功打开", text="成功打开", anchor=tk.CENTER)
        self.tree.heading("成功注册", text="成功注册", anchor=tk.CENTER)
        self.tree.heading("最近注册时间", text="最近注册时间", anchor=tk.CENTER)
        self.tree.heading("成功发送", text="成功发送", anchor=tk.CENTER)
        self.tree.heading("是否有未读消息", text="是否有未读消息", anchor=tk.CENTER)
        self.tree.heading("最近发送时间", text="最近发送时间", anchor=tk.CENTER)

        self.file_content_tab.grid_rowconfigure(1, weight=1)
        self.file_content_tab.grid_columnconfigure(0, weight=1)

    def initWindow(self):
        root = tk.Tk()
        root.geometry("1000x600")

        def on_login_success(token):
            root.destroy()
            main_root = tk.Tk()
            main_root.geometry("1000x600")
            main_app = MainApp(main_root, token)
            main_root.mainloop()

        LoginWindow(root, on_login_success)
        # MainApp(root=root)
        root.mainloop()

    def export(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        print('导出窗口数据')
        group_name = self.group_name.get()
        if group_name in App.running_groups:
            print(f"{get_log_header()}:  警告", "该分组正在运行中！", file=self.stdout)
            messagebox.showwarning("警告", "该分组正在运行中！请等待运行结束后再导出")
            return
        export_excel_file(group_name, log_file=self.stdout)
        current_directory = os.getcwd()
        output_file_path = os.path.join(current_directory, f'{group_name}.xlsx')
        messagebox.showwarning("警告", f"{group_name}分组excel成功，请去{output_file_path}路径下查看")

    def export_message(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        print('导出消息数据')
        group_name = self.group_name.get()
        if group_name in App.running_groups:
            print(f"{get_log_header()}:  警告", "该分组正在运行中！", file=self.stdout)
            messagebox.showwarning("警告", "该分组正在运行中！请等待运行结束后再导出")
            return
        export_message_excel_file(group_name, log_file=self.stdout)
        current_directory = os.getcwd()
        output_file_path = os.path.join(current_directory, f'{group_name}_message.xlsx')
        messagebox.showwarning("警告", f"{group_name}分组excel成功，请去{output_file_path}路径下查看")

    def start(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

        if not checkInfo(self.main_app.token):
            result = messagebox.showerror("警告", "登录状态已过期，请重新登录！")
            if result:
                self.main_app.root.destroy()
            return

        group_name = self.group_name.get()
        if group_name in App.running_groups:
            print(f"{get_log_header()}:  警告", "该分组正在运行中！", file=self.stdout)
            messagebox.showwarning("警告", "该分组正在运行中！")
            return

        self.stop_event.clear()
        current_page_name = self.main_app.get_current_page_name()
        # self.update_tab_text(group_name)  # 更新子标签的文本
        # 获取当前选中的标签页并更新标签名
        # main_app.update_current_tab_text("group_name")
        # self.update_tab_text(group_name)  # 更新子标签的文本
        # 获取页面实例
        print(
            f'配置信息:版本:{version_code}, 发送最大失败次数:{self.main_app.max_send_failed_count}, 发送最大发送短信数量:{self.main_app.max_send_success_count},注册最大失败次数:{self.main_app.max_reg_failed_count},短信平台apiKey:{self.main_app.sms_api_key},内核版本:{self.main_app.core_version}')
        if current_page_name == '注册':
            print(f'{get_log_header()}:  执行注册', file=self.stdout)
            self.run_register()
            self.history()
        elif current_page_name == '发送信息':
            print(f'{get_log_header()}:  执行发送信息', file=self.stdout)
            self.run_send()
            self.history()
        elif current_page_name == '历史记录':
            print(f'{get_log_header()}:  执行历史记录', file=self.stdout)
            self.history()
            # self.showLog()
        else:
            print(f'{get_log_header()}:  执行出现问题', file=self.stdout)

    def history(self):
        group_name = self.group_name.get()
        if not group_name:
            print(f"{get_log_header()}:  警告", "分组名不能为空!")
            messagebox.showwarning("警告", "分组名不能为空!")
            return

        file_path = get_window_json(group_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.show_history(data)
            except Exception as e:
                print(f"{get_log_header()}:  读取文件时出错: {e}")
                messagebox.showwarning(f"读取文件时出错: {e}")
        else:
            print(f"{get_log_header()}:  警告", "未找到该分组的历史记录文件！")

    def showLog(self):
        group_name = self.group_name.get()
        if not group_name:
            print(f"{get_log_header()}:  警告", "分组名不能为空!")
            messagebox.showwarning("警告", "分组名不能为空!")
            return

        file_path = get_logs_file(group_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    self.log_text.configure(state='normal')
                    self.log_text.delete('1.0', tk.END)  # 清空Text组件中的现有内容
                    for line in lines:
                        self.log_text.insert(tk.END, line)
                        self.log_text.yview(tk.END)  # 自动滚动到最后一行
                    self.log_text.configure(state='disabled')
            except Exception as e:
                print(f"{get_log_header()}:  读取文件时出错: {e}")
                messagebox.showwarning(f"读取文件时出错: {e}")
        else:
            print(f"{get_log_header()}:  警告", "未找到该分组的历史记录文件！")
            messagebox.showwarning("警告", "未找到该分组的历史记录文件！")

    def show_history(self, data):
        self.tree.delete(*self.tree.get_children())

        def insert_data(parent, data):
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"{get_log_header()}:  是json对象,key:{key},value:{value}")
                    # node = self.tree.insert(
                    #     parent, 'end', text=key, values=(key, ''))
                    # insert_data(node, value)
            elif isinstance(data, list):
                for index, value in enumerate(data):
                    self.tree.insert(parent, index=index, text="", values=(
                        value.get('seq'), value.get('userName'), value.get('gvNumber', None),
                        value.get('isOpenSuccess'),
                        value.get('isRegisterSuccess'), value.get('registerActionTime'), value.get('sendSuccess'),
                        value.get('hasUnreadMsg'), value.get('sendActionTime')))
                    # node = self.tree.insert(parent, 'end', text=str(
                    #     index), values=(str(index), ''))
                    # insert_data(node, value)
            else:
                self.tree.insert(parent, 'end', text='', values=('', data))

        insert_data('', data)

    def end(self):
        if not self.stop_event.is_set():
            print(f"{get_log_header()}:  警告",
                  "用户点击结束按钮，等待程序运行结束!", file=self.stdout)
            self.reset_btn()

    def reset_btn(self):
        self.stop_event.set()  # 设置停止事件
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        group_name = self.group_name.get()
        App.running_groups.discard(group_name)
        self.start_button.config(state=tk.NORMAL)  # 重新启用运行按钮
        if self.window_type != 2:
            self.export_button.config(state=tk.NORMAL)

    def close_browser_with_title(self, title):
        print(f'{get_log_header()}:  get id to close', file=self.stdout)
        try:
            with open(get_window_json(title), 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    latest_entry = next((entry for entry in reversed(
                        data) if entry.get("name") == title), None)
                    if latest_entry:
                        id = latest_entry.get("id")
                        if id:
                            close_browser(id)
        except Exception as e:
            self.log(f"关闭浏览器时出错: {str(e)}\n", file=self.stderr)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx")])
        self.file_path.set(file_path)
        # if file_path:
        #     try:
        #         df = pd.read_excel(file_path)
        #         content = df.to_string(index=False)  # 将 DataFrame 转换为字符串
        #         self.file_text.delete(1.0, tk.END)
        #         self.file_text.insert(tk.INSERT, content)
        #     except Exception as e:
        #         print(f"{get_date_time()}:  读取文件时出错: {e}", file=self.stderr)
        #         messagebox.showwarning(f"读取文件时出错: {e}")

    def validate_excel_format(self, file_path, required):
        try:
            user_df = pd.read_excel(file_path)
            user_columns = [col.strip().lower() for col in user_df.columns]
            required_columns = [col.strip().lower() for col in required]
            is_contain = True
            for column in required_columns:
                if column not in user_columns:
                    is_contain = False
                    break
            return is_contain
        except Exception as e:
            print(
                f"{get_log_header()}:  Error validating Excel format: {e}", file=self.stderr)
            messagebox.showwarning(f"Error validating Excel format: {e}")
            return False

    def run_send(self):
        print(f'{get_log_header()}:  3')
        group_name = self.group_name.get()
        file_path = self.file_path.get()
        if not group_name:
            print(f"{get_log_header()}:  警告: 分组名不能为空!", file=self.stderr)
            messagebox.showwarning("警告: 分组名不能为空!")
            return
        if not file_path:
            print(f"{get_log_header()}:  警告: 请先选择一个文件!", file=self.stderr)
            messagebox.showwarning("警告: 请先选择一个文件!")
            return
        required_headers = ["号码", "内容"]
        if not self.validate_excel_format(file_path, required_headers):
            print(f"{get_log_header()}:  警告: 发送消息的Excel文件格式不正确!", file=self.stderr)
            # messagebox.showwarning("警告: 发送消息的Excel文件格式不正确!")
            return
        is_continuous_send = self.is_continuous_send.get()
        print(f'{get_log_header()}:  发送消息{group_name}, {file_path}，是否是连发模式:{is_continuous_send}')
        if group_name in App.running_groups:
            messagebox.showwarning("警告", "该分组正在运行中！")
            return
        current_page_name = self.main_app.get_current_page_name()
        now_page = self.main_app.pages[current_page_name]
        now_page.update_current_sub_tab_text(group_name)
        print(f'{get_log_header()}:  分组名: {group_name}, 文件路径: {file_path}')
        App.running_groups.add(group_name)
        self.start_button.config(state=tk.DISABLED)  # 禁用运行按钮
        threading.Thread(target=self.run_index_script,
                         args=(group_name, file_path, is_continuous_send)).start()

    def run_register(self):
        group_name = self.group_name.get()
        file_path = self.file_path.get()
        if not group_name:
            print(f"{get_log_header()}:  警告: 分组名不能为空!", file=self.stdout)
            messagebox.showwarning("警告", "分组名不能为空!")
            return
        if not file_path:
            print(f"{get_log_header()}:  警告: 请先选择一个文件!", file=self.stdout)
            messagebox.showwarning("警告", "请先选择一个文件!")
            return
        if self.main_app.sms_api_key in ["", None]:
            print(
                f"{get_log_header()}:  警告: 注册功能需配置短信平台Api key!请去设置页面配置!", file=self.stdout)
            messagebox.showwarning("警告", "注册功能需配置短信平台Api key!请去设置页面配置!")
            return

        is_bussiness_account = self.is_business_account.get()
        if is_bussiness_account:
            required_headers = ["账号", "密码", "socks5"]
        else:
            required_headers = ["账号", "密码", "辅助邮箱", "socks5"]
        if not self.validate_excel_format(file_path, required_headers):
            print(f"{get_log_header()}:  警告: 注册的Excel文件格式不正确!", file=self.stdout)
            messagebox.showwarning("警告", "注册的Excel文件格式不正确!")
            return
        print(f'{get_log_header()}:  注册{group_name}, {file_path}  是否是企业账号:{is_bussiness_account}')
        if group_name in App.running_groups:
            messagebox.showwarning("警告", "该分组正在运行中！")
            return
        current_page_name = self.main_app.get_current_page_name()
        now_page = self.main_app.pages[current_page_name]
        now_page.update_current_sub_tab_text(group_name)
        print(f'{get_log_header()}:  分组名: {group_name}, 文件路径: {file_path}')
        App.running_groups.add(group_name)
        self.start_button.config(state=tk.DISABLED)  # 禁用运行按钮
        self.export_button.configure(state=tk.DISABLED)
        threading.Thread(target=self.run_register_script,
                         args=(group_name, file_path, is_bussiness_account)).start()

    def update_tab_text(self, new_text):
        current_tab = self.tab_control.select()
        if current_tab:
            self.tab_control.tab(current_tab, text=new_text)

    # def run_index_script(self, group_name, file_path):
    #     with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stderr):
    #         try:
    #             asyncio.run(index_main1(group_name, file_path, self.stop_event))
    #         except Exception as e:
    #             print(f"{get_date_time()}:  运行发送信息脚本时出错: {e}", file=self.stderr)
    #             # messagebox.showwarning(f"运行发送信息脚本时出错: {e}")
    def run_index_script(self, group_name, file_path, is_continuous_send):
        thread = threading.Thread(
            target=self._run_index_script_thread, args=(group_name, file_path, is_continuous_send))
        thread.start()

    def _run_index_script_thread(self, group_name, file_path, is_continuous_send):
        # 在子线程中设置输出重定向
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stderr):
            try:
                asyncio.run(index_main1(group_name, file_path,
                                        self.stop_event, is_continuous_send, self.main_app.max_send_success_count,
                                        self.main_app.max_send_failed_count, self.main_app.sms_api_key,
                                        logFile=self.stderr))  # 直接调用 main 函数
                self.reset_btn()
                print(f"{get_log_header()}:  运行发送信息已结束！！！", file=self.stderr)
            except Exception as e:
                print(f"{get_log_header()}:  运行发送已退出！！！ 运行发送信息脚本时出错: {e}", file=self.stderr)
                self.reset_btn()

    def run_register_script(self, group_name, file_path, is_bussiness_account):
        thread = threading.Thread(
            target=self._run_register_script_thread, args=(group_name, file_path, is_bussiness_account))
        thread.start()

    def _run_register_script_thread(self, group_name, file_path, is_bussiness_account):
        # 在子线程中设置输出重定向
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stderr):
            try:
                asyncio.run(register_main(group_name, file_path,
                                          self.stop_event, is_bussiness_account, self.main_app.max_reg_failed_count,
                                          self.main_app.sms_api_key, self.main_app.core_version, logFile=self.stderr))
                self.reset_btn()
                print(f"{get_log_header()}:  运行注册已结束！！！", file=self.stderr)
            except Exception as e:
                print(f"{get_log_header()}:  运行注册已退出！！！ 运行注册脚本时出错: {e}", file=self.stderr)
                self.reset_btn()

    def process_queue(self):
        while not self.queue.empty():
            message = self.queue.get_nowait()
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.INSERT, message)
            self.log_text.yview(tk.END)  # 自动滚动到最后一行
            self.log_text.configure(state='disabled')
        self.parent.after(100, self.process_queue)

    def log(self, message):
        self.queue.put(message)
        with open(f'{get_logs_file(self.group_name.get())}', 'a', encoding='utf-8') as log_file:
            log_file.write(message)


class StdRedirector:
    def __init__(self, log_func):
        self.log_func = log_func

    def write(self, message):
        self.log_func(message)

    def flush(self):
        pass


class MainApp:
    def __init__(self, root, token):
        self.root = root
        self.root.title("Wiza")
        self.token = token
        self.file_path = tk.StringVar()
        self.api_key = tk.StringVar()
        self.group_name = tk.StringVar()
        self.max_num = tk.StringVar()
        self.fetched_num = tk.StringVar()

        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=10, pady=10)
        self.queue = queue.Queue()
        self.root.after(100, self.process_queue)
        self.stop_event = threading.Event()  # 添加停止事件
        self.stdout = StdRedirector(self.log)
        self.stderr = StdRedirector(self.log)
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        self.frame.grid_rowconfigure(6, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        self.api_key_label = tk.Label(self.frame, text="请输入ApiKey:")
        self.api_key_label.grid(row=0, column=0, pady=5)
        self.api_key_entry = tk.Entry(self.frame, textvariable=self.api_key)
        self.api_key_entry.grid(row=0, column=1, pady=5, sticky='ew')

        self.group_name_label = tk.Label(self.frame, text="请输入分组名:")
        self.group_name_label.grid(row=1, column=0, pady=5)
        self.group_name_entry = tk.Entry(self.frame, textvariable=self.group_name)
        self.group_name_entry.grid(row=1, column=1, pady=5, sticky='ew')

        self.fetch_num_label = tk.Label(self.frame, text="请输入最大提取数量(不超过2500):")
        self.fetch_num_label.grid(row=2, column=0, pady=5)
        self.fetch_num_entry = tk.Entry(self.frame, textvariable=self.max_num)
        self.fetch_num_entry.grid(row=2, column=1, pady=5, sticky='ew')

        self.file_label = tk.Label(self.frame, text=f"请选择筛选条件Json文件:")
        self.file_label.grid(row=3, column=0, pady=5, sticky='e')

        self.file_entry = tk.Entry(
            self.frame, textvariable=self.file_path, width=50)
        self.file_entry.grid(row=3, column=1, pady=5, sticky='ew')

        self.browse_button = tk.Button(
            self.frame, text="浏览", command=self.browse_excel_file)
        self.browse_button.grid(row=3, column=2, pady=5, sticky='w')

        self.fetch_num_button = tk.Button(
            self.frame, text="获取数量", command=self.action1)
        self.fetch_num_button.grid(row=4, column=0, pady=5)

        self.create_list_button = tk.Button(
            self.frame, text="创建列表", command=self.action2)
        self.create_list_button.grid(row=4, column=1, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, width=100, height=50, pady=10)
        self.log_text.grid(row=6, columnspan=2, sticky="nsew")

    def process_queue(self):
        while not self.queue.empty():
            message = self.queue.get_nowait()
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.INSERT, message)
            self.log_text.yview(tk.END)  # 自动滚动到最后一行
            self.log_text.configure(state='disabled')
        self.frame.after(100, self.process_queue)

    def log(self, message):
        self.queue.put(message)
        with open(f'{get_logs_file(self.group_name.get())}', 'a', encoding='utf-8') as log_file:
            log_file.write(message)

    def action1(self):
        self.fetch(1)

    def action2(self):
        self.fetch(2)

    def fetch(self, fetch_type):
        api_key = self.api_key.get()
        if not api_key:
            messagebox.showwarning("警告", "请输入apikey")
            print(f"{get_log_header()}:  警告: 请输入apikey", file=self.stderr)
            return
        group_name = self.group_name.get()
        if not group_name:
            messagebox.showwarning("警告", "请输入分组名称")
            print(f"{get_log_header()}:  警告: 请输入分组名称", file=self.stderr)
            return
        max_num = self.max_num.get()
        if not max_num:
            messagebox.showwarning("警告", "请输入最大提取数量")
            print(f"{get_log_header()}:  警告: 请输入最大提取数量", file=self.stderr)
            return
        elif not max_num.isdigit():
            messagebox.showwarning("警告", "最大提取数量仅支持数字")
            print(f"{get_log_header()}:  警告: 最大提取数量仅支持数字", file=self.stderr)
            return
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showwarning("警告", "请输入筛选条件Json文件")
            print(f"{get_log_header()}:  警告: 请输入筛选条件Json文件", file=self.stderr)
            return

        print(file_path)
        filter_json_info = get_json_obj_file_info(file_path, None)
        result = messagebox.askokcancel("警告",
                                        f"apiKey: {api_key}  \n\n分组名: {group_name}  \n\n最大提取数量: {max_num}  \n\n筛选条件json文件路径: {file_path} \n\n是否确定继续操作?")
        print(
            f"{get_log_header()}:  执行操作：apiKey: {api_key} 分组名: {group_name} 最大提取数量: {max_num} 筛选条件json文件路径: {file_path}",
            file=self.stderr)
        if result:
            if fetch_type == 1:
                print(f"{get_log_header()}:  开始获取数量。。。", file=self.stderr)
                thread = threading.Thread(
                    target=self.fetch_number, args=(api_key, filter_json_info))
                thread.start()
            elif fetch_type == 2:
                print(f"{get_log_header()}:  开始创建列表。。。", file=self.stderr)
                thread = threading.Thread(
                    target=self.create_list, args=(api_key, filter_json_info, group_name, int(max_num)))
                thread.start()
        else:
            print(f"{get_log_header()}:  用户取消请求！！", file=self.stderr)

    def browse_excel_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.json")])
        self.file_path.set(file_path)

    def create_list(self, api_key, filter_json, group_name, max_num):
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stderr):
            user_number = self.fetch_number(api_key, filter_json)
            if user_number > 0:
                self.create_list2(user_number, api_key, filter_json, group_name, max_num)

    def create_list2(self, total_account_number, api_key, search_info, list_name, max_profiles):
        try:
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
            conn.request("POST", "/api/prospects/create_prospect_list",
                         payload, headers)
            res = conn.getresponse()
            data = res.read()
            data_str = data.decode("utf-8")
            print(f"{get_log_header()} api: /api/prospects/create_prospect_list", file=self.stderr)
            # print(f"{get_log_header()} payload: {payload}", file=self.stderr)
            print(f"{get_log_header()} headers: {headers}", file=self.stderr)
            print(f"{get_log_header()} response: {data_str}", file=self.stderr)
            data_json = json.loads(data_str)
            print(f"{get_log_header()} the list id is ：{data_json['data']['id']}", file=self.stderr)
            search_account_number = max_profiles
            if total_account_number > search_account_number:
                list_id = data_json['data']['id']
                self.is_list_finish(list_id, api_key)
                self.continueSearch(list_id, api_key, max_profiles, total_account_number, search_account_number)
        except Exception as e:
            print(f"{get_log_header()} 创建列表发生异常: {e}", file=self.stderr)

    def is_list_finish(self, list_id, api_key):
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
                print(f"{get_log_header()} response: {data_str}", file=self.stderr)
                data_json = json.loads(data_str)
                list_status = data_json['data']['status']
                if list_status == 'finished':
                    print(f"{get_log_header()} 当前列表{list_id}已完成查找, 开始导出excel", file=self.stderr)
                    self.download_valid_contacts(api_key, list_id)
                    print(f"{get_log_header()} 当前列表{list_id}已完成, 开始进行下次查找", file=self.stderr)
                    break
                else:
                    print(f"{get_log_header()} 当前列表{list_id}还未查找完成，5分钟后再次检查列表状态", file=self.stderr)
                    time.sleep(300)
            except Exception as e:
                print(f"{get_log_header()} 请求发生异常: {e}", file=self.stderr)

    def download_valid_contacts(self, api_key, list_id):
        """
        下载指定联系人列表的有效联系人数据并以列表ID命名保存到本地文件。

        参数:
        - api_key: API密钥，授权访问API。
        - list_id: 列表的ID，系统生成。
        """
        try:
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
                df = pd.DataFrame(data_array)
                # 将DataFrame导出为Excel文件
                df.to_excel(f"{list_name}.xlsx", index=False)
                current_directory = os.getcwd()
                output_file_path = os.path.join(current_directory, f'{list_name}.xlsx')
                print(f"{get_log_header()}  列表{list_name}信息导出excel成功，请去{output_file_path}路径下查看")
        except Exception as e:
            print(f"{get_log_header()}  列表{list_id}信息导出异常")
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

    def continueSearch(self, list_id, api_key, max_profiles, total_account_number, search_account_number):
        try:
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
            print(f"{get_log_header()} api: /api/prospects/continue_search")
            # print(f"{get_log_header()} payload: {payload}", file=self.stderr)
            print(f"{get_log_header()} headers: {headers}", file=self.stderr)
            print(f"{get_log_header()} response: {data_str}", file=self.stderr)
            search_account_number = search_account_number + max_profiles
            if total_account_number > search_account_number:
                list_id = data_json['data']['id']
                print(f"{get_log_header()} 开始在列表{list_id}的基础上开始下一轮的查找", file=self.stderr)
                self.is_list_finish(list_id, api_key)
                self.continueSearch(list_id, api_key, max_profiles, total_account_number, search_account_number)
            else:
                print("查找完毕！", file=self.stderr)
        except Exception as e:
            print(f"查找发生异常,结束查找:{e}！", file=self.stderr)

    def fetch_number(self, api_key, filter_json):
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stderr):
            try:
                conn = http.client.HTTPSConnection("wiza.co")

                payload = json.dumps({
                    "filters": filter_json
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
                print(f"{get_log_header()} api: /api/prospects/search", file=self.stderr)
                # print(f"{get_log_header()} payload: {payload}", file=self.stderr)
                print(f"{get_log_header()} headers: {headers}", file=self.stderr)
                print(f"{get_log_header()} response: {data_str}", file=self.stderr)
                # print(f"{get_log_header()} 查询结果: {data_str}", file=self.stderr)
                data_json = json.loads(data_str)
                total_account_number = data_json['data']['total']
                print(f"{get_log_header()} 共查询到{total_account_number}个人", file=self.stderr)
                return total_account_number
            except Exception as e:
                print(f"{get_log_header()} 请求数量发生异常 {e}", file=self.stderr)
                return 0


def get_config(self):
    config_file_path = get_config_file()
    config_info = get_json_obj_file_info(config_file_path, None)
    self.max_send_failed_count = config_info.get('maxSendFailedCount', 3)
    self.max_send_success_count = config_info.get('maxSendSuccessCount', 3)
    self.max_reg_failed_count = config_info.get('maxRegFailedCount', 3)
    self.sms_api_key = config_info.get(
        'smsApiKey', "")
    self.core_version = config_info.get('coreVersion', '126')


def get_current_tab(self):
    return self.tab_control.select()


def get_current_page_name(self):
    return self.page_name


def update_tab_text(self, new_text):
    current_page_index = self.tab_control.index(self.current_page)
    self.tab_control.tab(current_page_index, text=new_text)  # 确保使用 text 参数


def show_register(self):
    self.show_page("注册")


def show_send_message(self):
    self.show_page("发送信息")


def show_history(self):
    self.show_page("历史记录")


def show_setting(self):
    self.show_page("设置")


def show_page(self, page_name):
    self.page_name = page_name
    if page_name not in self.pages:
        if page_name == "注册":
            self.pages[page_name] = RegisterPage(self.tab_control, self)
        elif page_name == "发送信息":
            self.pages[page_name] = SendMessagePage(self.tab_control, self)
        elif page_name == "历史记录":
            self.pages[page_name] = HistoryPage(self.tab_control, self)
        elif page_name == "设置":
            self.pages[page_name] = SettingPage(self.tab_control, self)

    if self.current_page:
        self.tab_control.forget(self.current_page)
    self.current_page = self.pages[page_name]
    self.tab_control.add(self.current_page, text=page_name.capitalize())
    self.tab_control.select(self.current_page)


def add_app(self):
    current_page = self.current_page
    if isinstance(current_page, RegisterPage):
        current_page.add_app("窗口")
    elif isinstance(current_page, SendMessagePage):
        current_page.add_app("窗口")
    elif isinstance(current_page, HistoryPage):
        current_page.add_app("窗口", opt=True)


class RegisterPage(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.app_frames = []

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill='both')

        self.add_app("注册")

    def add_app(self, title, group_name=""):
        print(
            f'{self.main_app.max_send_failed_count}---{self.main_app.max_send_success_count}---{self.main_app.max_reg_failed_count}')
        tab_frame = tk.Frame(self.tab_control)
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(0, weight=1)
        self.tab_control.add(tab_frame, text=title)  # 显示text参数
        app_frame = App(tab_frame, title, self.main_app, group_name, type=1)
        self.app_frames.append(app_frame)

    def update_current_sub_tab_text(self, new_text):
        current_tab = self.tab_control.select()
        if current_tab:
            self.tab_control.tab(current_tab, text=new_text)


class SettingPage(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        config_info = self.getConfig()
        self.max_send_failed_count = tk.StringVar(
            value=config_info.get("maxSendFailedCount", 3))
        self.max_send_success_count = tk.StringVar(
            value=config_info.get("maxSendSuccessCount", 6))
        self.max_reg_failed_count = tk.StringVar(
            value=config_info.get("maxRegFailedCount", 3))
        self.core_version = tk.StringVar(
            value=config_info.get("coreVersion", "126"))
        self.sms_api_key = tk.StringVar(value=config_info.get(
            "smsApiKey", ""))

        self.parent = parent
        self.main_app = main_app
        self.tab_frame = tk.Frame(self)
        self.tab_frame.pack(expand=1, fill='both', pady=60)
        self.tab_frame.columnconfigure(0, weight=1)
        self.tab_frame.columnconfigure(1, weight=1)
        self.input_label = tk.Label(
            self.tab_frame, text=f"发送失败最大次数:", anchor="center")
        self.input_label.grid(row=0, column=0, padx=5, pady=10, sticky="e")
        self.input_entry = tk.Entry(
            self.tab_frame, textvariable=self.max_send_failed_count)
        self.input_entry.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self.input_label = tk.Label(
            self.tab_frame, text=f"单账号最大发送短信数:", anchor="center")
        self.input_label.grid(row=1, column=0, padx=5, pady=10, sticky="e")
        self.input_entry = tk.Entry(
            self.tab_frame, textvariable=self.max_send_success_count)
        self.input_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        self.input_label = tk.Label(
            self.tab_frame, text=f"注册失败最大次数:", anchor="center")
        self.input_label.grid(row=2, column=0, padx=5, pady=10, sticky="e")
        self.input_entry = tk.Entry(
            self.tab_frame, textvariable=self.max_reg_failed_count)
        self.input_entry.grid(row=2, column=1, padx=5, pady=10, sticky="w")

        self.input_label = tk.Label(
            self.tab_frame, text=f"短信平台key:", anchor="center")
        self.input_label.grid(row=3, column=0, padx=5, pady=10, sticky="e")
        self.input_entry = tk.Entry(
            self.tab_frame, textvariable=self.sms_api_key)
        self.input_entry.grid(row=3, column=1, padx=5, pady=10, sticky="w")

        self.version_label = tk.Label(
            self.tab_frame, text=f"内核版本:", anchor="center")
        self.version_label.grid(row=4, column=0, padx=5, pady=10, sticky="e")
        self.version_entry = tk.Entry(
            self.tab_frame, textvariable=self.core_version)
        self.version_entry.grid(row=4, column=1, padx=5, pady=10, sticky="w")

        self.save_button = tk.Button(
            self.tab_frame, text="保存", command=self.saveConfig)
        self.save_button.grid(row=5, columnspan=2, pady=5)

        self.use_label = tk.Label(
            self.tab_frame, text="使用说明: http://154.23.179.49/#/guide", cursor="hand2", fg="blue")
        self.use_label.grid(row=6, columnspan=2, column=0, pady=5)
        self.use_label.bind("<Button-1>", openBrowse)

    def saveConfig(self):
        send_failed_count = self.max_send_failed_count.get()
        reg_failed_count = self.max_reg_failed_count.get()
        send_success_count = self.max_send_success_count.get()
        sms_api_key = self.sms_api_key.get()
        core_version = self.core_version.get()
        if send_failed_count in ["", None]:
            messagebox.showwarning("警告", "请输入发送失败最大次数")
            return
        if send_success_count in ["", None]:
            messagebox.showwarning("警告", "请输入单账号每天最大发送短信数量")
            return
        if reg_failed_count in ["", None]:
            messagebox.showwarning("警告", "请输入注册失败最大次数")
            return

        if core_version in ["", None]:
            messagebox.showwarning("警告", "请输入内核版本号")
            return
        # if sms_api_key in ["", None]:
        #     messagebox.showwarning("警告", "请输入短信平台api key")
        #     return
        config_info = self.getConfig()
        try:
            config_info['maxSendFailedCount'] = int(send_failed_count)
        except Exception as e:
            messagebox.showwarning("警告", "发送失败最大次数必须为数字")
            return

        try:
            config_info['maxSendSuccessCount'] = int(send_success_count)
        except Exception as e:
            messagebox.showwarning("警告", "单账号每天最大发送短信数量必须为数字")
            return

        try:
            config_info['maxRegFailedCount'] = int(reg_failed_count)
        except Exception as e:
            messagebox.showwarning("警告", "注册失败最大次数必须为数字")
            return
        config_info['smsApiKey'] = sms_api_key
        config_info['coreVersion'] = core_version
        config_file_path = get_config_file()
        write_json_to_file(config_file_path, config_info, None)
        self.main_app.max_send_failed_count = config_info['maxSendFailedCount']
        self.main_app.max_reg_failed_count = config_info['maxRegFailedCount']
        self.main_app.max_send_success_count = config_info['maxSendSuccessCount']
        self.main_app.sms_api_key = config_info['smsApiKey']
        self.main_app.core_version = config_info['coreVersion']
        messagebox.showinfo("成功", "配置文件保存成功")

    def getConfig(self):
        config_file_path = get_config_file()
        config_info = get_json_obj_file_info(config_file_path, None)
        return config_info


class SendMessagePage(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.app_frames = []

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill='both')

        self.add_app("发送短信")

    def add_app(self, title, group_name=""):
        tab_frame = tk.Frame(self.tab_control)
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(0, weight=1)
        self.tab_control.add(tab_frame, text=title)  # 显示text参数
        app_frame = App(tab_frame, title, self.main_app, group_name, type=2)
        self.app_frames.append(app_frame)

    def update_current_sub_tab_text(self, new_text):
        current_tab = self.tab_control.select()
        if current_tab:
            self.tab_control.tab(current_tab, text=new_text)


class HistoryPage(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.app_frames = []

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill='both')

        self.add_app("历史记录")

    def add_app(self, title, group_name="", ):
        tab_frame = tk.Frame(self.tab_control)
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(0, weight=1)
        self.tab_control.add(tab_frame, text=title)  # 显示text参数
        app_frame = App(tab_frame, title, self.main_app,
                        group_name=group_name, type=3)
        self.app_frames.append(app_frame)

    def update_current_sub_tab_text(self, new_text):
        current_tab = self.tab_control.select()
        if current_tab:
            self.tab_control.tab(current_tab, text=new_text)


def initialize_folders():
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

    folders = [
        "account_info",
        "message_info",
        "message_record",
        "window_info",
        "logs",  # 新增日志文件夹,
        "config"
    ]
    for folder in folders:
        path = os.path.join(app_data_dir, folder)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"{get_log_header()}:  文件夹 {path} 已创建")
        else:
            print(f"{get_log_header()}:  文件夹 {path} 已存在")
    print(f"{get_log_header()}:  初始化检查完成。")
    # with open(f'{get_logs_file("test")}', 'a', encoding='utf-8') as log_file:
    #         log_file.write("hahaha")
    # window_info = get_window_json('test5')
    # json_info = get_json_file_info(window_info, None)
    # print(f'{get_date_time()}:  window_info:{json_info}')
    # json_info[1]['code'] = "100"
    # write_json_to_file(window_info, json_info, None)
    # json_info = get_json_file_info(window_info, None)
    # print(f'{get_date_time()}:  window_info:{json_info}')


if __name__ == "__main__":
    initialize_folders()
    root = tk.Tk()
    root.geometry("1000x600")


    def on_login_success(token):
        root.destroy()
        main_root = tk.Tk()
        main_root.geometry("1000x600")
        main_app = MainApp(main_root, token)
        main_root.mainloop()


    login_window = LoginWindow(root, on_login_success)
    # MainApp(root=root)
    root.mainloop()
