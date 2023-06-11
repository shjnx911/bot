from freqtrade.strategy.interface import IStrategy
import numpy as np
import pandas as pd
from functools import reduce
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

from freqtrade.strategy import (
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IStrategy,
    IntParameter,
)

class test8(IStrategy):
    stoploss = -0.99
    minimal_roi = {"0": 0.04}

    # Plotting
    plot_config = {
        'main_plot': {'sma': {'color': 'blue'}},
        'subplots': {
            "rsi": {
                'rsi': {'color': 'orange'},
                'rsi_buy_hline': {'color': 'grey', 'plotly': {'opacity': 0.4}},
                'rsi_sell_hline': {'color': 'grey', 'plotly': {'opacity': 0.4}}
            },
        },
    }

    # Parameters
    sma = IntParameter(13, 56, default=15, space="buy")
    rsi_buy_hline = IntParameter(20, 40, default=15, space="buy")
    rsi_sell_hline = IntParameter(75, 95, default=85, space="sell")
    rebuy_limit = IntParameter(1, 10, default=5, space="buy")
    rebuy_percent = DecimalParameter(0, 1, default=0.25, space="buy")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for val in self.sma.range:
            dataframe[f'sma_{val}'] = ta.SMA(dataframe, timeperiod=val)

        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        conditions.append(
            (dataframe['close'] > dataframe[f'sma_{self.sma.value}'])
            & (dataframe['rsi'] > self.rsi_buy_hline.value)
        )
        # Thêm trường 'rebuy_0' vào DataFrame
        dataframe['rebuy_0'] = 0
        dataframe['rebuy_0_price'] = 0

        for i in range(1, self.rebuy_limit.value + 1):
            buy_condition = (dataframe[f'rebuy_{i-1}'].shift(1) == 1)
            price_condition = (dataframe['close'].shift(1) < dataframe['close'].shift(1) * (1 - self.rebuy_percent.value))
            dataframe.loc[buy_condition & price_condition, f'rebuy_{i}'] = 1
            dataframe.loc[dataframe[f'rebuy_{i}'] == 1, f'rebuy_{i}_price'] = dataframe['close']

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for i in range(1, self.rebuy_limit.value + 1):
            buy_condition = (dataframe[f'rebuy_{i}'].shift(1) == 1)
            price_condition = (dataframe['close'] > dataframe[f'rebuy_{i}_price'] * (1 + self.minimal_roi[0]))
            dataframe.loc[buy_condition & price_condition, f'resell_{i}'] = 1
        return dataframe
