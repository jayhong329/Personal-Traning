## 設定 OpenAI API Key 變數
from dotenv import load_dotenv
import os
import openai
import gradio as gr
import pymysql

# Load the environment variables from .env file
load_dotenv()

# Access the API key
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key

# 系統提示詞
SYSTEM_PROMPT = """你是台北市立圖書館的 AI 客服，擅長查找資料庫內容並提供正確內容給使用者。
你的任務是：
* Think step by step, carefully and logically.
* 理解用戶問題，提供準確的圖書館相關信息
* 基於資料庫查詢結果，生成完整且友善的回答
* 如果資料庫中沒有直接相關的答案，嘗試提供相關的建議
* 保持專業、友善的對話風格

回答時請：
- 使用正體中文
- 條理清晰地組織信息
- 確保信息準確性
- 必要時提供延伸建議"""

desc = "直接輸入您的問題或關鍵詞 " \
       "AI 助手會根據圖書館問答資料庫回復相關服務與政策。" 

article = "<h1> 圖書館客服問答系統 </h1>"\
          "<h3>使用說明:</h3> " \
          "<ul><li>直接輸入您的問題或關鍵詞</li>" \
          "<li>AI 助手會根據圖書館問答資料庫回復相關服務與政策</li></ul>"



def handle_user_query(user_query):
    db_results = []  
    try:
        connection = connect_db()
        with connection.cursor() as cursor:
            # 使用參數化查詢防止 SQL 注入
            query = "SELECT question, answer FROM faq_table WHERE question LIKE %s"
            cursor.execute(query, (f"%{user_query}%",))
            db_results = cursor.fetchall()
    except Exception as e:
        print(f"資料庫查詢錯誤：{str(e)}")
        db_results = [{"question": "資料庫錯誤", "answer": "無法檢索數據，請稍後再試。"}]
    finally:
        if connection:
            connection.close()
    return db_results


# 連接到 MySQL 資料庫
def connect_db():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset=os.getenv('DB_CHARSET'),
        cursorclass=pymysql.cursors.DictCursor
    )

def get_ai_response(user_query, db_results):
    try:
        # 初始化 db_results 為空列表（如果未提供）
        if db_results is None:
            db_results = []

        # 將 db_results 轉換為字符串格式
        context = f"用戶問題：{user_query}\n\n相關的資料庫結果：\n"
        
        if isinstance(db_results, list):
            for result in db_results:
                # 檢查 result 是否為元組
                if isinstance(result, tuple):
                    # 假設元組中的順序是 (question, answer)
                    question, answer = result
                    context += f"問：{question}\n"
                    context += f"答：{answer}\n\n"
                # 檢查 result 是否為字典
                elif isinstance(result, dict):
                    context += f"問：{result.get('question', '')}\n"
                    context += f"答：{result.get('answer', '')}\n\n"
                else:
                    context += str(result) + "\n"
        else:
            context += str(db_results)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=messages,
            temperature=0.1,
            stream=True
        )

        full_response = ""
        for chunk in response:
            content = chunk.choices[0].delta.get('content', '')
            if content:
                full_response += content

        # 清理並返回回應
        return full_response.strip()

    except Exception as e:
        print(f"AI 處理時發生錯誤：{str(e)}")
        print(f"錯誤類型：{type(e)}")
        print(f"db_results 類型：{type(db_results)}")
        if isinstance(db_results, list):
            print(f"第一個結果類型：{type(db_results[0])}")
        import traceback
        print(f"詳細錯誤：\n{traceback.format_exc()}")
        return f"AI 回應生成失敗：{str(e)}"

# 使用 ChatInterface 創建聊天界面
gr.close_all()
gr.ChatInterface(
    fn=get_ai_response,
    theme="Soft",
    title=article,
    examples=[
        "請問圖書館的開放時間是什麼時候？",
        "我想了解如何辦理借書證",
        "兒童區有什麼特別的服務？",
        "幫我介紹一下圖書館的資源嗎？"]).queue().launch(debug=True)