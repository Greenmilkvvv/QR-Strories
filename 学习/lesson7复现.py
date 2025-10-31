# Lesson7: Backtrader来啦: 可视化篇（重构）

# %%

# 第1章 observers 观测器

'''
backtrader.observers.Broker: 
    记录了经纪商 broker 中各时间点的可用资金和总资产; 可视化时, 会同时展示 cash 和 values 曲线; 
    如果想各自单独展示 cash 和 values, 可以分别调用 backtrader.observers.Cash 和 backtrader.observers.Value; 

backtrader.observers.BuySell: 
    记录了回测过程中的买入和卖出信号; 可视化时, 会在价格曲线上标注买卖点; 

backtrader.observers.Trades: 
    记录了回测过程中每次交易的盈亏（从买入建仓到卖出清仓算一次交易）; 可视化时, 会绘制盈亏点; 

backtrader.observers.TimeReturn: 
    记录了回测过程中的收益序列; 可视化时, 会绘制 TimeReturn 收益曲线; 

backtrader.observers.DrawDown: 
    记录了回测过程的回撤序列; 可视化时, 绘制回撤曲线; 

backtrader.observers.Benchmark: 
    记录了业绩基准的收益序列, 业绩基准的数据必须事先通过 adddata、resampledata、replaydata 等数据
    添加函数添加进大脑中 cerebro; 可视化时, 会同时绘制策略本身的收益序列
    （即: backtrader.observers.TimeReturn 绘制的收益曲线）和业绩基准的收益曲线。
'''

# %%

## 第1.1节 如何添加 observers

'''
addobserver(obscls, *args, **kwargs):
    observers 观测器是通过 addobserver() 添加给大脑 cerebro 的：
    参数 obscls 对应 observers 类下的观测器、*args, **kwargs 对应观测器支持设置的参数

bt.Cerebro(stdstats=False):
    对于 Broker、Trades、BuySell 3个观测器, 默认是自动添加给 cerebro 的, 
    可以在实例化大脑时, 通过 stdstats 来控制: bt.Cerebro(stdstats=False) 表示可视化时, 
    不展示 Broker、Trades、BuySell 观测器；反之, 自动展示；默认情况下是自动展示。
'''

import backtrader as bt 
import pandas as pd

cerebro = bt.Cerebro(stdstats=False)  # stdstats=False 表示不展示 Broker、Trades、BuySell 观测器
cerebro.addobserver(bt.observers.Broker)  # 添加 xxx 观测器
cerebro.addobserver(bt.observers.Trades)  
cerebro.addobserver(bt.observers.BuySell)  
cerebro.addobserver(bt.observers.DrawDown)
cerebro.addobserver(bt.observers.TimeReturn)

# 添加业绩基准时, 需要事先将业绩基准的数据添加给 cerebro
# banchdata = bt.feeds.PandasData(dataname=data, fromdate=st_date, todate=ed_date)
# cerebro.adddata(banchdata, name='xxxx')
# cerebro.addobserver(bt.observers.Benchmark, data=banchdata)


# %%

## 第1.2节 如何读取 observers 中的数据
'''
observers 中记录了各种回测数据, 可以将其看作是一个支持可视化展示的数据存储器, 
所以 observers 属于 lines 对象。如果想在 Strategy 中读取 observers 中的数据, 
就会用到 line 的相关操作, observers 的数据通过 self.stats 对象 来连接。

【注意时间】
observers 是在所有指标被计算完之后、在执行 Strategy 的 next 方法之后才运行并统计数据的, 
所以读取的最新数据 [0] 相对与 next 的当前时刻是晚一天的。
比如 2019-04-08 的总资产为 99653.196672, 2019-04-09 的总资产为 99599.008652, 
2019-04-09 这一天的收益为 -0.0005437, 如果在 next 通过 self.stats.timereturn.line[0] 提取, 
取值为 -0.0005437 时, 对应的 next 的当前时间是  2019-04-10
'''

class MyStrategy(bt.Strategy): 
    def next(self): 
        # 当前时点的前一天的可用现金 
        print( self.stats.broker.cash[0] )
        # 当前时点的前一天的总资产
        print( self.stats.broker.value[0] ) 
        # 当前时点的前一天的收益
        print( self.stats.timereturn.line[0] )
        # observers 取得[0]值，对应的 next 中 self.data.datetime[-1] 这一天的值


# %% 

## 第1.3节 自定义 observers   

'''
和之前各种自定义一致，自定义 observers 同样是在继承父类  bt.observer.Observer 的基础上, 自定义新的的observers。
下面是 Backtrader 官网提供的例子，用于统计已成功创建的订单的价格和到期订单的价格。
'''

class OrderObserver(bt.observer.Observer): 
    lines = ('created', 'expired') 

    plotinfo = dict( 
        plot = True, subplot = True,plotlinelabels = True
    )

    plotlines = dict( 
        created=dict(marker='*', markersize=8.0, color='lime', fillstyle='full'),
        expired=dict(marker='s', markersize=8.0, color='red', fillstyle='full')
    )

    def next(self): 
        for order in self._owner._orderspending:
            if order.data is not self.data:
                continue

            if not order.isbuy():
                continue

            # Only interested in "buy" orders, because the sell orders
            # in the strategy are Market orders and will be immediately
            # executed

            if order.status in [bt.Order.Accepted, bt.Order.Submitted]:
                self.lines.created[0] = order.created.price

            elif order.status in [bt.Order.Expired]:
                self.lines.expired[0] = order.created.price

'''
observers 本身是 Lines 对象，所以构建逻辑与自定义 Indicator 类似，
将要统计的数据指定为相应的 line，然后随着回测的进行依次存入数据；

作为 Lines 对象的 Observers 和 Indicator ，类内部都有 
plotinfo = dict(...)、plotlines = dict(...) 属性，
用于回测结束后通过 cerebro.plot() 方法进行可视化展示；

有时候如果想修改 Backtrader 已有观测器的相关属性，可以直接继承该观测器，然后设置属性取值进行修改。
如下面在原始 bt.observers.BuySell 的基础上，修改买卖点的样式。
'''
