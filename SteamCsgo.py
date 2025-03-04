import os
import time
import requests
import pandas as pd
import random
from fake_useragent import UserAgent
from lxml import etree
from urllib.parse import urlencode


class SteamCsgo:
    def __init__(self, start, save_file_path, page_num):
        # 确认起始爬取值 第几个商品
        self.start = start
        # 确认要爬多少页
        self.page_num = page_num
        # 确认存储位置
        self.save_file_path = save_file_path
        # 初始化数据列表
        self.item_datas = []
        # 定义url前头
        self.base_url = 'https://steamcommunity.com/market/search/render/?query=&'

    def get_page(self):
        count = 0
        for page in range(self.page_num):
            params = {
                'start': self.start + 100 * page,
                'count': 100,
                'search_descriptions': 0,
                'sort_column': 'price',
                'sort_dir': 'asc',
                'appid': 730
            }
            current_url = 'https://steamcommunity.com/market/search/render/?query=&' + urlencode(params)
            try:
                requests.DEFAULT_RETRIES = 5  # 增加重试连接次数
                s = requests.session()
                s.keep_alive = False  # 关闭多余连接
                res = requests.get(url=current_url, headers=self.init_headers())
                if res.status_code == 200:
                    count = count + 1
                    if count % 10 == 0:
                        time.sleep(60)
                    print('已成功获取第{}页'.format(page + 1))
                    page_info = res.json()
                    self.parse_page(page_info)
                    self.save_to_csv()
                    time.sleep(random.random() * 15)
                else:
                    print('失败')
            except requests.ConnectionError as e:
                print(e)
                print('{}页获取失败'.format(page))
                return None

    def parse_page(self, page_info):
        page_html = page_info['results_html'].replace('\r', '').replace('\n', '').replace('\t', '')
        tree = etree.HTML(page_html)

        for i in tree.xpath('//a[@class="market_listing_row_link"]'):
            info = {}
            info['饰品名称'] = i.xpath('.//span[@class="market_listing_item_name"]/text()')[0]  # 名称
            info['饰品价格'] = i.xpath('.//span[@class="normal_price"]/text()')[0]  # 起价
            info['当前在售数量'] = i.xpath('.//span[@class="market_listing_num_listings_qty"]/@data-qty')[0]  # 当前在售数量
            self.item_datas.append(info)

    # 存储到csv
    def save_to_csv(self):
        df = pd.DataFrame(self.item_datas)
        df = df.reindex(columns=['饰品名称', '饰品价格', '当前在售数量'])
        if os.path.exists(self.save_file_path) and os.path.getsize(self.save_file_path):
            df.to_csv(self.save_file_path, mode='a', encoding='utf-8', header=None, index=False)
        else:
            df.to_csv(self.save_file_path, mode='a', encoding='utf-8', index=False)
            print('已创建' + self.save_file_path)
        self.item_datas = []

    # 生成随机ua
    def init_headers(self):
        headers = {
            'User-Agent': UserAgent().random,
            'Accept-Language': 'zh-CN',
            # 'Referer': 'https: // steamcommunity.com / market / search?appid = 730'
        }
        return headers


if __name__ == '__main__':
    S = SteamCsgo(6500, './CsgoSteam.csv', 60)
    S.get_page()

    # For a web GUI, I recommend creating a separate Flask application
    # Create a new file called app.py with the following code:
    """
    from flask import Flask, render_template, request
    from SteamCsgo import SteamCsgo
    
    app = Flask(__name__)
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            price_range = int(request.form['price_range'])
            output_file = request.form['output_file']
            refresh_time = int(request.form['refresh_time'])
            
            steam = SteamCsgo(price_range, output_file, refresh_time)
            steam.get_page()
            return 'Data collection complete! Check your CSV file.'
            
        return render_template('index.html')
        
    if __name__ == '__main__':
        app.run(debug=True)
    """
    
    # Then create a templates folder and add index.html:
    """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSGO Data Collector</title>
        <style>
            body { 
                font-family: Arial;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .form-group {
                margin: 20px 0;
            }
            label {
                display: block;
                margin-bottom: 5px;
            }
            input {
                width: 100%;
                padding: 8px;
            }
            button {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>CSGO Market Data Collector</h1>
        <form method="POST">
            <div class="form-group">
                <label>Price Range:</label>
                <input type="number" name="price_range" required>
            </div>
            <div class="form-group">
                <label>Output File Name:</label>
                <input type="text" name="output_file" value="CsgoSteam.csv" required>
            </div>
            <div class="form-group">
                <label>Refresh Time (seconds):</label>
                <input type="number" name="refresh_time" value="60" required>
            </div>
            <button type="submit">Start Collection</button>
        </form>
    </body>
    </html>
    """
    
    # To use this:
    # 1. Install Flask: pip install flask
    # 2. Create the files as shown above
    # 3. Run: python app.py
    # 4. Open browser to http://localhost:5000
