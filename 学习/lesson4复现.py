# lesson 4 交易-上

# %%

import pandas as pd
import backtrader as bt

cerebro = bt.Cerebro()

'''
Backtrader 在交易中的工作流: 

Step1: 设置交易条件: 初始资金、交易税费、滑点、成交量限制等;
Step2: 在 Strategy 策略逻辑中下达交易指令 buy、sell、close, 或取消交易 cancel;
Step3: Order 模块会解读交易订单, 解读的信息将交由经纪商 Broker 模块处理; 
Step4: 经纪商 Broker 会根据订单信息检查订单并确定是否接收订单;
Step5: 经纪商 Broker 接收订单后, 会按订单要求撮合成交 trade, 并进行成交结算;
Step6: Order 模块返回经纪商 Broker 中的订单执行结果. 
'''

# %%
# 第1章 Broker 中的交易条件

'''
回测过程中涉及的交易条件设置, 最常见的有初始资金、交易税费、滑点、期货保证金比率等, 
有时还会对成交量做限制、对涨跌幅做限制、对订单生成和执行时机做限制.

上述大部分交易条件都可以通过 Broker 来管理, 主要有 2 中操作方式: 
- 方式1: 通过设置 backtrader.brokers.BackBroker() 类中的参数, 生成新的 broker 实例, 再将新的实例赋值给 cerebro.broker ;
- 方式2: 通过调用 broker 中的 ”set_xxx“ 方法来修改条件, 还可通过 ”get_xxx“ 方法查看当前设置的条件取值。
'''

# 第1.1节 资金管理

"""
Broker 默认初始资金: 10000, 可通过 cash 参数 和 set_cash() 方法来修改
此外还提供了add_cash() 方法增加或减少资金

Broker 会检查提交的订单现金需求与当前现金是否匹配
cash 也会随着每次交易进行迭代更新用以匹配当前头寸
"""

# 初始化

cerebro.broker.set_cash(100000000.0) # 初始资金
# print('当前初始资金', end='')
cerebro.broker.get_cash() # 查看当前资金


# 简写形式
# cerebro.broker.setcash(100000000.0) # 设置初始资金
# cerebro.broker.getcash() # 获取当前可用资金


# 在strategy 中增加/获取资金

# self.broker.add_cash(10000) # 正数表示增加资金
# self.broker.add_cash(-10000) # 负数表示减少资金
# self.broker.getcash() # 获取当前可用资金


# %%
# 第1.2节 持仓查询

'''
Broker 每次交易后, 都会更新 cash 以及 持仓信息, 
可通过 getposition() 方法查询当前持仓信息 通常在 Strategy 中进行持仓查询操作

当前总资产 = 当前可用资金 + 当前持仓总市值
当前持仓总市值为当前持仓中所有标的各自持仓市值之和, 

如果只有一个标的, 就有:
当前总资产 999943.18 = 当前可用资金 996735.39 + 当前持仓数量 100.00 * 当前 close 32.0779 : 

在计算当前可用资金时, 除了考虑扣除购买标的时的费用外, 还需要考虑扣除交易费用 !!!
'''

class TestStrategy(bt.Strategy): 
    def next(self): 
        print('当前可用资金', self.broker.get_cash())
        print('当前持仓总市值', self.broker.get_value())
        print('当前持仓数量', self.broker.getposition().size)
        print('当前持仓成本', self.broker.getposition().price)

        # 也可以直接获取持仓
        print('当前持仓量', self.getposition(self.data).size)
        print('当前持仓成本', self.getposition(self.data).price)
        # 注: getposition() 需要指定具体的标的数据集

cerebro.addstrategy(TestStrategy)
cerebro.run() # 由于此时未添加数据 所以返回空列表

# %%
# 第2章 滑点管理

'''
实际交易中, 由于市场波动、网络延迟等原因, 交易指令中指定的交易价格与实际成交价格会存在较大差别, 出现滑点.
为了让回测结果更真实, 在交易前可以通过 brokers 设置滑点, 滑点的类型有 2 种: 【百分比滑点】和【固定滑点】

不论哪种设置方式, 都是起到相同的作用: 买入时, 在指定价格的基础上提高实际买入价格; 
卖出时, 在指定价格的基础上, 降低实际卖出价格; 买的 “更贵”, 卖的 “更便宜” 。

注: 在 Backtrader 中, 如果同时设置了百分比滑点和固定滑点, 前者的优先级高于后者, 最终按百分比滑点的设置处理。
'''

# 第2.1节 百分比滑点
'''
假设设置了 n% 的滑点, 如果指定的买入价为 x, 那实际成交时的买入价会提高至 x * (1+ n%) ; 
同理, 若指定的卖出价为 x, 那实际成交时的卖出价会降低至 x * (1- n%), 下面时将滑点设置为 0.01% 的例子: 
'''

# 方式1: 通过 BackBroker 类中的 slip_perc 参数设置百分比滑点
cerebro.broker = bt.broker.BackBroker(slip_perc=0.0001) # 设置滑点为 0.01%

# 方式2: 通过调用 brokers 的 set_slippage_perc 方法设置百分比滑点
cerebro.broker.set_slippage_perc(0.0001) # 设置滑点为 0.01%

# %%
# 第2.2节 固定滑点

'''
假设设置了大小为 n 的固定滑点, 如果指定的买入价为 x, 那实际成交时的买入价会提高至 x + n ; 
同理, 若指定的卖出价为 x, 那实际成交时的卖出价会降低至 x - n, 下面时将滑点固定为 0.001 的例子: 
'''

# 方式1: 通过 BackBroker 类中的 slip_fixed 参数设置固定滑点
cerebro.broker = bt.broker.BackBroker(slip_fixed=0.001) # 设置滑点为 0.001

# 方式2: 通过调用 brokers 的 set_slippage_fixed 方法设置固定滑点
cerebro.broker.set_slippage_fixed(fixed=0.001)

#%%
# 第2.3节 有关滑点的其他设置

'''
除了用于设置滑点的 
- slip_perc 
- slip_fixed 
两个参数外, broker 还提供了其他参数用于处理价格出现滑点后的极端情况: 

slip_open: 是否对开盘价做滑点处理;
           该参数在 BackBroker() 类中默认为 False, 
           在 set_slippage_perc 和set_slippage_fixed 方法中默认为 True; 

slip_match: 是否将滑点处理后的新成交价与成交当天的价格区间 low ~ high 做匹配;
            如果为 True, 则根据新成交价重新匹配调整价格区间, 确保订单能被执行, 默认取值为 True; 
            如果为 False, 则不会与价格区间做匹配, 订单不会执行, 但会在下一日执行一个空订单; 

slip_out: 如果新成交价高于最高价或低于最高价, 是否以超出的价格成交;
          如果为 True, 则允许以超出的价格成交; (仅在slip_match=True时才有用, 可以超出最高价/最低价执行; 否则只能执行空订单)
          如果为 False, 实际成交价将被限制在价格区间内  low ~ high, 默认取值为 False; 

slip_limit: 是否对限价单执行滑点;
            如果为 True, 即使 slip_match 为False, 也会对价格做匹配, 确保订单被执行, 默认取值为 True; 
            如果为 False, 则不做价格匹配; 
'''
# 方法1: 
# cerebro.broker = bt.brokers.BackBroker(..., slip_perc=0, slip_fixed=0,  slip_open=False, slip_match=True, slip_out=False, slip_limit=True, ...)

# 方法2: 
# cerebro.broker.set_slippage_fixed(..., fixed=..., slip_open=False, slip_match=True, slip_out=False, slip_limit=True, ...)


# 下面是将滑点设置为固定 0.35 , 对上述参数去不同的值, 标的 600466.SH 在 2019-01-17 的成交情况做对比: 

# 情况1: 
'''由于 slip_open=False , 不会对开盘价做滑点处理, 所以仍然以原始开盘价 32.63307367 成交'''
cerebro.brokerset_slippage_fixed(fixed=0.35,
                   slip_open=False,
                   slip_match=True,
                   slip_out=False)

# 情况2: 
'''
滑点调整的新成交价为 32.63307367+0.35 = 32.98307367, 超出了当天最高价 32.94151482
由于允许做价格匹配 slip_match=True, 但不以超出价格区间的价格执行 slip_out=False
最终以最高价 32.9415 成交
'''
cerebro.set_slippage_fixed(fixed=0.35,
                   slip_open=True,
                   slip_match=True,
                   slip_out=False)

# 情况3: 
'''
滑点调整的新成交价为 32.63307367+0.35 = 32.98307367, 超出了当天最高价 32.94151482
允许做价格匹配 slip_match=True, 而且运行以超出价格区间的新成交价执行 slip_out=True
最终以新成交价 32.98307367 成交
'''
cerebro.set_slippage_fixed(fixed=0.35,
                   slip_open=True,
                   slip_match=True,
                   slip_out=True)

# 情况4: 
'''
滑点调整的新成交价为 32.63307367+0.35 = 32.98307367, 超出了当天最高价 32.94151482
由于不进行价格匹配 slip_match=False, 新成交价超出价格区间无法成交
2019-01-17 这一天订单不会执行, 但会在下一日 2019-01-18 执行一个空订单
再往后的 2019-07-02, 也未执行订单, 下一日 2019-07-03 执行空订单
即使 2019-07-03的 open 39.96627412+0.35 < high 42.0866713 满足成交条件, 也不会补充成交
'''
cerebro.set_slippage_fixed(fixed=0.35,
                   slip_open=True,
                   slip_match=False,
                   slip_out=True)


# %%
# 第3章 交易税费管理

'''
交易费收取规则--------------------------

- 股票: 目前 A 股的交易费用分为 2 部分: 佣金和印花税, 
    1.佣金: 双边征收, 不同证券公司收取的佣金各不相同, 一般在 0.02%-0.03% 左右, 单笔佣金不少于 5 元；
    2.印花税: 只在卖出时收取, 税率为 0.1%。

- 期货: 期货交易费用包括 交易所收取手续费 和 期货公司收取佣金 2 部分, 
    1.交易所手续费较为固定；
    2.不同期货公司佣金不一致, 而且不同期货品种的收取方式不相同, 
        有的按照固定费用收取, 
        有的按成交金额的固定百分比收取: 合约现价*合约乘数*手续费费率
    3.除了交易费用外, 期货交易时还需上交一定比例的保证金

      
交易费收取方式--------------------------

- 根据交易品种的不同: 
    1. 股票 Stock-like 模式
    2. 期货 Futures-like 模式

- 根据计算方式的不同: 
    1. PERC 百分比费用模式
    2. FIXED 固定费用模式

交易费参数--------------------------

1. commission: 手续费 / 佣金；
2. mult: 乘数；
3. margin: 保证金 / 保证金比率 。
4. 双边征收: 买入和卖出操作都要收取相同的交易费用
'''

# 第3.1节 通过 BackBroker() 设置

# BackBroker 中有一个 commission 参数，用来全局设置交易手续费。
# 如果是股票交易，可以简单的通过该方式设置交易佣金，但该方式无法满足期货交易费用的各项设置。
cerebro.broker = bt.brokers.BackBroker(commission= 0.0002)  # 设置 0.0002 = 0.02% 的手续费


# %%
# 第3.2节 通过 setcommission() 设置

# 如果想要完整又方便的设置交易费用，
# 可以调用 broker 的 setcommission() 方法，
# 该方法基本上可以满足大部分的交易费用设置需求







# %%
# 第3.3节 通过 addcommissioninfo() 设置





# %%
# 第3.3.1节 自定义交易费用的例子1: 自定义期货百分比费用





# %%
# 第3.3.2节 自定义交易费用的例子2: 考虑佣金和印花税的股票百分比费用




# %%
# 第4章 成交量限制管理

# 第4.1节 形式1: bt.broker.fillers.FixedSize(size) 





# %%
# 第4.2节 形式2: bt.broker.fillers.FixedBarPerc(perc)


# %%
# 第4.3节 形式3: bt.broker.fillers.BarPointPerc(minmov=0.01, perc=100.0)




# %%
# 第5章 交易时机管理
# 第5.1节 Cheat-On-Open




# %%
# 第5.2节 Cheat-On-Close



