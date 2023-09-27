#########################################
#Ch7 網格交易機器人
###########################################

import shioaji as sj
import ShioajiLogin
from  ShioajiLogin import shioajiLogin
import datetime
import time

SIMULATION_MODE=True
REBOOT_HOUR=7
QUANTITY=1 #張數
stockid='2881'

api=shioajiLogin(simulation=SIMULATION_MODE)
def DayTradeBot():
    #Start Bot flow at 8 AM
    while(1):        
        cooldown=60
        time.sleep(cooldown)
        now = datetime.datetime.now()
        hour=now.hour
        if(hour<8):
           continue
        if(hour>=14):
           continue
       
    contract = api.Contracts.Stocks[stockid]
    
    import kbars
    yesterday=kbars.sub_N_Days(1)
    sub30days=kbars.sub_N_Days(30)
    kbars_1m=kbars.getKbars(api,contract \
                            ,sub30days.strftime('%Y-%m-%d')\
                            ,yesterday.strftime('%Y-%m-%d'))
    kbars_1d=kbars.resampleKbars(kbars_1m,period='1d')
    kbars_last5d=kbars_1d.tail(5)
    #成交價
    stockPrice=api.snapshots([contract])
    
    #處理訂單成交的狀況,用來更新交割款
    def place_cb(stat, msg):
        if "trade_id" in msg:
            code    =msg['code']
            action  =msg['action']
            price   =msg['price']
            quantity=msg['quantity']
            if(action=='Buy'):
                print('buy '+code)
                print('quantity:'+quantity)
                print('price:'+price)
            elif(action=='Sell'):
                print('sell '+code)
                print('quantity:'+quantity)
                print('price:'+price)
            else:
                pass
            
    api.set_order_callback(place_cb)
       
    lastCandle=kbars_last5d.iloc[-1]
    #爆大量
    cond1=lastCandle['Volume']>kbars_last5d['Volume'].mean()
    #上漲
    cond2=lastCandle['Close']>=lastCandle['Open']*1.02
    increase=lastCandle['Close']-lastCandle['Open']
    #沒有上影線
    upper_shadow=lastCandle['High']-lastCandle['Close']
    cond3=upper_shadow<increase*0.05
    #確認股票可以當沖
    cond4=contract.day_trade.name=='Yes'
    print('cond1:'+str(cond1))
    print('cond2:'+str(cond2))
    print('cond3:'+str(cond3))
    print('cond4:'+str(cond4))
    cond=cond1 and cond2 and cond3 and cond4
    #用來更新買賣訊號和下單的迴圈        
    sentdeal=False
    while(1):
        cooldown=60
        #sleep to n seconds 
        time.sleep(cooldown)
        
        now = datetime.datetime.now()
        hour=now.hour
        if(hour<9):
           continue
        if(hour>=14):
           continue
        minute=now.minute
        #calculate conditions here
        if(hour==9 and sentdeal==False):
            
            #send orders here
            if(cond):
                order = api.Order(
                    price=stockPrice, 
                    quantity=QUANTITY, 
                    action=sj.constant.Action.Buy, 
                    price_type=sj.constant.StockPriceType.MKT, 
                    order_type=sj.constant.OrderType.ROD, 
                    order_cond =sj.constant.STOCK_ORDER_COND_CASH,
                    order_lot=sj.constant.StockOrderLot.Common, 
                    # daytrade_short=False,
                    account=api.stock_account
                )
                trade = api.place_order(contract, order)
                print('Buy')
            #else pass
            sentdeal=True
        if(hour==13 and minute>20 and sentdeal==True):
            #send orders here
            if(cond):
                order = api.Order(
                    price=stockPrice, 
                    quantity=QUANTITY, 
                    action=sj.constant.Action.Sell, 
                    price_type=sj.constant.StockPriceType.MKT, 
                    order_type=sj.constant.OrderType.ROD, 
                    order_cond =sj.constant.STOCK_ORDER_COND_CASH,
                    order_lot=sj.constant.StockOrderLot.Common, 
                    daytrade_short=sj.constant.DayTrade.Yes,
                    account=api.stock_account
                )
                trade = api.place_order(contract, order)
                print('Sell')
            sentdeal=False
            break
        
DayTradeBot()
while(1):         
    #check reboot once per 30 minutes
    current_time = time.time()
    cooldown=60*30
    time_to_sleep = cooldown - (current_time % cooldown)
    time.sleep(time_to_sleep)
    
    #check weekday and hour
    now = datetime.datetime.now()
    hour=now.hour
    weekday= now.weekday()
    print('hour:',hour)
    if(hour==REBOOT_HOUR):
        print('reboot bot')
        api.logout()
        api=shioajiLogin(simulation=SIMULATION_MODE)
        DayTradeBot()