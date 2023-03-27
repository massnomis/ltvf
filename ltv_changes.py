import plotly.express as px
import pandas as pd

from shroomdk import ShroomDK
import plotly.graph_objects as go
import os
import streamlit as st
import warnings
warnings.filterwarnings("ignore")
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
    


query = '''
with
  changes as (
    select
      BLOCK_NUMBER as BLOCK_NUMBER_,
      BLOCK_TIMESTAMP as BLOCK_TIMESTAMP_,
      EVENT_INPUTS:asset as asset,
      EVENT_INPUTS:liquidationBonus as lb,
      EVENT_INPUTS:liquidationThreshold as lt,
      EVENT_INPUTS:ltv as ltv
    from
      ethereum.core.fact_event_logs
    where
      CONTRACT_ADDRESS = lower('0x311bb771e4f8952e6da169b425e7e92d6ac45756')
      and EVENT_NAME = 'CollateralConfigurationChanged'
  ),
  lables as (
    select
      ADDRESS,
      SYMBOL
    from
ethereum.core.dim_contracts     
    where
      ADDRESS IN (
        select
          asset
        from
          changes
      )
  )
select
  *
from
  changes
  left join lables on lables.ADDRESS = changes.asset
  order by BLOCK_TIMESTAMP_ desc
  '''

with st.expander("Query"):
    st.code(query)


cheat = run_query_flipside(query)
cheat['LT'] = cheat['LT'].astype(float) / 100
cheat['LB'] = cheat['LB'].astype(float) / 100
cheat['LTV'] = cheat['LTV'].astype(float) /100
# if SYMBOL is null then its MKR
cheat['SYMBOL'] = cheat['SYMBOL'].fillna('MKR')
cheat = cheat.sort_values(by = 'BLOCK_TIMESTAMP_')
st.write(cheat)
for symbol in cheat['SYMBOL'].unique():
    # st.write(symbol)
    # st.plotly_chart(px.line(cheat[cheat['SYMBOL'] == symbol], x = 'BLOCK_NUMBER_', y=['LTV'], color = 'SYMBOL'), use_container_width=True)
    df = (cheat[cheat['SYMBOL'] == symbol])
    df.to_csv('ltv_bysymbol/AAVE{}.csv'.format(symbol), index = False)

st.plotly_chart(px.line(cheat, x = 'BLOCK_NUMBER_', y=['LTV'], color = 'SYMBOL'), use_container_width=True)

q_comp = '''
with
  compound as (
    SELECT
      BLOCK_NUMBER as block_number_,
      TX_HASH,
      BLOCK_TIMESTAMP as block_timestamp_,
      EVENT_INPUTS:gToken as token,
      EVENT_INPUTS:newCollateralFactorMantissa / 10000000000000000 as new_collateral,
      EVENT_INPUTS:oldCollateralFactorMantissa / 10000000000000000 as old_collateral
    FROM  
      ethereum.core.fact_event_logs
    WHERE
      CONTRACT_ADDRESS = lower('0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b')
      AND EVENT_NAME = ('NewCollateralFactor')
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
  OLD_COLLATERAL,
  NEW_COLLATERAL
from
  add_symbol'''

df_comp = run_query_flipside(q_comp)
df_comp['BLOCK_TIMESTAMP_'] = pd.to_datetime(df_comp['BLOCK_TIMESTAMP_'])
df_comp = df_comp.sort_values(by = 'BLOCK_TIMESTAMP_')
# for df_comp['SYMBOL'] strip the first charecter if its a c
df_comp['SYMBOL'] = df_comp['SYMBOL'].str.replace('c', '')
# df_comp['min'] = df_comp['BLOCK_NUMBER_'].groupby(df_comp['SYMBOL']).transform('min')
# df_comp['max'] = df_comp['BLOCK_NUMBER_'].groupby(df_comp['SYMBOL']).transform('max')

with st.expander("Query"):
    st.code(q_comp)
st.plotly_chart(px.line(df_comp, x = 'BLOCK_NUMBER_', y=['NEW_COLLATERAL'], color = 'SYMBOL'), use_container_width=True)
st.write(df_comp)


for symbol in df_comp['SYMBOL'].unique():
    # st.write(symbol)
    # st.plotly_chart(px.line(df_comp[df_comp['SYMBOL'] == symbol], x = 'BLOCK_NUMBER_', y=['NEW_COLLATERAL'], color = 'SYMBOL'), use_container_width=True)
    df = (df_comp[df_comp['SYMBOL'] == symbol])
    df.to_csv('ltv_bysymbol/COMP_{}.csv'.format(symbol), index = False)




