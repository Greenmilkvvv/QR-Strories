# lesson 1 熟悉backtrader使用方法
# 并没有添加真正的策略 只是将

# %%
import backtrader as bt
import pandas as pd
import datetime    

# %%

# 实例化
cerebro = bt.Cerebro()

# %%

# 数据准备
daily_price = pd.read_csv('daily_price.csv', 
                          parse_dates=['datetime'])
trade_info = pd.read_csv('trade_info.csv', 
                         parse_dates=['trade_date'])

# %%

# 按照股票代码, 传入数据形成资产池, 目标是
    # 使用 unique() 方法 得到唯一的股票代码组合
    ## 对于每一个股票
for stock in daily_price['sec_code'].unique(): 
    ## 1.日期对齐, 获取回测区间中的所有的交易日
    data = pd.DataFrame(daily_price['datetime'].unique(), 
                       columns=['datetime'])
    df = daily_price[ daily_price['sec_code'] == stock ][
        ['datetime', 
         'open', 'high', 'low', 'close', 'volume', 
         'openinterest']
         ]
    data_ = pd.merge(data, df, how = 'left', on = 'datetime')
    data_ = data_.set_index("datetime")

    # 2.数据缺失值处理
    ## 日期对齐时会使得有些交易日的数据为空，所以需要对缺失数据进行填充
    data_.loc[:,['volume', 'openinterest']] = data_.loc[:, ['volume', 'openinterest']].fillna(0)
    ## 使用fillna(method='pad')，也称为前向填充，用前一个有效值来填充当前缺失值, 如果连续缺失 填0
    data_.loc[:,['open', 'high', 'low', 'close']] = data_.loc[:,['open', 'high', 'low', 'close']].fillna(method='pad')
    data_.loc[:,['open', 'high', 'low', 'close']] = data_.loc[:,['open', 'high', 'low', 'close']].fillna(0)
    # 3. 导入数据feed到backtrader的接口
    datafeed = bt.feeds.PandasData(dataname=data_, fromdate = datetime.datetime(2019,1,2), 
                                    todate = datetime.datetime(2021,1,28))
    cerebro.adddata(datafeed, name=stock) # 通过name=stock实现了数据集和资产的一一对应

    print(f"{stock} 传输完成 !")

#%%

# 编写策略

class TestStrategy(bt.Strategy):
    """选股策略"""
    params = (
        ('maperiod', 15),
        ('printlog', False),
    )

    def __init__(self): 
        self.buy_stock = trade_info # 保留调仓数据
        self.trade_dates = pd.to_datetime(self.buy_stock['trade_date'].unique()).tolist()
        self.order_list = []  # 记录以往订单，方便调仓日对未完成订单做处理
        self.buy_stocks_pre = []  # 记录上一期持仓

    def next(self): # next是backtrader的内置函数，在每一个交易日结束时调用
        dt = self.datas[0].datetime.date(0) # 获取当前的回测时间点
        # 如果是调仓日，就调仓操作
        if dt in self.trade_dates: 
            print("--------------{} 为调仓日----------".format(dt))
            if len(self.order_list) > 0: # 如果有未完成的订单，先取消
                for order in self.order_list:
                    self.cancel(order) # 重置订单列表
            # 提取当前调仓日的持仓情况列表
            buy_stocks_data = self.buy_stock[self.buy_stock['trade_date'] == dt]
            long_list = buy_stocks_data['sec_code'].tolist() # 持仓代码
            # 对不想要的资产平仓
            sell_stock = [i for i in self.buy_stocks_pre if i not in long_list]
            print('平仓: ', sell_stock)
            if len(sell_stock) > 0:
                print("-----------对不再持有的股票进行平仓--------------")
                for stock in sell_stock: 
                    data = self.getdatabyname(stock)
                    if self.getposition(data).size > 0: # 如果有持仓
                        order = self.close(data=data) # 平仓
                        self.order_list.append(order) # 记录订单
            # 买入此次调仓的股票 多退少补 调整仓位
            print("-----------对此次调仓的股票进行买入--------------")
            for stock in long_list:

                # 持仓权重提取
                w = buy_stocks_data[buy_stocks_data['sec_code'] == stock]['weight'].iloc[0] 
                data = self.getdatabyname(stock)

                # 为减少可用资金不足的情况，留 5% 的现金做备用
                order = self.order_target_percent(data, w*0.95) # 按照权重买入
                self.order_list.append(order)
            
            self.buy_stocks_pre = long_list # 更新持仓列表

            # 交易记录日志（可省略，默认不输出结果）

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        # 未处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 已经处理过的订单
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy(): # 如果是买入指令
                self.log(
                    'BUY EXECUTED, ref:%.0f，Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                        (order.ref,  # 订单编号
                        order.executed.price,  # 成交价
                        order.executed.value,  # 成交额
                        order.executed.comm,  # 佣金
                        order.executed.size,  # 成交量
                        order.data._name)
                    )
            else: # 卖出指令
                self.log(
                    'SELL EXECUTED, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                         (order.ref,
                          order.executed.price,
                          order.executed.value,
                          order.executed.comm,
                          order.executed.size,
                          order.data._name)
                )


# %%
# 回测系统调试

cerebro.broker.setcash(100000000.0) # 设置初始资金
cerebro.broker.setcommission(commission=0.0003) # 设置交易手续费
cerebro.broker.set_slippage_perc(perc=0.005) # 设置滑点

cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl' ) # 计算每日收益率 返回时间序列
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown') # 计算最大回撤
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio') # 计算夏普比率
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='anunal_return') # 计算年化收益

cerebro.addstrategy(TestStrategy, printlog = True) # 添加策略


#%%
# 启动回测
result = cerebro.run()
# 从返回的 result 中提取回测结果
strat = result[0]
# 返回日度收益率序列
daily_return = pd.Series(strat.analyzers.pnl.get_analysis())

# %%
# 打印评价指标
print("--------------- AnnualReturn -----------------")
print(strat.analyzers.anunal_return.get_analysis())
print("--------------- SharpeRatio -----------------")
print(strat.analyzers.sharpe_ratio.get_analysis())
print("--------------- DrawDown -----------------")
print(strat.analyzers.drawdown.get_analysis())