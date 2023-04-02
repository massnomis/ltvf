
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
    # write second to last row
    # st.write(df.iloc[-2:-1])
    # write second to last row
    # drop na
    name = file.split('_')[0]
    st.write(name)

    df = df.dropna()
    df['price_volatility_60'] = df['price_volatility'].rolling(60).mean()
    df['rolling_USDT_60'] =  df['combined_USDT'].rolling(60).mean()

    df['rolling_USDT_Vola_60'] = df['rolling_USDT_60'].rolling(60).mean()
    df['liquidity_volatility_60'] = df['combined_USDT'].pct_change().rolling(60).std()*(252**0.5)














    df['formula_c'] = (((df['price_volatility'] ** 0.5) / (df['rolling_USDT_Vola']) ) / df['rolling_USDT']) * 10000000000
    df['formula_a'] = ((df['price_volatility'] ** 2) / df['rolling_USDT']) * 100000000000
    
    df['formula_c_60_fixed'] = (((df['price_volatility_60'] ** 0.5) / (df['rolling_USDT_Vola_60']) ) / df['rolling_USDT_60']) * 10000000000
    df['formula_a_60_fixed'] = ((df['price_volatility_60'] ** 2) / df['rolling_USDT_60']) * 100000000000
    
    st.write(file)
    st.write(df)
    # df['OLD']
    df = df.drop(columns=['OLD_COLLATERAL'])
    # df['block_timestamp'] = df['block_timestamp'].astype(str)
    df_last = df.iloc[-2:-1]

    # df_last['block_timestamp'] = str(df_last['block_timestamp'])
    # st.write(df_last)
    df_last['asset'] = file
    df_last = df_last.reset_index()
    # st.bar_chart(df_last)
    # fig.add_trace(go.Scatter(x=df['NEW_COLLATERAL'], y=df['rolling_USDT'], name=file))

    st.plotly_chart(px.scatter(df, x="block_timestamp", y="rolling_USDT", title=file), use_container_width=True)
    st.plotly_chart(px.scatter(df, x="block_timestamp", y="NEW_COLLATERAL", title=file), use_container_width=True)
    st.plotly_chart(px.scatter(df, x="block_timestamp", y="rolling_USDT_Vola", title=file), use_container_width=True)
    st.plotly_chart(px.scatter(df, x="block_timestamp", y="formula_c", title=file), use_container_width=True)
    fig = go.Figure()
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'))

    fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['formula_c'], name="formula_c", yaxis='y1'))
    # y2
    fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['NEW_COLLATERAL'], name="LTV", yaxis='y2'))
    # fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['formula_a'], name="formula_a", yaxis='y1'))
    df_combined = df_combined.append(df_last)
    df['assert'] = file
    combined_assets_df = combined_assets_df.append(df)
    st.plotly_chart(fig, use_container_width=True)

    fig_60 = go.Figure()
    fig_60.update_layout(yaxis2=dict(overlaying='y', side='right'))

    fig_60.add_trace(go.Scatter(x=df['block_timestamp'], y=df['formula_c_60_fixed'], name="formula_c_60", yaxis='y1'))
    # y2
    fig_60.add_trace(go.Scatter(x=df['block_timestamp'], y=df['NEW_COLLATERAL'], name="LTV", yaxis='y2'))
    # fig_60.add_trace(go.Scatter(x=df['block_timestamp'], y=df['formula_a_60_fixed'], name="formula_a_60", yaxis='y1'))
    # df_combined = df_combined.append(df_last)
    st.plotly_chart(fig_60, use_container_width=True)
    fig = go.Figure()
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'))

    # fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['formula_c'], name="formula_c", yaxis='y1'))
    # y2
    fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['NEW_COLLATERAL'], name="LTV", yaxis='y2'))
    fig.add_trace(go.Scatter(x=df['block_timestamp'], y=df['formula_a'], name="formula_a", yaxis='y1'))
    st.plotly_chart(fig, use_container_width=True)


    fig_60 = go.Figure()
    fig_60.update_layout(yaxis2=dict(overlaying='y', side='right'))

    # fig_60.add_trace(go.Scatter(x=df['block_timestamp'], y=df['formula_c_60_fixed'], name="formula_c_60", yaxis='y1'))
    # y2
    fig_60.add_trace(go.Scatter(x=df['block_timestamp'], y=df['NEW_COLLATERAL'], name="LTV", yaxis='y2'))
    fig_60.add_trace(go.Scatter(x=df['block_timestamp'], y=df['formula_a_60_fixed'], name="formula_a_60", yaxis='y1'))
    # df_combined = df_combined.append(df_last)
    
    
    
    st.plotly_chart(fig_60, use_container_width=True)
# st.plotly_chart(fig)
df_combined = df_combined.drop(columns=['TX_HASH', 'index', 'TOKEN_ADDRESS'])
df_combined = df_combined.reset_index()
st.write(df_combined)

st.plotly_chart(px.bar(df_combined, x="NEW_COLLATERAL", y="rolling_USDT_Vola", color="asset", title="rolling_USDT_Vola", barmode='group'), use_container_width=True)
st.plotly_chart(px.bar(df_combined, x="NEW_COLLATERAL", y="formula_a", color="asset", title="formula_a", barmode='group'), use_container_width=True)
st.plotly_chart(px.bar(df_combined, x="NEW_COLLATERAL", y="formula_c", color="asset", title="formula_c", barmode='group'), use_container_width=True)
st.plotly_chart(px.bar(df_combined, x="NEW_COLLATERAL", y="rolling_USDT", color="asset", title="rolling_USDT", barmode='group'), use_container_width=True)
st.plotly_chart(px.bar(df_combined, x="NEW_COLLATERAL", y="price_volatility", color="asset", title="price_volatility", barmode='group'), use_container_width=True)




df_corr = df_combined.corr()
st.write(df_corr)
# heatmap
fig = go.Figure(data=go.Heatmap(
                     z=df_corr.values,
                        x=df_corr.columns,
                        y=df_corr.columns,
                        colorscale='Viridis'))
st.plotly_chart(fig, use_container_width=True)
st.write(combined_assets_df)
# combined_assets_df.to_csv('combined_assets_df.csv')










