import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

print(webdriver.__version__)

cur_time = time.time()
print(cur_time)
time.sleep(3)
duration = time.time() - cur_time
print(duration)

# # 指定WebDriver的路径
# # 替换下面的路径为你的WebDriver的实际路径
# service = Service(driver_path)
# # 初始化WebDriver
# # 如果你使用的是ChromeDriver，用webdriver.Chrome()
# # 如果你使用的是geckodriver，用webdriver.Firefox()
# driver = webdriver.Chrome(service=service)
#
# # 打开百度页面
# driver.get('https://www.baidu.com')
#
# # 在这里，你可以添加更多的代码来与页面交互
# # 例如，打印页面的标题
# print(driver.title)
#
# # 完成后，关闭浏览器
# driver.quit()
