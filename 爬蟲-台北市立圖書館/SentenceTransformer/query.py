'''
匯入套件
'''
from sentence_transformers import SentenceTransformer
import faiss
import pymysql

# 基本設定
model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
model = SentenceTransformer(model_name)

# 資料庫連線
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='P@ssw0rd',
    database='taipei_library',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 讀取索引
index_path = './vector925.index'
index = faiss.read_index(index_path)

# 允許用戶輸入查詢句子
query = input("請輸入您的問題：")

# 將查詢句子轉換成向量
query_vector = model.encode(
    [query], 
    batch_size=6, 
    show_progress_bar=False,
    normalize_embeddings=True  # 確保向量被正規化
)

# 查詢，增加 k 值
D, I = index.search(query_vector, k=5)

# 設定相似度閾值
similarity_threshold = 0.5

# 過濾結果
filtered_results = []
for d, i in zip(D[0], I[0]):
    if i >= 0 and d > similarity_threshold:
        filtered_results.append((d, i))

# 根據相似度排序結果
filtered_results.sort(key=lambda x: x[0], reverse=True)

print(f"\n找到 {len(filtered_results)} 個相關結果：\n")

# 根據 Document IDs 從資料庫中獲取對應的答案
try:
    with connection.cursor() as cursor:
        for similarity, doc_id in filtered_results:
            sql = "SELECT id, question, answer FROM library_qa WHERE id = %s"
            cursor.execute(sql, (doc_id,))
            result = cursor.fetchone()
            if result:
                print(f"相似度: {similarity:.4f}")
                print(f"ID: {result['id']}")
                print(f"問題: {result['question']}")
                print(f"答案: {result['answer']}")
                print("-" * 50)
except Exception as e:
    print("資料庫查詢失敗")
    print(e)

# 釋放記憶體
del index

# 關閉資料庫連線
connection.close()