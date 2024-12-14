from datetime import datetime
import numpy as np
from scipy.stats import norm
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Black-Scholes functions
N = norm.cdf

def BS_CALL(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * N(d1) - K * np.exp(-r * T) * N(d2)

def REVERSE_BS_CALL(p, K, T, r=0.35, sigma=0.34, alpha=10):
    s = K + 10 * alpha
    err1 = round(BS_CALL(s, K, T, r, sigma), 0) - p
    if err1 > 0:
        alpha = -1 * alpha
    s = s + 10 * alpha
    err2 = round(BS_CALL(s, K, T, r, sigma), 0) - p

    while err1 * err2 > 0:
        s = s + 10 * alpha
        err1 = err2
        err2 = round(BS_CALL(s, K, T, r, sigma), 0) - p

    err = abs(round(BS_CALL(s - 10 * alpha, K, T, r, sigma), 0) - p)
    if abs(err) < abs(err2):
        best = s - 10 * alpha
        minimum = abs(err)
    else:
        best = s
        minimum = abs(err2)

    for i in range(min(s, s - 10 * alpha), max(s, s - 10 * alpha) + 1, abs(alpha)):
        err = abs(round(BS_CALL(i, K, T, r, sigma), 0) - p)
        if err < abs(minimum):
            minimum = err
            best = i
    return best

def zahromlastprice():
    url = "https://landing.irfarabi.com/bot/zAhrom.php?read=true"
    #url = "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/2839111977611376/12"
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # این خط خطاهای HTTP را بررسی می‌کند
        json_data = response.json()
        result = json_data['result']
        return result

        if 'closingPriceDaily' in json_data and json_data['closingPriceDaily']:
            return json_data['closingPriceDaily'][0]['pDrCotVal']
        else:
            return None  # یا مقدار پیش‌فرض دیگری که مایلید برگردانید
    except requests.RequestException as e:
        print(f"HTTP Request error: {e}")
        return None
    except ValueError as e:
        print(f"Data format error: {e}")
        return None


# Function to handle start command
async def start(update: Update, context: CallbackContext):
    try:
        maturity = datetime(year=2025, month=1, day=15)
        remainday = (maturity - datetime.now()).days
        strikeprice = 22000
        last_price = zahromlastprice()['pDrCotVal']
        result = REVERSE_BS_CALL(last_price, strikeprice, remainday / 365)

        ahrom = zahromlastprice()['AhrompClosing']
        percent_change = ((result / ahrom -1) * 100)
     
        
        await update.message.reply_text(f"قیمت فردایی اهرم: {result:,}\n قیمت آخرین اهرم: {ahrom:,}\n تفاوت درصدی: {percent_change:.1f}%")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# Main function to run the bot
if __name__ == '__main__':
    TOKEN = ""
    app = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running...")
    app.run_polling()
