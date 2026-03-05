# Groww Trade API — Comprehensive Research

> **Date**: 2026-03-05  
> **SDK Docs**: https://groww.in/trade-api/docs/python-sdk  
> **Latest SDK Version**: 1.5.0 (3 Dec 2025)  
> **Package**: `pip install growwapi`  
> **Python requirement**: 3.9+

---

## Table of Contents

1. [Overview & Prerequisites](#1-overview--prerequisites)
2. [Authentication](#2-authentication)
3. [Rate Limits](#3-rate-limits)
4. [SDK Modules — Complete API Reference](#4-sdk-modules--complete-api-reference)
   - 4.1 [Instruments](#41-instruments)
   - 4.2 [Live Data](#42-live-data)
   - 4.3 [Historical Data](#43-historical-data)
   - 4.4 [Backtesting](#44-backtesting)
   - 4.5 [Feed (WebSocket)](#45-feed-websocket)
   - 4.6 [Orders](#46-orders)
   - 4.7 [Smart Orders (GTT / OCO)](#47-smart-orders-gtt--oco)
   - 4.8 [Portfolio](#48-portfolio)
   - 4.9 [Margin](#49-margin)
   - 4.10 [User](#410-user)
5. [Annexures — Constants & Enums](#5-annexures--constants--enums)
6. [Exception Handling](#6-exception-handling)
7. [SDK Version History](#7-sdk-version-history)
8. [Mapping to Our Scanner Codebase](#8-mapping-to-our-scanner-codebase)
9. [Gaps & Limitations](#9-gaps--limitations)
10. [Integration Feasibility Assessment](#10-integration-feasibility-assessment)

---

## 1. Overview & Prerequisites

### What is it?
Groww Trade API is a **paid** broker API for programmatic trading on NSE, BSE,
and MCX exchanges. It provides:
- **Market data** — live quotes, LTP, OHLC, option chains, Greeks
- **Historical data** — candle data (1min to 1month) since 2020
- **WebSocket feeds** — real-time streaming for up to 1000 instruments
- **Order management** — place/modify/cancel regular and smart orders
- **Portfolio** — holdings, positions, margin details

### Prerequisites
| Requirement | Detail |
|---|---|
| Groww account | Must have a Groww demat + trading account |
| Trading API Subscription | **Paid** — must be active in Groww app/web |
| Python | 3.9+ |
| Install | `pip install growwapi` |

### Quick Start
```python
from growwapi import GrowwAPI

API_AUTH_TOKEN = "your_token"
groww = GrowwAPI(API_AUTH_TOKEN)
```

---

## 2. Authentication

Two authentication flows are supported:

### Flow 1: API Key + Secret (Daily Approval)
- Get API Key and Secret from Groww developer portal
- Requires **daily approval** — you must re-approve each day
- Generates a session token

### Flow 2: TOTP (Persistent — No Manual Daily Approval)
- Uses `pyotp` library for time-based one-time passwords
- No manual daily step — token refreshes automatically
- **Recommended for automated/scheduled trading systems**

### Token Lifecycle
- Tokens are short-lived (session-based)
- Must be regenerated on each new session
- SDK handles token management internally once initialized

---

## 3. Rate Limits

| Category | Per-Second | Per-Minute |
|---|---|---|
| **Orders** | 10 | 250 |
| **Live Data** (quotes, LTP, OHLC) | 10 | 300 |
| **Non-Trading** (instruments, portfolio, margin, user) | 20 | 500 |
| **Feed** (WebSocket) | Up to 1000 subscriptions | N/A |

### Impact on our scanner
- Our scanner processes ~130 F&O stocks. At 50 per `get_ltp()` batch, that's
  3 calls = well within 10/sec limit.
- Historical data for 30 stocks at 1 call/stock = 30 calls = within 300/min.
- Feed (1000 instrument cap) can cover **all** 130 F&O stocks simultaneously.

**Exception class**: `GrowwAPIRateLimitException` — raised when limits exceeded.

---

## 4. SDK Modules — Complete API Reference

### 4.1 Instruments

**Purpose**: Download and look up the full instrument master.

#### Key Methods

| Method | Params | Returns |
|---|---|---|
| `get_instrument_by_groww_symbol(groww_symbol)` | `"NSE-RELIANCE"` | `dict` with all instrument fields |
| `get_instrument_by_exchange_and_trading_symbol(exchange, trading_symbol)` | `exchange=groww.EXCHANGE_NSE, trading_symbol="RELIANCE"` | `dict` |
| `get_instrument_by_exchange_token(exchange_token)` | `"2885"` | `dict` |
| `get_all_instruments()` | — | `pd.DataFrame` (full instrument master) |

#### Instrument CSV Columns
| Column | Type | Description |
|---|---|---|
| `exchange` | str | NSE, BSE, MCX |
| `exchange_token` | str | Unique exchange token (needed for Feed subscriptions) |
| `trading_symbol` | str | e.g. `RELIANCE`, `NIFTY25OCT24000CE` |
| `groww_symbol` | str | e.g. `NSE-RELIANCE`, `NSE-NIFTY-30Sep25-24650-CE` |
| `name` | str | Company/instrument name |
| `instrument_type` | str | `EQ`, `IDX`, `FUT`, `CE`, `PE` |
| `segment` | str | `CASH`, `FNO`, `COMMODITY` |
| `series` | str | `EQ`, `A`, `B`, etc. |
| `isin` | str | `INE002A01018` |
| `underlying_symbol` | str | For derivatives — e.g. `NIFTY`, `BANKNIFTY` |
| `underlying_exchange_token` | str | Exchange token of the underlying |
| `lot_size` | int | Min trading lot (1 for equity) |
| `expiry_date` | str | For derivatives (YYYY-MM-DD) |
| `strike_price` | float | For options |
| `tick_size` | float | Min price movement |
| `freeze_quantity` | int | Max quantity per order |
| `is_reserved` | bool | Reserved for trading |
| `buy_allowed` | bool | Buying allowed |
| `sell_allowed` | bool | Selling allowed |

#### Groww Symbol Format
- **Equity**: `NSE-WIPRO`, `BSE-RELIANCE`
- **Index**: `NSE-NIFTY`, `BSE-SENSEX`
- **Future**: `NSE-NIFTY-30Sep25-FUT`
- **Call Option**: `NSE-NIFTY-30Sep25-24650-CE`
- **Put Option**: `NSE-NIFTY-30Sep25-24650-PE`

CSV URL: `groww.INSTRUMENT_CSV_URL` → `https://growwapi-assets.groww.in/instruments/instrument.csv`

#### Relevance to Scanner
- **Replace hardcoded `SECTOR_STOCKS` / `ALL_FNO_STOCKS`** with dynamic instrument master
- Use `get_all_instruments()` → filter by `segment == "CASH"` and `instrument_type == "EQ"` for equity universe
- `exchange_token` is required for WebSocket Feed subscriptions
- `trading_symbol` maps 1:1 with our existing symbol format (e.g. `RELIANCE`)

---

### 4.2 Live Data

**Purpose**: Real-time market data snapshots (REST API, not streaming).

#### Key Methods

| Method | Params | Batch Size | Returns |
|---|---|---|---|
| `get_quote(exchange, segment, trading_symbol)` | single instrument | 1 | Full quote dict |
| `get_ltp(segment, exchange_trading_symbols)` | tuple of `"NSE_RELIANCE"` format | **Up to 50** | `{symbol: ltp}` |
| `get_ohlc(segment, exchange_trading_symbols)` | tuple | **Up to 50** | `{symbol: {open, high, low, close}}` |
| `get_option_chain(exchange, underlying, expiry_date)` | single underlying | All strikes | Full chain with Greeks |
| `get_greeks(exchange, underlying, trading_symbol, expiry)` | single contract | 1 | `{delta, gamma, theta, vega, rho, iv}` |

#### get_quote Response — CRITICAL (Full Schema)

This is the **most important** method for our scanner. A single call returns:

```python
{
    "average_price": 150.25,
    "bid_quantity": 1000,
    "bid_price": 150,
    "day_change": -0.5,
    "day_change_perc": -0.33,
    "upper_circuit_limit": 151,
    "lower_circuit_limit": 148.5,
    "ohlc": {"open": 149.50, "high": 150.50, "low": 148.50, "close": 149.50},
    "depth": {
        "buy": [{"price": 100.5, "quantity": 1000}],
        "sell": [{"price": 100.5, "quantity": 1000}]
    },
    "high_trade_range": 150.5,
    "implied_volatility": 0.25,
    "last_trade_quantity": 500,
    "last_trade_time": 1633072800000,
    "low_trade_range": 148.25,
    "last_price": 149.5,
    "market_cap": 5000000000,
    "offer_price": 150.5,
    "offer_quantity": 2000,
    "oi_day_change": 100,                    # ← OI day change
    "oi_day_change_percentage": 0.5,         # ← OI day change %
    "open_interest": 2000,                   # ← Current OI
    "previous_open_interest": 1900,          # ← Previous day OI
    "total_buy_quantity": 5000,
    "total_sell_quantity": 4000,
    "volume": 10000,
    "week_52_high": 160,
    "week_52_low": 140
}
```

**Key fields for our scanner:**
- `open_interest`, `previous_open_interest`, `oi_day_change`, `oi_day_change_percentage`
  → Fills our `oi_analysis.py` which currently returns placeholder scores
- `volume`, `total_buy_quantity`, `total_sell_quantity` → Volume analysis
- `implied_volatility` → IV ranking (currently not available)
- `depth.buy/sell` → Order book depth (5 levels)
- `day_change_perc` → Gap % calculation during market hours

#### get_option_chain Response
Returns per-strike data with full Greeks:
```python
{
    "underlying_ltp": 25641.7,
    "strikes": {
        "23400": {
            "CE": {
                "greeks": {"delta": 0.99, "gamma": 0, "theta": -1.08, "vega": 0.69, "rho": 5.18, "iv": 25.34},
                "trading_symbol": "NIFTY25N1823400CE",
                "ltp": 2200, "open_interest": 7, "volume": 5
            },
            "PE": { ... }
        }
    }
}
```

---

### 4.3 Historical Data

**Status**: `get_historical_candle_data()` is **DEPRECATED** — use Backtesting API (`get_historical_candles()`) instead.

#### Deprecated Method (still works)

| Method | Params |
|---|---|
| `get_historical_candle_data(trading_symbol, exchange, segment, start_time, end_time, interval_in_minutes)` | `trading_symbol="RELIANCE"`, times in `yyyy-MM-dd HH:mm:ss` or epoch millis |

#### Data Retention (Historical Data API — deprecated)

| Interval | Max Span | Data Available |
|---|---|---|
| 1 min | 7 days | Last 3 months |
| 5 min | 15 days | Last 3 months |
| 10 min | 30 days | Last 3 months |
| 1 hour | 150 days | Last 3 months |
| 4 hours | 365 days | Last 3 months |
| 1 day | 1080 days (~3 years) | Full history |
| 1 week | No limit | Full history |

#### Response Format
```python
{
    "candles": [
      [1633072800, 150, 155, 145, 152, 10000],   # [epoch_sec, O, H, L, C, V]
    ],
    "start_time": "2025-01-01 15:30:00",
    "end_time": "2025-01-01 15:30:00",
    "interval_in_minutes": 5
}
```

---

### 4.4 Backtesting

**Purpose**: Fetch historical OHLCV + OI candle data for strategy backtesting.
This is the **recommended** replacement for the deprecated Historical Data API.

#### Key Methods

| Method | Params | Returns |
|---|---|---|
| `get_expiries(exchange, underlying_symbol, year?, month?)` | Symbol + optional year/month | `{"expiries": ["2024-01-25", ...]}` |
| `get_contracts(exchange, underlying_symbol, expiry_date)` | — | `{"contracts": ["NSE-NIFTY-02Jan25-28500-PE", ...]}` |
| `get_historical_candles(exchange, segment, groww_symbol, start_time, end_time, candle_interval)` | Uses `groww_symbol` format | OHLCV + OI candles |

#### get_historical_candles Response
```python
{
    "candles": [
        ["2025-09-24T10:30:00", 245.95, 246.15, 245.05, 245.6, 735060, null],
        # [timestamp, open, high, low, close, volume, open_interest]
        # OI is populated for FNO instruments; null for equities
    ],
    "closing_price": 245.40,
    "start_time": "2025-09-24 10:30:00",
    "end_time": "2025-09-24 12:00:00",
    "interval_in_minutes": 30
}
```

**Key difference from deprecated API:**
- Uses `groww_symbol` instead of `trading_symbol`
- Returns **Open Interest** for FNO instruments
- Time format is `yyyy-MM-dd HH:mm:ss` (not epoch)
- Uses candle interval constants (not raw minutes)

#### Candle Intervals
| Constant | Value |
|---|---|
| `groww.CANDLE_INTERVAL_MIN_1` | 1minute |
| `groww.CANDLE_INTERVAL_MIN_2` | 2minute |
| `groww.CANDLE_INTERVAL_MIN_3` | 3minute |
| `groww.CANDLE_INTERVAL_MIN_5` | 5minute |
| `groww.CANDLE_INTERVAL_MIN_10` | 10minute |
| `groww.CANDLE_INTERVAL_MIN_15` | 15minute |
| `groww.CANDLE_INTERVAL_MIN_30` | 30minute |
| `groww.CANDLE_INTERVAL_HOUR_1` | 1hour |
| `groww.CANDLE_INTERVAL_HOUR_4` | 4hour |
| `groww.CANDLE_INTERVAL_DAY` | 1day |
| `groww.CANDLE_INTERVAL_WEEK` | 1week |
| `groww.CANDLE_INTERVAL_MONTH` | 1month |

#### Backtesting Data Limits

| Interval | Max Span |
|---|---|
| 1 min, 2 min, 3 min, 5 min | 30 days |
| 10 min, 15 min, 30 min | 90 days |
| 1 hour, 4 hours, 1 day, 1 week, 1 month | 180 days |

**Data availability**: Equity, Index and FNO from **2020 onwards**.

---

### 4.5 Feed (WebSocket)

**Purpose**: Real-time streaming via NATS WebSocket. Provides LTP, market depth,
index values, order updates, and position updates.

#### Initialization
```python
from growwapi import GrowwFeed, GrowwAPI

groww = GrowwAPI(API_AUTH_TOKEN)
feed = GrowwFeed(groww)
```

#### Subscription Methods

| Method | Data | Scope |
|---|---|---|
| `subscribe_ltp(instruments_list, on_data_received=callback)` | Last traded price | Equity + FNO |
| `subscribe_index_value(instruments_list, on_data_received=callback)` | Index value | Indices |
| `subscribe_market_depth(instruments_list, on_data_received=callback)` | 5-level order book | Equity + FNO |
| `subscribe_fno_order_updates(on_data_received=callback)` | F&O order execution events | User orders |
| `subscribe_equity_order_updates(on_data_received=callback)` | Equity order events | User orders |
| `subscribe_fno_position_updates(on_data_received=callback)` | F&O position changes | User positions |

#### Getter Methods (synchronous polling)

| Method | Returns |
|---|---|
| `feed.get_ltp()` | `{exchange: {segment: {token: {tsInMillis, ltp}}}}` |
| `feed.get_index_value()` | `{exchange: {segment: {token: {tsInMillis, value}}}}` |
| `feed.get_market_depth()` | `{exchange: {segment: {token: {tsInMillis, buyBook, sellBook}}}}` |
| `feed.get_fno_order_update()` | Order update dict |
| `feed.get_equity_order_update()` | Order update dict |
| `feed.get_fno_position_update()` | Position update dict |

#### Instrument List Format
```python
instruments_list = [
    {"exchange": "NSE", "segment": "CASH", "exchange_token": "2885"},    # RELIANCE
    {"exchange": "NSE", "segment": "FNO",  "exchange_token": "35241"},   # FNO contract
]
```
- `exchange_token` comes from the instruments CSV
- **Up to 1000 instruments** can be subscribed simultaneously

#### Usage Pattern — Synchronous Polling
```python
feed.subscribe_ltp(instruments_list)
for i in range(10):
    time.sleep(3)
    print(feed.get_ltp())
feed.unsubscribe_ltp(instruments_list)
```

#### Usage Pattern — Async Callback
```python
def on_data_received(meta):
    print(feed.get_ltp())

feed.subscribe_ltp(instruments_list, on_data_received=on_data_received)
feed.consume()  # BLOCKING — runs event loop
```

#### Callback Metadata
```python
meta = {
    "exchange": "NSE",
    "segment": "CASH",
    "feed_type": "ltp",          # ltp | order_updates | position_updates
    "feed_key": "2885"           # exchange_token
}
```

#### LTP Response Format
```python
{"ltp": {"NSE": {"CASH": {"2885": {"tsInMillis": 1746174479582.0, "ltp": 1419.1}}}}}
```

#### Market Depth Response Format
```python
{
    "NSE": {
        "CASH": {
            "2885": {
                "tsInMillis": 1746156600.0,
                "buyBook": {
                    "1": {"price": 1418.8, "qty": 113.0},
                    "2": {"price": 1418.7, "qty": 23.0},
                    "3": {"price": 1418.6, "qty": 206.0},
                    "4": {"price": 1418.5, "qty": 774.0},
                    "5": {"price": 1418.4, "qty": 1055.0}
                },
                "sellBook": { ... }
            }
        }
    }
}
```

#### Order Update Response
```python
{
    "qty": 75,
    "price": "130",
    "filledQty": 75,
    "avgFillPrice": "110",
    "growwOrderId": "GMKFO250214150557M2HR6EJF2HSE",
    "exchangeOrderId": "1400000179694433",
    "orderStatus": "EXECUTED",
    "duration": "DAY",
    "exchange": "NSE",
    "segment": "FNO",
    "product": "NRML",
    "contractId": "NIFTY2522025400CE"
}
```

---

### 4.6 Orders

**Purpose**: Place, modify, cancel, and track orders.

#### Key Methods

| Method | Description |
|---|---|
| `place_order(...)` | Place a new order |
| `modify_order(...)` | Modify pending order |
| `cancel_order(exchange_order_id, segment)` | Cancel pending order |
| `get_order_status(exchange_order_id, segment)` | Check order status |
| `get_order_status_by_reference(reference_id, segment)` | Check by idempotency ref |
| `get_order_detail(exchange_order_id, segment)` | Full order details |
| `get_order_list(segment, page, page_size, start_date, end_date)` | Order history |
| `get_trade_list_for_order(exchange_order_id, segment)` | Fills for an order |

#### place_order Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `trading_symbol` | str | Yes | e.g. `"RELIANCE"`, `"NIFTY25OCT24000CE"` |
| `exchange` | str | Yes | `groww.EXCHANGE_NSE` |
| `segment` | str | Yes | `groww.SEGMENT_CASH` or `groww.SEGMENT_FNO` |
| `transaction_type` | str | Yes | `groww.TRANSACTION_TYPE_BUY` / `SELL` |
| `order_type` | str | Yes | `LIMIT`, `MARKET`, `SL`, `SL_M` |
| `quantity` | int | Yes | Number of shares/lots |
| `price` | str | For LIMIT/SL | Limit price as decimal string |
| `trigger_price` | str | For SL/SL_M | Trigger price |
| `product` | str | Yes | `CNC`, `MIS`, `NRML` |
| `duration` | str | Yes | `groww.VALIDITY_DAY` |
| `reference_id` | str | No | 8-20 char idempotency key |

#### Order Types
| Constant | Value | Use Case |
|---|---|---|
| `groww.ORDER_TYPE_LIMIT` | `LIMIT` | Exact price, may not fill immediately |
| `groww.ORDER_TYPE_MARKET` | `MARKET` | Immediate fill at best available |
| `groww.ORDER_TYPE_STOP_LOSS` | `SL` | Trigger + limit price |
| `groww.ORDER_TYPE_STOP_LOSS_MARKET` | `SL_M` | Trigger + market execution |

#### Product Types
| Constant | Value | Description |
|---|---|---|
| `groww.PRODUCT_CNC` | `CNC` | Cash & Carry (delivery, full payment) |
| `groww.PRODUCT_MIS` | `MIS` | Margin Intraday Square-off (auto-close EOD) |
| `groww.PRODUCT_NRML` | `NRML` | Normal margin (overnight F&O) |

#### Order Status Values
`NEW` → `ACKED` → `TRIGGER_PENDING` → `APPROVED` → `EXECUTED` → `COMPLETED`

Other: `REJECTED`, `FAILED`, `CANCELLED`, `CANCELLATION_REQUESTED`, `MODIFICATION_REQUESTED`, `DELIVERY_AWAITED`

---

### 4.7 Smart Orders (GTT / OCO)

**Purpose**: Automated entry/exit strategies.

#### GTT — Good Till Triggered
Arms a single order when a price trigger condition is met.

```python
groww.create_smart_order(
    smart_order_type=groww.SMART_ORDER_TYPE_GTT,
    reference_id="gtt-ref-unique123",
    segment=groww.SEGMENT_CASH,
    trading_symbol="TCS",
    quantity=10,
    product_type=groww.PRODUCT_CNC,
    exchange=groww.EXCHANGE_NSE,
    duration=groww.VALIDITY_DAY,
    trigger_price="3985.00",
    trigger_direction=groww.TRIGGER_DIRECTION_DOWN,
    order={"order_type": groww.ORDER_TYPE_LIMIT, "price": "3990.00",
           "transaction_type": groww.TRANSACTION_TYPE_BUY}
)
```

#### OCO — One Cancels the Other
Sets target + stop-loss simultaneously. When one leg fires, the other auto-cancels.

```python
groww.create_smart_order(
    smart_order_type=groww.SMART_ORDER_TYPE_OCO,
    reference_id="oco-ref-unique456",
    segment=groww.SEGMENT_FNO,
    trading_symbol="NIFTY25OCT24000CE",
    quantity=50,
    product_type=groww.PRODUCT_MIS,
    exchange=groww.EXCHANGE_NSE,
    duration=groww.VALIDITY_DAY,
    net_position_quantity=50,
    transaction_type=groww.TRANSACTION_TYPE_SELL,
    target={"trigger_price": "120.50", "order_type": groww.ORDER_TYPE_LIMIT, "price": "121.00"},
    stop_loss={"trigger_price": "95.00", "order_type": groww.ORDER_TYPE_STOP_LOSS_MARKET, "price": None}
)
```

#### OCO Restrictions
- OCO is meant to **exit an existing position**
- F&O: Must already hold the contract
- CASH: Only `MIS` (intraday) positions supported
- COMMODITY: **Not supported** for smart orders

#### Smart Order Management
| Method | Description |
|---|---|
| `modify_smart_order(smart_order_id, ...)` | Modify active smart order |
| `cancel_smart_order(segment, smart_order_type, smart_order_id)` | Cancel active smart order |
| `get_smart_order(segment, smart_order_type, smart_order_id)` | Get smart order details |
| `get_smart_order_list(segment?, smart_order_type?, status?, page?, page_size?, start/end_date_time?)` | List/filter smart orders |

#### Modify vs Cancel+Create Matrix

| Field | GTT | OCO | Recommendation |
|---|---|---|---|
| Quantity | ✅ Modify | ✅ Modify | Use modify |
| Trigger price | ✅ Modify | ✅ Modify (both legs) | Use modify |
| Trigger direction | ✅ Modify | N/A | Use modify |
| Order type | ✅ Modify | ❌ | GTT: modify; OCO: cancel+create |
| Limit price | ✅ Modify | ❌ | GTT: modify; OCO: cancel+create |
| Duration/validity | ❌ | ✅ Modify | OCO: modify; GTT: cancel+create |
| Product type | ❌ | ✅ Modify | OCO: modify; GTT: cancel+create |
| Symbol/contract | ❌ | ❌ | Cancel + create |

#### Smart Order Status Constants
| Constant | Value |
|---|---|
| `groww.SMART_ORDER_STATUS_ACTIVE` | Monitoring trigger conditions |
| `groww.SMART_ORDER_STATUS_TRIGGERED` | Condition met, order placed |
| `groww.SMART_ORDER_STATUS_CANCELLED` | User cancelled |
| `groww.SMART_ORDER_STATUS_EXPIRED` | Time/date expiry |
| `groww.SMART_ORDER_STATUS_FAILED` | Placement or trigger failed |
| `groww.SMART_ORDER_STATUS_COMPLETED` | Successfully completed |

#### Mapping to Our Trade Plans
Our `TradePlanGenerator` outputs: `entry`, `stop_loss`, `target_1`, `target_2`, `quantity`, `bias`

**Execution flow:**
1. Place entry order (`place_order` with `LIMIT` or `MARKET`)
2. Once filled → create OCO (`create_smart_order` with `OCO`)
   - `target.trigger_price` = our `target_1`
   - `stop_loss.trigger_price` = our `stop_loss`
   - `product_type` = `MIS` (intraday)
3. Monitor via `get_smart_order` or Feed order updates

---

### 4.8 Portfolio

**Purpose**: View holdings and positions.

#### Key Methods

| Method | Returns |
|---|---|
| `get_holdings_for_user(timeout?)` | List of long-term equity delivery holdings |
| `get_positions_for_user(segment?)` | All positions (CASH/FNO/COMMODITY) |
| `get_position_for_trading_symbol(trading_symbol, segment)` | Position for specific symbol |

#### Holdings Response
```python
{
    "holdings": [{
        "isin": "INE545U01014",
        "trading_symbol": "RELIANCE",
        "quantity": 10,
        "average_price": 100,
        "pledge_quantity": 2,
        "demat_locked_quantity": 1,
        "groww_locked_quantity": 1.5,
        "repledge_quantity": 0.5,
        "t1_quantity": 3,
        "demat_free_quantity": 5,
        "corporate_action_additional_quantity": 1,
        "active_demat_transfer_quantity": 1
    }]
}
```

#### Positions Response
```python
{
    "positions": [{
        "trading_symbol": "RELIANCE",
        "segment": "CASH",
        "credit_quantity": 10,
        "credit_price": 12500,
        "debit_quantity": 5,
        "debit_price": 12000,
        "carry_forward_credit_quantity": 8,
        "carry_forward_credit_price": 12300,
        "carry_forward_debit_quantity": 3,
        "carry_forward_debit_price": 11800,
        "exchange": "NSE",
        "symbol_isin": "INE123A01016",
        "quantity": 15,
        "product": "CNC",
        "net_carry_forward_quantity": 10,
        "net_price": 12400,
        "net_carry_forward_price": 12200,
        "realised_pnl": 500
    }]
}
```

---

### 4.9 Margin

**Purpose**: Check available margin and calculate required margin for orders.

#### Key Methods

| Method | Description |
|---|---|
| `get_available_margin_details()` | Full margin breakdown (equity, F&O, commodity) |
| `get_order_margin_details(segment, orders)` | Calculate margin for single/basket orders |

#### Available Margin Response — Key Fields
| Field | Description |
|---|---|
| `clear_cash` | Available cash |
| `net_margin_used` | Total margin in use |
| `collateral_available` | Pledged collateral available |
| **F&O** | |
| `net_fno_margin_used` | Total F&O margin used |
| `span_margin_used` | SPAN margin component |
| `exposure_margin_used` | Exposure margin component |
| `future_balance_available` | Available for futures |
| `option_buy_balance_available` | Available for option buying |
| `option_sell_balance_available` | Available for option selling |
| **Equity** | |
| `cnc_balance_available` | Delivery (CNC) buying power |
| `mis_balance_available` | Intraday (MIS) buying power |
| **Commodity** | |
| `commodity_span_margin`, `commodity_exposure_margin`, etc. | MCX margin details |

#### Order Margin Calculation
```python
order_details = [{
    "trading_symbol": "RELIANCE",
    "transaction_type": groww.TRANSACTION_TYPE_BUY,
    "quantity": 1,
    "price": 2500,
    "order_type": groww.ORDER_TYPE_LIMIT,
    "product": groww.PRODUCT_CNC,
    "exchange": groww.EXCHANGE_NSE
}]
margin = groww.get_order_margin_details(segment=groww.SEGMENT_CASH, orders=order_details)
# Returns: total_requirement, brokerage_and_charges, span_required, exposure_required, etc.
```

#### Relevance to Scanner
- Pre-validate trade plans: check if `mis_balance_available` >= required margin
- Calculate exact brokerage via API instead of estimating in `trade_plan.py`

---

### 4.10 User

**Purpose**: Get user profile and trading permissions.

#### Method
```python
profile = groww.get_user_profile()
```

#### Response
```python
{
    "vendor_user_id": "d86890d1-c60d-4ebd-9730-4feee5451670",
    "ucc": "924189",
    "nse_enabled": true,
    "bse_enabled": true,
    "ddpi_enabled": false,
    "active_segments": ["CASH", "FNO", "COMMODITY"]
}
```

- `active_segments` → validate user has `FNO` access before attempting F&O orders
- `ddpi_enabled` → if false, TPIN+OTP required for selling holdings (not relevant for MIS)

---

## 5. Annexures — Constants & Enums

### Exchanges
| SDK Constant | Value | Description |
|---|---|---|
| `GrowwAPI.EXCHANGE_BSE` | `BSE` | Bombay Stock Exchange |
| `GrowwAPI.EXCHANGE_NSE` | `NSE` | National Stock Exchange |
| `GrowwAPI.EXCHANGE_MCX` | `MCX` | Multi Commodity Exchange |

### Segments
| SDK Constant | Value | Description |
|---|---|---|
| `GrowwAPI.SEGMENT_CASH` | `CASH` | Equity delivery/intraday |
| `GrowwAPI.SEGMENT_FNO` | `FNO` | Futures & Options |
| `GrowwAPI.SEGMENT_COMMODITY` | `COMMODITY` | MCX commodities |

### Order Types
| SDK Constant | Value | Description |
|---|---|---|
| `GrowwAPI.ORDER_TYPE_LIMIT` | `LIMIT` | Specific price, may not fill |
| `GrowwAPI.ORDER_TYPE_MARKET` | `MARKET` | Best available price |
| `GrowwAPI.ORDER_TYPE_STOP_LOSS` | `SL` | Trigger + limit |
| `GrowwAPI.ORDER_TYPE_STOP_LOSS_MARKET` | `SL_M` | Trigger + market |

### Products
| SDK Constant | Value | Description |
|---|---|---|
| `GrowwAPI.PRODUCT_CNC` | `CNC` | Cash & Carry (delivery) |
| `GrowwAPI.PRODUCT_MIS` | `MIS` | Margin Intraday Square-off |
| `GrowwAPI.PRODUCT_NRML` | `NRML` | Normal margin (overnight F&O) |

### Transaction Types
| SDK Constant | Value |
|---|---|
| `GrowwAPI.TRANSACTION_TYPE_BUY` | `BUY` |
| `GrowwAPI.TRANSACTION_TYPE_SELL` | `SELL` |

### Validity
| SDK Constant | Value |
|---|---|
| `GrowwAPI.VALIDITY_DAY` | `DAY` |

### Instrument Types
| Value | Description |
|---|---|
| `EQ` | Equity |
| `IDX` | Index |
| `FUT` | Futures |
| `CE` | Call Option |
| `PE` | Put Option |

---

## 6. Exception Handling

All exceptions are in `growwapi.groww.exceptions`.

### Exception Hierarchy
```
GrowwBaseException                        # Base for all errors
├── GrowwAPIException                     # Client/API errors
│   ├── GrowwAPIAuthenticationException   # Auth failed (invalid key/token)
│   ├── GrowwAPIAuthorisationException    # Permission denied
│   ├── GrowwAPIBadRequestException       # Malformed request/params
│   ├── GrowwAPINotFoundException         # Resource not found
│   ├── GrowwAPIRateLimitException        # Rate limit exceeded
│   └── GrowwAPITimeoutException          # Request timed out
├── GrowwFeedException                    # Feed errors
├── GrowwFeedConnectionException          # WebSocket connection failure
└── GrowwFeedNotSubscribedException       # Tried to read unsubscribed topic
```

### Attributes
- **API exceptions**: `msg` (str), `code` (str)
- **Feed exceptions**: `msg` (str)
- **Not-subscribed**: `msg` (str), `topic` (str)

### Error Handling Pattern for Scanner
```python
from growwapi.groww.exceptions import (
    GrowwAPIRateLimitException,
    GrowwAPITimeoutException,
    GrowwAPIAuthenticationException,
)

try:
    quote = groww.get_quote(...)
except GrowwAPIRateLimitException:
    time.sleep(1)  # Back off and retry
except GrowwAPITimeoutException:
    logger.warning("Groww API timeout, using fallback")
except GrowwAPIAuthenticationException:
    logger.error("Auth failed — check token")
    raise
```

---

## 7. SDK Version History

| Version | Date | Highlights |
|---|---|---|
| **1.5.0** | 3 Dec 2025 | Commodity trading support (MCX) |
| **1.4.0** | 2 Dec 2025 | `get_user_profile` API |
| **1.3.0** | 24 Nov 2025 | Option Chain retrieval API |
| **1.2.0** | 29 Oct 2025 | Smart Orders (GTT, OCO) |
| **1.1.0** | 8 Oct 2025 | NATS ping stability fix |
| **1.0.0** | 3 Oct 2025 | Historical data APIs, backtesting docs |
| **0.0.10** | 22 Sep 2025 | Standardized headers, auth docs |
| **0.0.9** | 4 Sep 2025 | Checksum-based token generation |
| **0.0.8** | 11 Jun 2025 | TOTP support |
| **0.0.7** | 21 May 2025 | Feed bug fixes, protobuf parsing |
| **0.0.5** | 21 Apr 2025 | Packaging/licensing cleanup |
| **0.0.4** | 25 Mar 2025 | Exception handling in feed |
| **0.0.3** | 25 Mar 2025 | Multi-instrument feed, bulk LTP, instruments DataFrame, margin API |
| **0.0.1** | 27 Feb 2025 | Initial release — orders, portfolio, feed, instruments, historical |

**SDK maturity**: ~13 months old. 16 releases. Actively maintained.

---

## 8. Mapping to Our Scanner Codebase

### Current Data Sources → Groww Replacements

| Current Source | Current Module | Groww Replacement | Benefit |
|---|---|---|---|
| jugaad-data `stock_df()` | `data/fetcher.py → get_historical_data()` | `get_historical_candles()` | Reliable, no scraping, includes OI for FNO |
| yfinance `yf.download()` batch | `data/fetcher.py → get_bulk_historical()` | `get_historical_candles()` per symbol (no batch) | Eliminates `.NS` suffix hacks |
| jugaad-data `NSELive.stock_quote()` | `data/fetcher.py → get_live_quote()` | `get_quote()` | Returns OI, IV, depth + everything our quote needs |
| yfinance `Ticker.info` (live fallback) | `data/fetcher.py → get_live_quote()` | `get_ltp()` batch (50 at a time) | Fast, reliable, avoids yfinance `.info` parsing |
| yfinance sector index download | `data/fetcher.py → get_sector_returns()` | Keep yfinance OR compute from constituents | Groww has no direct sector index endpoint |
| yfinance `^INDIAVIX` | `data/fetcher.py → get_india_vix()` | `get_ltp(segment=CASH, "NSE_INDIA VIX")` or keep yfinance | Needs testing with VIX symbol |
| Placeholder 0.25 | `indicators_pkg/oi_analysis.py` | `get_quote()` → `open_interest`, `oi_day_change_percentage` | **Fills the biggest gap** |
| None (no execution) | `analysis/trade_plan.py` output | `place_order()` + `create_smart_order(OCO)` | Full automation |
| Hardcoded `ALL_FNO_STOCKS` | `config/sectors.py` | `get_all_instruments()` → filter | Dynamic, always current |

### Symbol Format Mapping

| Our Scanner | yfinance | Groww `trading_symbol` | Groww `groww_symbol` |
|---|---|---|---|
| `RELIANCE` | `RELIANCE.NS` | `RELIANCE` | `NSE-RELIANCE` |
| `HDFCBANK` | `HDFCBANK.NS` | `HDFCBANK` | `NSE-HDFCBANK` |
| `M&M` | `M%26M.NS` | `M&M` | `NSE-M&M` |

**Key**: Our `symbol` format maps **directly** to Groww's `trading_symbol`. No suffix needed.

### Specific Module Integration Points

#### `data/fetcher.py` DataFetcher class
- `get_historical_data()` → `groww.get_historical_candles()` using `groww_symbol=f"NSE-{symbol}"`
- `get_live_quote()` → `groww.get_quote()` — maps all fields 1:1
- `get_bulk_historical()` → Loop `get_historical_candles()` (no batch equivalent, but rate limit allows 10/sec)
- `get_india_vix()` → `groww.get_ltp()` with VIX instrument
- `get_preopen_data()` → No direct Groww equivalent (keep NSE scraping or skip)
- `get_fii_dii_data()` → No Groww equivalent (keep NSE API call)
- `get_us_market_data()` → No Groww equivalent (keep yfinance)

#### `indicators_pkg/oi_analysis.py`
- `analyse_oi_signal()` currently receives `oi_change_pct` but **never gets real data**
- With Groww: `get_quote()` → `oi_day_change_percentage` feeds directly into this function
- `open_interest` + `previous_open_interest` → compute change ourselves

#### `analysis/trade_plan.py` TradePlanGenerator
- Output `entry`, `stop_loss`, `target_1`, `target_2`, `quantity`, `bias` → maps to Groww orders
- `product=MIS` for intraday, `exchange=NSE`, `duration=DAY`

#### `analysis/scoring.py`
- `oi_signal` weight is 0.18 (highest individual weight) — currently always placeholder
- With real OI data, scoring accuracy improves significantly

#### `backtest_pkg/engine.py`
- Could use `get_historical_candles()` with intraday intervals (5min/15min)
- Current backtest uses daily OHLCV; Groww enables intraday candle backtesting
- **Limitation**: Backtesting API max 30 days for 5min candles, 90 days for 15min

---

## 9. Gaps & Limitations

### What Groww CANNOT Do for Us

| Need | Current Source | Groww Ability | Workaround |
|---|---|---|---|
| **Sector index returns** | yfinance `^NSEBANK`, `^CNXIT`, etc. | Not available | Keep yfinance for `get_sector_returns()`, or compute from sector stock prices |
| **FII/DII data** | NSE API `fiidiiTradeReact` | Not available | Keep direct NSE API call |
| **US market data** | yfinance `^GSPC`, `^IXIC` | Not available (India only) | Keep yfinance |
| **Pre-open market data** | NSE API via jugaad-data | Not available | Keep NSE scraping |
| **GIFT Nifty / SGX Nifty** | yfinance | Not available | Keep yfinance |
| **Delivery quantity/percentage** | jugaad-data `stock_df()` DELIV_QTY | Not in live quote | jugaad-data for daily, or NSE bhavcopy |
| **Batch historical download** | yfinance `yf.download()` | No batch endpoint | Loop per symbol (rate limit: 10/sec = 130 stocks in 13s) |

### Data Limits Summary

| Data Type | Groww Limit | Our Need | OK? |
|---|---|---|---|
| Daily OHLCV | ~3 years | 180 days (LOOKBACK_DAYS) | ✅ |
| 5-min candles | 30 days (backtesting) / 15 days (historical) | Intraday analysis | ⚠️ Limited for extended backtesting |
| Live LTP batch | 50 per call | ~130 F&O stocks | ✅ (3 calls) |
| WebSocket | 1000 instruments | ~130 + indices = ~145 | ✅ |
| Order rate | 10/sec, 250/min | Max 2 trades/day | ✅ (massive headroom) |

### Cost Considerations
- **Trading API Subscription**: Paid (pricing not publicly documented — check Groww app)
- **Brokerage**: Groww charges ₹20/order for intraday; our `risk.py` already uses this rate
- **No free tier** for the API — this is a production trading API, not a data API

### SDK Maturity Risks
- SDK is ~13 months old (v0.0.1 was Feb 2025)
- Breaking changes happened early (`GrowwClient` → `GrowwAPI` in v0.0.3)
- Stable since v1.0.0 (Oct 2025)
- TOTP flow added in v0.0.8 (Jun 2025) — essential for automation
- Feed stability issues were fixed in v0.0.7 and v1.1.0

---

## 10. Integration Feasibility Assessment

### Verdict: **Highly Beneficial — Recommended for Phased Integration**

### Phase 1 — Data Layer (Low Risk, High Value)
Replace jugaad-data + yfinance for core data:
- Create `broker/groww_adapter.py` implementing same interface as `DataFetcher`
- Use `get_quote()` for live quotes with **real OI data**
- Use `get_historical_candles()` for daily OHLCV
- Keep yfinance for sector indices, US markets, India VIX, FII/DII (fallback)
- **Impact**: OI scoring becomes real (currently 0.18 weight is wasted)

### Phase 2 — Trade Execution (Medium Risk, High Value)
Wire trade plans to actual orders:
- `place_order()` for entries
- `create_smart_order(OCO)` for SL + target bracket
- `subscribe_equity_order_updates()` for fill monitoring
- Pre-validate via `get_order_margin_details()`
- **Impact**: Scanner becomes a full auto-trading system

### Phase 3 — Real-Time Mode (Medium Risk, Medium Value)
Add WebSocket-based live monitoring:
- `GrowwFeed.subscribe_ltp()` for 130+ instruments
- Replace polling-based scanner with event-driven
- Real-time P&L tracking via position updates
- **Impact**: Faster reaction to intraday setups

### Phase 4 — Enhanced Backtesting (Low Risk, Nice-to-Have)
- Use intraday candle data (5min/15min) for more granular backtesting
- Replace current daily-only backtest with intraday simulation
- Use `get_expiries()` + `get_contracts()` for F&O strategy testing
- **Impact**: More realistic backtest with intraday price action

### Architecture Decision
Use **adapter pattern** so the scanner works with or without Groww:
```
data/
├── fetcher.py              # Existing (jugaad + yfinance)
├── base.py                 # Abstract DataProvider interface
└── groww_provider.py       # Groww implementation

broker/
├── base.py                 # Abstract BrokerInterface
├── groww_broker.py          # Groww order execution
└── paper_broker.py          # Paper trading (for testing)
```

Config switch: `DATA_PROVIDER = "groww"` or `DATA_PROVIDER = "default"` in config.

---

*Research complete. All 13 SDK documentation pages reviewed. Ready for plan document.*
