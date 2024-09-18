from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# 设置Chrome选项
chrome_options = Options()
chrome_options.add_argument('--headless')  # 如果你不需要看到浏览器窗口，可以使用headless模式

# ChromeDriver的路径（手动指定路径，或者确保已添加到系统路径）
webdriver_path = r'C:\Users\wwwwi\Downloads\chromedriver_win32 (1)\chromedriver.exe'

# 创建Chrome WebDriver实例
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# 打开目标网页
url = "https://www.ciweimao.com/chapter/111715642"
driver.get(url)

# 通过XPath找到目标元素
element = driver.find_element(By.XPATH, '//*[@id="J_BookCnt"]')

# 提取文本，忽略span标签
content_with_span = element.get_attribute('innerHTML')

from bs4 import BeautifulSoup

# 解析HTML内容并删除span标签
soup = BeautifulSoup(content_with_span, 'html.parser')
for span in soup.find_all('span'):
    span.extract()  # 移除span标签及其内容

# 获取纯文本
clean_text = soup.get_text()

# 输出提取的文本
print(clean_text)

# 关闭浏览器
driver.quit()
