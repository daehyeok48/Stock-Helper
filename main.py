# Import API key from config.py
from config import client_id
from config import client_secret
from config import update_interval

import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import requests
from bs4 import BeautifulSoup
import pandas as pd
import webbrowser

# Set up logging to a file
logging.basicConfig(
    filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Log the start of the process
logging.info("Starting stock data retrieval")


# get stock price from naver financial
def get_stock_price_naver(stock_code):
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        response = requests.get(url)

        if response.status_code != 200:
            logging.info(f"Error fetching stock page: {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        price_tag = soup.find("p", {"class": "no_today"})
        if price_tag:
            price = price_tag.find("span", {"class": "blind"}).text.replace(",", "")
            return float(price)
        else:
            logging.info("Could not find price on the page.")
            return None
    except Exception as e:
        logging.info(f"Exception occurred while scraping stock price: {e}")
        return None


def get_related_news(stock_name, client_id, client_secret, num_news=20):
    url = (
        f"https://openapi.naver.com/v1/search/news.json?query={stock_name}&display=100"
    )
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}

    news_list = []
    start = 1
    while len(news_list) < num_news:
        paginated_url = f"{url}&start={start}"
        response = requests.get(paginated_url, headers=headers)
        if response.status_code == 200:
            news_data = response.json()
            items = news_data.get("items", [])
            for item in items:
                if len(news_list) >= num_news:
                    break
                title = item.get("title").replace("<b>", "").replace("</b>", "")
                link = item.get("link")
                news_list.append({"title": title, "url": link})

            start += 100
            if not items:
                break
        else:
            logging.info("Error fetching news:", response.status_code)
            break

    return news_list


# save CSV
def save_to_csv(stock_name, stock_price, news_list, filename="stock_news.csv"):
    df = pd.DataFrame(news_list)
    df = df[["title", "url"]]
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    logging.info(f"Data saved to {filename}")


# update stock price
def update_stock_price():
    stock_code = entry.get()

    stock_price = get_stock_price_naver(stock_code)
    if stock_price is not None:

        price_label.config(text=f"주식 가격: {stock_price:.0f} 원")

    root.after(update_interval * 1000, update_stock_price)


# run when user press "search" button
def p():
    stock_code = entry.get()

    stock_price = get_stock_price_naver(stock_code)
    if stock_price is None:
        logging.info("Could not retrieve the stock price.")
        return

    price_label.config(text=f"주식 가격: {stock_price:.2f} 원")

    news_list = get_related_news(stock_code, client_id, client_secret)
    if not news_list:
        logging.info("No related news found.")
        return

    save_to_csv(stock_code, stock_price, news_list)

    for i in tree.get_children():
        tree.delete(i)

    df = pd.read_csv("stock_news.csv")
    for index, row in df.iterrows():
        tree.insert("", "end", values=(row["title"], row["url"]))


def on_double_click(event):
    item = tree.selection()[0]
    url = tree.item(item, "values")[1]
    webbrowser.open(url)


# set main window
root = tk.Tk()
root.title("Stock-Helper")
root.geometry("600x500")

# generate label
label = tk.Label(root, text="주식 코드를 입력하세요! (ex. 삼성전자 005930)")
label.grid(row=0, column=0)

# generate entry
entry = tk.Entry(root)
entry.grid(row=0, column=1)

# generate button
button = tk.Button(root, text="검색", command=p)
button.grid(row=0, column=2)

# print stock price
price_label = tk.Label(root, text="현재의 주식 가격: ")
price_label.grid(row=1, column=0, columnspan=3)


tree = ttk.Treeview(root, columns=("Title", "URL"), show="headings", height=20)
tree.heading("Title", text="News Title")
tree.heading("URL", text="URL")
tree.grid(row=2, column=0, columnspan=3)


tree.bind("<Double-1>", on_double_click)

# run
root.mainloop()
