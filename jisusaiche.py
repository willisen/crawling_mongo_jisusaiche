__author__ = "zhong"
__date__ = "2019/6/22 0022 下午 19:03"

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import pymongo
import lxml, json

myclient = pymongo.MongoClient('mongodb://localhost:27017/')
mydb = myclient['jisusaichedb']
mycol = mydb['201901']

#增加
def save_to_mongo(result):
    '''
    :param result: 要保存的数据
    :return: 是否成功
    '''
    try:
        if mycol.insert_one(result):
            print('储存到MongoDB成功')
    except Exception:
        print('储存到MongoDB失败')

#删除
def dele_mongo(result):
    '''
    :param result: 必须要与存储时的值一样，存储时：{'2':[123456789]}，删除时：{'2':[123456789]}
    :return:
    '''
    try:
        if mycol.delete_one(result):
            print('删除成功')
    except Exception:
        print('删除失败')

'''
网址
https://www.1681380.com
https://www.1681380.com/view/PK10/pk10kai.html   pk10
https://www.1681380.com/view/PK10/pk10kai_history.html
'''

driver = webdriver.Chrome("chromedriver")
wait = WebDriverWait(driver, 3)

# 把元素的selector存在字典中
dict_selector = {'开奖历史': '#kjls > a', '选择日期': '#dateframe > input',
                 '上个月': 'prev',
                 '下个月': 'next',
                 '获取日期': 'calendar-display',
                 '点击日期': 'date'
                 }


def judge_element_visible(name_str):
    '''
    判断元素是否可见
    :param name_str: CSS_SELECTOR
    :return: 真或者假
    '''
    try:
        day_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, name_str)))
        return True
    except:
        return False


def get_date():
    '''
    历史的一页#datebox > div.calendar-inner > div > div.view.view-date > div.calendar-ct > ul > li:nth-child(2) > ol > li:nth-child(1-42)
    当天的除外
    返回列表
    '''
    old_day_str1 = '#datebox > div.calendar-inner > div > div.view.view-date > div.calendar-ct > ul > li:nth-child(2) > ol > '
    old_day_str2 = 'li:nth-child'
    list_str = []
    for i in range(1, 43):
        list_str.append(old_day_str1 + old_day_str2 + '(' + str(i) + ')')

    return list_str


def back_first_day(list_str):
    '''
    返回第一天索引
    :param list_str: 当月页面的selector列表
    :return: 当月第一天
    '''
    for i, element in enumerate(list_str):
        if driver.find_element_by_css_selector(element).get_attribute("class") == 'old':  # 获取节点的class属性
            print(i)
            continue
        else:
            return i


def back_last_day(list_str):
    '''
    返回最后一天索引
    :param list_str: 当月页面的selector列表
    :return: 当月的最后一天
    '''
    for i, element in enumerate(list_str):
        if driver.find_element_by_css_selector(element).get_attribute("class") != 'new':  # 获取节点的class属性
            continue
        else:
            return i


# 选择开始日期
def choose_year_date_begin(list_str):
    '''
    对列表进行切片操作
    :param list_str: 需要切片的列表
    :return: 切片后的新列表
    '''
    first = back_first_day(list_str)
    last = back_last_day(list_str)
    lis = list_str[first:last]

    return lis


def initweb(url):
    '''
    初始化网址
    :param url: 网址
    :return:
    '''
    driver.get(url)
    driver.maximize_window()
    if judge_element_visible(dict_selector['选择日期']):
        print('加载完成')
    else:
        print('加载失败')


def analysis_html(html):
    '''
    解析html
    :param html: 当日的html
    :return: 解析完毕的列表
    '''
    soup = BeautifulSoup(html, "lxml")
    li = []
    for tr in soup.find_all(name='tr'):
        for td in tr.find_all(name='td'):
            li.append(td.text)

    return li[8:]


def get_history(str):
    '''
    返回当前页的日期
    :param str: 日期节点的selector
    :return: 返回日期
    '''
    input = driver.find_element_by_class_name(dict_selector['点击日期'])
    input.click()
    s = driver.find_element_by_class_name(str).text
    input.click()
    return s


def is_dateopen():
    if judge_element_visible(get_date()[0]):
        return True
    else:
        input = driver.find_element_by_class_name(dict_selector['点击日期'])
        input.click()


def set_month_year(year_month):
    '''
    判断当前月份是否和需要的一致，不一致
    :param month:年月份
    :return:真或假
    '''
    driver.refresh()  # 刷新页面
    year_month = year_month.replace('.', '/')
    d = get_history(dict_selector['获取日期'])

    is_dateopen()
    time.sleep(1)
    while year_month != d:
        time.sleep(1)
        driver.find_element_by_class_name(dict_selector['上个月']).click()
        time.sleep(1)
        d = get_history(dict_selector['获取日期'])


def get_now_day_html():
    '''

    :return: 返回当天数据的列表
    '''
    lis = choose_year_date_begin(get_date())
    is_dateopen()
    time.sleep(2)
    for i in range(len(lis)):
        is_dateopen()
        time.sleep(2)
        driver.find_element_by_css_selector(lis[i]).click()
        time.sleep(2)
        save_month_data(analysis_html(driver.page_source))

def save_month_data(li):
    di = {}
    for i in range(0, len(li), 11):
        d = {li[i]: li[i + 1:i + 3]}
        di.update(d)

    save_to_mongo(di)


if __name__ == '__main__':
    # 初始化
    initweb("https://www.1681380.com/view/PK10/pk10kai_history.html")
    # 选择月份
    set_month_year('2019/1')
    # 解析并保存
    get_now_day_html()
