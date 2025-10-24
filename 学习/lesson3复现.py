# Lesson 3 

'''
在编写策略时，除了常规的高开低收成交量等行情数据外，还会用到各式各样的指标（变量），
比如宏观经济指标、基本面分析指标、技术分析指标、另类数据等等。
Backtrader 大致有 2 种获取指标的方式：

1. 直接通过 DataFeeds 模块导入已经计算好的指标，比如《数据篇》中的导入新增指标 PE、PB: 
2. 在编写策略时调用 Indicators 指标模块临时计算指标，比如 5 日均线、布林带等 。
'''

# %%
import pandas as pd
import backtrader as bt
import backtrader.indicators as btind
import datetime
import tushare as ts

token = '251624ebd8ce6534da92c287e3db586b7c54ec71b92cd34468a81042'
ts.set_token(token)
pro = ts.pro_api(token=token)

def get_data_bytushare(code, start_date, end_date): 
    df = ts.pro_bar(ts_code=code, adj='qfq',start_date=start_date, end_date=end_date)
    df = df[['trade_date', 'open', 'high', 'low', 'close','vol']]
    df.columns = ['trade_date', 'open', 'high', 'low', 'close','volume']
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.index = df['trade_date']
    df.sort_index(inplace=True)
    df.fillna(0.0, inplace=True)
    return df

# from lesson2复现 import get_data_bytushare

# 恒瑞医药
data1 = get_data_bytushare('600276.SH','20200101','20211015')
# 贵州茅台
data2 = get_data_bytushare('600519.SH','20200101','20211015')


# %%

data1