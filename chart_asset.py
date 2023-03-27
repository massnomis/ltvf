import streamlit as st
import pandas as pd
import os 
from shroomdk import ShroomDK

import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import sys
import ccxt
st.set_page_config(layout="wide")
sdk = ShroomDK('d939cf57-7bd9-408c-9a7f-58c4cc900b03')

list_of_blocks = []

def run_query_flipside(query):
    try:
        df = pd.DataFrame(sdk.query(query).rows, columns=sdk.query(query).columns)
        
        return df
    except:
        st.write('Query failed')
        st.write(sdk.query(query).error)
        return None
# take every csv from depth_parsed_v3 that has 'AAVE' in it
# name = 'AAVE'
# name = st.text_input('Enter asset name', value='AAVE')
list_of_assets = ['ZRX', 'UNI', 'YFI', 'MKR', 'AAVE', 'LINK', 'BAT', 'SUSHI']
# list_of_assets = ['BAT']
for name in list_of_assets:
    ltv_df = pd.read_csv('ltv_bysymbol/{}.csv'.format(name))
    # st.write(ltv_df.head())
    st.title(name)


    min = ltv_df['BLOCK_NUMBER_'].min()
    max = ltv_df['BLOCK_NUMBER_'].max()
    # st.plotly_chart(px.line(ltv_df, x = 'BLOCK_NUMBER_', y=['NEW_COLLATERAL'], color = 'SYMBOL'), use_container_width=True)

    list_of_AAVE_v3 = []
    for file in os.listdir('depth_parsed_v3'):
        if name in file:
            list_of_AAVE_v3.append(file)
    with st.expander('Show csvs for v3'):
        st.write(list_of_AAVE_v3)

    list_of_aave_v2 = []
    for file in os.listdir('uniswapv2'):
        if name in file:
            list_of_aave_v2.append(file)
            # st.write
            # df = pd.read_csv('uniswapv2/'+file)
    with st.expander('Show csvs for v2'):
        st.write(list_of_aave_v2)
    v2_aave = pd.DataFrame()    
    for i in range(len(list_of_aave_v2)):   
        df = pd.read_csv('uniswapv2/'+list_of_aave_v2[i])
        # csv_file = 
        # st.write(df.head()) 
        # base_token = list_of_aave_v2[i].split('-')
        # st.write(df)
        base_token = list_of_aave_v2[i].split('-')[1].split('_')[0]

        # base_token = base_token.split('_')[0]
        df = df[['block', f'reserve {name}', 'volume for slippage 5%']]
        df = df[df['block'] >= min]
        df = df[df['block'] <= max]
        df['block'] = df['block'].apply(lambda x: int(x / 6000) * 6000)
        # try:
        #     df['Price_USDC'] = df[f'reserve {name}'] / df[f'reserve USDC']
        # except:
        #     pass
        df = df.groupby(['block']).agg({f'reserve {name}': 'mean', 'volume for slippage 5%': 'mean'}).reset_index()

        # sum_aave_df = sum_aave_df.groupby(np.arange(len(sum_aave_df))/1000).sum()


        v2_aave = pd.concat([v2_aave, df])
    # st.write(v2_aave)
    sum_aave_df = v2_aave[['block', f'reserve {name}', 'volume for slippage 5%']]




    # chunk into 1000 block segments
    # sum_aave_df = sum_aave_df.groupby(np.arange(len(sum_aave_df))/1000).sum()

    # st.write(sum_aave_df.head())
    # st.plotly_chart(px.bar(sum_aave_df, x=['block'], y='volume for slippage 5%'))

    sum_aave_df['block'] = sum_aave_df['block'].apply(lambda x: int(x / 6000) * 6000)
    # st.write(df)

    sum_aave_df = sum_aave_df.groupby(['block']).agg({f'reserve {name}': 'sum', 'volume for slippage 5%': 'sum'}).reset_index()
    # order b amountUSD
    list_of_blocks = sum_aave_df['block'].tolist()
    # st.code(str(list_of_blocks))
    # remove "['" and "']"
    list_of_blocks = str(list_of_blocks)[1:-1]
    q = f'''
    select block_number  as  "block_number"  , block_timestamp as "block_timestamp" from ethereum.core.fact_blocks
    where block_number in ({list_of_blocks})
    '''
    # st.code(q)
    df_q = run_query_flipside(q)
    # st.write(df_q)
    df_q['block_timestamp'] = pd.to_datetime(df_q['block_timestamp'])
    # round it to the day
    df_q['block_timestamp'] = df_q['block_timestamp'].apply(lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))
    min_ = ccxt.binance().iso8601(df_q['block_timestamp'].min())
    sum_aave_df = sum_aave_df.merge(df_q, left_on='block', right_on='block_number')
    daily_candles = ccxt.binance().fetch_ohlcv(symbol=f'{name}/USDT', timeframe='1d', since=min_, limit=1000)
    daily_candles = pd.DataFrame(daily_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    daily_candles['timestamp'] = pd.to_datetime(daily_candles['timestamp'], unit='ms')
    sum_aave_df = sum_aave_df.merge(daily_candles, left_on='block_timestamp', right_on='timestamp')
    # st.write(daily_candles)
    # df_6k = df_6k.sort_values(by=['block'], ascending=False)
    # reset index
    # df_6k = df_6k.reset_index(drop=True)
    # st.write(df_6k)
    sum_aave_df['reserve_USDT'] = sum_aave_df[f'reserve {name}'] * sum_aave_df['close']
    sum_aave_df['slippage_USDT'] = sum_aave_df['volume for slippage 5%'] * sum_aave_df['close']
    with st.expander('Show v2 data'):
        st.write(sum_aave_df)

    fig = go.Figure()
    # set up first axis
    # set up second axis
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'))
    # put higher on first axis

    fig.add_trace(go.Scatter(x=sum_aave_df['block'], y=sum_aave_df['slippage_USDT'], name='USDT', yaxis='y1'))
    fig.add_trace(go.Scatter(x=sum_aave_df['block'], y=sum_aave_df['volume for slippage 5%'], name='Native', yaxis='y1'))
    # fig.add_trace(go.Bar(x=aave_v3_df['blocknum'], y=aave_v3_df[f'{name}-slippagemap_5'], name='Uniswap V3', yaxis='y1'))
    # put lower on second axis
    fig.add_trace(go.Line(x=ltv_df['BLOCK_NUMBER_'], y=ltv_df['NEW_COLLATERAL'], name='LTV', yaxis='y2'))
    fig.update_layout(barmode='group')
    # make it log scale
    # fig.update_yaxes(type="log")
    st.plotly_chart(fig, use_container_width=True)
    aave_v3_df = pd.DataFrame()
    for i in range(len(list_of_AAVE_v3)):
        df = pd.read_csv('depth_parsed_v3/'+list_of_AAVE_v3[i])
        quote_token_1 = list_of_AAVE_v3[i].split('-')[0].split('_')[0]
        quote_token_2 = list_of_AAVE_v3[i].split('-')[1].split('_')[0]
        tokens = [quote_token_1, quote_token_2]
        # quote_token is the one that is not the name
        quote_token = [x for x in tokens if x != name][0]
        df = df[['blocknum', f'{name}-slippagemap_5']]
        # st.write(df.head())
        df = df[df['blocknum'] >= min]
        df = df[df['blocknum'] <= max]
        # st.write(max)
        # st.write(min)
        # st.write(df.head())
        df['blocknum'] = df['blocknum'].apply(lambda x: int(x / 6000) * 6000)
        # try:
        # st.write(df.head())
        #     df['Price_USDC'] = df[f'reserve {name}'] / df[f'reserve USDC']
        # except:
        #     pass
        df = df.groupby(['blocknum']).agg({f'{name}-slippagemap_5': 'mean'}).reset_index()






        aave_v3_df = aave_v3_df.append(df)

    aave_v3_df = aave_v3_df.groupby(['blocknum']).agg({f'{name}-slippagemap_5': 'sum'}).reset_index()
    # st.write(aave_v3_df.head())
    aave_v3_df = aave_v3_df.merge(df_q, left_on='blocknum', right_on='block_number')
    # st.write(aave_v3_df.head())
    # timestamp
    aave_v3_df = aave_v3_df.merge(daily_candles, left_on='block_timestamp', right_on='timestamp')
    aave_v3_df[f'{name}-slippagemap_5_USDT'] = aave_v3_df[f'{name}-slippagemap_5'] * aave_v3_df['close']
    with st.expander('Show AAVE v3'):
        st.write(aave_v3_df)




    st.plotly_chart(px.scatter(aave_v3_df, x=['blocknum'], y=f'{name}-slippagemap_5'))



    mega_merge = sum_aave_df.merge(aave_v3_df, left_on='block', right_on='blocknum')
    # st.write(mega_merge.head())
    mega_merge['native_5%_slippage'] = mega_merge[f'{name}-slippagemap_5'] + mega_merge['volume for slippage 5%']
    mega_merge['native_5%_slippage_USDT'] = mega_merge[f'{name}-slippagemap_5_USDT'] + mega_merge['slippage_USDT']

    fig = go.Figure()
    # set up first axis
    # set up second axis
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'))
    # put higher on first axis
    fig.add_trace(go.Scatter(x=mega_merge['block'], y=mega_merge['native_5%_slippage_USDT'], name='USDT', yaxis='y1'))
    fig.add_trace(go.Scatter(x=mega_merge['block'], y=mega_merge['native_5%_slippage'], name='Native', yaxis='y1'))
    # fig.add_trace(go.Bar(x=aave_v3_df['blocknum'], y=aave_v3_df[f'{name}-slippagemap_5'], name='Uniswap V3', yaxis='y1'))
    # put lower on second axis
    fig.add_trace(go.Line(x=ltv_df['BLOCK_NUMBER_'], y=ltv_df['NEW_COLLATERAL'], name='LTV', yaxis='y2'))
    fig.update_layout(barmode='group')
    # make it log scale
    # fig.update_yaxes(type="log")
    st.plotly_chart(fig, use_container_width=True)

    mega_merge['combined_USDT'] = mega_merge['native_5%_slippage_USDT'] + mega_merge['slippage_USDT']
    mega_merge['combined_native'] = mega_merge['native_5%_slippage'] + mega_merge['volume for slippage 5%']


    fig = go.Figure()
    # set up first axis
    # set up second axis
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'))
    # put higher on first axis
    fig.add_trace(go.Scatter(x=mega_merge['block'], y=mega_merge['combined_USDT'], name='USDT', yaxis='y1'))
    fig.add_trace(go.Scatter(x=mega_merge['block'], y=mega_merge['combined_native'], name='Native', yaxis='y1'))
    # fig.add_trace(go.Bar(x=aave_v3_df['blocknum'], y=aave_v3_df[f'{name}-slippagemap_5'], name='Uniswap V3', yaxis='y1'))
    # put lower on second axis
    fig.add_trace(go.Line(x=ltv_df['BLOCK_NUMBER_'], y=ltv_df['NEW_COLLATERAL'], name='LTV', yaxis='y2'))
    fig.update_layout(barmode='group')
    # make it log scale
    # fig.update_yaxes(type="log")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander('Show Combined'):
        st.write(mega_merge)


    # sum_aave_df = 
    # aave_v3_df

    fig = go.Figure()
    # set up first axis
    # set up second axis
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'))
    # put higher on first axis
    fig.add_trace(go.Bar(x=sum_aave_df['block'], y=sum_aave_df['volume for slippage 5%'], name='Uniswap V2', yaxis='y1'))
    # aave_v3_df
    fig.add_trace(go.Bar(x=aave_v3_df['blocknum'], y=aave_v3_df[f'{name}-slippagemap_5'], name='Uniswap V3', yaxis='y1'))
    # 
    # stack bars
    fig.update_layout(barmode='stack')
    # add the ltv
    fig.add_trace(go.Line(x=ltv_df['BLOCK_NUMBER_'], y=ltv_df['NEW_COLLATERAL'], name='LTV', yaxis='y2'))
    st.plotly_chart(fig, use_container_width=True)
    st.write(sum_aave_df)
    aave_v3_df['30_day_volatility'] = aave_v3_df['close'].rolling(30).std()
    aave_v3_df['60_day_volatility'] = aave_v3_df['close'].rolling(60).std()
    aave_v3_df['90_day_volatility'] = aave_v3_df['close'].rolling(90).std()
    aave_v3_df['120_day_volatility'] = aave_v3_df['close'].rolling(120).std()
    aave_v3_df['150_day_volatility'] = aave_v3_df['close'].rolling(150).std()
    st.write(aave_v3_df)
    st.write(ltv_df)
    # i dont mind 0 values for now, i want to see the blocknum to start at like 10 million
    # backwards_merge = aave_v3_df.merge(sum_aave_df, left_on='blocknum', right_on='block')
    # st.write(backwards_merge.head())
    # st.write(sum_aave_df.head())
    min_block = sum_aave_df['block'].min()
    # st.write(min_block)

    # st.write(aave_v3_df.head())
    min_max_b = aave_v3_df['blocknum'].min()
    # st.write(min_max_b)
    # add in missing blocknums until you reach the min blocknum
    min_ltv = ltv_df['BLOCK_NUMBER_'].min()
    max_ltv = ltv_df['BLOCK_NUMBER_'].max()
    # ltv_df ffill
    # ltv_df = ltv_df.fillna(method='ffill')
    ltv_df['BLOCK_NUMBER_'] = ltv_df['BLOCK_NUMBER_'].apply(lambda x: int(x / 6000) * 6000)
    # ltv_df['BLOCK_NUMBER_'] = ltv_df['BLOCK_NUMBER_'].ffill()
    # fill in the missing blocknums
    # drop blocktime
    ltv_df = ltv_df.drop(columns=['BLOCK_TIMESTAMP_'])


    # fill in missing blocknums
    #
    # ltv_df
    # set index to blocknum
    ltv_df = ltv_df.set_index('BLOCK_NUMBER_')
    ltv_df['BLOCK_NUMBER_'] = ltv_df.index
    # # reindex to fill in missing blocknums
    ltv_df = ltv_df.reindex(range((ltv_df.index.min()), (ltv_df.index.max() + 1), 6000))
    ltv_df = ltv_df.fillna(method='ffill')
    # drop na
    ltv_df = ltv_df.dropna()
    # ltv_df['BLOCK_NUMBER_'] = ltv_df.index
    # # 

    ltv_df = ltv_df.reset_index(drop=True)
    # drop duplicate blocknums
    ltv_df = ltv_df.drop_duplicates(subset=['BLOCK_NUMBER_'])
    # drop index
    # st.write(ltv_df.head())
    # also tail
    # st.write(ltv_df.tail())
    for i in range(min_ltv, max_ltv, 6000):
        if i not in aave_v3_df['blocknum'].values:
            # st.write(i)
            # add in the missing blocknum
            aave_v3_df = aave_v3_df.append({'blocknum': i}, ignore_index=True)
        if i not in sum_aave_df['block'].values:
            # st.write(i)
            # add in the missing blocknum
            sum_aave_df = sum_aave_df.append({'block': i}, ignore_index=True)
    # sort aave_v3_df by blocknum
    aave_v3_df = aave_v3_df.sort_values(by=['blocknum'])
    # fill na with 0
    aave_v3_df = aave_v3_df.fillna(0)
    # drop duplicates
    # aave_v3_df = aave_v3_df.drop_duplicates(subset=['blocknum'])
    st.write(aave_v3_df.head())

    backwards_merge = aave_v3_df.merge(sum_aave_df, left_on='blocknum', right_on='block')
    # st.write(backwards_merge.head())\
    backwards_merge['USDT_slippage_combined'] = backwards_merge['volume for slippage 5%'] + backwards_merge[f'{name}-slippagemap_5_USDT']
    backwards_merge['native_slippage_combined'] = backwards_merge['volume for slippage 5%'] + backwards_merge[f'{name}-slippagemap_5']
    # backwards_merge['formula_a'] is volatility squared divided by usdt slippage
    backwards_merge['formula_a'] = ((backwards_merge['30_day_volatility'] ** 2) / backwards_merge['USDT_slippage_combined']) * 100000000
    # fill na with 0
    # for formula b, use some kind of v2 vs v3 weighted average

    
    
    backwards_merge = backwards_merge.fillna(0)
    # if the data is 1970, then drop the row
    # if backwards_merge['block_timestamp'] == '1970-01-01T00:00:00':
    #     backwards_merge = backwards_merge.drop(backwards_merge.index[0])
    # sort by blocknum
    backwards_merge = backwards_merge.sort_values(by=['blocknum'])
    backwards_merge['lagging_formula_a_moving_avg'] = backwards_merge['formula_a'].rolling(30).mean()
    # backwards_merge['formula_b'] = ((backwards_merge['30_day_volatility'] ** 2) / backwards_merge['native_slippage_combined']) * 100000000
    for index, row in backwards_merge.iterrows():
        if row['volume_x'] == 0:
            # drop the row
            backwards_merge = backwards_merge.drop(index)
    
    backwards_merge['v2_v3_ratio_USDT'] =  backwards_merge[f'{name}-slippagemap_5_USDT'] / backwards_merge['volume for slippage 5%']
    backwards_merge['formula_b'] = (((backwards_merge['30_day_volatility'] ** 0.5) * (backwards_merge['v2_v3_ratio_USDT']) ) / backwards_merge['USDT_slippage_combined']) * 100000000
    # usdt_combined_volati
    backwards_merge['USDT_slippage_combined_volatility'] = backwards_merge['USDT_slippage_combined'].rolling(30).std()/backwards_merge['USDT_slippage_combined'].rolling(30).mean()
    backwards_merge['formula_c'] = (((backwards_merge['30_day_volatility'] ** 0.5) / (backwards_merge['USDT_slippage_combined_volatility']) ) / backwards_merge['USDT_slippage_combined']) * 100000000000
    st.write(backwards_merge)
    fig = go.Figure()
    # set up first axis
    # set up second axis
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'))
    # put higher on first axis
    fig.add_trace(go.Line(x=backwards_merge['blocknum'], y=backwards_merge['formula_a'], name='formula_a', yaxis='y1'))
    fig.add_trace(go.Line(x=backwards_merge['blocknum'], y=backwards_merge['lagging_formula_a_moving_avg'], name='lagging_formula_a_moving_avg', yaxis='y1'))
    fig.add_trace(go.Line(x=backwards_merge['blocknum'], y=backwards_merge['formula_b'], name='formula_b', yaxis='y1'))
    fig.add_trace(go.Line(x=backwards_merge['blocknum'], y=backwards_merge['formula_c'], name='formula_c', yaxis='y1'))
    # fig.add_trace(go.Bar(x=backwards_merge['blocknum'], y=backwards_merge['native_slippage_combined'], name='Native', yaxis='y1'))

    # put lower on second axis
    fig.add_trace(go.Line(x=ltv_df['BLOCK_NUMBER_'], y=ltv_df['NEW_COLLATERAL'], name='LTV', yaxis='y2'))
    # fig.update_layout(barmode='group')
    # make it log scale
    # fig.update_yaxes(type="log")
    st.plotly_chart(fig, use_container_width=True)

    # backwards_merge = backwards_merge.merge(ltv_df, left_on='blocknum', right_on='BLOCK_NUMBER_')
    # # drop duplicate blocknum
    # backwards_merge = backwards_merge.drop(columns=['BLOCK_NUMBER_'])
    # # st.write(backwards_merge.head())
    # fill na with 0
    # backwards_merge = backwards_merge.fillna(0)
    # st.write(backwards_merge)