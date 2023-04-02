
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    st.title(name)

    df = df.dropna()
    df['price_volatility_60'] = df['price_volatility'].rolling(60).mean()
    df['rolling_USDT_60'] =  df['combined_USDT'].rolling(60).mean()
    df['rolling_USDT_Vola_60'] = df['rolling_USDT_60'].rolling(60).mean()
    df['liquidity_volatility_60'] = df['combined_USDT'].pct_change().rolling(60).std()*(252**0.5)
    df['formula_c'] = (((df['price_volatility'] ** 0.5) / (df['rolling_USDT_Vola']) ) / df['rolling_USDT']) * 10000000000
    df['formula_a'] = ((df['price_volatility'] ** 2) / df['rolling_USDT']) * 100000000000
    df['formula_c_60_fixed'] = (((df['price_volatility_60'] ** 0.5) / (df['rolling_USDT_Vola_60']) ) / df['rolling_USDT_60']) * 10000000000
    df['formula_a_60_fixed'] = ((df['price_volatility_60'] ** 2) / df['rolling_USDT_60']) * 100000000000
    st.write(df)
    df = df.drop(columns=['OLD_COLLATERAL'])

    for col in df.columns:
        if col == 'block_timestamp':
            continue
        
        st.plotly_chart(px.line(df, x='block_timestamp', y=col, title=col), use_container_width=True)







    df_last = df.iloc[-2:-1]
    df_last['asset'] = file
    df_last = df_last.reset_index()

    df_combined = df_combined.append(df_last)
    df['assert'] = file


    combined_assets_df = combined_assets_df.append(df)

df_combined = df_combined.drop(columns=['TX_HASH', 'index', 'TOKEN_ADDRESS'])
df_combined = df_combined.reset_index()
st.write(df_combined)




df_corr = df_combined.corr()
st.write(df_corr)
fig = go.Figure(data=go.Heatmap(
                     z=df_corr.values,
                        x=df_corr.columns,
                        y=df_corr.columns,
                        colorscale='Viridis'))
st.plotly_chart(fig, use_container_width=True)
st.write(combined_assets_df)










