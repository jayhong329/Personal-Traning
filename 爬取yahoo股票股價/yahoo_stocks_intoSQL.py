import requests as req
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor
import pymysql

# 資料庫連線
connection = pymysql.connect(
    host = 'localhost',
    user = 'root',
    password = 'P@ssw0rd',
    database = 'stock',
    charset = 'utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 自行輸入股票代碼.顯示個股資料並寫入資料庫內
def fetch_stock_data(stock_code):
    url = f"https://tw.stock.yahoo.com/quote/{stock_code}"
    res = req.get(url)
    soup = bs(res.text, "lxml")
    
    stock_id = soup.select_one('span.C\(\$c-icon\)').get_text()
    stock_name = soup.select('h1')[1].get_text()
    
    # 获取股价并去掉逗号
    stock_price = soup.select_one('.Fz\(32px\)').get_text().replace(',', '')
    stock_price = float(stock_price)  # 转换为浮点数

    stock_percent = soup.select('.Fz\(20px\)')[0].get_text()
    stock_status = ""

    # 判断涨跌状态
    try:
        if soup.select_one('#main-0-QuoteHeader-Proxy .C\(\$c-trend-down\)'):
            stock_status = '-'
        elif soup.select('#main-0-QuoteHeader-Proxy .C\(\$c-trend-up\)'):
            stock_status = '+'
        else:
            stock_status = ''
    except Exception as e:
        print(f"Error in parsing status for {stock_code}: {e}")
        stock_status = ''

    # 回傳 tuple 格式的資料
    return (stock_id, stock_name, stock_price, stock_status, stock_percent)

def main():
    stock_codes = input("請輸入股票代碼（以逗號分隔）：").split(',')
    results = []

    for code in stock_codes:
        code = code.strip()  # 去除多餘的空白
        try:
            stock_data = fetch_stock_data(code)
            results.append(stock_data)  # stock_data 已經是一個元組
        except Exception as e:
            print(f"抓取股票代碼 {code} 時發生錯誤: {e}")

    # 輸出的 result 是一個元組
    for result in results:
        print(f"股票代號: {result[0]}, 名稱: {result[1]}, 股價: {result[2]}, 狀態: {result[3]}, 漲跌幅: {result[4]}")

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

if __name__ == "__main__":
    main()