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
import math
import ccxt
st.set_page_config(layout="wide")
sdk = ShroomDK('d939cf57-7bd9-408c-9a7f-58c4cc900b03')


st.write('''
Our goal here is to come up with a formula that will
''')



def run_query_flipside(query):
    try:
        df = pd.DataFrame(sdk.query(query).rows, columns=sdk.query(query).columns)
        return df
    except:
        st.write('Query failed')
        st.write(sdk.query(query).error)
        return None
def get_price(timestamp, name):
    name = name.replace(' ', '')
    if name == 'WBTC':
        name = 'BTC'
    if name == 'WETH':
        name = 'ETH'
    if name == 'USDT':
        name = 'BUSD'
    if name == 'FEI':
        name = 'BUSD'
    if name == 'DAI':
        name = 'BUSD'
    price = pd.DataFrame(ccxt.binance().fetch_ohlcv(symbol=f'{name}/USDT', timeframe='1d', since=ccxt.binance().iso8601(timestamp), limit=1000))
    price = price[4]
    return price
# with st.expander('dir'):
#     st.write(os.listdir('univ2v3'))
full_volume_df = pd.DataFrame()
for file in os.listdir('univ2v3'):
    if 'full' in file:
        df = pd.read_csv('univ2v3/'+file)
        try:
            df['blocknumber'] = df['blocknumber'].astype('int')
            full_volume_df = pd.merge(full_volume_df, df, how = 'left', on = 'blocknumber')
        except:
            full_volume_df = pd.concat([full_volume_df, df], axis = 1)
    else:
        pass
full_volume_df['blocknumber'] = full_volume_df['blocknumber'].apply(lambda x: int(x / 6500) * 6500)
full_volume_df = full_volume_df.groupby(['blocknumber']).mean().reset_index()
list_of_blocks = str(full_volume_df['blocknumber'].tolist())[1:-1]
q = f'''
select block_number  as  "blocknumber"  , block_timestamp as "block_timestamp" from ethereum.core.fact_blocks
where block_number in ({list_of_blocks})
'''
df_q = run_query_flipside(q)
for col in full_volume_df.columns[1:]:
    full_volume_df.rename(columns={col: col.split('volume')[1]}, inplace=True)
for col in full_volume_df.columns[1:]:
    full_volume_df.rename(columns={col: col.split('for')[0]}, inplace=True)
full_volume_df = pd.merge(full_volume_df, df_q, on='blocknumber')
for col in full_volume_df.columns[1:-2]:
    if col.isupper():
        full_volume_df[col+'_price'] = ''
placeholder_df = st.empty()
full_volume_df['block_timestamp'] = pd.to_datetime(full_volume_df['block_timestamp'])
full_volume_df['block_timestamp'] = full_volume_df['block_timestamp'].apply(lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))



for col in full_volume_df.columns[1:-2]:
    if col.isupper():
        full_volume_df[col+'_price'] = get_price(full_volume_df['block_timestamp'].min(), name=col)
        full_volume_df[col+'_price_eth'] = full_volume_df[col+'_price'] / get_price(full_volume_df['block_timestamp'].min(), name='ETH')
        full_volume_df[col+'liquidity USDT'] = full_volume_df[col+'_price'] * full_volume_df[col]
        full_volume_df[col+'30_day_price_volatiliy'] = (full_volume_df[col+'_price'].std())/(full_volume_df[col+'_price'].rolling(30).mean())
        full_volume_df[col+'30_day_price_volatiliy_eth'] = (full_volume_df[col+'_price_eth'].std())/(full_volume_df[col+'_price_eth'].rolling(30).mean())



LINK_max  = 1000000000
AAVE_max  = 16000000
UNI_max  = 1000000000
YFI_max =  30000
COMP_max = 10000000
SUSHI_max = 250000000
MKR_max =  1005577
BAT_max = 1500000000
ZRX_max  = 1000000000



st.write("We take max supply for each token from the official website and divide the liquidity by it. This gives us an idea of how much of the total supply is liquid.")

full_volume_df['LINK_Liq_div_max_supply'] = (full_volume_df[' LINK ']/LINK_max).rolling(30).mean() *10000
full_volume_df['AAVE_Liq_div_max_supply'] = (full_volume_df[' AAVE ']/AAVE_max).rolling(30).mean()*10000
full_volume_df['UNI_Liq_div_max_supply'] = (full_volume_df[' UNI ']/UNI_max).rolling(30).mean()*10000
full_volume_df['YFI_Liq_div_max_supply'] = (full_volume_df[' YFI ']/YFI_max).rolling(30).mean()*10000
full_volume_df['COMP_Liq_div_max_supply'] = (full_volume_df[' COMP ']/COMP_max).rolling(30).mean()*10000
full_volume_df['SUSHI_Liq_div_max_supply'] = (full_volume_df[' SUSHI ']/SUSHI_max).rolling(30).mean()*10000
full_volume_df['MKR_Liq_div_max_supply'] = (full_volume_df[' MKR ']/MKR_max).rolling(30).mean()*10000
full_volume_df['BAT_Liq_div_max_supply'] = (full_volume_df[' BAT ']/BAT_max).rolling(30).mean()*10000
full_volume_df['ZRX_Liq_div_max_supply'] = (full_volume_df[' ZRX ']/ZRX_max).rolling(30).mean() *10000



# 

st.write("We take the volatility of the price and divide it by the liquidity divided by the max supply. This gives us an idea of how much of the total supply is liquid and how volatile the price is. We then take the exponential of this value to get a value between 0 and 1. The higher the value, Higher the proposed LTV.")

full_volume_df['T_LTV_A_LINK'] = math.e**((full_volume_df[' LINK 30_day_price_volatiliy'] / (full_volume_df['LINK_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_AAVE'] = math.e**((full_volume_df[' AAVE 30_day_price_volatiliy'] / (full_volume_df['AAVE_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_UNI'] = math.e**((full_volume_df[' UNI 30_day_price_volatiliy'] / (full_volume_df['UNI_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_YFI'] = math.e**((full_volume_df[' YFI 30_day_price_volatiliy'] / (full_volume_df['YFI_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_COMP'] = math.e**((full_volume_df[' COMP 30_day_price_volatiliy'] / (full_volume_df['COMP_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_SUSHI'] = math.e**((full_volume_df[' SUSHI 30_day_price_volatiliy'] / (full_volume_df['SUSHI_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_MKR'] = math.e**((full_volume_df[' MKR 30_day_price_volatiliy'] / (full_volume_df['MKR_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_BAT'] = math.e**((full_volume_df[' BAT 30_day_price_volatiliy'] / (full_volume_df['BAT_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ZRX'] = math.e**((full_volume_df[' ZRX 30_day_price_volatiliy'] / (full_volume_df['ZRX_Liq_div_max_supply'])) *-1)
st.plotly_chart(px.scatter(full_volume_df, x = 'block_timestamp', y = [col for col in full_volume_df.columns if '30_day_price_volatiliy' in col], log_y=True), use_container_width=True)

st.plotly_chart(px.scatter(full_volume_df, x = 'block_timestamp', y = [col for col in full_volume_df.columns if 'liquidity USDT' in col]), use_container_width=True)
st.plotly_chart(px.scatter(full_volume_df, x = 'block_timestamp', y = [col for col in full_volume_df.columns if 'Liq_div_max_supply' in col]), use_container_width=True)

full_volume_df['T_LTV_B_LINK'] = (full_volume_df['LINK_Liq_div_max_supply'])/(full_volume_df[' LINK 30_day_price_volatiliy']  )
full_volume_df['T_LTV_B_AAVE'] = (full_volume_df['AAVE_Liq_div_max_supply'])/(full_volume_df[' AAVE 30_day_price_volatiliy']  )
full_volume_df['T_LTV_B_UNI'] = (full_volume_df['UNI_Liq_div_max_supply'])/(full_volume_df[' UNI 30_day_price_volatiliy']  )
full_volume_df['T_LTV_B_YFI'] = (full_volume_df['YFI_Liq_div_max_supply'])/(full_volume_df[' YFI 30_day_price_volatiliy']  )
full_volume_df['T_LTV_B_COMP'] = (full_volume_df['COMP_Liq_div_max_supply'])/(full_volume_df[' COMP 30_day_price_volatiliy']  )
full_volume_df['T_LTV_B_SUSHI'] = (full_volume_df['SUSHI_Liq_div_max_supply'])/(full_volume_df[' SUSHI 30_day_price_volatiliy']  )
full_volume_df['T_LTV_B_MKR'] = (full_volume_df['MKR_Liq_div_max_supply'])/(full_volume_df[' MKR 30_day_price_volatiliy']  )
full_volume_df['T_LTV_B_BAT'] = (full_volume_df['BAT_Liq_div_max_supply'])/(full_volume_df[' BAT 30_day_price_volatiliy']  )
full_volume_df['T_LTV_B_ZRX'] = (full_volume_df['ZRX_Liq_div_max_supply'])/(full_volume_df[' ZRX 30_day_price_volatiliy']  )
st.write("This is the LTV for the 30 day price volatility, without using the log function")
st.plotly_chart(px.scatter(full_volume_df, x = 'blocknumber', y = [col for col in full_volume_df.columns if 'T_LTV_A' in col], log_y=True), use_container_width=True)

st.plotly_chart(px.scatter(full_volume_df, x = 'blocknumber', y = [col for col in full_volume_df.columns if 'T_LTV_B' in col]), use_container_width=True)

st.write("This is the LTV for the 30 day price volatility, using the log function, and multiplying by 10")
full_volume_df['T_LTV_C_LINK'] = ((full_volume_df['LINK_Liq_div_max_supply']))/((full_volume_df[' LINK 30_day_price_volatiliy']  )*10)
full_volume_df['T_LTV_C_AAVE'] = ((full_volume_df['AAVE_Liq_div_max_supply']))/((full_volume_df[' AAVE 30_day_price_volatiliy']  )*10)
full_volume_df['T_LTV_C_UNI'] = ((full_volume_df['UNI_Liq_div_max_supply']))/((full_volume_df[' UNI 30_day_price_volatiliy']  )*10)
full_volume_df['T_LTV_C_YFI'] = ((full_volume_df['YFI_Liq_div_max_supply']))/((full_volume_df[' YFI 30_day_price_volatiliy']  )*10)
full_volume_df['T_LTV_C_COMP'] = ((full_volume_df['COMP_Liq_div_max_supply']))/((full_volume_df[' COMP 30_day_price_volatiliy']  )*10)
full_volume_df['T_LTV_C_SUSHI'] = ((full_volume_df['SUSHI_Liq_div_max_supply']))/((full_volume_df[' SUSHI 30_day_price_volatiliy']  )*10)
full_volume_df['T_LTV_C_MKR'] = ((full_volume_df['MKR_Liq_div_max_supply']))/((full_volume_df[' MKR 30_day_price_volatiliy']  )*10)
full_volume_df['T_LTV_C_BAT'] = ((full_volume_df['BAT_Liq_div_max_supply']))/((full_volume_df[' BAT 30_day_price_volatiliy']  )*10)
full_volume_df['T_LTV_C_ZRX'] = ((full_volume_df['ZRX_Liq_div_max_supply']))/((full_volume_df[' ZRX 30_day_price_volatiliy']  )*10)
st.plotly_chart(px.scatter(full_volume_df, x = 'blocknumber', y = [col for col in full_volume_df.columns if 'T_LTV_C' in col]), use_container_width=True)
st.plotly_chart(px.scatter(full_volume_df, x = 'blocknumber', y = [col for col in full_volume_df.columns if '30_day_price_volatiliy_eth' in col]), use_container_width=True)




st.write("This is the LTV for the 30 day price volatility, using the log function, and multiplying by, and using the ETH price volatility rather than being dolar based")
full_volume_df['T_LTV_A_ETH_LINK'] = math.e**((full_volume_df[' LINK 30_day_price_volatiliy_eth'] / (full_volume_df['LINK_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ETH_AAVE'] = math.e**((full_volume_df[' AAVE 30_day_price_volatiliy_eth'] / (full_volume_df['AAVE_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ETH_UNI'] = math.e**((full_volume_df[' UNI 30_day_price_volatiliy_eth'] / (full_volume_df['UNI_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ETH_YFI'] = math.e**((full_volume_df[' YFI 30_day_price_volatiliy_eth'] / (full_volume_df['YFI_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ETH_COMP'] = math.e**((full_volume_df[' COMP 30_day_price_volatiliy_eth'] / (full_volume_df['COMP_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ETH_SUSHI'] = math.e**((full_volume_df[' SUSHI 30_day_price_volatiliy_eth'] / (full_volume_df['SUSHI_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ETH_MKR'] = math.e**((full_volume_df[' MKR 30_day_price_volatiliy_eth'] / (full_volume_df['MKR_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ETH_BAT'] = math.e**((full_volume_df[' BAT 30_day_price_volatiliy_eth'] / (full_volume_df['BAT_Liq_div_max_supply']))*-1)
full_volume_df['T_LTV_A_ETH_ZRX'] = math.e**((full_volume_df[' ZRX 30_day_price_volatiliy_eth'] / (full_volume_df['ZRX_Liq_div_max_supply']))*-1)
st.plotly_chart(px.scatter(full_volume_df, x = 'blocknumber', y = [col for col in full_volume_df.columns if 'T_LTV_A_ETH' in col]), use_container_width=True)




st.write("full data set")
st.write(full_volume_df)

q_comp = '''
with
  compound as (
    SELECT
      BLOCK_NUMBER as BLOCK_NUMBER_,
      TX_HASH,
      BLOCK_TIMESTAMP as BLOCK_TIMESTAMP_,
      EVENT_INPUTS:gToken as "token",
      EVENT_INPUTS:newCollateralFactorMantissa / 10000000000000000 as NEW_COLLATERAL,
      EVENT_INPUTS:oldCollateralFactorMantissa / 10000000000000000 as OLD_COLLATERAL
    FROM  
      ethereum.core.fact_event_logs
    WHERE
      CONTRACT_ADDRESS = lower('0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b')
      AND EVENT_NAME = ('NewCollateralFactor')
  )

SELECT
*
from
  compound'''

df_comp = run_query_flipside(q_comp)
df_comp['BLOCK_TIMESTAMP_'] = pd.to_datetime(df_comp['BLOCK_TIMESTAMP_'])
df_comp = df_comp.sort_values(by = 'BLOCK_TIMESTAMP_')
ctoken_meta_q = '''select * from 
ethereum.compound.ez_asset_details'''
df_ctoken_meta = run_query_flipside(ctoken_meta_q)
df_ctoken_meta = df_ctoken_meta.drop(columns=['UNDERLYING_CONTRACT_METADATA','CTOKEN_METADATA'])

merged = pd.merge(df_comp, df_ctoken_meta, left_on = 'token', right_on = 'CTOKEN_ADDRESS', how = 'left')
merged['BLOCK_TIMESTAMP_'] = pd.to_datetime(merged['BLOCK_TIMESTAMP_'])
only_max_df = pd.DataFrame()
for i in merged['token'].unique():
    df = merged[merged['token'] == i]
    df = df[df['BLOCK_TIMESTAMP_'] == df['BLOCK_TIMESTAMP_'].max()]
    only_max_df = pd.concat([only_max_df, df])
only_max_df = only_max_df.reset_index()
st.write(only_max_df)
st.write("The following chart shows the current collateral factor for each cToken.")
st.plotly_chart(px.bar(only_max_df, x = 'NEW_COLLATERAL', y = 'NEW_COLLATERAL', color = 'UNDERLYING_SYMBOL', barmode='group'), use_container_width=True)
st.write("The following chart shows the change in collateral factor for each cToken over time.")
st.plotly_chart(px.line(merged, x = 'BLOCK_TIMESTAMP_', y=['NEW_COLLATERAL'], color = 'UNDERLYING_SYMBOL'), use_container_width=True)



fig = go.Figure()
fig = subplots.make_subplots(specs=[[{"secondary_y": True}]])

for symbol in ['COMP', 'AAVE', 'UNI', 'YFI', 'SUSHI', 'MKR', 'BAT', 'ZRX']:
    df_merged_single = merged[merged['UNDERLYING_SYMBOL'] == symbol]
    fig.add_trace(go.Scatter(x=df_merged_single['BLOCK_TIMESTAMP_'], y=merged['NEW_COLLATERAL'],
                        mode='lines',
                        name=symbol+' reality'), secondary_y=False)

    fig.add_trace(go.Scatter(x=full_volume_df['block_timestamp'], y=full_volume_df[f'T_LTV_A_ETH_{symbol}'],
                        mode='lines',
                        name=symbol), secondary_y=True)
fig.update_layout(
    title="Collateral Factor vs proposed Collateral Factor",
    xaxis_title="Date",
    yaxis_title="Collateral Factor",
    legend_title="Legend Title",
    font=dict(
        family="Courier New, monospace",
        size=18,
        color="RebeccaPurple"
    )
)


st.plotly_chart(fig, use_container_width=True)


st.write("Conclusion")
st.write("I belive that using ETH in the volality function is the best fit for creating an LTV formula. However, given the lack of high enough LTV's for COMP, and some other assets, it could be assumed that some liquidity data is missing")
