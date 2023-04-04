import streamlit as st
import pandas as pd
import os 
from shroomdk import ShroomDK
import plotly.subplots as subplots
from plotly import *
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import sys
import ccxt
st.set_page_config(layout="wide")
sdk = ShroomDK('d939cf57-7bd9-408c-9a7f-58c4cc900b03')
def run_query_flipside(query):
    try:
        df = pd.DataFrame(sdk.query(query).rows, columns=sdk.query(query).columns)
        return df
    except:
        st.write('Query failed')
        st.write(sdk.query(query).error)
        return None




suppy_caps = '''with
  compound as (
    SELECT
      BLOCK_NUMBER as block_number_,
      TX_HASH,
      BLOCK_TIMESTAMP as block_timestamp_,
      EVENT_INPUTS:pToken as token,
EVENT_INPUTS:newBorrowCap/1000000000000000000 as newBorrowCap
    FROM  
      ethereum.core.fact_event_logs
    WHERE
      CONTRACT_ADDRESS = lower('0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b')
      AND EVENT_NAME = ('NewBorrowCap')
  ),
  labels as (
    select
      ADDRESS,
      SYMBOL
    from
      ethereum.core.dim_contracts
    where
      ADDRESS IN (
        select
          token
        from
          compound
      )
  ),
  add_symbol as (
    SELECT
      *
    FROM
      compound
      left join labels on labels.ADDRESS = compound.token
  )
SELECT
  BLOCK_NUMBER_,
  BLOCK_TIMESTAMP_,
  SYMBOL,
  TX_HASH,
  TOKEN as TOKEN_ADDRESS,
newBorrowCap
from
  add_symbol'''





reserves = '''
with hourly as (
SELECT
  BLOCK_HOUR,
  UNDERLYING_SYMBOL,
  median(RESERVES_TOKEN_AMOUNT) as RESERVES_TOKEN_AMOUNT,
  median(BORROWS_TOKEN_AMOUNT) as BORROWS_TOKEN_AMOUNT,
  median(SUPPLY_TOKEN_AMOUNT) as SUPPLY_TOKEN_AMOUNT
from
  ethereum.compound.ez_market_stats
where
  CTOKEN_ADDRESS in (
    lower('0x35a18000230da775cac24873d00ff85bccded550'),
    lower('0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e'),
    lower('0xface851a4921ce59e912d19329929ce6da6eb0c7'),
    lower('0x80a2ae356fc9ef4305676f7a3e2ed04e12c33946'),
    lower('0x95b4ef2869ebd94beb4eee400a99824bf5dc325b'),
    lower('0x4b0181102a0112a2ef11abee5563bb4a3176c9d7'),
    lower('0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407')
  )
  and RESERVES_TOKEN_AMOUNT > 0
  and BORROWS_TOKEN_AMOUNT > 0
  and SUPPLY_TOKEN_AMOUNT > 0
group by
  UNDERLYING_SYMBOL,
  BLOCK_HOUR
order by
  BLOCK_HOUR asc
)
select date_trunc('day', BLOCK_HOUR) as day, 
 UNDERLYING_SYMBOL,
  median(RESERVES_TOKEN_AMOUNT) as RESERVES_TOKEN_AMOUNT,
  median(BORROWS_TOKEN_AMOUNT) as BORROWS_TOKEN_AMOUNT,
  median(SUPPLY_TOKEN_AMOUNT) as SUPPLY_TOKEN_AMOUNT
from hourly

group by 
UNDERLYING_SYMBOL,
day
order by day desc
'''
# @st.cache
def get_caps():
    df_caps = run_query_flipside(suppy_caps)
    return df_caps



df_caps = get_caps()
# 
df_caps['NEWBORROWCAP'] = df_caps['NEWBORROWCAP'].astype(float)
df_caps['block_number_'] = df_caps['BLOCK_NUMBER_'].apply(lambda x: int(x / 6000) * 6000)
# remove c  from symbol
df_caps['SYMBOL'] = df_caps['SYMBOL'].apply(lambda x: x[1:])
#     big_df = big_df.groupby(['block']).agg({'volume for slippage 5%': 'sum'}).reset_index()
# df_caps = df_caps.groupby(['block_number_', 'SYMBOL']).agg({'NEWBORROWCAP': 'sum'}).reset_index()
# ffill block number

# df_caps  = df_caps.groupby(['SYMBOL']).apply(lambda x: x.ffill())
df_caps['day'] = pd.to_datetime(df_caps['BLOCK_TIMESTAMP_'])
# strip time from datetime
df_caps['day'] = df_caps['day'].dt.date
st.write(df_caps)


# @st.cache
def get_reserves():
    df_reserves = run_query_flipside(reserves)
    return df_reserves


df_reserves = get_reserves()
df_reserves['DAY'] = pd.to_datetime(df_reserves['DAY'])
# strip time from datetime
df_reserves['DAY'] = df_reserves['DAY'].dt.date
df_reserves['utilization'] = (df_reserves['BORROWS_TOKEN_AMOUNT']/df_reserves['SUPPLY_TOKEN_AMOUNT']) * 100
#     big_df['block'] = big_df['block'].apply(lambda x: int(x / 6000) * 6000)
# df_reserves['block'] = df_reserves['BLOCK_NUMBER_'].apply(lambda x: int(x / 6000) * 6000)

st.write(df_reserves)
st.plotly_chart(px.line(df_reserves, x='DAY', y='utilization', color='UNDERLYING_SYMBOL', title='Reserves Utilization'), use_container_width=True)

mega_df = pd.DataFrame()
list_of_assets = ['ZRX', 'UNI', 'YFI', 'MKR', 'AAVE', 'LINK', 'BAT', 'SUSHI']
for name in list_of_assets:
    df_caps_MKR = df_caps[df_caps['SYMBOL'] == f'{name}'].reset_index()
    df_reserves_MKR = df_reserves[df_reserves['UNDERLYING_SYMBOL'] == f'{name}'].reset_index()
    mkr_filled = pd.read_csv(f'filled_info/{name}_filledInfo.csv')
    df_caps_MKR = df_caps_MKR.drop(columns=[ 'day','BLOCK_NUMBER_', 'BLOCK_TIMESTAMP_', 'TX_HASH', 'TOKEN_ADDRESS', 'index'])
    min_block = df_caps_MKR['block_number_'].min()
    # st.write(mkr_filled)
    max_block = mkr_filled['block'].max()
    try:
        df_caps_MKR = df_caps_MKR.drop(columns=['index'])
    except:
        pass

    df_caps_MKR = df_caps_MKR.set_index('block_number_')
    df_caps_MKR = df_caps_MKR.reindex(range(min_block,max_block, 6000))
    df_caps_MKR = df_caps_MKR.fillna(method='ffill')
    df_caps_MKR['block_number_'] = df_caps_MKR.index
    df_caps_MKR = df_caps_MKR.reset_index(drop=True)
    mkr_filled['block_timestamp'] = pd.to_datetime(mkr_filled['block_timestamp'])
    df_reserves_MKR['DAY'] = pd.to_datetime(df_reserves_MKR['DAY'])
    merged_df_0 = pd.merge(mkr_filled, df_reserves_MKR, how='left', left_on='block_timestamp', right_on='DAY')
    merged_df_1 = pd.merge(merged_df_0, df_caps_MKR, how='left', left_on='block', right_on='block_number_')
    # st.write(merged_df_1)
    merged_df_1['C_Inverse_30'] = 10000000- merged_df_1['Formula C'] 
    merged_df_1['C_Inverse_60'] = 10000000- merged_df_1['Formula C (60 Days)'] 

    try:   
        merged_df_1 = merged_df_1.drop(columns=['index'])
    except:
        pass
    try:   
        merged_df_1 = merged_df_1.drop(columns=['DAY'])
    except:
        pass
    try:   
        merged_df_1 = merged_df_1.drop(columns=['Unnamed: 0'])
    except:
        pass
    try:   
        merged_df_1 = merged_df_1.drop(columns=['LTV'])
    except:
        pass 
    try:   
        merged_df_1 = merged_df_1.drop(columns=['LB'])
    except:
        pass
     
    try:   
        merged_df_1 = merged_df_1.drop(columns=['LT'])
    except:
        pass 

    try:   
        merged_df_1 = merged_df_1.drop(columns=['ASSET'])
    except:
        pass 
    try:   
        merged_df_1 = merged_df_1.drop(columns=['ADDRESS'])
    except:
        pass 
    # merged_df_1['Formula B'] = (merged_df_1['utilization']    ) 
    # try:   
    #     merged_df_1 = merged_df_1.dropna()
    # except:

    #     pass 
    # st.write(merged_df_1)

    merged_df_1['Price Volatility Secondary Calc 30 Days'] = merged_df_1['Asset Price'].std()/merged_df_1['Asset Price'].rolling(30).mean()
    merged_df_1['Price Volatility Secondary Calc 60 Days'] = merged_df_1['Asset Price'].std()/merged_df_1['Asset Price'].rolling(60).mean()
    merged_df_1['Price Volatility Secondary Calc 90 Days'] = merged_df_1['Asset Price'].std()/merged_df_1['Asset Price'].rolling(90).mean()

    merged_df_1['Asset Liquidity Volatility Secondary Calc 30 Days'] = merged_df_1['Asset Liquidity'].std()/merged_df_1['Asset Liquidity'].rolling(30).mean()
    merged_df_1['Asset Liquidity Volatility Secondary Calc 60 Days'] = merged_df_1['Asset Liquidity'].std()/merged_df_1['Asset Liquidity'].rolling(60).mean()
    merged_df_1['Asset Liquidity Volatility Secondary Calc 90 Days'] = merged_df_1['Asset Liquidity'].std()/merged_df_1['Asset Liquidity'].rolling(90).mean()
    merged_df_1['Formula A Secondary Volatility Calc 30 Days'] = ((merged_df_1['Asset Liquidity Volatility Secondary Calc 30 Days'] ** 2) / merged_df_1['Asset Liquidity']) * 100000000000
    merged_df_1['Formula A Secondary Volatility Calc 60 Days'] = ((merged_df_1['Asset Liquidity Volatility Secondary Calc 60 Days'] ** 2) / merged_df_1['Asset Liquidity']) * 100000000000
    merged_df_1['Formula A Secondary Volatility Calc 90 Days'] = ((merged_df_1['Asset Liquidity Volatility Secondary Calc 90 Days'] ** 2) / merged_df_1['Asset Liquidity']) * 100000000000
    # merged_df_1['formula_a'] = ((merged_df_1['30_day_volatility'] ** 2) / merged_df_1['USDT_slippage_combined']) * 100000000000
    merged_df_1['formula_a_constant_liq'] = (1) / merged_df_1['Asset Liquidity (60 Days)'] * 100000000000



    with st.expander(f'View {name} Data'):
        st.write(merged_df_1)

        st.write(merged_df_1.columns)
        fig = go.Figure()
        fig = subplots.make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=merged_df_1['block_timestamp'], y=merged_df_1['NEW_COLLATERAL'], name='NEW_COLLATERAL'), secondary_y=False)
        fig.add_trace(go.Scatter(x=merged_df_1['block_timestamp'], y=merged_df_1['Formula C'], name='Formula C'), secondary_y=True)
        fig.add_trace(go.Scatter(x=merged_df_1['block_timestamp'], y=merged_df_1['Formula C (60 Days)'], name='Formula C (60 Days)'), secondary_y=True)
        fig.update_layout(title='Formula C', xaxis_title='Date', yaxis_title='Value')
        st.plotly_chart(fig, use_container_width=True)
        fig = go.Figure()
        fig = subplots.make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=merged_df_1['block_timestamp'], y=merged_df_1['NEW_COLLATERAL'], name='NEW_COLLATERAL'), secondary_y=False)
        fig.add_trace(go.Scatter(x=merged_df_1['block_timestamp'], y=merged_df_1['C_Inverse_60'], name='C_Inverse_60'), secondary_y=True)
        fig.add_trace(go.Scatter(x=merged_df_1['block_timestamp'], y=merged_df_1['C_Inverse_30'], name='C_Inverse_30'), secondary_y=True)
        fig.update_layout(title='Formula C Inverse', xaxis_title='Date', yaxis_title='Value')
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(px.line(merged_df_1, x='block_timestamp', y=['Price Volatility Secondary Calc 30 Days', 'Asset Volatility (30 Days)'], title=f'{name} Volatility'), use_container_width=True)
        for col in merged_df_1.columns:
            st.plotly_chart(px.line(merged_df_1, x='block_timestamp', y=col, title=f'{name} {col}'), use_container_width=True)

    df_corr = merged_df_1.corr()
    with st.expander(f'View {name} Corr'):  
        st.title('Correlation')
        st.write(df_corr)
        fig = go.Figure(data=go.Heatmap(
                            z=df_corr.values,
                                x=df_corr.columns,
                                y=df_corr.columns,
                                colorscale='Viridis'))
        st.plotly_chart(fig, use_container_width=True)
        st.write("all assets")

    mega_df = mega_df.append(merged_df_1)


st.write(mega_df)
megadf_corr = mega_df.corr()
with st.expander(f'View All Assets Corr'):
    st.title('Correlation')
    st.write(megadf_corr)
    fig = go.Figure(data=go.Heatmap(
                        z=megadf_corr.values,
                            x=megadf_corr.columns,
                            y=megadf_corr.columns,
                            colorscale='Viridis'))
    st.plotly_chart(fig, use_container_width=True)
    st.write("all assets")


from sklearn import *
