import tkinter as tk
from tkinter import messagebox
from pyncm import GetCurrentSession, SetCurrentSession
from pyncm.apis.login import LoginViaCellphone
from utils import center_window  # 假设中心窗口逻辑被提取到 utils.py


class LoginWindow:
    def __init__(self, root, on_login_success, cookie_file="cookie.txt"):
        """
        登录窗口的初始化。

        :param root: 主 Tkinter 窗口
        :param on_login_success: 登录成功后的回调函数
        :param cookie_file: Cookie 存储文件路径
        """
        self.root = root
        self.on_login_success = on_login_success
        self.cookie_file = cookie_file

        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("登录")
        self.login_window.geometry("250x200")
        center_window(self.login_window, 250, 200)
        
        # 检查是否有 Cookie 并尝试登录
        if self.cookie_login():
            return
        
        self.create_widgets()

    def create_widgets(self):
        """创建登录窗口的控件。"""
        tk.Label(self.login_window, text="手机号:").grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.entry_phone = tk.Entry(self.login_window)
        self.entry_phone.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        tk.Label(self.login_window, text="密码:").grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.entry_password = tk.Entry(self.login_window, show="*")
        self.entry_password.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self.btn_login = tk.Button(self.login_window, text="登录", command=self.login)
        self.btn_login.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=10)

        self.btn_anonymous_login = tk.Button(self.login_window, text="匿名登录", command=self.anonymous_login)
        self.btn_anonymous_login.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=10)

    def login(self):
        """执行手机号和密码登录。"""
        phone = self.entry_phone.get()
        password = self.entry_password.get()
        try:
            response = LoginViaCellphone(phone=phone, password=password)
            if response['code'] == 200:
                messagebox.showinfo("成功", "登录成功")
                
                # 保存 Cookie 到文件
                self.save_cookie(GetCurrentSession().cookies.get_dict())
                
                self.login_window.destroy()
                self.on_login_success()
            else:
                messagebox.showerror("错误", f"登录失败: {response.get('message', '未知错误')}")
        except Exception as e:
            messagebox.showerror("错误", f"登录时发生错误: {e}")

    def anonymous_login(self):
        """执行匿名登录。"""
        messagebox.showinfo("提示", "已使用匿名登录")
        self.login_window.destroy()
        self.on_login_success()

    def cookie_login(self):
        """
        尝试通过存储的 Cookie 登录。
        :return: 如果成功通过 Cookie 登录返回 True，否则返回 False。
        """
        try:
            with open(self.cookie_file, "r") as file:
                cookie_string = file.read().strip()
                cookies = {item.split("=")[0]: item.split("=")[1] for item in cookie_string.split("; ")}
                
                # 设置会话的 Cookie
                session = GetCurrentSession()
                session.cookies.update(cookies)
                SetCurrentSession(session)
                
                # 测试是否登录成功
                if "__csrf" in cookies:
                    messagebox.showinfo("成功", "通过 Cookie 登录成功")
                    self.on_login_success()
                    self.login_window.destroy()
                    return True
        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("错误", f"通过 Cookie 登录失败: {e}")
        return False

    def save_cookie(self, cookies):
        """
        保存 Cookie 到文件。
        :param cookies: 字典形式的 Cookie。
        """
        cookie_string = "; ".join([f"{key}={value}" for key, value in cookies.items()])
        with open(self.cookie_file, "w") as file:
            file.write(cookie_string)
