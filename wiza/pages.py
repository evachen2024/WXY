
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

        self.use_label = tk.Label(
            self.frame, text="使用说明: http://154.23.179.49/#/guide", cursor="hand2", fg="blue")
        self.use_label.grid(row=5, columnspan=2, column=0, pady=5)
        self.use_label.bind("<Button-1>", openBrowse)

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

