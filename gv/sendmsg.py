from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import re

# Assuming these functions are defined in a separate file named register.py
from register import get_visible_elements, get_visible_element
from utils import get_date_time,get_log_header


def send_message(driver, seq, message, logFile):
    message_nav = select_message_nav(driver, logFile)
    if message_nav:
        print(f'{get_log_header()}:{seq}:  获取消息导航按钮成功', file=logFile)
        try:
            # //*[@id="gvPageRoot"]/div[2]/gv-side-panel/mat-sidenav-container/mat-sidenav-content/div/div[2]/gv-side-nav/div/div/mat-nav-list/a[2]
            # //*[@id="gvPageRoot"]/div[2]/gv-side-panel/mat-sidenav-container/mat-sidenav-content/div/div[2]/gv-side-nav/div/div/mat-nav-list/a[2]/span/span/span[2]
            had_msg = get_visible_elements(driver, logFile, By.XPATH,
                                           '//*[@id="gvPageRoot"]/div[2]/gv-side-panel/mat-sidenav-container/mat-sidenav-content/div/div[2]/gv-side-nav/div/div/mat-nav-list/a[2]/span/span/span[2]',
                                           10000)
        except:
            had_msg = None

        if had_msg:
            print(f'{get_log_header()}:{seq}:  含有未读消息', file=logFile)
            return 'hadUnreadMsg'
        else:
            print(f'{get_log_header()}:{seq}:  不含有未读消息', file=logFile)
            try:
                loading_view = driver.find_element(By.CLASS_NAME, 'gvMessagingView-loading')
                if loading_view:
                    WebDriverWait(driver, 30).until(EC.invisibility_of_element(loading_view))
            except:
                js_code = "var overlay = document.querySelector('.gvMessagingView-loading'); if (overlay) {overlay.style.display = 'none';}"
                driver.execute_script(js_code)
                time.sleep(1)

            # //*[@id="messaging-view"]/div/md-content/div/div
            conversation_list = get_visible_element(driver, logFile, By.CLASS_NAME,
                                                    'gvMessagingView-conversationListHeader')
            if conversation_list:
                print(f'{get_log_header()}:{seq}:  开始获取新建消息按钮', file=logFile)
                add_message_btn = get_visible_element(driver, logFile, By.CLASS_NAME, 'gvMessagingView-actionButton')
                if add_message_btn:
                    print(f'{get_log_header()}:{seq}:  获取新建消息按钮成功', file=logFile)
                    time.sleep(2)
                    add_message_btn.click()
                    print(f'{get_log_header()}:{seq}:  开始获取号码输入框', file=logFile)
                    element = get_visible_element(driver, logFile, By.CLASS_NAME, 'cdk-overlay-pane')
                    if element:
                        print(f'{get_log_header()}:{seq}:  获取到了弹窗', file=logFile)
                        time.sleep(2)
                        js_code = "var overlay = document.querySelector('.cdk-overlay-pane'); if (overlay) {overlay.style.display = 'none';}"
                        driver.execute_script(js_code)
                        time.sleep(2)
                    else:
                        print(f'{get_log_header()}:{seq}:  没有获取到弹窗', file=logFile)

                    input_div = get_visible_element(driver, logFile, By.CLASS_NAME, 'input-field')
                    if input_div:
                        number_input = input_div.find_element(By.TAG_NAME, 'input')
                        if number_input:
                            print(f'{get_log_header()}:{seq}:  获取号码输入框成功', file=logFile)
                            time.sleep(1)
                            number_input.clear()
                            time.sleep(2)
                            number_input.send_keys(message['phone'])
                            number_input.send_keys(',')
                            number_input.send_keys(Keys.ESCAPE)
                            time.sleep(2)

                            try:
                                had_msg = get_visible_elements(driver, logFile, By.XPATH,
                                                               '//a[contains(@aria-label,"Messages:")]', 1000)
                                if had_msg:
                                    print(f'{get_log_header()}:{seq}:  含有未读消息', file=logFile)
                                    return 'hadUnreadMsg'
                            except:
                                pass

                            delete_icon = get_visible_elements(driver, logFile, By.CLASS_NAME, 'mat-mdc-chip-remove')
                            if delete_icon and len(delete_icon) > 0:
                                print(f'{get_log_header()}:{seq}:  开始获取内容输入框', file=logFile)
                                message_input = get_visible_element(driver, logFile, By.CLASS_NAME, 'message-input')
                                if message_input:
                                    print(f'{get_log_header()}:{seq}:  获取内容输入框成功', file=logFile)
                                    message_input.click()
                                    time.sleep(1)
                                    message_input.clear()
                                    time.sleep(1)
                                    message_input.send_keys(message['message'])
                                    time.sleep(2)
                                    print(f'{get_log_header()}:{seq}:  开始获取发送按钮', file=logFile)
                                    send_btn = get_visible_element(driver, logFile, By.XPATH,
                                                                   '//button[@aria-label="Send message"]')
                                    if send_btn:
                                        print(f'{get_log_header()}:{seq}: 开始点击发送按钮', file=logFile)
                                        send_btn.click()
                                        time.sleep(5)
                                        send_success = is_msg_send_success(driver, logFile)
                                        if send_success:
                                            print(f'{get_log_header()}:{seq}:  发送成功', file=logFile)
                                            return 'sendSuccess'
                                        else:
                                            print(f'{get_log_header()}:{seq}:  发送失败', file=logFile)
                                    else:
                                        print(f'{get_log_header()}:{seq}:  获取发送按钮失败', file=logFile)
                else:
                    print(f'{get_log_header()}:{seq}:  获取新建消息按钮失败', file=logFile)
    else:
        print(f'{get_log_header()}:{seq}:  获取消息导航按钮失败', file=logFile)


def select_message_nav(driver, logFile):
    try:
        elements = get_visible_elements(driver, logFile, By.XPATH,
                                        '//*[@id="gvPageRoot"]/div[2]/gv-side-panel/mat-sidenav-container/mat-sidenav-content/div/div[2]/gv-side-nav/div/div/mat-nav-list/a[2]')
        if elements:
            if len(elements) > 1:
                elements[1].click()
                return elements[1]
            if len(elements) == 1:
                elements[0].click()
                return elements[0]
    except Exception as e:
        print(f'{get_log_header()}:  获取消息导航按钮失败:{e}', file=logFile)


def is_msg_send_success(driver, logFile):
    try:
        elements = get_visible_elements(driver, logFile, By.CLASS_NAME, 'status')
        if elements and len(elements) > 0:
            last_element = elements[-1]
            reg_exp = re.compile(r'\b\d{1,2}:\d{2}\s+[AP]M\b')
            text = last_element.text
            if reg_exp.search(text):
                print(f'{get_log_header()}:  发送时间为:{text}', file=logFile)
                return True
    except Exception as e:
        print(f'{get_log_header()}:  isMsgSendSuccess:{e}', file=logFile)
    return False

# If you need to use these functions in other files, you can import them like this:
# from this_file_name import send_message, select_message_nav, is_msg_send_success
