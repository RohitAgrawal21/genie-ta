# Technical Analysis Rules Engine — STRATEGY

> Auto-extracted codifiable trading rules from 12 technical analysis books.
> Each rule can be evaluated from OHLCV data programmatically.
> Murphy (Technical Analysis of the Financial Markets) processed via PDF OCR (key chapters: MAs, Bollinger Bands, Envelopes, Volume/OI).

---

## 1. CANDLESTICK REVERSAL PATTERNS

### 1.1 Hammer

- **name:** Hammer
- **setup:** After a decline: candle with (a) small real body at upper end of range, (b) lower shadow >= 2× real body height, (c) no or very short upper shadow
- **signal:** buy
- **confirmation:** none required (more bullish if white body; strongest if lower shadow >= 3× real body)
- **invalidation:** close below hammer's low
- **timeframe:** EOD / intraday
- **source:** Nison — Japanese Candlestick Charting Techniques, Ch 4; Morris — Candlestick Charting Explained, Ch 4
- **strength:** high
- **conflicts:** none

### 1.2 Hanging Man

- **name:** Hanging Man
- **setup:** After a rally (preferably at all-time high or significant high): same shape as hammer — small real body at upper end, lower shadow >= 2× real body, no/short upper shadow
- **signal:** sell
- **confirmation:** required — next session must close below hanging man's real body
- **invalidation:** market continues higher and closes above hanging man's high
- **timeframe:** EOD / intraday
- **source:** Nison — Ch 4; Morris — Ch 4
- **strength:** high
- **conflicts:** none

### 1.3 Bullish Engulfing

- **name:** Bullish Engulfing
- **setup:** After a downtrend: (1) first candle is black (bearish) real body, (2) second candle is white (bullish) real body that completely engulfs the first candle's real body
- **signal:** buy
- **confirmation:** none (stronger on high volume on day 2)
- **invalidation:** close below the low of the engulfing pattern
- **timeframe:** EOD
- **source:** Nison — Ch 4; Morris — Ch 4; Rhoads — Candlestick Charting For Dummies
- **strength:** high
- **conflicts:** none

### 1.4 Bearish Engulfing

- **name:** Bearish Engulfing
- **setup:** After an uptrend: (1) first candle is white real body, (2) second candle is black real body that completely engulfs the first candle's real body
- **signal:** sell
- **confirmation:** none (stronger on high volume on day 2)
- **invalidation:** close above the high of the engulfing pattern
- **timeframe:** EOD
- **source:** Nison — Ch 4; Morris — Ch 4; Rhoads
- **strength:** high
- **conflicts:** none

### 1.5 Dark Cloud Cover

- **name:** Dark Cloud Cover
- **setup:** After an uptrend: (1) first candle is a long white body, (2) second candle opens above prior high, then closes below the midpoint of the first candle's white body
- **signal:** sell
- **confirmation:** none (closing deeper into white body = stronger)
- **invalidation:** close above the high of day 2
- **timeframe:** EOD
- **source:** Nison — Ch 4; Morris — Ch 4; Person — Candlestick and Pivot Point Trading Triggers
- **strength:** high
- **conflicts:** Nison prefers open above prior HIGH; some Japanese sources accept open above prior CLOSE

### 1.6 Piercing Pattern

- **name:** Piercing Pattern
- **setup:** After a downtrend: (1) first candle is a long black body, (2) second candle opens below prior low, then closes above the midpoint of the first candle's black body
- **signal:** buy
- **confirmation:** none
- **invalidation:** close below the low of day 2
- **timeframe:** EOD
- **source:** Nison — Ch 4; Morris — Ch 4
- **strength:** high
- **conflicts:** none

### 1.7 Morning Star

- **name:** Morning Star
- **setup:** After a downtrend: (1) long black candle, (2) small real body (spinning top) that gaps down from day 1's body, (3) white candle that closes well into day 1's black body (above midpoint)
- **signal:** buy
- **confirmation:** none (stronger if day 3 closes above midpoint of day 1)
- **invalidation:** close below the low of the star (day 2)
- **timeframe:** EOD
- **source:** Nison — Ch 5; Morris — Ch 5
- **strength:** high
- **conflicts:** none

### 1.8 Evening Star

- **name:** Evening Star
- **setup:** After an uptrend: (1) long white candle, (2) small real body (spinning top) that gaps up from day 1's body, (3) black candle that closes well into day 1's white body (below midpoint)
- **signal:** sell
- **confirmation:** none
- **invalidation:** close above the high of the star (day 2)
- **timeframe:** EOD
- **source:** Nison — Ch 5; Morris — Ch 5
- **strength:** high
- **conflicts:** none

### 1.9 Morning Doji Star

- **name:** Morning Doji Star
- **setup:** Same as Morning Star but day 2 is a doji (open ≈ close) instead of a spinning top
- **signal:** buy
- **confirmation:** none
- **invalidation:** close below doji's low
- **timeframe:** EOD
- **source:** Nison — Ch 5; Morris — Ch 5
- **strength:** high (stronger than regular morning star)
- **conflicts:** none

### 1.10 Evening Doji Star

- **name:** Evening Doji Star
- **setup:** Same as Evening Star but day 2 is a doji instead of a spinning top
- **signal:** sell
- **confirmation:** none
- **invalidation:** close above doji's high
- **timeframe:** EOD
- **source:** Nison — Ch 5; Morris — Ch 5
- **strength:** high (stronger than regular evening star)
- **conflicts:** none

### 1.11 Shooting Star

- **name:** Shooting Star
- **setup:** After an uptrend: (1) small real body at lower end of range, (2) long upper shadow >= 2× real body, (3) little or no lower shadow. Does NOT need to gap up from prior candle (unlike evening star).
- **signal:** sell
- **confirmation:** bearish confirmation next session preferred
- **invalidation:** close above shooting star's high
- **timeframe:** EOD / intraday
- **source:** Nison — Ch 5; Morris — Ch 5
- **strength:** med
- **conflicts:** none

### 1.12 Inverted Hammer

- **name:** Inverted Hammer
- **setup:** After a downtrend: same shape as shooting star — small real body at lower end, long upper shadow >= 2× body, little/no lower shadow
- **signal:** buy
- **confirmation:** required — bullish confirmation next session (close above inverted hammer's body)
- **invalidation:** close below inverted hammer's low
- **timeframe:** EOD
- **source:** Nison — Ch 5; Morris — Ch 5
- **strength:** med
- **conflicts:** none

### 1.13 Harami (Bullish)

- **name:** Bullish Harami
- **setup:** After a downtrend: (1) long black candle, (2) small real body (any color) contained within day 1's real body
- **signal:** buy
- **confirmation:** bullish follow-through preferred
- **invalidation:** close below the low of day 1
- **timeframe:** EOD
- **source:** Nison — Ch 6; Morris — Ch 6
- **strength:** med
- **conflicts:** none

### 1.14 Harami (Bearish)

- **name:** Bearish Harami
- **setup:** After an uptrend: (1) long white candle, (2) small real body contained within day 1's real body
- **signal:** sell
- **confirmation:** bearish follow-through preferred
- **invalidation:** close above the high of day 1
- **timeframe:** EOD
- **source:** Nison — Ch 6; Morris — Ch 6
- **strength:** med
- **conflicts:** none

### 1.15 Harami Cross (Bullish)

- **name:** Bullish Harami Cross
- **setup:** After a downtrend: (1) long black candle, (2) doji contained within day 1's real body
- **signal:** buy
- **confirmation:** none
- **invalidation:** close below the low of day 1
- **timeframe:** EOD
- **source:** Nison — Ch 6; Morris — Ch 6
- **strength:** high (stronger than regular harami)
- **conflicts:** none

### 1.16 Harami Cross (Bearish)

- **name:** Bearish Harami Cross
- **setup:** After an uptrend: (1) long white candle, (2) doji contained within day 1's real body
- **signal:** sell
- **confirmation:** none
- **invalidation:** close above the high of day 1
- **timeframe:** EOD
- **source:** Nison — Ch 6; Morris — Ch 6
- **strength:** high
- **conflicts:** none

### 1.17 Tweezers Top

- **name:** Tweezers Top
- **setup:** After an uptrend: two or more candles with matching highs (exact or near-exact same high)
- **signal:** sell
- **confirmation:** bearish candle pattern on second candle strengthens signal
- **invalidation:** close above the tweezers high
- **timeframe:** EOD
- **source:** Nison — Ch 6
- **strength:** med
- **conflicts:** none

### 1.18 Tweezers Bottom

- **name:** Tweezers Bottom
- **setup:** After a downtrend: two or more candles with matching lows
- **signal:** buy
- **confirmation:** bullish candle pattern on second candle strengthens signal
- **invalidation:** close below the tweezers low
- **timeframe:** EOD
- **source:** Nison — Ch 6
- **strength:** med
- **conflicts:** none

### 1.19 Three White Soldiers

- **name:** Three White Soldiers (Advancing)
- **setup:** Three consecutive long white candles, each closing near its high, each opening within the prior candle's real body
- **signal:** buy
- **confirmation:** none
- **invalidation:** close below the open of the third candle; watch for "advance block" (shrinking bodies) or "stalled pattern" (third body much smaller)
- **timeframe:** EOD
- **source:** Nison — Ch 6; Morris — Ch 6
- **strength:** high
- **conflicts:** none

### 1.20 Three Black Crows

- **name:** Three Black Crows
- **setup:** Three consecutive long black candles, each closing near its low, each opening within the prior candle's real body
- **signal:** sell
- **confirmation:** none
- **invalidation:** close above the open of the third candle
- **timeframe:** EOD
- **source:** Nison — Ch 6; Morris — Ch 6
- **strength:** high
- **conflicts:** none

### 1.21 Doji at Top

- **name:** Doji (Northern — after rally)
- **setup:** After an uptrend or at resistance: a doji (open ≈ close) appears
- **signal:** sell
- **confirmation:** bearish candle next session
- **invalidation:** close above doji's high
- **timeframe:** EOD / intraday
- **source:** Nison — Ch 8; Morris — Ch 8
- **strength:** med (stronger when market is overbought per oscillator)
- **conflicts:** none

### 1.22 Dragonfly Doji

- **name:** Dragonfly Doji
- **setup:** Doji where open and close are at or near the high; long lower shadow; no upper shadow. After a downtrend = bullish.
- **signal:** buy (after decline) / sell (after rally, less common)
- **confirmation:** none
- **invalidation:** close below dragonfly's low
- **timeframe:** EOD
- **source:** Nison — Ch 8
- **strength:** high
- **conflicts:** none

### 1.23 Gravestone Doji

- **name:** Gravestone Doji
- **setup:** Doji where open and close are at or near the low; long upper shadow; no lower shadow. After an uptrend = bearish.
- **signal:** sell (after rally)
- **confirmation:** none
- **invalidation:** close above gravestone's high
- **timeframe:** EOD
- **source:** Nison — Ch 8
- **strength:** high
- **conflicts:** none

### 1.24 Tri-Star

- **name:** Tri-Star
- **setup:** Three consecutive doji candles; middle doji gaps away from the other two
- **signal:** buy (bullish tri-star at bottom) / sell (bearish tri-star at top)
- **confirmation:** none
- **invalidation:** close beyond the pattern's extreme
- **timeframe:** EOD
- **source:** Nison — Ch 8; Morris — performance data shows avg +0.48% (bull) / −0.61% (bear) over 10 days
- **strength:** med (rare pattern)
- **conflicts:** none

### 1.25 Belt-Hold (Bullish)

- **name:** Bullish Belt-Hold (Yorikiri)
- **setup:** After a downtrend: a long white candle that opens at its low (no lower shadow) and closes near its high
- **signal:** buy
- **confirmation:** none
- **invalidation:** close below the belt-hold's open/low
- **timeframe:** EOD
- **source:** Nison — Ch 6
- **strength:** med
- **conflicts:** none

### 1.26 Belt-Hold (Bearish)

- **name:** Bearish Belt-Hold
- **setup:** After an uptrend: a long black candle that opens at its high (no upper shadow) and closes near its low
- **signal:** sell
- **confirmation:** none
- **invalidation:** close above the belt-hold's open/high
- **timeframe:** EOD
- **source:** Nison — Ch 6
- **strength:** med
- **conflicts:** none

---

## 2. CANDLESTICK CONTINUATION PATTERNS

### 2.1 Rising Three Methods

- **name:** Rising Three Methods
- **setup:** In an uptrend: (1) long white candle, (2) three small-body candles (ideally black) that decline but stay within day 1's range, (3) long white candle that closes above day 1's close
- **signal:** buy (continuation)
- **confirmation:** day 5 close above day 1's high
- **invalidation:** any candle closes below day 1's low
- **timeframe:** EOD
- **source:** Nison — Ch 7; Morris — avg +0.71% over 10 days
- **strength:** high
- **conflicts:** none

### 2.2 Falling Three Methods

- **name:** Falling Three Methods
- **setup:** In a downtrend: (1) long black candle, (2) three small-body candles (ideally white) that rally but stay within day 1's range, (3) long black candle that closes below day 1's close
- **signal:** sell (continuation)
- **confirmation:** day 5 close below day 1's low
- **invalidation:** any candle closes above day 1's high
- **timeframe:** EOD
- **source:** Nison — Ch 7; Morris
- **strength:** high
- **conflicts:** none

### 2.3 Window Up (Gap Up)

- **name:** Window Up
- **setup:** A gap between the prior candle's high and the current candle's low (current low > prior high). In Japanese terminology, "window."
- **signal:** buy (continuation in uptrend)
- **confirmation:** none
- **invalidation:** window is "closed" — price retraces and closes below the gap
- **timeframe:** EOD / intraday
- **source:** Nison — Ch 7
- **strength:** med
- **conflicts:** none

### 2.4 Window Down (Gap Down)

- **name:** Window Down
- **setup:** Gap where current high < prior low
- **signal:** sell (continuation in downtrend)
- **confirmation:** none
- **invalidation:** window is closed — price retraces and closes above the gap
- **timeframe:** EOD / intraday
- **source:** Nison — Ch 7
- **strength:** med
- **conflicts:** none

---

## 3. OSCILLATOR RULES

### 3.1 RSI Oversold Reversal

- **name:** RSI Oversold Reversal
- **setup:** RSI(14) crosses above 30 from below
- **signal:** buy
- **confirmation:** price closes above prior swing high, or bullish candle pattern
- **invalidation:** RSI falls back below 30; or price makes new low
- **timeframe:** EOD
- **source:** Elder — Trading for a Living, Ch 31; Knight — Chart Your Way To Profits; Morris uses RSI(14) with 35/65 levels
- **strength:** high
- **conflicts:** Elder uses 30/70 levels; Morris uses 35/65 for filtering candle patterns; Person uses 20/80 in combination with stochastics

### 3.2 RSI Overbought Reversal

- **name:** RSI Overbought Reversal
- **setup:** RSI(14) crosses below 70 from above
- **signal:** sell
- **confirmation:** price closes below prior swing low, or bearish candle pattern
- **invalidation:** RSI rises back above 70
- **timeframe:** EOD
- **source:** Elder — Ch 31; Knight
- **strength:** high
- **conflicts:** Morris uses 65 instead of 70

### 3.3 RSI Bullish Divergence

- **name:** RSI Bullish Divergence
- **setup:** Price makes a lower low, but RSI(14) makes a higher low
- **signal:** buy
- **confirmation:** RSI turns up from its higher low
- **invalidation:** price makes a new lower low confirmed by RSI making new low too
- **timeframe:** EOD
- **source:** Elder — Ch 31; Rosenbloom — The Complete Trading Course; Knight
- **strength:** high
- **conflicts:** none

### 3.4 RSI Bearish Divergence

- **name:** RSI Bearish Divergence
- **setup:** Price makes a higher high, but RSI(14) makes a lower high
- **signal:** sell
- **confirmation:** RSI turns down from its lower high
- **invalidation:** price makes new high confirmed by RSI new high
- **timeframe:** EOD
- **source:** Elder — Ch 31; Rosenbloom; Knight
- **strength:** high
- **conflicts:** none

### 3.5 Stochastic Oversold Buy

- **name:** Stochastic Oversold Buy
- **setup:** Slow Stochastic %K(14,3) crosses above %D while both are below 20 (Elder uses 30; Person uses 20)
- **signal:** buy
- **confirmation:** %K crosses above %D (bullish crossover)
- **invalidation:** %K falls back below %D while still under 20
- **timeframe:** EOD
- **source:** Elder — Ch 30 (5-bar slow stoch, 3-day smoothing); Person — Candlestick and Pivot Point Trading Triggers (14-period); Nison — Ch 14
- **strength:** high
- **conflicts:** Elder uses 5-bar window; Person uses 14-period. Elder uses 30/70 zones with Triple Screen; Person uses 20/80. Both are valid — 14-period with 20/80 is most common.

### 3.6 Stochastic Overbought Sell

- **name:** Stochastic Overbought Sell
- **setup:** Slow Stochastic %K(14,3) crosses below %D while both are above 80
- **signal:** sell
- **confirmation:** %K crosses below %D (bearish crossover)
- **invalidation:** %K rises back above %D while still above 80
- **timeframe:** EOD
- **source:** Elder — Ch 30; Person; Nison — Ch 14
- **strength:** high
- **conflicts:** see 3.5 conflicts

### 3.7 Stochastic Bullish Divergence

- **name:** Stochastic Bullish Divergence
- **setup:** Price makes a lower low but Stochastic makes a higher low
- **signal:** buy
- **confirmation:** Stochastic turns up
- **invalidation:** price and Stochastic both make new lows
- **timeframe:** EOD
- **source:** Person — Technical Trading Tactics, Ch 8; Elder
- **strength:** high
- **conflicts:** none

### 3.8 MACD Signal Line Crossover (Bullish)

- **name:** MACD Bullish Crossover
- **setup:** MACD line (12-period EMA minus 26-period EMA) crosses above the Signal line (9-period EMA of MACD)
- **signal:** buy
- **confirmation:** crossover occurs below the zero line (stronger signal per Elder)
- **invalidation:** MACD crosses back below Signal line
- **timeframe:** EOD
- **source:** Elder — Ch 26 (MACD Lines trading rules); Person — Candlestick and Pivot Point Trading Triggers; Morris uses MACD(12/26/9/9); Knight
- **strength:** high
- **conflicts:** none — standard 12/26/9 parameters universally agreed

### 3.9 MACD Signal Line Crossover (Bearish)

- **name:** MACD Bearish Crossover
- **setup:** MACD line crosses below the Signal line
- **signal:** sell
- **confirmation:** crossover occurs above the zero line (stronger)
- **invalidation:** MACD crosses back above Signal line
- **timeframe:** EOD
- **source:** Elder — Ch 26; Person; Knight
- **strength:** high
- **conflicts:** none

### 3.10 MACD-Histogram Divergence (Bullish)

- **name:** MACD-Histogram Bullish Divergence
- **setup:** Price makes a new low but MACD-Histogram makes a shallower (higher) low
- **signal:** buy
- **confirmation:** MACD-Histogram ticks up from its higher low
- **invalidation:** MACD-Histogram makes a new low matching price
- **timeframe:** EOD / weekly
- **source:** Elder — Ch 26 ("the strongest signals in technical analysis"); Rosenbloom
- **strength:** high
- **conflicts:** none

### 3.11 MACD-Histogram Divergence (Bearish)

- **name:** MACD-Histogram Bearish Divergence
- **setup:** Price makes a new high but MACD-Histogram makes a lower high
- **signal:** sell
- **confirmation:** MACD-Histogram ticks down from its lower high
- **invalidation:** MACD-Histogram makes a new high matching price
- **timeframe:** EOD / weekly
- **source:** Elder — Ch 26; Rosenbloom
- **strength:** high
- **conflicts:** none

### 3.12 MACD Zero-Line Cross (Bullish)

- **name:** MACD Zero-Line Bullish Cross
- **setup:** MACD histogram crosses above zero (MACD line crosses above signal line)
- **signal:** buy
- **confirmation:** rising histogram bars
- **invalidation:** histogram drops back below zero
- **timeframe:** EOD / intraday
- **source:** Person — Candlestick and Pivot Point Trading Triggers (HCD trigger); Rosenbloom
- **strength:** med
- **conflicts:** none

---

## 4. ELDER PROPRIETARY INDICATORS

### 4.1 Elder-Ray Bull Power Buy

- **name:** Elder-Ray Bull Power Buy
- **setup:** (1) 13-day EMA is rising (uptrend), (2) Bear Power (= Low − 13-day EMA) is negative but rising (ticking up toward zero)
- **signal:** buy
- **confirmation:** Bear Power crosses above zero confirms bulls fully in control
- **invalidation:** Bear Power makes a new low; or 13-day EMA turns down
- **timeframe:** EOD
- **source:** Elder — Ch 41. Formula: Bull Power = High − 13-day EMA; Bear Power = Low − 13-day EMA
- **strength:** high
- **conflicts:** none

### 4.2 Elder-Ray Bear Power Sell

- **name:** Elder-Ray Bear Power Sell
- **setup:** (1) 13-day EMA is falling (downtrend), (2) Bull Power (= High − 13-day EMA) is positive but falling (ticking down toward zero)
- **signal:** sell
- **confirmation:** Bull Power crosses below zero
- **invalidation:** Bull Power makes a new high; or 13-day EMA turns up
- **timeframe:** EOD
- **source:** Elder — Ch 41
- **strength:** high
- **conflicts:** none

### 4.3 Force Index — 2-Day EMA Buy

- **name:** Force Index Short-Term Buy
- **setup:** Force Index = (Close today − Close yesterday) × Volume today. When the 2-day EMA of Force Index falls below zero during an uptrend (identified by weekly chart)
- **signal:** buy
- **confirmation:** Force Index turns back positive
- **invalidation:** Force Index falls to a new multi-week low; or weekly trend reverses
- **timeframe:** EOD (used as Screen 2 in Triple Screen)
- **source:** Elder — Ch 42, 43
- **strength:** high
- **conflicts:** none

### 4.4 Force Index — 13-Day EMA Trend

- **name:** Force Index Trend Confirmation
- **setup:** 13-day EMA of Force Index: positive = bulls control, negative = bears control. New highs in 13-day Force Index confirm breakaway/continuation moves.
- **signal:** buy (positive) / sell (negative)
- **confirmation:** none
- **invalidation:** sign reversal
- **timeframe:** EOD
- **source:** Elder — Ch 42
- **strength:** med
- **conflicts:** none

---

## 5. ELDER TRIPLE SCREEN TRADING SYSTEM

### 5.1 Triple Screen — Full System

- **name:** Elder Triple Screen
- **setup:**
  - **Screen 1 (Market Tide):** On the weekly chart, identify trend using weekly MACD-Histogram slope. Slope up = bullish (only take longs). Slope down = bearish (only take shorts). A single uptick/downtick signals a trend change.
  - **Screen 2 (Market Wave):** On the daily chart, use an oscillator (2-day EMA of Force Index, Elder-ray Bear/Bull Power, or Stochastic) to find counter-trend pullbacks. Weekly up + daily oscillator oversold = buy zone. Weekly down + daily oscillator overbought = sell zone.
  - **Screen 3 (Entry):** Trailing buy-stop (if bullish): place buy order 1 tick above prior day's high; lower daily if decline continues. Trailing sell-stop (if bearish): place sell order 1 tick below prior day's low; raise daily if rally continues.
- **signal:** buy / sell (per Screen 1 direction)
- **confirmation:** all three screens must align
- **invalidation:** weekly MACD-Histogram reverses slope; or stop-loss hit (1 tick below trade-day low for longs, 1 tick above for shorts)
- **timeframe:** weekly + EOD + intraday entry
- **source:** Elder — Ch 43 (Triple Screen Trading System)
- **strength:** high
- **conflicts:** none — this is a complete trading system

**Triple Screen Decision Matrix:**
| Weekly Trend | Daily Oscillator | Action | Order Type |
|---|---|---|---|
| Up | Down (oversold) | Go long | Trailing buy-stop |
| Up | Up | Stand aside | None |
| Down | Up (overbought) | Go short | Trailing sell-stop |
| Down | Down | Stand aside | None |

---

## 6. MOVING AVERAGE RULES

### 6.1 Price Crosses Above Rising MA

- **name:** MA Support Bounce
- **setup:** Price pulls back to a rising moving average (commonly 20, 50, or 200-day) and closes above it
- **signal:** buy
- **confirmation:** bullish candle at the MA; rising volume
- **invalidation:** close below the MA
- **timeframe:** EOD
- **source:** Elder — Ch 25 (EMA as support/resistance); Knight — Chart Your Way To Profits; Nison — Ch 13 (candles with MAs)
- **strength:** high
- **conflicts:** none

### 6.2 Golden Cross

- **name:** Golden Cross
- **setup:** 50-day MA crosses above the 200-day MA
- **signal:** buy
- **confirmation:** price is above both MAs
- **invalidation:** 50-day MA turns back below 200-day MA (Death Cross)
- **timeframe:** EOD
- **source:** Knight — Chart Your Way To Profits; Rosenbloom — The Complete Trading Course
- **strength:** high (long-term signal)
- **conflicts:** none

### 6.3 Death Cross

- **name:** Death Cross
- **setup:** 50-day MA crosses below the 200-day MA
- **signal:** sell
- **confirmation:** price is below both MAs
- **invalidation:** 50-day MA crosses back above 200-day MA
- **timeframe:** EOD
- **source:** Knight; Rosenbloom
- **strength:** high (long-term signal)
- **conflicts:** none

### 6.4 Triple MA Crossover System

- **name:** Triple MA Crossover (3/9/18)
- **setup:** 3-period MA crosses above 9-period MA, and 9-period MA crosses above 18-period MA — all three turning in same direction
- **signal:** buy (all rising) / sell (all falling)
- **confirmation:** all three MAs aligned in same direction
- **invalidation:** fastest MA (3) crosses back in opposite direction
- **timeframe:** EOD / intraday
- **source:** Person — A Complete Guide to Technical Trading Tactics, Ch 8 (3/9/18 crossover); Elder references Donchian's 4/9/18
- **strength:** med
- **conflicts:** Person uses 3/9/18; Elder cites Donchian's 4/9/18. Minor parameter difference.

### 6.5 13-Day EMA Slope as Trend Filter

- **name:** 13-Day EMA Trend Filter
- **setup:** Slope of 13-day EMA: rising = uptrend, falling = downtrend. Trade only in direction of EMA slope.
- **signal:** buy (rising) / sell (falling) — used as a filter, not standalone
- **confirmation:** none
- **invalidation:** EMA slope reverses
- **timeframe:** EOD / weekly
- **source:** Elder — Ch 41, 43 (can substitute for weekly MACD-Histogram as Triple Screen first screen)
- **strength:** med
- **conflicts:** none

---

## 7. BOLLINGER BAND RULES

### 7.1 Bollinger Band Squeeze

- **name:** Bollinger Band Squeeze
- **setup:** Bollinger Bands (20-period, 2 std dev) contract to their narrowest width in at least 6 months. Bandwidth = (Upper Band − Lower Band) / Middle Band is at a minimum.
- **signal:** neutral (breakout imminent — direction unknown)
- **confirmation:** close outside the band in the breakout direction with expanding volume
- **invalidation:** bands expand but price reverses back inside
- **timeframe:** EOD
- **source:** Knight — Chart Your Way To Profits; Farley — The Master Swing Trader (13-bar, 2 std dev for intraday); Morris — Squeeze Alert pattern data
- **strength:** high
- **conflicts:** Standard is 20-bar/2 std dev. Farley uses 13-bar/2 std dev for intraday for faster sensitivity.

### 7.2 Bollinger Band Walk (Upper)

- **name:** Bollinger Band Upper Walk
- **setup:** In a strong uptrend, price repeatedly touches or closes above the upper Bollinger Band (20, 2) while the bands are expanding
- **signal:** buy (trend continuation — do NOT treat as overbought sell signal)
- **confirmation:** expanding bandwidth; rising volume
- **invalidation:** price closes below the middle band (20-day MA)
- **timeframe:** EOD
- **source:** Knight; Elder
- **strength:** med
- **conflicts:** none

### 7.3 Bollinger Band Walk (Lower)

- **name:** Bollinger Band Lower Walk
- **setup:** In a strong downtrend, price repeatedly touches or closes below the lower Bollinger Band while bands expand
- **signal:** sell (continuation — do NOT treat as oversold buy signal)
- **confirmation:** expanding bandwidth; rising volume on down days
- **invalidation:** price closes above the middle band
- **timeframe:** EOD
- **source:** Knight; Elder
- **strength:** med
- **conflicts:** none

### 7.4 Bollinger Band Target

- **name:** Bollinger Band Price Target
- **setup:** Price bounces off one Bollinger Band (20, 2) and crosses the 20-day MA
- **signal:** target = opposite band. If price bounces off lower band and crosses above 20-day MA → target upper band. If bounces off upper band and crosses below 20-day MA → target lower band.
- **confirmation:** sustained close beyond the 20-day MA
- **invalidation:** price reverses back through the 20-day MA before reaching opposite band
- **timeframe:** EOD
- **source:** Murphy — Technical Analysis of the Financial Markets, Ch 9
- **strength:** med
- **conflicts:** none

### 7.5 Envelope Band Overextension

- **name:** Moving Average Envelope Touch
- **setup:** Price touches or penetrates an envelope band: 3% envelope around 21-day MA (daily) or 5% envelope around 10-week MA (weekly)
- **signal:** mean-reversion expected — price is overextended. Touch of upper envelope = overbought; touch of lower envelope = oversold.
- **confirmation:** reversal candle pattern at the envelope boundary
- **invalidation:** price closes beyond envelope for 3+ consecutive bars (trending, not mean-reverting)
- **timeframe:** EOD (3%/21-day) or weekly (5%/10-week)
- **source:** Murphy — Technical Analysis of the Financial Markets, Ch 9
- **strength:** med
- **conflicts:** Bollinger Bands (20, 2σ) vs Envelopes (fixed %) — Bollinger adapts to volatility, envelopes do not. Use Bollinger in volatile markets, envelopes in stable-volatility markets.

---

## 8. PIVOT POINT RULES

### 8.1 Daily Pivot Point Calculation

- **name:** Daily Pivot Point Levels
- **setup:**
  - PP = (High + Low + Close) / 3
  - R1 = (2 × PP) − Low
  - S1 = (2 × PP) − High
  - R2 = PP + (High − Low)
  - S2 = PP − (High − Low)
- **signal:** neutral (levels define support/resistance zones)
- **confirmation:** candle pattern or oscillator signal at a pivot level
- **invalidation:** price slices through level without reversal on above-average volume
- **timeframe:** intraday / EOD (calculated from prior day's OHLC)
- **source:** Person — A Complete Guide to Technical Trading Tactics; Person — Candlestick and Pivot Point Trading Triggers
- **strength:** high
- **conflicts:** none

### 8.2 Pivot Point Bounce Buy

- **name:** Pivot Support Bounce
- **setup:** Price declines to S1 or S2 pivot level and forms a bullish candle pattern (hammer, engulfing, piercing) at that level
- **signal:** buy
- **confirmation:** stochastic oversold (%K below 20) at the pivot level; or bullish candle confirmation
- **invalidation:** close below the pivot support level
- **timeframe:** intraday / EOD
- **source:** Person — Candlestick and Pivot Point Trading Triggers (P3T method — Pivot Point, Pattern, and Trigger)
- **strength:** high
- **conflicts:** none

### 8.3 Pivot Point Resistance Sell

- **name:** Pivot Resistance Rejection
- **setup:** Price rallies to R1 or R2 pivot level and forms a bearish candle pattern (shooting star, engulfing, dark cloud) at that level
- **signal:** sell
- **confirmation:** stochastic overbought (%K above 80) at the pivot level; or bearish candle confirmation
- **invalidation:** close above the pivot resistance level
- **timeframe:** intraday / EOD
- **source:** Person — Candlestick and Pivot Point Trading Triggers
- **strength:** high
- **conflicts:** none

---

## 9. CHART PATTERN RULES

### 9.1 Head and Shoulders Top

- **name:** Head and Shoulders Top
- **setup:** (1) Left shoulder: rally to a peak on volume, pullback. (2) Head: rally to a higher peak (ideally on lower volume than left shoulder), pullback to neckline. (3) Right shoulder: rally to a peak lower than the head (often on diminished volume), then decline toward neckline. (4) Breakdown: price closes below the neckline.
- **signal:** sell (on neckline break)
- **confirmation:** neckline break on increasing volume; retest of neckline from below fails
- **invalidation:** price reclaims neckline and closes above right shoulder
- **timeframe:** EOD / weekly
- **source:** Knight — Chart Your Way To Profits (73 references); Rosenbloom — The Complete Trading Course; Farley
- **strength:** high
- **conflicts:** none

### 9.2 Inverse Head and Shoulders

- **name:** Inverse Head and Shoulders
- **setup:** Mirror of H&S Top at bottoms. Neckline breakout on volume = buy.
- **signal:** buy (on neckline break)
- **confirmation:** neckline break on volume; retest from above holds
- **invalidation:** price falls back below neckline and closes below right shoulder
- **timeframe:** EOD / weekly
- **source:** Knight; Rosenbloom; Farley
- **strength:** high
- **conflicts:** none

### 9.3 Double Top

- **name:** Double Top
- **setup:** Two peaks at approximately the same price level with a trough between them. Breakdown confirmed by close below the trough (support).
- **signal:** sell
- **confirmation:** break of trough support on volume
- **invalidation:** price closes above the double-top peaks
- **timeframe:** EOD
- **source:** Knight; Rosenbloom; Farley
- **strength:** high
- **conflicts:** none

### 9.4 Double Bottom

- **name:** Double Bottom
- **setup:** Two troughs at approximately the same price level with a peak between them. Breakout confirmed by close above the peak (resistance).
- **signal:** buy
- **confirmation:** break of peak resistance on volume
- **invalidation:** price closes below the double-bottom troughs
- **timeframe:** EOD
- **source:** Knight; Rosenbloom; Farley
- **strength:** high
- **conflicts:** none

### 9.5 Ascending Triangle

- **name:** Ascending Triangle Breakout
- **setup:** Flat upper resistance line with rising lower trendline (higher lows). Breakout = close above the flat resistance.
- **signal:** buy
- **confirmation:** breakout on expanding volume
- **invalidation:** price breaks below the rising trendline
- **timeframe:** EOD
- **source:** Knight; Rosenbloom; Brooks (wedge variant)
- **strength:** high
- **conflicts:** none

### 9.6 Descending Triangle

- **name:** Descending Triangle Breakdown
- **setup:** Flat lower support line with declining upper trendline (lower highs). Breakdown = close below flat support.
- **signal:** sell
- **confirmation:** breakdown on expanding volume
- **invalidation:** price breaks above the declining trendline
- **timeframe:** EOD
- **source:** Knight; Rosenbloom
- **strength:** high
- **conflicts:** none

### 9.7 Bull Flag

- **name:** Bull Flag Breakout
- **setup:** (1) Sharp, near-vertical advance (the "pole") on heavy volume. (2) Tight, downward-sloping parallel consolidation channel (the "flag") on declining volume. (3) Breakout above the flag's upper boundary on expanding volume.
- **signal:** buy
- **confirmation:** breakout on volume; measured move target = pole height added to breakout point
- **invalidation:** close below the flag's lower boundary
- **timeframe:** EOD / intraday
- **source:** Knight; Rosenbloom; Nison — Ch 16 (swing targets, flags, pennants)
- **strength:** high
- **conflicts:** none

### 9.8 Bear Flag

- **name:** Bear Flag Breakdown
- **setup:** Mirror of bull flag — sharp decline, then upward-sloping consolidation, then breakdown below the flag's lower boundary
- **signal:** sell
- **confirmation:** breakdown on volume; target = pole height subtracted from breakdown
- **invalidation:** close above the flag's upper boundary
- **timeframe:** EOD / intraday
- **source:** Knight; Rosenbloom
- **strength:** high
- **conflicts:** none

---

## 10. PRICE ACTION RULES (AL BROOKS)

### 10.1 Trend Bar Momentum

- **name:** Trend Bar as Momentum Signal
- **setup:** A trend bar is a candle with a body that is larger than average and closes near its extreme (near high for bull trend bar, near low for bear trend bar). Two or more consecutive trend bars in one direction = strong momentum.
- **signal:** buy (bull trend bars) / sell (bear trend bars)
- **confirmation:** follow-through bar in same direction
- **invalidation:** opposite trend bar appears immediately
- **timeframe:** EOD / intraday
- **source:** Brooks — Trading Price Action Trends, Ch 2 (570 references to "trend bar")
- **strength:** high
- **conflicts:** none

### 10.2 Two-Bar Reversal

- **name:** Two-Bar Reversal
- **setup:** Two consecutive bars with opposite trend characteristics: (1) Bullish: a bear trend bar followed immediately by a bull trend bar of similar size that closes above the bear bar's open. (2) Bearish: a bull trend bar followed by a bear trend bar closing below the bull bar's open.
- **signal:** buy (bullish two-bar) / sell (bearish two-bar)
- **confirmation:** entry above signal bar's high (for buy) or below signal bar's low (for sell)
- **invalidation:** entry bar fails — if buying, price falls below signal bar's low
- **timeframe:** EOD / intraday
- **source:** Brooks — Ch 4-5 (139 references)
- **strength:** high
- **conflicts:** none

### 10.3 Inside Bar Breakout

- **name:** Inside Bar Breakout
- **setup:** A bar whose high is below the prior bar's high AND whose low is above the prior bar's low (ii = two consecutive inside bars = even stronger). Breakout = price exceeds the inside bar's range.
- **signal:** buy (break above) / sell (break below) — trade in direction of prevailing trend
- **confirmation:** strong trend bar on breakout
- **invalidation:** breakout fails — price reverses and breaks opposite side of inside bar
- **timeframe:** EOD / intraday
- **source:** Brooks — Ch 4 (113 references); Farley — NR7 variant
- **strength:** med
- **conflicts:** none

### 10.4 Outside Bar

- **name:** Outside Bar Reversal
- **setup:** A bar whose high is above the prior bar's high AND whose low is below the prior bar's low. Close near the extreme signals direction: close near high = bullish; close near low = bearish.
- **signal:** buy (close near high) / sell (close near low)
- **confirmation:** follow-through in direction of close
- **invalidation:** next bar reverses and closes beyond the outside bar's opposite extreme
- **timeframe:** EOD / intraday
- **source:** Brooks — Ch 7 (88 references)
- **strength:** med
- **conflicts:** none

### 10.5 Breakout Pullback

- **name:** Breakout Pullback Entry
- **setup:** After a breakout from a trading range or pattern, price pulls back 1-5 bars to near the breakout level (which should now act as support/resistance). Entry on the pullback in the breakout direction.
- **signal:** buy (if bullish breakout) / sell (if bearish breakout)
- **confirmation:** pullback holds above breakout level; signal bar at pullback low
- **invalidation:** price retraces fully back into the prior range
- **timeframe:** EOD / intraday
- **source:** Brooks — Ch 3 (104 references)
- **strength:** high
- **conflicts:** none

### 10.6 Measured Move

- **name:** Measured Move Target
- **setup:** After completing a two-legged move (leg 1 → pullback → leg 2), the expected target for leg 2 equals the length of leg 1 projected from the pullback's end. MM = Pullback_end + (Leg1_end − Leg1_start).
- **signal:** neutral (target/exit level)
- **confirmation:** none
- **invalidation:** price fails to reach the target and reverses
- **timeframe:** EOD / intraday
- **source:** Brooks (133 references); Nison — Ch 16 (swing targets)
- **strength:** med
- **conflicts:** none

### 10.7 Micro Channel Break

- **name:** Micro Channel Break
- **setup:** A micro channel is a tight trend with no pullbacks — every bar's low is at or above the prior bar's low (bull) or every bar's high is at or below the prior bar's high (bear). A break of the micro channel (bar low < prior bar's low in bull micro) signals at least a small pullback.
- **signal:** first break usually leads to pullback, not reversal — buy the pullback in a bull trend
- **confirmation:** none
- **invalidation:** trend resumes without pullback; or deep reversal ensues
- **timeframe:** intraday
- **source:** Brooks — Ch 16 (113 references)
- **strength:** med
- **conflicts:** none

---

## 11. SWING TRADING RULES (FARLEY)

### 11.1 NR7 Breakout

- **name:** NR7 — Narrowest Range of 7 Bars
- **setup:** The current bar has the narrowest high-low range of the last 7 bars. This signals a volatility contraction ("coiled spring"). Trade the breakout in either direction from the next bar.
- **signal:** buy (if breakout above NR7 high) / sell (if breakdown below NR7 low)
- **confirmation:** trend bar on breakout
- **invalidation:** false breakout — price reverses and breaks opposite side
- **timeframe:** EOD / intraday
- **source:** Farley — The Master Swing Trader, Ch 9 (52 references)
- **strength:** high
- **conflicts:** none

### 11.2 First Rise / First Failure

- **name:** First Rise / First Failure (FR/FF)
- **setup:** First Rise: after a basing/bottoming pattern, the first rally to a new short-term high. First Failure: after a topping pattern, the first decline to a new short-term low. These first moves define the new range.
- **signal:** buy (first rise confirms new uptrend) / sell (first failure confirms new downtrend)
- **confirmation:** volume confirmation on the breakout
- **invalidation:** price reverses back into the prior range
- **timeframe:** EOD
- **source:** Farley — Ch 5 (25 references)
- **strength:** med
- **conflicts:** none

### 11.3 Power Spike

- **name:** Power Spike — High Volume Event
- **setup:** An exceptionally high-volume bar (>= 2× average volume) at a key price level. The direction of the close on the power spike prints the likely future direction.
- **signal:** buy (if closes bullish on spike) / sell (if closes bearish)
- **confirmation:** follow-through in spike direction
- **invalidation:** price reverses and closes beyond the power spike's opposite extreme
- **timeframe:** EOD
- **source:** Farley — Ch 11 (33 references)
- **strength:** high
- **conflicts:** none

### 11.4 Cross-Verification

- **name:** Cross-Verification (Multiple Timeframe S/R Confluence)
- **setup:** A support or resistance level is confirmed when it aligns across multiple timeframes (e.g., daily support = weekly support = monthly trendline) and/or multiple methods (e.g., pivot level = Fibonacci retracement = prior swing low).
- **signal:** buy (at confluent support) / sell (at confluent resistance)
- **confirmation:** candle reversal pattern at the confluent level
- **invalidation:** price closes through the confluent level on volume
- **timeframe:** multi-timeframe
- **source:** Farley — throughout (61 references); Rosenbloom (120 references to "confluence")
- **strength:** high
- **conflicts:** none

---

## 12. VOLUME RULES

### 12.1 Volume Confirms Trend

- **name:** Volume-Trend Confirmation
- **setup:** In an uptrend, volume increases on up days and decreases on down days (pullbacks). In a downtrend, volume increases on down days and decreases on rallies.
- **signal:** buy (volume confirms uptrend) / sell (volume confirms downtrend)
- **confirmation:** none
- **invalidation:** volume diverges from trend (rising volume on pullbacks = warning)
- **timeframe:** EOD
- **source:** Elder — Ch 32; Rosenbloom; Nison — Ch 15; O'Neil
- **strength:** high
- **conflicts:** none

### 12.2 Volume Precedes Price

- **name:** Volume Spike Precedes Breakout
- **setup:** A sudden spike in volume (>= 1.5× the 50-day average volume) occurs during or just before a price breakout from a consolidation pattern
- **signal:** buy (if upside breakout) / sell (if downside breakout)
- **confirmation:** breakout bar closes near its extreme
- **invalidation:** breakout fails and price returns to consolidation range
- **timeframe:** EOD
- **source:** O'Neil — How to Make Money in Stocks (volume as key component of CAN SLIM "S"); Rosenbloom (momentum burst)
- **strength:** high
- **conflicts:** none

### 12.3 Volume Dry-Up at Base

- **name:** Volume Dry-Up
- **setup:** During a basing pattern (cup, flat base, etc.), volume contracts significantly (below average) near the end of the base, just before the breakout
- **signal:** neutral (setup for imminent breakout)
- **confirmation:** volume explodes on breakout day
- **invalidation:** volume stays low and price fails to break out
- **timeframe:** EOD / weekly
- **source:** O'Neil — How to Make Money in Stocks ("extreme trading volume dry-ups will normally occur near the lows in the price pullback")
- **strength:** high
- **conflicts:** none

---

## 13. O'NEIL CAN SLIM SYSTEM

### 13.1 C — Current Quarterly Earnings

- **name:** CAN SLIM — C (Current Earnings)
- **setup:** Current quarter's earnings per share (EPS) up at least 25% versus same quarter last year. Preferred: 40-70%+ increase. Two consecutive quarters of significant increases is even better.
- **signal:** buy (if criteria met as part of CAN SLIM screening)
- **confirmation:** accelerating quarterly EPS growth (each quarter's % increase > prior)
- **invalidation:** two quarters of material EPS slowdown
- **timeframe:** quarterly data check
- **source:** O'Neil — How to Make Money in Stocks, Ch 1 ("three out of four of the 500 best stocks showed earnings increases averaging more than 70%")
- **strength:** high
- **conflicts:** none — this is partly fundamental, but codifiable from earnings data

### 13.2 A — Annual Earnings Growth

- **name:** CAN SLIM — A (Annual Earnings)
- **setup:** Annual EPS growth rate of at least 25% over each of the past 3-5 years
- **signal:** buy (filter)
- **confirmation:** stable or accelerating growth trajectory
- **invalidation:** annual growth drops below 25%
- **timeframe:** annual data check
- **source:** O'Neil — Ch 2
- **strength:** high
- **conflicts:** none

### 13.3 N — New High from a Proper Base

- **name:** CAN SLIM — N (New High Breakout)
- **setup:** Stock breaks out to a new 52-week high from a sound price consolidation pattern (cup-with-handle, flat base, double bottom). The base should be at least 5-7 weeks long. Decline from peak to trough within the base is typically 12-33%.
- **signal:** buy (on the breakout)
- **confirmation:** volume on breakout day >= 1.5× average daily volume
- **invalidation:** stock falls 7-8% below the breakout price (O'Neil's absolute stop rule)
- **timeframe:** EOD / weekly
- **source:** O'Neil — Ch 3
- **strength:** high
- **conflicts:** none

### 13.4 S — Supply/Demand (Volume)

- **name:** CAN SLIM — S (Supply and Demand)
- **setup:** Volume on up days should exceed volume on down days. On breakout day, volume should spike to at least 50% above average.
- **signal:** buy (volume confirms demand)
- **confirmation:** continued above-average volume for first few days of advance
- **invalidation:** price rises on declining volume (distribution)
- **timeframe:** EOD
- **source:** O'Neil — Ch 4
- **strength:** high
- **conflicts:** none

### 13.5 L — Leader (Relative Strength)

- **name:** CAN SLIM — L (Relative Strength Rating)
- **setup:** Stock's Relative Strength Rating (price performance vs. all other stocks over prior 12 months) must be >= 80, preferably >= 90
- **signal:** buy (filter — only buy leaders)
- **confirmation:** RS line making new highs before price does
- **invalidation:** RS rating drops below 70
- **timeframe:** weekly check
- **source:** O'Neil — Ch 5
- **strength:** high
- **conflicts:** none

### 13.6 M — Market Direction

- **name:** CAN SLIM — M (Market Direction)
- **setup:** 3 out of 4 stocks follow the general market direction. Confirm market uptrend before buying. Market tops are identified by "distribution days" — 4-5 days of higher volume selling within a 2-3 week span while the index stalls or drops.
- **signal:** buy only in confirmed uptrend / sell or stand aside in downtrend
- **confirmation:** market follow-through day: on day 4-7 of a rally attempt, a major index gains >= 1.5% on higher volume than the prior day
- **invalidation:** accumulation of distribution days (4-5 within 2-3 weeks)
- **timeframe:** EOD (index level)
- **source:** O'Neil — Ch 7
- **strength:** high
- **conflicts:** none

### 13.7 Cup-with-Handle Pattern

- **name:** Cup-with-Handle Breakout
- **setup:** (1) Prior uptrend. (2) Price forms a U-shaped cup (7-65 weeks). Correction from lip to bottom is 12-33%. (3) Handle: short pullback from the right lip (1-2 weeks), declining no more than 12-15% from the handle's high, with volume drying up. (4) Breakout: price clears the handle's high (the "pivot point") on >= 50% above-average volume.
- **signal:** buy (on breakout above the handle high)
- **confirmation:** volume >= 1.5× average on breakout; handle forms in upper half of cup
- **invalidation:** 7-8% decline below buy point (O'Neil's absolute stop-loss rule)
- **timeframe:** weekly (pattern formation) / EOD (entry)
- **source:** O'Neil — Ch 3 (13 references to cup-with-handle)
- **strength:** high
- **conflicts:** none

---

## 14. MOMENTUM & DIVERGENCE RULES (ROSENBLOOM)

### 14.1 Impulse Buy

- **name:** Impulse Buy (First Pullback After Momentum Burst)
- **setup:** (1) Identify a "momentum burst" — 3+ consecutive strong trend bars creating a sharp acceleration in price with a volume spike. (2) Wait for the first pullback/retracement after the burst. (3) Enter on the first sign of the pullback ending (bullish candle, MA support).
- **signal:** buy
- **confirmation:** pullback holds above the 20-EMA or the start of the burst; volume declines on pullback, rises on resumption
- **invalidation:** price retraces more than 61.8% of the burst move; or violates the burst's starting point
- **timeframe:** EOD / intraday
- **source:** Rosenbloom — The Complete Trading Course (39 references to "impulse buy")
- **strength:** high
- **conflicts:** none

### 14.2 Momentum Divergence Warning

- **name:** Multi-Indicator Momentum Divergence
- **setup:** Price makes a new high/low but one or more momentum indicators (RSI, MACD, Stochastic, Rate of Change) fail to confirm — i.e., they make a lower high or higher low. Stronger when multiple indicators diverge simultaneously.
- **signal:** sell (at new highs with divergence) / buy (at new lows with divergence)
- **confirmation:** trendline break or moving average break after divergence
- **invalidation:** momentum catches up and confirms the new price extreme
- **timeframe:** EOD / weekly
- **source:** Rosenbloom (215 references to "divergence"); Elder — MACD-Histogram divergence
- **strength:** high
- **conflicts:** none

### 14.3 Fibonacci Confluence Zone

- **name:** Fibonacci Retracement Confluence
- **setup:** Multiple Fibonacci retracement levels (38.2%, 50%, 61.8%) from different swing moves cluster at the same price zone, creating a strong support/resistance area
- **signal:** buy (at Fibonacci support confluence) / sell (at Fibonacci resistance confluence)
- **confirmation:** candle pattern or oscillator signal at the zone; zone aligns with a moving average or pivot level (cross-verification per Farley)
- **invalidation:** price closes decisively through the confluence zone
- **timeframe:** EOD
- **source:** Rosenbloom — Ch 6 (Fibonacci Retracement Confluence Zones); Farley — cross-verification
- **strength:** high
- **conflicts:** none

---

## 15. CANDLES + WESTERN TOOLS (COMBINED SIGNALS)

### 15.1 Candle at Moving Average Support

- **name:** Bullish Candle at MA Support
- **setup:** Price pulls back to a rising moving average (20 or 50-day) and prints a bullish candlestick reversal pattern (hammer, bullish engulfing, morning star) at or near the MA
- **signal:** buy
- **confirmation:** close above the MA on the confirmation day
- **invalidation:** close below the MA
- **timeframe:** EOD
- **source:** Nison — Ch 13 (Candles with Moving Averages); Person — Candlestick and Pivot Point Trading Triggers
- **strength:** high
- **conflicts:** none

### 15.2 Candle at Trendline

- **name:** Candle Reversal at Trendline
- **setup:** Price touches a well-established trendline (at least 3 touches) and prints a reversal candlestick pattern at the trendline
- **signal:** buy (at support trendline) / sell (at resistance trendline)
- **confirmation:** spring/upthrust (brief violation then recovery per Nison Ch 11)
- **invalidation:** close beyond the trendline on volume
- **timeframe:** EOD
- **source:** Nison — Ch 11 (Candles with Trend Lines, Springs and Upthrusts)
- **strength:** high
- **conflicts:** none

### 15.3 Candle with Oscillator Confirmation

- **name:** Candle Pattern + Oscillator Confluence
- **setup:** A candlestick reversal pattern appears AND an oscillator (RSI, Stochastic, or MACD) simultaneously confirms: e.g., bullish engulfing at a point where RSI(14) < 30 and turning up, or Stochastic %K crosses above %D below 20
- **signal:** buy / sell (per the candle + oscillator agreement)
- **confirmation:** both signals aligned
- **invalidation:** oscillator fails to confirm the candle signal
- **timeframe:** EOD / intraday
- **source:** Nison — Ch 14 (Candles with Oscillators); Person — P3T method (Pivot + Pattern + Trigger)
- **strength:** high
- **conflicts:** none

---

## 16. PARABOLIC SAR

### 16.1 Parabolic SAR Trailing Stop

- **name:** Parabolic SAR
- **setup:** Stop_tomorrow = Stop_today + AF × (EP_trade − Stop_today). AF starts at 0.02, increases by 0.02 with each new extreme point (new high for longs, new low for shorts), maxes at 0.20. EP = extreme point of trade.
- **signal:** sell (when price hits the SAR from above) / buy (when price hits SAR from below)
- **confirmation:** use only in trending markets; if whipsawed twice in a row, stop using and switch to range tools
- **invalidation:** two consecutive whipsaws = market is ranging, stop using Parabolic
- **timeframe:** EOD
- **source:** Elder — Ch 44 (Parabolic Trading System, after Wilder 1976)
- **strength:** med (excellent in trends, terrible in ranges)
- **conflicts:** none

---

## 17. CHANNEL TRADING

### 17.1 Channel Boundary Fade

- **name:** Channel Boundary Reversal
- **setup:** Price touches the upper boundary of a well-defined price channel (parallel trendlines) → sell/short. Price touches the lower boundary → buy.
- **signal:** buy (at lower channel line) / sell (at upper channel line)
- **confirmation:** reversal candle at the boundary
- **invalidation:** close outside the channel boundary on volume (channel breakout)
- **timeframe:** EOD
- **source:** Elder — Ch 45 (Channel Trading Systems); Brooks — Ch 15 (Channels); Farley
- **strength:** med
- **conflicts:** none

---

## 18. MARKET WIZARDS — CODIFIABLE RULES

### 18.1 Trend Following — Let Profits Run

- **name:** Trend Following with Trailing Stops
- **setup:** Enter in direction of the established trend (price above 200-day MA for longs). Trail stops using a fixed percentage (e.g., 20-25% from the high) or a moving average (e.g., 10-week MA).
- **signal:** buy (trend up) / sell (trend down)
- **confirmation:** trend confirmed by moving average alignment
- **invalidation:** trailing stop hit
- **timeframe:** EOD / weekly
- **source:** Schwager — Market Wizards (multiple traders: Ed Seykota, Richard Dennis, trend-following philosophy)
- **strength:** high
- **conflicts:** Specific trailing stop percentage varies by trader

> **Note:** Market Wizards is primarily interviews and trading philosophy. Very few codifiable OHLCV rules beyond general trend-following principles. The book's value is in risk management principles rather than specific entry setups.

---

## FLAGGED FOR REVIEW

The following rules have setups that remain somewhat subjective or require manual judgment that may be difficult to fully automate:

1. **"Extended rally" / "at all-time high"** — Hanging Man requires the stock to be "after an extended rally, preferably at an all-time high" (Nison). How many bars constitutes "extended"? Suggest: define as >= 20% rally from a recent swing low, or price at 52-week high.

2. **"Small real body"** — Many candlestick patterns require a "small real body" (spinning top). How small relative to recent bars? Suggest: real body <= 30% of the average real body of the prior 10 bars.

3. **"Long" candle body** — Patterns like engulfing, three soldiers require "long" bodies. Suggest: body >= 70% of the average real body of the prior 10 bars.

4. **"Well into" the prior body** — Morning/Evening Star require day 3 to close "well into" day 1's body. Nison says "above midpoint." This is codifiable using the midpoint.

5. **Brooks's "signal bar" quality** — Brooks describes many nuances about what makes a "good" signal bar (small tails, close near extreme, appropriate size). The exact thresholds are subjective in his text.

6. **Rosenbloom's "momentum burst"** — Defined as "3+ consecutive strong trend bars creating a sharp acceleration." What quantifies "sharp"? Suggest: 3+ bars where each bar's body > 1.5× 10-bar average body, and total move > 2× ATR(14).

7. **Cross-Verification (Farley)** — Counting how many independent S/R methods converge at one level requires checking multiple systems simultaneously. Codifiable but complex to implement.

8. **O'Neil's "proper base"** — Cup-with-Handle and other base patterns have many qualitative criteria (handle should form in upper half, volume dry-up shape, etc.). The 7-65 week and 12-33% correction parameters are codifiable; the shape quality is harder.

---

## SUMMARY

| Category | Rule Count |
|---|---|
| Candlestick Reversal Patterns | 26 |
| Candlestick Continuation Patterns | 4 |
| Oscillator Rules (RSI, Stochastic, MACD) | 12 |
| Elder Proprietary Indicators | 4 |
| Elder Triple Screen System | 1 (multi-component) |
| Moving Average Rules | 5 |
| Bollinger Band Rules | 5 |
| Pivot Point Rules | 3 |
| Chart Pattern Rules | 8 |
| Price Action Rules (Brooks) | 7 |
| Swing Trading Rules (Farley) | 4 |
| Volume Rules | 3 |
| O'Neil CAN SLIM System | 7 (one per letter + cup-with-handle) |
| Momentum & Divergence (Rosenbloom) | 3 |
| Combined Candle + Western | 3 |
| Parabolic SAR | 1 |
| Channel Trading | 1 |
| Market Wizards | 1 |
| **TOTAL** | **98** |

**Flagged for review:** 8 rules with subjective thresholds (see above)
**Parameter conflicts logged:** 4 (RSI levels, Stochastic periods, MA crossover periods, Bollinger Band periods for intraday)
