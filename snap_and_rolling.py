
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as subplots
import streamlit as st
from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests
import os
import json
import sys
import ccxt

from shroomdk import ShroomDK

import math







st.set_page_config(layout="wide")


st.write("""

""")




sdk = ShroomDK('d939cf57-7bd9-408c-9a7f-58c4cc900b03')
fig = go.Figure()
df_combined = pd.DataFrame()
combined_assets_df = pd.DataFrame()
for file in os.listdir('joint_liq'):
    df = pd.read_csv('joint_liq/' + file)
    try:
        df = df.drop(columns=['Unnamed: 0'])
    except:
        pass
  
    if file.startswith('AAVE'):
        # skip AAVE
        continue



    # name is the string before _ in the file name
    name = file.split('_')[0]





    df = df.dropna()
    df['price_volatility_60'] = df['price_volatility'].rolling(60).mean()
    df['rolling_USDT_60'] =  df['combined_USDT'].rolling(60).mean()
    # df['rolling_USDT_Vola_60'] = df['rolling_USDT_60'].rolling(60).mean()
    df['liquidity_volatility_60'] = df['combined_USDT'].pct_change().rolling(60).std()*(252**0.5)
    df['formula_c'] = (((df['price_volatility'] ** 0.5) / (df['rolling_USDT_Vola']) ) / df['rolling_USDT']) * 10000000000
    df['formula_a'] = ((df['price_volatility'] ** 2) / df['rolling_USDT']) * 100000000000
    df['formula_c_60_fixed'] = (((df['price_volatility_60'] ** 0.5) / (df['liquidity_volatility_60']) ) / df['rolling_USDT_60']) * 10000000000
    df['formula_a_60_fixed'] = ((df['price_volatility_60'] ** 2) / df['rolling_USDT_60']) * 100000000000
    
    
    
    


    
    df = df.drop(columns=['OLD_COLLATERAL'])

    # rename columns
    # b_price is Asset Price
    # price_volatility is Asset Volatility (30 Days)
    # combined_USDT is Asset Liquidity
    # rolling_USDT is Asset Liquidity (30 Days)
    # rolling_USDT_Vola is Asset Liquidity Volatility (30 Days)
    # price_volatility_60 is Asset Volatility (60 Days)
    # rolling_USDT_60 is Asset Liquidity (60 Days)
    #  rolling_USDT_Vola_60 is Asset Liquidity Volatility (60 Days)
    # liquidity_volatility_60 is Asset Liquidity Volatility (60 Days)
    # formula_c is  Formula C
    # formula_a is Formula A
    # formula_c_60_fixed is Formula C (60 Days)
    # formula_a_60_fixed is Formula A (60 Days)

    df = df.rename(columns={'b_price': 'Asset Price', 
    'price_volatility': 'Asset Volatility (30 Days)',
     'combined_USDT': 'Asset Liquidity', 
     'rolling_USDT': 'Asset Liquidity (30 Days)', 
     'rolling_USDT_Vola': 'Asset Liquidity Volatility (30 Days)',
      'price_volatility_60': 'Asset Volatility (60 Days)', 
     'rolling_USDT_60': 'Asset Liquidity (60 Days)', 
    #  'rolling_USDT_Vola_60': 'Asset Liquidity Volatility (60 Days)', 
     'liquidity_volatility_60': 'Asset Liquidity Volatility (60 Days)', 
     'formula_c': 'Formula C',
      'formula_a': 'Formula A',
       'formula_c_60_fixed': 'Formula C (60 Days)',
        'formula_a_60_fixed': 'Formula A (60 Days)'})
    # st.write(df.columns)


    with st.expander(    name
):
        st.write(df)

        for col in df.columns:
            if col == 'block_timestamp':
                continue
            if col == 'TX_HASH':    
                continue
            if col == 'TOKEN_ADDRESS':
                continue
            if col == 'index':
                continue
            if col == 'block':
                continue
            try:
                st.plotly_chart(px.line(df, x='block_timestamp', y=col, title=col), use_container_width=True)
            except:
                pass

        fig = go.Figure()
        fig = subplots.make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['NEW_COLLATERAL'], name='NEW_COLLATERAL'), secondary_y=False)
        fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['Formula A'], name='Formula A'), secondary_y=True)
        fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['Formula A (60 Days)'], name='Formula A (60 Days)'), secondary_y=True)
        fig.update_layout(title='Formula A', xaxis_title='Date', yaxis_title='Value')
        st.plotly_chart(fig, use_container_width=True)

        fig = go.Figure()
        fig = subplots.make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['NEW_COLLATERAL'], name='NEW_COLLATERAL'), secondary_y=False)
        fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['Formula C'], name='Formula C'),     secondary_y=True)
        fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['Formula C (60 Days)'], name='Formula C (60 Days)'), secondary_y=True)
        fig.update_layout(title='Formula C', xaxis_title='Date', yaxis_title='Value')
        st.plotly_chart(fig, use_container_width=True)



    df_last = df.iloc[-2:-1]
    df_last['asset'] = name
    df_last = df_last.reset_index()
    df_combined = df_combined.append(df_last)
    df['assert'] = name
    combined_assets_df = combined_assets_df.append(df)

df_combined = df_combined.drop(columns=['TX_HASH', 'index', 'TOKEN_ADDRESS'])
df_combined = df_combined.reset_index()
try:
    df_combined = df_combined.drop(columns=['index']) 
except:
    pass
try:
    df_combined = df_combined.drop(columns=['TX_HASH']) 
except:
    pass


st.title('Combined Assets')
st.write(df_combined)




df_corr = df_combined.corr()
st.title('Correlation')
st.write(df_corr)
fig = go.Figure(data=go.Heatmap(
                     z=df_corr.values,
                        x=df_corr.columns,
                        y=df_corr.columns,
                        colorscale='Viridis'))
st.plotly_chart(fig, use_container_width=True)
st.write("all assets")
st.write(combined_assets_df)










