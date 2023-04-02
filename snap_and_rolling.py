
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


st.title("""
Compound LTV Changes and Analysis
""")

st.markdown("""
There has been frequent discussion recently on analyzing risk parameters for digital assets in lending protocols. More an art than a science, these risk parameters are often calculated based on a variety of internal and external datapoints and occurrences. However, there is no reason why risk models, and LTV ratios in particular, should not be scientifically and mathematically monitored. As an initial try to find a best fit LTV ratio for a variety of crypto assets, three unique formulas were attempted to model the crypto-assets LTV changes. 


Prior to showing the results, it is imperative to introduce the context, definitions, and formulas used in the analysis. 
""")
st.title("""
Tokens
""")
st.markdown("""

All analysis in this report was done on Compound V2. Eight specific tokens (notably, “long tail assets”) were researched and analyzed in this model: ZRX, UNI, YFI, MKR, AAVE, LINK, BAT, SUSHI. MKR, YFI, AAVE, LINK, SUSHI tokens specifically were part of a push to add some longer tail assets to Compound in 2021. BAT, COMP, ZRX are from the earlier days of Compound and UNI is from the middle, right as the UNI token launched. The reasoning as to why these tokens were chosen is due to their small marginal differences (across liquidity, volume, market cap) can show a lot on the underlying metrics of LTV compared to ETH or USDC which are volume and liquidity intensive assets. However, it is notable to share several bad data errors which came up throughout the analysis. Keep these in mind as the results are discussed. Regarding SUSHI, its liquidity will be weaker on Uniswap V2 and Uniswap V3, as Sushiswap is the main venue for this token and thus most of its trading and volume occurs there. On AAVE, its liquidity drops significantly as the AAVE Safety module moved a significant amount of liquidity towards Balancer, while BAT and ZRX lacks liquidity data altogether from its earlier blocks.
""")
st.title("""
Formulas and Definitions
""")
st.markdown("""

Three formulas were used in this analysis. Below are their definitions, the logic behind them, and how they were used throughout the report. 
""")
st.title("""

Definitions used throughout the analysis:
""")
st.code("""
'30_day_volatility' = close.rolling(30).std/close (the standard deviation of the rolling close)
""")
st.code("""
'USDT_slippage_combined' = USDT equivalent quote volume for Uniswap V2 and Uniswap V3 (added)
""")
st.code("""

'v2_v3_ratio_USD' = (v2 liquidity (USDT) at 5%) / (v3 Liquidity (USDT) at 5%)
    """)
st.code("""

'USDT_slippage_combined_volatility' = ['USDT_slippage_combined'].rolling(30).std() / ['USDT_slippage_combined'].rolling(30).mean() 

""")
st.markdown("""




The formulas are the following: 



Formula A (“standard view”):
""")

st.code("""
 ((['30_day_volatility'] ** 2) / ['USDT_slippage_combined']) """)
st.markdown("""
The logic behind this formula is that volatility and slippage are the main drivers for LTV changes, with volatility being weighted higher. Meanwhile, slippage is able to “control” and “buffer” liquidity.




Formula C (“Stickiness By Volatility”)
""")
st.code("""


(((['30_day_volatility'] ** 0.5) / (['USDT_slippage_combined_volatility']) ) / ['USDT_slippage_combined']) 
""")
st.markdown("""

This formula is very similar to A and B, but includes a more quantitative measure on the reaction of liquidity depth towards volatility. 


As you can see, all formulas are relatively similar, yet with acute differences that create practical reasoning for which to use to estimate the LTV based on its formulas. The subsequent report showcases which formula has a best fit correlation (to the naked eye) with the formula and LTV ratio. 
""")
st.title("""
The Results
""")
st.markdown("""

As discussed, the aim of this analysis is to estimate (or even predict) LTV changes based on the varied formulas. It is logical each asset has a different preferred formula than its peers, however these three formulas best exemplify that volatility and slippage are the main drivers of LTV changes, yet some assets need a preference for their stickiness of their liquidity or their liquidity depth. These results are quite informative to understand the dynamics of these assets. 

""")
st.title("""









Takeaways

""")
st.markdown("""

Overall, Formula C has the best fit correlation to the LTV ratio. This is because it is able to capture the stickiness of liquidity depth towards volatility. This is especially true for the longer tail assets, as they are more volatile and have less liquidity depth.

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










