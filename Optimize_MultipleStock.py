# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 13:50:16 2023

@author: user
"""
import shioaji as sj
from  ShioajiLogin import shioajiLogin
import kbars
import backtesttool
import numpy as np
import pandas as pd
SIMULATION_MODE=True
avgDays=5
rise=1.02
shadowlimit=0.05
Commission=0.001425
Tax=0.0015
Trading_cost=Commission+Tax
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

api=shioajiLogin(simulation=SIMULATION_MODE)
stocks_kbars_1d={}
for stockid in stockids:    
    contract = api.Contracts.Stocks[stockid]
    yesterday=kbars.sub_N_Days(1)
    lastyear=kbars.sub_N_Days(365)
    kbars_1m=kbars.getKbars(api,contract \
                            ,lastyear.strftime('%Y-%m-%d')\
                            ,yesterday.strftime('%Y-%m-%d'))
    kbars_1d=kbars.resampleKbars(kbars_1m,period='1d')
    stocks_kbars_1d[stockid]=kbars_1d
    
bestparameters={'avgDays':5, "rise":1.02,"shadowlimit":0.05}
bestprofit=0
for avgDays in np.arange(5,30,1):
    for rise in np.arange(1.01,1.10,0.01):
        for shadowlimit in np.arange(0.05,0.5,0.05):                
            conds=[]
            profits=[]
            debugdata=[]
            
            df_all=pd.DataFrame()
            for stockid in stockids:
                kbars_1d=stocks_kbars_1d[stockid]
                k_yesterday=kbars_1d.shift(1)
                cond1=k_yesterday['Volume']>\
                    k_yesterday.rolling(avgDays).mean()['Volume']
                cond2=k_yesterday['Close']>k_yesterday['Open']*rise
                increase=k_yesterday['Close']-k_yesterday['Open']
                upper_shadow=k_yesterday['High']-k_yesterday['Close']
                cond3=upper_shadow<increase*shadowlimit
                cond=cond1 * cond2 * cond3
                profit=kbars_1d[cond]['Close']/kbars_1d[cond]['Open']
                profit=profit-1-Trading_cost
                conds.append(cond)
                profits.append(profit)
            
            #把前面的報酬率綜合起來,一天只交易一檔股票
            profit_combine={}
            for profit in profits:
                d=profit.to_dict()
                for key in d:
                    if(not key  in profit_combine):
                        profit_combine[key]=d[key]
            totalprofit=0
            for key in d:
                totalprofit=totalprofit+profit_combine[key]
            if(totalprofit>bestprofit):
                bestprofit=totalprofit
                bestparameters['avgDays']=avgDays
                bestparameters['rise']=rise                
                bestparameters['shadowlimit']=shadowlimit
                
                
print("bestprofit:"+str(bestprofit))
print("avgDays:"+str(bestparameters['avgDays']))
print("rise:"+str(bestparameters['rise']))
print("shadowlimit:"+str(bestparameters['shadowlimit']))


    