# ETF 轮动
# 基于 上证50ETF（510050）、创业板50ETF（159949）

## 摘要
## 无脑全仓多空, 按收盘价计算, 计算一只股票的close/MA20 - 1, 
## 若都小于0则清仓, 买入大于0时两者中较高者

# %%

import pandas as pd 
import backtrader as bt
import akshare as ak
# import tushare as ts
import matplotlib.pyplot as plt

cerebro = bt.Cerebro()

"""
原理: 
- 以上证50ETF作为大盘股代表, 以创业板50ETF作为小盘股代表。
- 上证50ETF主要反映的是大盘蓝筹股的走势, 其成份股主要是市值较大、流动性好、盈利能力强的优质企业。大盘股的投资特点是稳健、低风险, 但可能收益较低。
相比之下, 创业板50ETF主要反映的是小盘成长股的走势, 其成份股主要是市值较小、成长性较强的创新型企业。小盘股的投资特点是高风险、高收益。

- akshare api: 
- ak.etf_fund_daily(symbol='510050', period='daily',
                start_date=START, end_date=END, adjust='qfq')

                

策略: 
- 动量投资策略的基本原理是强者恒强, 弱者恒弱。即过去表现较好的资产在未来一段时间内很可能会继续表现优越, 而过去表现较差的资产在未来一段时间内很可能会继续表现不佳。动量策略通过捕捉市场的趋势来实现盈利。
- 本策略试图采用价格与均线的比值捕捉大盘和小盘之间的轮动, 实现在两个ETF中进行择时交易, 可以在不同市场环境下选择相对表现较好的指数ETF进行投资, 获得更好的收益。
"""

# %%

# 1. 数据获取

def get_data(symbol, start): 

    df = ak.fund_etf_hist_em(symbol=symbol, start_date=start,  adjust='qfq')
    df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date']) 
    df.set_index('date', inplace=True) 
    return df 

SZ50_ETF = get_data(symbol='510050', start='20190722')
CYB50_ETF = get_data(symbol='159949', start='20190722')

datafeeds1 = bt.feeds.PandasData(dataname = SZ50_ETF, name = 'SZ50_ETF')
datafeeds2 = bt.feeds.PandasData(dataname = CYB50_ETF, name = 'CYB50_ETF')
cerebro.adddata(datafeeds1)
cerebro.adddata(datafeeds2)

# %%

# 2. 自定义指标 close/MA20 - 1

class MomentumIndicator(bt.Indicator): 
    
    # 新指标注册
    lines = ('momentum', )

    # 参数 
    params = (
        ('target_period', 20), # 默认使用 MA20  
    )

    def __init__(self): 
        super().__init__() 
        sma = bt.ind.SMA(self.data.close, period=self.params.target_period) 
        self.lines.momentum = self.data.close / sma - 1.0

    # def next(self): 
    #     # 计算指标
    #     # close / MA20 -1
    #     close = self.data.close[0]
    #     ma20 = sum(self.data.close.get(ago=0, size = self.params.target_period)) / self.params.target_period

    #     self.lines.momentum[0] = close / ma20 - 1
    #     # self.lines.momentum[0] = self.data.close[0] / self.data.close.get(ago=0, size = self.params.target_period) - 1

# %%

# 3. 策略

class ETFMomentumStrategy(bt.Strategy): 
    
    # 参数
    params = (
        ('size_pct', 0.95), # 仓位默认95%
        ('target_period', 20), # 默认使用 MA20
    )

    # 初始化
    ## 给每一只股票生成指标 MomentumIndicator
    def __init__(self): 
        # 创建 dict 给两个股票生成指标
        self.sig = {}
        self.sig['SZ50_ETF'] = MomentumIndicator(self.getdatabyname('SZ50_ETF'))
        self.sig['CYB50_ETF'] = MomentumIndicator(self.getdatabyname('CYB50_ETF'))

    def next(self):

        # 对两只股票联合判断
        signal_sz50 = self.sig['SZ50_ETF'][0] # 上证50 
        signal_cyb50 = self.sig['CYB50_ETF'][0] # 创业板50

        # 若都小于0则清仓
        if signal_sz50 < 0 and signal_cyb50 < 0:
            # 清仓
            for d in self.datas:
                self.close(data=d)


         # 买入大于0时两者中较高者
        elif signal_sz50 > signal_cyb50:
            self.order = self.order_target_percent(
                data = self.getdatabyname('SZ50_ETF'), 
                target = self.params.size_pct
            ) # 上证50ETF

        elif signal_sz50 < signal_cyb50:
            self.order = self.order_target_percent(
                data = self.getdatabyname('CYB50_ETF'), 
                target = self.params.size_pct
            ) # 创业板50ETF

        print(self.datetime.date(0),
              'sz50', signal_sz50, 'cyb50', signal_cyb50,
              'pos_sz', self.getposition(self.getdatabyname('SZ50_ETF')).size,
              'pos_cyb', self.getposition(self.getdatabyname('CYB50_ETF')).size)

cerebro.addstrategy(ETFMomentumStrategy)

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
# cerebro.plot(style='candlestick', barup='red', bardown='green')