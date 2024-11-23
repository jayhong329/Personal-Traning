import requests as req
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor
import pymysql
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
# 嘗試找到股票代號.名稱.價格.漲跌幅.狀態
    stock_id = stock_code  # 使用輸入的股票代碼
    # stock_id = soup.select_one('span.C\(\$c-icon\)').get_text()
    
    stock_name = soup.select('h1')[1].get_text()
    stock_price = soup.select_one('.Fz\(32px\)')  # 確保這個選擇器正確
    stock_price = stock_price.get_text().replace(',', '') if stock_price else "0"  # 清理數據
    stock_price = float(stock_price)  # 轉換為浮點數
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
        print(f"Error in parsing status for {stock_code}: {e}")
        stock_status = ''


    # # 回傳 tuple 格式的資料
    # return (stock_id, stock_name, stock_price, stock_status, stock_percent)
    return {
        '股票代號': stock_id,
        '名稱': stock_name,
        '價格': stock_price,
        '漲跌幅': stock_percent,
        '狀態': stock_status
    }

def get_all_stock_data(stock_codes):
    results = []
    for code in stock_codes:
        stock_info = fetch_stock_data(code)
        results.append(stock_info)
    return results

def plot_stock_info(stock_data):
    # 創建子圖
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'domain'}, {'type': 'table'}]])
    
    # 添加餅圖
    fig.add_trace(go.Pie(labels=stock_data['名稱'], values=stock_data['價格'], name="股票價格"), 1, 1)
    
    # 添加表格
    fig.add_trace(go.Table(
        header=dict(values=list(stock_data.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[stock_data[col] for col in stock_data.columns],
                   fill_color='lavender',
                   align='left')
    ), 1, 2)
    
    # 更新布局
    fig.update_layout(title_text="股票資訊圖表")
    
    # 顯示圖表
    fig.show()

def main():
    stock_codes = input("請輸入股票代碼（以逗號分隔）：").split(',')
    results = []

    for code in stock_codes:
        code = code.strip()
        print(f"正在處理股票代碼：{code}")
        stock_info = fetch_stock_data(code)
        results.append(stock_info)

    # 將股票資訊轉換為 DataFrame
    df = pd.DataFrame(results)
    print(df)
    
    # 繪製圖表
    plot_stock_info(df)

    try:
        with connection.cursor() as cursor:  # 使用 with 語法自動處理游標的打開和關閉
            # 直接寫入資料 (新舊資料都在)
            sql = "INSERT INTO `my_stock` (`stock_id`, `stock_name`, `stock_price`, `stock_status`, `stock_percent`) VALUES (%s, %s, %s, %s, %s)"

            # 準備要插入的資料
            insert_data = [(result['股票代號'], result['名稱'], result['價格'], result['狀態'], result['漲跌幅']) for result in results]
            
            # 使用 executemany() 插入多筆資料
            cursor.executemany(sql, insert_data)

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