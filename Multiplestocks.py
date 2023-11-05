import shioaji as sj
import ShioajiLogin
from  ShioajiLogin import shioajiLogin
import logging
import datetime
import threading, time
from threading import Thread, Lock
import math
SIMULATION_MODE=True
REBOOT_HOUR=7
money=200000 
stockids=['2330','2317','2454','2412','2382',
          '2308','2881','6505','2882','2303',
          '1303','2886','1301','3711','2891',
          '2002','1216','5880','2884','1326',
          '2207','2892','3045','2885','3231',
          '2395','5871','2301','2880','3008',
          '3037','2912','2357','3034','2345',
          '2603','1101','6669','4904','2408',
          '2887','2327','2890','5876','6488',
          '4938','8069','2379','2883','1590',
          '3661','9910','3443','2801','2356',
          '2376','8046','2633','3529','2618',
          '2609','1402','1605','2377','2888',
          '1102','2105','2615','1476','2383',
          '2324','6409','2610','2409','2474',
          '8454','6415','3481','6446','2360',
          '5347','3017','2353','6770','1504',
          '2834','2347','9945','2344','2371',
          '2368','3044','3702','9941','1229',
          '5274','2449','4958','5483','3533'
          ]
def DayTradeBot():
    api=shioajiLogin(simulation=SIMULATION_MODE)
        
    #Start Bot flow at 8 AM
    while(1):        
        cooldown=60
        time.sleep(cooldown)
        now = datetime.datetime.now()
        hour=now.hour
        if(hour==8):
           break

    class Emptyclass:
        def __init__(self):
            pass
    stockObjects=[]    
    for stockid in stockids:
        stockObjects.append(Emptyclass())
        contract=api.Contracts.Stocks[stockid]            
        import kbars
        yesterday=kbars.sub_N_Days(1)
        sub30days=kbars.sub_N_Days(30)
        kbars_1m=kbars.getKbars(api,contract \
                                ,sub30days.strftime('%Y-%m-%d')\
                                ,yesterday.strftime('%Y-%m-%d'))
        kbars_1d=kbars.resampleKbars(kbars_1m,period='1d')
        kbars_last5d=kbars_1d.tail(5)        
        lastCandle=kbars_last5d.iloc[-1]
        #爆大量
        cond1=lastCandle['Volume']>kbars_last5d['Volume'].mean()
        #上漲
        cond2=lastCandle['Close']>=lastCandle['Open']*1.02
        increase=max(lastCandle['Close']-lastCandle['Open'],\
                     lastCandle['Open']*0.02)
        #沒有上影線
        upper_shadow=lastCandle['High']-lastCandle['Close']
        cond3=upper_shadow<increase*0.05
        #確認股票可以當沖
        cond4=contract.day_trade.name=='Yes'
        cond=cond1 and cond2 and cond3 and cond4
        stockPrice=api.snapshots([contract])[0].close
        stockObjects[-1].stockid=stockid
        stockObjects[-1].contract=contract
        stockObjects[-1].price=stockPrice
        stockObjects[-1].signal=cond
    
        
    #處理訂單成交的狀況
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
       
    #實際下單        
    sentdeal=False
    while(1):
        cooldown=60
        now = datetime.datetime.now()
        hour=now.hour
        if(hour<9):
           #sleep to n seconds 
           time.sleep(cooldown)
           continue
        if(hour>=14):
           break
        minute=now.minute
        #calculate conditions here
        if(hour==9 and sentdeal==False):
            for obj in stockObjects:
                #send orders here
                contract=obj.contract
                stockPrice=api.snapshots([contract])[0].close
                quantity=math.floor(money/(1000*stockPrice))
                stockid=obj.stockid
                cond=obj.signal
                if(quantity<1):
                    continue
                elif(cond):
                    order = api.Order(
                        price=stockPrice, 
                        quantity=quantity, 
                        action=sj.constant.Action.Buy, 
                        price_type=sj.constant.StockPriceType.MKT, 
                        order_type=sj.constant.OrderType.ROD, 
                        order_cond =sj.constant.STOCK_ORDER_COND_CASH,
                        order_lot=sj.constant.StockOrderLot.Common, 
                        # daytrade_short=False,
                        account=api.stock_account
                    )
                    trade = api.place_order(contract, order)
                    print('Buy '+stockid)
                    break
            #else pass
            sentdeal=True
        if(hour==13 and minute>20 and sentdeal==True):
            #send orders here
            if(cond):
                order = api.Order(
                    price=stockPrice, 
                    quantity=quantity, 
                    action=sj.constant.Action.Sell, 
                    price_type=sj.constant.StockPriceType.MKT, 
                    order_type=sj.constant.OrderType.ROD, 
                    order_cond =sj.constant.STOCK_ORDER_COND_CASH,
                    order_lot=sj.constant.StockOrderLot.Common, 
                    daytrade_short=sj.constant.DayTrade.Yes,
                    account=api.stock_account
                )
                trade = api.place_order(contract, order)
                print('Sell '+stockid)
            sentdeal=False
        #sleep to n seconds 
        time.sleep(cooldown)
    api.logout()
        
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
        DayTradeBot()