# Rule -> Function Map (Phase B)

Generated from engine/rules.py REGISTRY. One function per STRATEGY.md rule.

**impl tags:** clean = deterministic from OHLCV+indicators | heuristic = pattern/swing approximation | fundamental = needs EPS data (not evaluated) | context = needs benchmark/cross-section (engine-level)

| Rule | Name | Category | Kind | impl | Strength | Function |
|---|---|---|---|---|---|---|
| 1.1 | Hammer | candlestick | entry | clean | high | `fn` |
| 1.2 | Hanging Man | candlestick | entry | clean | high | `fn` |
| 1.3 | Bullish Engulfing | candlestick | entry | clean | high | `fn` |
| 1.4 | Bearish Engulfing | candlestick | entry | clean | high | `fn` |
| 1.5 | Dark Cloud Cover | candlestick | entry | clean | high | `fn` |
| 1.6 | Piercing Pattern | candlestick | entry | clean | high | `fn` |
| 1.7 | Morning Star | candlestick | entry | clean | high | `fn` |
| 1.8 | Evening Star | candlestick | entry | clean | high | `fn` |
| 1.9 | Morning Doji Star | candlestick | entry | clean | high | `fn` |
| 1.10 | Evening Doji Star | candlestick | entry | clean | high | `fn` |
| 1.11 | Shooting Star | candlestick | entry | clean | med | `fn` |
| 1.12 | Inverted Hammer | candlestick | entry | clean | med | `fn` |
| 1.13 | Bullish Harami | candlestick | entry | clean | med | `fn` |
| 1.14 | Bearish Harami | candlestick | entry | clean | med | `fn` |
| 1.15 | Bullish Harami Cross | candlestick | entry | clean | high | `fn` |
| 1.16 | Bearish Harami Cross | candlestick | entry | clean | high | `fn` |
| 1.17 | Tweezers Top | candlestick | entry | clean | med | `fn` |
| 1.18 | Tweezers Bottom | candlestick | entry | clean | med | `fn` |
| 1.19 | Three White Soldiers | candlestick | entry | clean | high | `fn` |
| 1.20 | Three Black Crows | candlestick | entry | clean | high | `fn` |
| 1.21 | Doji at Top | candlestick | entry | clean | med | `fn` |
| 1.22 | Dragonfly Doji | candlestick | entry | clean | high | `fn` |
| 1.23 | Gravestone Doji | candlestick | entry | clean | high | `fn` |
| 1.24 | Tri-Star | candlestick | entry | clean | med | `fn` |
| 1.25 | Bullish Belt-Hold | candlestick | entry | clean | med | `fn` |
| 1.26 | Bearish Belt-Hold | candlestick | entry | clean | med | `fn` |
| 2.1 | Rising Three Methods | candlestick | entry | clean | high | `fn` |
| 2.2 | Falling Three Methods | candlestick | entry | clean | high | `fn` |
| 2.3 | Window Up | candlestick | entry | clean | med | `fn` |
| 2.4 | Window Down | candlestick | entry | clean | med | `fn` |
| 3.1 | RSI Oversold Reversal | oscillator | entry | clean | high | `r_3_1` |
| 3.2 | RSI Overbought Reversal | oscillator | exit | clean | high | `r_3_2` |
| 3.3 | RSI Bullish Divergence | oscillator | entry | heuristic | high | `r_3_3` |
| 3.4 | RSI Bearish Divergence | oscillator | exit | heuristic | high | `r_3_4` |
| 3.5 | Stochastic Oversold Buy | oscillator | entry | clean | high | `r_3_5` |
| 3.6 | Stochastic Overbought Sell | oscillator | exit | clean | high | `r_3_6` |
| 3.7 | Stochastic Bullish Divergence | oscillator | entry | heuristic | high | `r_3_7` |
| 3.8 | MACD Bullish Crossover | oscillator | entry | clean | high | `r_3_8` |
| 3.9 | MACD Bearish Crossover | oscillator | exit | clean | high | `r_3_9` |
| 3.10 | MACD-Histogram Bullish Divergence | oscillator | entry | heuristic | high | `r_3_10` |
| 3.11 | MACD-Histogram Bearish Divergence | oscillator | exit | heuristic | high | `r_3_11` |
| 3.12 | MACD Zero-Line Bullish Cross | oscillator | entry | clean | med | `r_3_12` |
| 4.1 | Elder-Ray Bull Power Buy | elder | entry | clean | high | `r_4_1` |
| 4.2 | Elder-Ray Bear Power Sell | elder | exit | clean | high | `r_4_2` |
| 4.3 | Force Index 2-Day Buy | elder | entry | clean | high | `r_4_3` |
| 4.4 | Force Index 13-Day Trend | elder | filter | clean | med | `r_4_4` |
| 5.1 | Elder Triple Screen | system | entry | heuristic | high | `r_5_1` |
| 6.1 | MA Support Bounce | ma | entry | clean | high | `r_6_1` |
| 6.2 | Golden Cross | ma | entry | clean | high | `r_6_2` |
| 6.3 | Death Cross | ma | exit | clean | high | `r_6_3` |
| 6.4 | Triple MA Crossover (3/9/18) | ma | entry | clean | med | `r_6_4` |
| 6.5 | 13-Day EMA Trend Filter | ma | filter | clean | med | `r_6_5` |
| 7.1 | Bollinger Band Squeeze | bollinger | level | clean | high | `r_7_1` |
| 7.2 | Bollinger Band Upper Walk | bollinger | entry | clean | med | `r_7_2` |
| 7.3 | Bollinger Band Lower Walk | bollinger | exit | clean | med | `r_7_3` |
| 7.4 | Bollinger Band Target | bollinger | entry | clean | med | `r_7_4` |
| 7.5 | Envelope Overextension | bollinger | entry | clean | med | `r_7_5` |
| 8.1 | Daily Pivot Levels | pivot | level | clean | high | `r_8_1` |
| 8.2 | Pivot Support Bounce | pivot | entry | clean | high | `r_8_2` |
| 8.3 | Pivot Resistance Rejection | pivot | exit | clean | high | `r_8_3` |
| 9.1 | Head and Shoulders Top | chart | exit | heuristic | high | `r_9_1` |
| 9.2 | Inverse Head and Shoulders | chart | entry | heuristic | high | `r_9_2` |
| 9.3 | Double Top | chart | exit | heuristic | high | `r_9_3` |
| 9.4 | Double Bottom | chart | entry | heuristic | high | `r_9_4` |
| 9.5 | Ascending Triangle | chart | entry | heuristic | high | `r_9_5` |
| 9.6 | Descending Triangle | chart | exit | heuristic | high | `r_9_6` |
| 9.7 | Bull Flag | chart | entry | heuristic | high | `r_9_7` |
| 9.8 | Bear Flag | chart | exit | heuristic | high | `r_9_8` |
| 10.1 | Trend Bar Momentum | price_action | entry | clean | high | `r_10_1` |
| 10.2 | Two-Bar Reversal | price_action | entry | clean | high | `r_10_2` |
| 10.3 | Inside Bar Breakout | price_action | entry | clean | med | `r_10_3` |
| 10.4 | Outside Bar Reversal | price_action | entry | clean | med | `r_10_4` |
| 10.5 | Breakout Pullback | price_action | entry | heuristic | high | `r_10_5` |
| 10.6 | Measured Move | price_action | level | heuristic | med | `r_10_6` |
| 10.7 | Micro Channel Break | price_action | entry | heuristic | med | `r_10_7` |
| 11.1 | NR7 Breakout | swing | entry | clean | high | `r_11_1` |
| 11.2 | First Rise / First Failure | swing | entry | heuristic | med | `r_11_2` |
| 11.3 | Power Spike | swing | entry | clean | high | `r_11_3` |
| 11.4 | Cross-Verification | swing | entry | heuristic | high | `r_11_4` |
| 12.1 | Volume-Trend Confirmation | volume | filter | clean | high | `r_12_1` |
| 12.2 | Volume Precedes Breakout | volume | entry | clean | high | `r_12_2` |
| 12.3 | Volume Dry-Up | volume | level | clean | high | `r_12_3` |
| 13.1 | CAN SLIM C (Current Earnings) | canslim | filter | fundamental | high | `fn` |
| 13.2 | CAN SLIM A (Annual Earnings) | canslim | filter | fundamental | high | `fn` |
| 13.3 | CAN SLIM N (New High Breakout) | canslim | entry | clean | high | `r_13_3` |
| 13.4 | CAN SLIM S (Supply/Demand) | canslim | filter | clean | high | `r_13_4` |
| 13.5 | CAN SLIM L (Relative Strength) | canslim | filter | context | high | `fn` |
| 13.6 | CAN SLIM M (Market Direction) | canslim | filter | context | high | `fn` |
| 13.7 | Cup-with-Handle Breakout | canslim | entry | heuristic | high | `r_13_7` |
| 14.1 | Impulse Buy | momentum | entry | heuristic | high | `r_14_1` |
| 14.2 | Momentum Divergence Warning | momentum | exit | heuristic | high | `r_14_2` |
| 14.3 | Fibonacci Confluence Zone | momentum | entry | heuristic | high | `r_14_3` |
| 15.1 | Bullish Candle at MA Support | combined | entry | clean | high | `r_15_1` |
| 15.2 | Candle Reversal at Trendline | combined | entry | heuristic | high | `r_15_2` |
| 15.3 | Candle + Oscillator Confluence | combined | entry | clean | high | `r_15_3` |
| 16.1 | Parabolic SAR | trailing | exit | clean | med | `r_16_1` |
| 17.1 | Channel Boundary Fade | channel | entry | heuristic | med | `r_17_1` |
| 18.1 | Trend Following | trend | filter | clean | high | `r_18_1` |

**Totals:** 98 rules — clean=69, heuristic=25, fundamental=2, context=2

## Key thresholds (tune here)

Candle anatomy (engine/patterns.py PARAMS):

```
{'doji_frac': 0.1, 'small_frac': 0.5, 'long_frac': 1.0, 'shadow_ratio': 2.0, 'near_extreme': 0.3, 'tiny_shadow': 0.1, 'trend_k': 5, 'tweezer_tol': 0.0015, 'level_tol': 0.02}
```

Oscillator/volume levels (engine/rules.py LV):

```
{'rsi_os': 30, 'rsi_ob': 70, 'stoch_os': 20, 'stoch_ob': 80, 'vol_spike': 1.5, 'power_spike': 2.0, 'level_tol': 0.02}
```