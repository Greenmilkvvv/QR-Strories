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

code = ''
CODE = '000400' # 许继电气
START = '20150701'
END = '20251031'
CASH = 100_000 

df = obtain_data(CODE, START, END)
datafeed = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data=datafeed, name=CODE)

# %%

# 2. 指标

class PivotPointIndicator(bt.Indicator): 
    ''' 支撑 阻力 指标 '''

    lines = ('pivot', 'resistance', 'support')

    def __init__(self): 
        self.addminperiod(1) # 1 天, 因为是计算的昨天

    def next(self): 

        self.lines.pivot[0] = self.data.close[-1] + self.data.high[-1] + self.data.low[-1]

        self.lines.resistance[0] = 2 * self.lines.pivot[0] - self.data.low[-1]

        self.lines.support[0] = 2 * self.lines.pivot[0] - self.data.high[-1]

    

# %%

# 3. 策略

class PivotPointStrategy(bt.Strategy): 

    params = (
        ('size_pct', 0.95), # 仓位默认95%
    )

    def __init__(self): 

        # 获取 C, S, R 数据线
        MyInd = PivotPointIndicator(self.data)
        self.C, self.S, self.R = MyInd.lines.pivot, MyInd.lines.support, MyInd.lines.resistance

        
    def next(self): 

        d = self.getdatabyname(CODE)

        # 检查现有持仓
        current_pos = self.getposition( self.getdatabyname(CODE) ).size

        # 生成买入信号
        if self.data.close[0] > self.C[0] and current_pos == 0 : 

            # 计算最大持仓
            cash = self.broker.get_cash()
            price = self.data.close[0]
            target_value = cash * self.params.size_pct
            target_shares = target_value // price
            target_shares = (target_shares // 100) * 100 # 100股为单位

            self.order_target_size(data = d, target=target_shares)
            
            # 日志
            print(f'买入 {CODE} {target_shares} 股')

        elif self.data.close[0] >= self.R[0] and current_pos > 0 : 

            self.order_target_size(data = d, target=0)

            # 日志
            print(f'平掉 {CODE} 多仓')



cerebro.addstrategy(PivotPointStrategy)



# %%

# 4. 交易管理 

## 滑点 百分比 0.0 因为资金量较小
cerebro.broker.set_slippage_perc(0.0) 

## 佣金 万三 + 最低 5 元（双向）
cerebro.broker.setcommission( 
    commission=0.0003, 
    stocklike = True
)


## 成交模式: 日度回测默认 Bar 开盘成交
cerebro.broker.set_coo(True)

## 最大成交量
# cerebro.broker.set_filler(
#     bt.broker.fillers.FixedBarPerc(perc=0.001)
# )

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


# %%

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
cerebro.plot(style='line', barup='red', bardown='green', plotlinetrades=False)