# 实现 Single Moving Average (SMA) 策略
# 参考 ZuraKakushadze,JuanAndrésSerur. 151 Trading Strategies 3.11 . 

# %%

import pandas as pd
import backtrader as bt 
import akshare as ak

cerebro = bt.Cerebro()

'''
 SMA(T) = ( P(1) + P(2) + ... + P(T) ) / T
        = \sum_{i=1}^{T} P(i) / T

此处 t=1 指的是 P(t) 到目前为止的最新的价格. T 是 MA 的长度. 

MA 发展出了 SMA 和 EMA. 

A simple strategy is de ned as follows 
(P is the price at t = 0, on the trading day immediately following the most recent trading day t = 1 in the time series P(t)) :

Signal = 
- Established long / liquidate short position if P > MA(t)
- Established short / liquidate long position if P < MA(t)

This strategy can be run as, e.g., long-only, short-only, or both long and short. It can be straightforwardly applied to multiple stocks (on a single-stock basis, with no cross-sectional interaction between the signals for individual stocks). With a large number of stocks, it may be possible to construct (near-)dollar-neutral portfolios.
'''

# %%

# 1. 数据获取

def get_ak_data(symbol: str, start: str, end: str) -> pd.DataFrame : 
    
    '''
    pd.DataFrame -> df[['date', 'open', 'high', 'low', 'close', 'volume']]
    '''

    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq") 

    df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date']) 
    df.set_index('date', inplace=True) 
    return df 

CODEs = ['300750', '002594', '000858', '600036']   # 宁德、比亚迪、五粮液、招行
START = '20200101'
END = '20231231'
CASH = 100_000 

for CODE in CODEs:
    df = get_ak_data(CODE, START, END) 
    datafeed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(datafeed, name=CODE)

# %% 

# 2. 自定义指标 手工双均线 (不使用 bt.ind.SMA )

class MyDMA(bt.Indicator): 
    '''手工双均线''' 

    lines = ('ma_fast', 'ma_slow') 

    params = (
        ('fast', 5), 
        ('slow', 10),
    )

    def __init__(self): 
        # 预先分配空间 (避免回测时反复分配空间) 
        self.addminperiod(self.params.slow)

    def next(self): 
        # 手工算均值 
        fast_avg = sum( self.data.close.get(ago=-i, size=1)[0] for i in range(self.params.fast) ) / self.params.fast 
        slow_avg = sum( self.data.close.get(ago=-i, size=1)[0] for i in range(self.params.slow) ) /self.params.slow

        self.lines.ma_fast[0] = fast_avg 
        self.lines.ma_slow[0] = slow_avg

# %% 

# 3. 策略 

class DMAStrategy(bt.Strategy): 
    params = ( 
        ('size_pct', 0.95), # 仓位默认95%
        ('fast', 20), 
        ('slow', 60), 
    )

    # def __init__(self): 

    #     self.dma = MyDMA( 
    #         self.data, 
    #         fast = self.params.fast, 
    #         slow = self.params.slow
    #     ) 

    #     self.signal = bt.ind.CrossOver( 
    #         self.dma.lines.ma_fast, 
    #         self.dma.lines.ma_slow
    #     )

    # def next(self): 
    #     # 头寸管理 

    #     if self.signal > 0: # 金叉 做多
    #         self.order = self.order_target_percent(target = self.params.size_pct)

    #     elif self.signal < 0: # 死叉 不做空
    #         self.order = self.order_target_percent(target = 0)

    def __init__(self):
        # 为每只股票预生成指标，存到 dict 里
        self.sig = {}
        for d in self.datas:   # self.datas 是列表，顺序同 adddata 顺序
            code = d._name
            dma = MyDMA(d, fast=self.p.fast, slow=self.p.slow)
            cross = bt.ind.CrossOver(dma.ma_fast, dma.ma_slow)
            self.sig[code] = cross

    def next(self):
        # 对每只股票独立判断
        for d in self.datas:
            code = d._name
            signal = self.sig[code][0]   # 当前信号
            pos = self.getposition(d).size

            if signal > 0 and not pos:   # 金叉且无仓 → 做多
                self.order_target_percent(data=d, target=self.p.size_pct)
            elif signal < 0 and pos:     # 死叉且有仓 → 平仓
                self.order_target_percent(data=d, target=0)

            # 调试用，跑通后注释
            print(d.datetime.date(0), code,
                  'close', d.close[0],
                  'signal', signal,
                  'pos', pos)
 
cerebro.addstrategy(DMAStrategy)

# %% 

# 4. 交易管理 

## 滑点 百分比 0.1%
cerebro.broker.set_slippage_perc(0.001) 

## 佣金 万三 + 最低 5 元（双向）
cerebro.broker.setcommission( 
    commission=0.0003, 
    stocklike = True
)


## 成交模式: 日度回测默认 Bar 开盘成交
cerebro.broker.set_coo(True)

## 最大成交量
cerebro.broker.set_filler(
    bt.broker.fillers.FixedBarPerc(perc=0.001)
)

# %%

# 5. 分析器 

cerebro.addanalyzer( 
    bt.analyzers.SharpeRatio, 
    _name = '_sharpe', 
    riskfreerate=0.03 
)

cerebro.addanalyzer( 
    bt.analyzers.DrawDown, 
    _name = '_drawdown'
)

cerebro.addanalyzer( 
    bt.analyzers.Returns, 
    _name = '_returns'
)

#%%

# 6. 运行

result = cerebro.run()
# 从返回的 result 中提取回测结果
strat = result[0]

# 结果
print('--------------- Performance -----------------')
print(f"最终市值: {cerebro.broker.getvalue():,.2f}")
print(f"夏普比率: {strat.analyzers._sharpe.get_analysis().get('sharperatio', 'N/A')}")
dd = strat.analyzers._drawdown.get_analysis()
print(f"最大回撤: {dd.max.drawdown:.2f}%")
ret = strat.analyzers._returns.get_analysis()
print(f"总收益: {ret['rtot']*100:.2f}%")

# %%

# 画图（可选）
cerebro.plot(style='candle', barup='red', bardown='green')