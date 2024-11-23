from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from yahoo_stocks_image_intoSQL import fetch_stock_data  # 導入獲取股票數據的函數

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"Hi {user.name}！✨👋👋\n🤡歡迎來到，Jay's bot！🤡\n👉使用 /getstock 命令可以獲取股票信息。\n👉也可以使用 emoji的(🎲 🎯 🎳 🏀 ⚽ 🎰)進行遊戲互動哦。🤪")

async def get_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        stock_codes = context.args  # 獲取用戶輸入的多個股票代號
        results = []

        for stock_code in stock_codes:
            stock_info = fetch_stock_data(stock_code)  # 調用函數獲取股票信息
            results.append(stock_info)

        # 返回多個股票信息
        message = ""
        for stock_info in results:
            message += (
                f"股票代號: {stock_info['股票代號']}\n"
                f"名稱: {stock_info['名稱']}\n"
                f"價格: {stock_info['價格']}\n"
                f"涨跌幅: {stock_info['漲跌幅']}\n"
                f"狀態: {stock_info['狀態']}\n\n"
            )
        await update.message.reply_text(message)
    else:
        await update.message.reply_text(f"此命令提供您查看當日股票信息，\n請您輸入 /getstock 0050 2330 即可查看多個股票信息 ")  # 回覆文本消息
        # await update.message.reply_text(update.message.text) # 回覆文本消息


async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理所有消息，包括文本、貼圖、媒體等。"""
    # print(f"Received message: {update.message}")  # 打印接收到的消息

    if update.message.sticker:  # 檢查是否為貼圖
        await update.message.reply_sticker(update.message.sticker.file_id)  # 回覆相同的貼圖
    elif update.message.audio:  # 檢查是否為音頻
        await update.message.reply_audio(audio=update.message.audio.file_id)  # 回覆音頻
    elif update.message.voice:  # 檢查是否為語音消息
        await update.message.reply_voice(voice=update.message.voice.file_id)  # 回覆語音消息
    elif update.message.photo:  # 檢查是否為照片
        await update.message.reply_photo(photo=update.message.photo[-1].file_id)  # 回覆最後一張照片
    elif update.message.video:  # 檢查是否為影片
        await update.message.reply_video(video=update.message.video.file_id)  # 回覆影片
    elif update.message.document:  # 檢查是否為文件
        await update.message.reply_document(document=update.message.document.file_id)  # 回覆文件
    elif update.message.location:  # 檢查是否為地點
        await update.message.reply_location(location=update.message.location)  # 回覆地點
    elif update.message.text:  # 確保文本不是空的
        await update.message.reply_text(update.message.text)  # 回覆文本消息
    
    elif update.message.dice:  # 確保消息中包含骰子信息
        await update.message.reply_text(f"你丟出了 {update.message.dice.value} 點！")  # 回復骰子點數   

    else:
        await update.message.reply_text("不支持的媒體類型。")  # 如果不支持的媒體類型

async def handle_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理骰子消息。"""
    if update.message.dice:  # 确保消息中包含骰子信息
        await update.message.reply_text(f"你丟出了 {update.message.dice.value} 点！")  # 回復骰子點數
    else:
        await update.message.reply_text("沒有收到骰子消息。")  # 如果没有骰子信息

def main():
    # 1. 建立應用程式並放入bot's token.
    app = ApplicationBuilder().token("7703115681:AAF59N2xdgiC3aWtCbRLW_I8Nd2ZHTUSNsQ").build()

    # 2. 執行不同的命令，會在 Telegram 得到不同的答案
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getstock", get_stock))
    
    # 處理所有消息，包括文本、貼圖、照片、影片、語音、文件等...
    app.add_handler(MessageHandler(filters.ALL, handle_all_messages))

    # 處理遊戲-骰子相關消息
    app.add_handler(MessageHandler(filters.Dice.ALL, handle_dice))

    # 執行 bot 直到使用者輸入"Ctrl-C"
    app.run_polling()


if __name__ == "__main__":
    main()