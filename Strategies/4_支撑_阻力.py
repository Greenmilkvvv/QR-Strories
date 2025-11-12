# 参考 "151 trading strategies"
# 3.14 - Strategy: Support and resistance


# 策略基于 "support" S 和 "resistance" R 

# 计算上主要基于 "Pivot Point" C，它是最高价、最低价和收盘价的平均值, 定义为
# pivot: C = ( P_H + P_L + P_C ) / 3 
# resistance: R = 2 * C - P_L
# support: S = 2 * C - P_H
## 其中 P_H P_L P_C 分别是昨天的最高价、最低价和收盘价。

# 我们可以构建如下定义交易信号: 
##  Signal = 
## - 做多 if P > C
## - 平掉多仓 if P >= R
## - 做空 if P < C
## - 平掉空仓 if P <= S


# %%

import pandas as pd 
import backtrader as bt 
import akshare as ak 

cerebro = bt.Cerebro() 


# %%

# 1. 数据

def obtain_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame: 

    '''
    股票代码: 
    symbol: 'xxxxxx'

    起始 / 结束日期:
    start / end: 'yyyymmdd'

    ============

    返回塞给 backtrader 的数据
    pd.DataFrame : df[['date', 'open', 'high', 'low', 'close', 'volume']]
    '''

    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
    df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df


# %%

# 2. 指标

class PivotPointIndicator(bt.Indicator): 
    ''' 支撑 阻力 指标 '''

    lines = ('pivot', 'resistance', 'support')

    def __init__(self): 

        self.lines.pivot = (self.data.high + self.data.low + self.data.close) / 3 # C 枢轴点

        self.lines.resistance = 2 * self.lines.pivot - self.data.low # R 阻力
        
        self.lines.support = 2 * self.lines.pivot - self.data.high # S 支撑

    





