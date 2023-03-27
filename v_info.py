import streamlit as st
import pandas as pd
import os 
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import sys
st.set_page_config(layout="wide")


def parse_csv(file):
    df_parse = pd.read_csv(file)
    df_parse = df_parse.reset_index()
    st.write(file)
    csv_file = file.split('/')[-1]
    st.write(csv_file)
    asset_0 = csv_file.split('-')[0]
    asset_1 = csv_file.split('-')[1]
    st.write(asset_0)
    st.write(asset_1)
    fee_tier = csv_file.split('-')[2].split('.')[0]
    df_parse = df_parse.rename(columns={f'level_0': 'blocknum', 
    'level_1': 'p0vs1',
    'level_2': 'p1vs0', 
    'level_3': 'asset_0-slippagemap_01', 
    'level_4': 'asset_0-slippagemap_2', 
    'level_5': 'asset_0-slippagemap_3', 
    'level_6': 'asset_0-slippagemap_4', 
    'level_7': 'asset_0-slippagemap_5'
    , 'level_8': 'asset_0-slippagemap_6',
    'level_9': 'asset_0-slippagemap_7',
    'level_10': 'asset_0-slippagemap_8',
    'level_11': 'asset_0-slippagemap_9', 
    'level_12': 'asset_0-slippagemap_10', 
    'level_13': 'asset_0-slippagemap_11', 
    'level_14': 'asset_0-slippagemap_12', 
    'level_15': 'asset_0-slippagemap_13', 
    'level_16': 'asset_0-slippagemap_14', 
    'level_17': 'asset_0-slippagemap_15', 
    'level_18': 'asset_0-slippagemap_16', 
    'level_19': 'asset_0-slippagemap_17', 
    'level_20': 'asset_0-slippagemap_18', 
    'level_21': 'asset_0-slippagemap_19', 
    'level_22': 'asset_0-slippagemap_20',
        'level_23': 'asset_1-slippagemap_01', 
        'level_24': 'asset_1-slippagemap_2',
        'level_25': 'asset_1-slippagemap_3',
        'level_26': 'asset_1-slippagemap_4',
        'level_27': 'asset_1-slippagemap_5',
            'level_28': 'asset_1-slippagemap_6',
            'level_29': 'asset_1-slippagemap_7', 
            'level_30': 'asset_1-slippagemap_8', 
            'level_31': 'asset_1-slippagemap_9',
            'level_32': 'asset_1-slippagemap_10',
            'level_33': 'asset_1-slippagemap_11', 
            'level_34': 'asset_1-slippagemap_12', 
            'level_35': 'asset_1-slippagemap_13', 
            'level_36': 'asset_1-slippagemap_14', 
            'level_37': 'asset_1-slippagemap_15', 
            'level_38': 'asset_1-slippagemap_16', 
            'level_39': 'asset_1-slippagemap_17', 
            'level_40': 'asset_1-slippagemap_18', 
            'blocknumber': 'asset_1-slippagemap_19', 
            'data': 'asset_1-slippagemap_20'})

    # st.write(df_parse)
    for col in df_parse.columns: 
        if 'slippagemap_01' in col:
            df_parse[col] = (df_parse[col]).str.split(':', expand=True)[2]
        if 'slippagemap_1 ' not in col:
            try:
                df_parse[col] = df_parse[col].str.split(':', expand=True)[1]
            except:
                pass
        try:
            df_parse[col] = df_parse[col].str.replace('}', '')
        except:
            pass
        try:
            df_parse[col] = df_parse[col].astype(float)
        except:
            pass
        # if contains "null", drop the row
    
            # df_bat_v3[col] = float(df_bat_v3[col])
        df_parse = df_parse.rename(columns={col: col.replace('asset_0', asset_0)})
        df_parse = df_parse.rename(columns={col: col.replace('asset_1', asset_1)})
    # st.write(df_parse)

    for index, row in df_parse.iterrows():
        if 'null' in str(row):
            df_parse.drop(index, inplace=True)
    # reset index   
    df_parse = df_parse.reset_index()
    # st.write(df_parse)
    for col in df_parse.columns:   

        if (df_parse[col].dtype) == 'object':
            try:
                df_parse[col] = df_parse[col].astype(float)
            except:
                try:
                    df_parse[col] = float(df_parse[col])
                except:
                    pd.to_numeric(df_parse[col])
                    
        # df_parse[col] = pd.to_numeric(df_parse[col])
        # st.write(df_bat_v3[col].dtype)
    df_parse.to_csv(f'depth_parsed_v3/{asset_0}-{asset_1}-{fee_tier}-parsed.csv')
    
    return df_parse

def parse_csv_10000(file):
    df_parse = pd.read_csv(file)
    df_parse = df_parse.reset_index()
    st.write(file)
    csv_file = file.split('/')[-1]
    st.write(csv_file)
    asset_0 = csv_file.split('-')[0]
    asset_1 = csv_file.split('-')[1]
    st.write(asset_0)
    st.write(asset_1)
    fee_tier = csv_file.split('-')[2].split('.')[0]
    # st.write(df_parse)
    df_parse = df_parse.rename(columns={f'level_0': 'blocknum', 
    'level_1': 'p0vs1',
    'level_2': 'p1vs0', 
    'level_3': 'asset_0-slippagemap_01', 
    'level_4': 'asset_0-slippagemap_2', 
    'level_5': 'asset_0-slippagemap_3', 
    'level_6': 'asset_0-slippagemap_4', 
    'level_7': 'asset_0-slippagemap_5'
    , 'level_8': 'asset_0-slippagemap_6',
    'level_9': 'asset_0-slippagemap_7',
    'level_10': 'asset_0-slippagemap_8',
    'level_11': 'asset_0-slippagemap_9', 
    'level_12': 'asset_0-slippagemap_10', 
    'level_13': 'asset_0-slippagemap_11', 
    # 'level_14': 'asset_0-slippagemap_12', 
    # 'level_15': 'asset_0-slippagemap_13', 
    # 'level_16': 'asset_0-slippagemap_14', 
    # 'level_17': 'asset_0-slippagemap_15', 
    # 'level_18': 'asset_0-slippagemap_16', 
    # 'level_19': 'asset_0-slippagemap_17', 
    # 'level_20': 'asset_0-slippagemap_18', 
    # 'level_21': 'asset_0-slippagemap_19', 
    # 'level_22': 'asset_0-slippagemap_20',
        'level_14': 'asset_1-slippagemap_01', 
        'level_15': 'asset_1-slippagemap_2',
        'level_16': 'asset_1-slippagemap_3',
        'level_17': 'asset_1-slippagemap_4',
        'level_18': 'asset_1-slippagemap_5',
            'level_19': 'asset_1-slippagemap_6',
            'level_20': 'asset_1-slippagemap_7', 
            'level_21': 'asset_1-slippagemap_8', 
            # 'level_': 'asset_1-slippagemap_9',
            # 'level_14': 'asset_1-slippagemap_10',
            # 'level_14': 'asset_1-slippagemap_11', 
            # 'level_14': 'asset_1-slippagemap_12', 
            # 'level_14': 'asset_1-slippagemap_13', 
            # 'level_14': 'asset_1-slippagemap_14', 
            # 'level_14': 'asset_1-slippagemap_15', 
            # 'level_14': 'asset_1-slippagemap_16', 
            # 'level_39': 'asset_1-slippagemap_17', 
            # 'level_40': 'asset_1-slippagemap_18', 
            'blocknumber': 'asset_1-slippagemap_9', 
            'data': 'asset_1-slippagemap_10'})

    # st.write(df_parse)
    for col in df_parse.columns: 
        if 'slippagemap_01' in col:
            df_parse[col] = (df_parse[col]).str.split(':', expand=True)[2]
        if 'slippagemap_1 ' not in col:
            try:
                df_parse[col] = df_parse[col].str.split(':', expand=True)[1]
            except:
                pass
        try:
            df_parse[col] = df_parse[col].str.replace('}', '')
        except:
            pass
        try:
            df_parse[col] = df_parse[col].astype(float)
        except:
            pass
        # if contains "null", drop the row
    
            # df_bat_v3[col] = float(df_bat_v3[col])
        df_parse = df_parse.rename(columns={col: col.replace('asset_0', asset_0)})
        df_parse = df_parse.rename(columns={col: col.replace('asset_1', asset_1)})
    # st.write(df_parse)

    for index, row in df_parse.iterrows():
        if 'null' in str(row):
            df_parse.drop(index, inplace=True)
    # reset index   
    df_parse = df_parse.reset_index()
    # st.write(df_parse)
    for col in df_parse.columns:   

        if (df_parse[col].dtype) == 'object':
            try:
                df_parse[col] = df_parse[col].astype(float)
            except:
                try:
                    df_parse[col] = float(df_parse[col])
                except:
                    pd.to_numeric(df_parse[col])
                    
        # df_parse[col] = pd.to_numeric(df_parse[col])
        # st.write(df_bat_v3[col].dtype)
    df_parse.to_csv(f'depth_parsed_v3/{asset_0}-{asset_1}-{fee_tier}-parsed.csv')
    # st/
    return df_parse

file = '/Users/massnomis/p_c/uniswapv3-raw/BAT-USDC-3000-data.csv'

# st.write(sys.path)
# df_bat_v3 = parse_csv(file)\p \\

dir = '/Users/massnomis/p_c/uniswapv3-raw'
dir = os.listdir(dir)
st.write(dir)
for csv_ in dir:
    p = '/Users/massnomis/p_c/uniswapv3-raw/'
    if '10000' in csv_:
        try:
            df = parse_csv_10000(p + csv_)
            st.write("done")
        except:
            st.write("error")
            pass
    else:
        try:
            df = parse_csv(p + csv_)
            st.write("done")
        except:
            st.write("error")
            pass

    # df = parse_csv(p + csv_)