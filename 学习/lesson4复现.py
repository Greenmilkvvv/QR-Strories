# lesson 4 交易-上

'''
Backtrader 在交易中的工作流: 

Step1: 设置交易条件: 初始资金、交易税费、滑点、成交量限制等;
Step2: 在 Strategy 策略逻辑中下达交易指令 buy、sell、close, 或取消交易 cancel;
Step3: Order 模块会解读交易订单, 解读的信息将交由经纪商 Broker 模块处理；
Step4: 经纪商 Broker 会根据订单信息检查订单并确定是否接收订单;
Step5: 经纪商 Broker 接收订单后, 会按订单要求撮合成交 trade, 并进行成交结算;
Step6: Order 模块返回经纪商 Broker 中的订单执行结果. 
'''

# %%
# 第1章 Broker 中的交易条件

# 第1.1节 资金管理





# %%
# 第1.2节 持仓查询




# %%
# 第2章 滑点管理

# 第2.1节 百分比滑点



# %%
# 第2.2节 固定滑点



#%%
# 第2.3节 有关滑点的其他设置







# %%
# 第3章 交易税费管理

# 第3.1节 通过 BackBroker() 设置



# %%
# 第3.2节 通过 setcommission() 设置







# %%
# 第3.3节 通过 addcommissioninfo() 设置



# %%
# 第3.3.1节 自定义交易费用的例子1：自定义期货百分比费用





# %%
# 第3.3.2节 自定义交易费用的例子2：考虑佣金和印花税的股票百分比费用




# %%
# 第4章 成交量限制管理

# 第4.1节 形式1：bt.broker.fillers.FixedSize(size) 





# %%
# 第4.2节 形式2：bt.broker.fillers.FixedBarPerc(perc)


# %%
# 第4.3节 形式3：bt.broker.fillers.BarPointPerc(minmov=0.01，perc=100.0)




# %%
# 第5章 交易时机管理
# 第5.1节 Cheat-On-Open




# %%
# 第5.2节 Cheat-On-Close



