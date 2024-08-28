import requests as req
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor
import pymysql


# # yahoo_stock_URL
# url = "https://tw.stock.yahoo.com/quote/8070.TW"

#想抓取的股票網址清單
stock_urls = [
  'https://tw.stock.yahoo.com/quote/8070',
  'https://tw.stock.yahoo.com/quote/6548',
  'https://tw.stock.yahoo.com/quote/2352',
  'https://tw.stock.yahoo.com/quote/8150',
  'https://tw.stock.yahoo.com/quote/2344',
  'https://tw.stock.yahoo.com/quote/6120',
]

# 資料庫連線
connection = pymysql.connect(
    host = 'localhost',
    user = 'root',
    password = 'P@ssw0rd',
    database = 'stock',
    charset = 'utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)


def getStock(stock_urls):
# 用 requests 的 get 方法把網頁抓下來
    res = req.get(stock_urls) 
# 指定 lxml 作為解析器
    soup = bs(res.text, "lxml")
# 嘗試找到股票代號.名稱.價格.漲跌幅
    stock_id = soup.select_one('span.C\(\$c-icon\)').get_text()
    stock_name = soup.select('h1')[1].get_text()
    stock_price = soup.select_one('.Fz\(32px\)').get_text()
    stock_percent = soup.select('.Fz\(20px\)')[0].get_text()
    stock_status = ""
    try:
        if soup.select_one('#main-0-QuoteHeader-Proxy .C\(\$c-trend-down\)'):
            stock_status= '-'
        elif soup.select_one('#main-0-QuoteHeader-Proxy .C\(\$c-trend-up\)'):
            stock_status= '+'
        else:
            stock_status = ''  
    except Exception as e:
        print(f"Error in parsing status for {stock_urls}: {e}")
        stock_status = ''

    # 回傳 tuple 格式的資料
    return (stock_id, stock_name, stock_price, stock_status, stock_percent)

# 使用執行緒池來並行抓取股票資訊
with ThreadPoolExecutor() as executor:
    results = list(executor.map(getStock, stock_urls))  # 收集所有結果

# 用迴圈印出所有結果
for result in results:
    print(result)

try:
    with connection.cursor() as cursor:  # 使用 with 語法自動處理游標的打開和關閉
        # 直接寫入資料 (新舊資料都在)
        sql = "INSERT INTO `my_stock` (`stock_id`, `stock_name`, `stock_price`, `stock_status`, `stock_percent`) VALUES (%s, %s, %s, %s, %s)"
        
        # 使用 executemany() 插入多筆資料
        cursor.executemany(sql, results)

        # 提交 SQL 執行結果
    connection.commit()

except Exception as e:
    # 回滾
    connection.rollback()
    print("SQL 執行失敗")
    print(e)

finally:
    # 關閉資料庫連線
    connection.close()