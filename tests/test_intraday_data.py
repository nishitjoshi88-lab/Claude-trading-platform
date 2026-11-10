"""Tests for quant/data/intraday.py: parsing, cleaning, splitting, quality figures.

Everything runs on small inline fixtures; nothing touches the network.
"""
import io
import json

import numpy as np
import pandas as pd
import pytest

from quant.data import intraday as I
from quant.data import store


def bars(start, n, price=100.0, step=0.1, freq="min", volume=10.0):
    ts = pd.date_range(start, periods=n, freq=freq)
    c = price + step * np.arange(n)
    return pd.DataFrame({"ts": ts, "open": c, "high": c + 0.5, "low": c - 0.5, "close": c + 0.2,
                         "volume": volume}).astype({k: "float32" for k in I.COLS[1:]})


def full_day(day, **kw):
    return bars(f"{day} 09:15", 375, **kw)


# ---------------------------------------------------------------- parsers

def test_parse_akshaj_reads_ist_bar_start_and_volume():
    text = ("date,open,high,low,close,volume\n"
            "2015-02-02 09:15:00,1000.85,1005.5,1000.85,1004.4,7478\n"
            "2015-02-02 09:16:00,1004.4,1008.65,1003.9,1004.0,333\n")
    df = I.parse_akshaj(io.StringIO(text))
    assert list(df.columns) == I.COLS
    assert df["ts"].tolist() == [pd.Timestamp("2015-02-02 09:15"), pd.Timestamp("2015-02-02 09:16")]
    assert df["ts"].dt.tz is None
    assert df["close"].dtype == "float32" and df["volume"].dtype == "float32"
    assert df["volume"].tolist() == [7478.0, 333.0]
    assert df["high"].iloc[1] == pytest.approx(1008.65, abs=1e-3)


def test_parse_sandeepkapri_day_first_dates_and_no_volume():
    text = ("Instrument,Date,Time,Open,High,Low,Close\n"
            "Nifty50,09-01-2015,9:15:00,8285.45,8295.9,8285.45,8292.1\n"
            "Nifty50,12-01-2015,15:29:00,8320,8321,8319,8320.5\n")
    df = I.parse_sandeepkapri(io.StringIO(text))
    # 09-01-2015 is 9 January, 12-01-2015 is 12 January (not 1 September / 1 December)
    assert df["ts"].tolist() == [pd.Timestamp("2015-01-09 09:15"), pd.Timestamp("2015-01-12 15:29")]
    assert df["volume"].isna().all()                 # the file has no volume: it must stay unknown, not 0
    assert df["open"].iloc[0] == pytest.approx(8285.45, abs=1e-2)


def test_parse_sandeepkapri_refuses_unparseable_timestamps():
    text = "Instrument,Date,Time,Open,High,Low,Close\nNifty50,2015/01/09,9:15,1,1,1,1\n"
    with pytest.raises(ValueError, match="could not be parsed"):
        I.parse_sandeepkapri(io.StringIO(text))


def test_parse_technovus_checks_epoch_against_ist_clock():
    good = ("Epoch,Timestamp,Open,High,Low,Close\n"
            "1491191100,2017-04-03T09:15:00,9219.63,9221.75,9202.9,9204.85\n")
    df = I.parse_technovus(io.StringIO(good))
    assert df["ts"].iloc[0] == pd.Timestamp("2017-04-03 09:15")      # 03:45 UTC + 05:30
    assert df["volume"].isna().all()
    bad = good.replace("1491191100", "1491171300")                   # epoch that would be UTC wall time
    with pytest.raises(ValueError, match="disagree"):
        I.parse_technovus(io.StringIO(bad))


def test_parse_aeron_label_is_bar_end_and_columns_are_optional():
    spot = "NIFTY,20121203,09:16,5882.30,5884.25,5873.10,5873.15\nNIFTY,20121203,15:30,5872.20,5873.15,5869.40,5869.95\n"
    df = I.parse_aeron(io.StringIO(spot))
    assert df["ts"].tolist() == [pd.Timestamp("2012-12-03 09:15"), pd.Timestamp("2012-12-03 15:29")]
    assert df["volume"].isna().all() and df["oi"].isna().all()
    fut = "BANKNIFTY_F1,20160901,09:16,19879.85,19879.85,19849.75,19854.00,33920,2825760\n"
    df = I.parse_aeron(io.StringIO(fut))
    assert df["volume"].iloc[0] == 33920 and df["oi"].iloc[0] == 2825760
    assert df["oi"].dtype == "float32"
    with pytest.raises(ValueError):                                   # another layout must not be guessed at
        I.parse_aeron(io.StringIO("20180829 091659;11746.1;11746.1;11728.5;11730.7;59\n"))


def test_parse_trademarkk_converts_to_naive_ist(tmp_path):
    ts = pd.to_datetime(["2021-05-24 03:45:00", "2021-05-24 03:46:00"]).tz_localize("UTC").tz_convert("Asia/Kolkata")
    idx = pd.DataFrame({"timestamp": ts, "open": [1.0, 2], "high": [1.5, 2.5], "low": [0.5, 1.5], "close": [1.2, 2.2],
                        "volume": [0, 0], "trading_day": "2021-05-24", "symbol": "NIFTY"})
    idx.to_parquet(tmp_path / "i.parquet")
    df = I.parse_trademarkk_index(tmp_path / "i.parquet")
    assert df["ts"].tolist() == [pd.Timestamp("2021-05-24 09:15"), pd.Timestamp("2021-05-24 09:16")]
    assert df["ts"].dt.tz is None

    opt = idx.assign(open_interest=[100, 200], strike=np.array([15000, 15000], dtype="int32"),
                     option_type=["CE", "PE"], expiry="2021-05-27")
    opt.to_parquet(tmp_path / "o.parquet")
    o = I.parse_trademarkk_options(tmp_path / "o.parquet")
    assert list(o.columns) == I.OPT_COLS
    assert o["expiry"].iloc[0] == pd.Timestamp("2021-05-27") and o["right"].tolist() == ["CE", "PE"]
    assert o["oi"].tolist() == [100.0, 200.0] and o["strike"].dtype == "float32"

    naive = idx.assign(timestamp=idx["timestamp"].dt.tz_localize(None))
    naive.to_parquet(tmp_path / "n.parquet")
    with pytest.raises(ValueError, match="timezone-aware"):
        I.parse_trademarkk_index(tmp_path / "n.parquet")


def _tiru_shard(path, rows):
    pd.DataFrame(rows, columns=["stock_name", "date", "open", "high", "low", "close"]).to_parquet(path)


def test_iter_tiru_joins_a_symbol_across_shards(tmp_path):
    _tiru_shard(tmp_path / "train-00000.parquet", [
        ["AAA", "2015-02-02 09:15:00+05:30", 1.0, 2, 1, 1.5],
        ["BBB", "2015-02-02 09:15:00+05:30", 10.0, 11, 9, 10.5]])
    _tiru_shard(tmp_path / "train-00001.parquet", [
        ["BBB", "2015-02-02 09:16:00+05:30", 10.5, 12, 10, 11.0],
        ["CCC", "2015-02-02 09:15:00+05:30", 5.0, 6, 4, 5.5]])
    got = dict(I.iter_tiru(sorted(tmp_path.glob("*.parquet"))))
    assert list(got) == ["AAA", "BBB", "CCC"]
    assert got["BBB"]["ts"].tolist() == [pd.Timestamp("2015-02-02 09:15"), pd.Timestamp("2015-02-02 09:16")]
    assert got["BBB"]["close"].tolist() == [10.5, 11.0]
    assert got["AAA"]["volume"].isna().all()


def test_iter_tiru_requires_ist_offset(tmp_path):
    _tiru_shard(tmp_path / "train-00000.parquet", [["AAA", "2015-02-02 03:45:00+00:00", 1.0, 2, 1, 1.5]])
    with pytest.raises(ValueError, match=r"\+05:30"):
        list(I.iter_tiru([tmp_path / "train-00000.parquet"]))


def test_parse_nse_index_daily_and_listing_dates():
    text = ("Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,Closing Index Value,Points Change\n"
            "CNX Nifty,09-01-2015,8285.45,8303.3,8190.8,8284.5,49.9\n"
            "India VIX,09-01-2015,16.4725,16.9075,14.4625,15.96,-.52\n")
    d = I.parse_nse_index_daily(text)
    assert d["name"].tolist() == ["CNX NIFTY", "INDIA VIX"]
    assert d["date"].iloc[0] == pd.Timestamp("2015-01-09") and d["high"].iloc[0] == 8303.3
    assert "CNX NIFTY" in I.NSE_INDEX_NAMES["NIFTY"]
    lst = I.parse_listing_dates("SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE\n"
                                "IRCTC,Indian Railway Catering,EQ,14-OCT-2019,2\nACC,ACC Limited,EQ,20-NOV-1996,10\n")
    assert lst == {"IRCTC": pd.Timestamp("2019-10-14"), "ACC": pd.Timestamp("1996-11-20")}


# ---------------------------------------------------------------- cleaning

def test_clean_bars_only_removes_rows():
    df = bars("2020-01-31 09:15", 5)
    extra = pd.DataFrame({
        "ts": pd.to_datetime(["2020-01-31 09:17",     # duplicate timestamp, different values
                              "2020-01-31 09:10",     # before the open
                              "2020-01-31 15:30",     # at/after the close
                              "2020-01-31 18:30",     # evening special session
                              "2020-01-31 12:00",     # zero price
                              "2020-01-31 12:01",     # high below low
                              "2020-01-31 12:02"]),   # missing close
        "open": [1.0, 100, 100, 100, 0, 100, 100], "high": [1.0, 101, 101, 101, 1, 99, 101],
        "low": [1.0, 99, 99, 99, 0, 100, 99], "close": [1.0, 100, 100, 100, 0, 100, np.nan], "volume": 1.0})
    raw = pd.concat([df, extra.astype({k: "float32" for k in I.COLS[1:]})], ignore_index=True).iloc[::-1].reset_index(drop=True)
    out, st = I.clean_bars(raw)
    assert out["ts"].tolist() == df["ts"].tolist()                    # exactly the five good bars survive
    assert st["dropped_duplicate_ts"] == 1 and st["dropped_outside_session"] == 3
    assert st["dropped_bad_price"] == 2 and st["dropped_high_below_low"] == 1
    assert st["was_out_of_order"] is True and st["rows_in"] == 12 and st["rows_out"] == 5
    assert out["ts"].is_monotonic_increasing
    # every output row is an input row, untouched
    merged = out.merge(raw, on=I.COLS, how="left", indicator=True)
    assert (merged["_merge"] == "both").all()


def test_clean_bars_duplicate_keeps_first_in_source_order():
    a = bars("2020-01-31 09:15", 2)
    b = a.copy()
    b["close"] = 999.0
    out, _ = I.clean_bars(pd.concat([a, b], ignore_index=True))
    assert len(out) == 2 and (out["close"] != 999.0).all()


def test_clean_bars_keeps_saturday_budget_session_and_gaps_stay_gaps():
    sat = full_day("2020-02-01")                                      # a Saturday NSE really traded on
    assert sat["ts"].iloc[0].dayofweek == 5
    holes = sat.drop(index=range(100, 130)).reset_index(drop=True)    # 30 minutes missing in the source
    out, st = I.clean_bars(holes)
    assert len(out) == 345 and st["dropped_outside_session"] == 0     # nothing dropped, nothing filled in
    assert pd.Timestamp("2020-02-01 10:55") not in set(out["ts"])
    assert I.clean_bars(sat)[1]["bars_open_or_close_outside_range"] == 0
    odd = sat.copy()
    odd.loc[0, "open"] = odd.loc[0, "high"] + 1                       # inconsistent bar: counted, not altered
    out, st = I.clean_bars(odd)
    assert st["bars_open_or_close_outside_range"] == 1 and out.loc[0, "open"] == odd.loc[0, "open"]


def test_floor_to_minute_relabels_stray_seconds_then_duplicates_resolve():
    df = bars("2015-06-24 15:02", 3)
    df.loc[0, "ts"] = pd.Timestamp("2015-06-24 15:02:01")
    out, n = I.floor_to_minute(df)
    assert n == 1 and out["ts"].iloc[0] == pd.Timestamp("2015-06-24 15:02:00")
    clash = pd.concat([df, bars("2015-06-24 15:02", 1, price=555.0)], ignore_index=True)
    cleaned, st = I.normalise(clash)
    assert st["relabelled_stray_seconds"] == 1 and st["dropped_duplicate_ts"] == 1
    assert len(cleaned) == 3 and cleaned["ts"].dt.second.eq(0).all()


def test_drop_misfiled_blocks_removes_foreign_rows_but_not_a_crash_day():
    days = pd.bdate_range("2015-06-17", "2015-06-30")
    parts = [full_day(str(d.date()), price=18000.0, step=0.5) for d in days]
    df = pd.concat(parts, ignore_index=True)
    bad_day = pd.Timestamp("2015-06-24")
    bad = (df["ts"].dt.normalize() == bad_day) & (df["ts"].dt.hour >= 11)      # most of one day is another instrument
    df.loc[bad, ["open", "high", "low", "close"]] = np.float32(1410.0)
    out, st = I.drop_misfiled_blocks(df, 1.2)
    assert st["dropped_misfiled"] == int(bad.sum()) and st["misfiled_days"] == ["2015-06-24"]
    assert (out["close"] > 10000).all()
    kept = out[out["ts"].dt.normalize() == bad_day]
    assert len(kept) == 375 - int(bad.sum())                                    # the good morning bars stay
    # a genuine 12 % fall is not touched
    crash = pd.concat(parts, ignore_index=True)
    after = crash["ts"] >= pd.Timestamp("2015-06-24")
    crash.loc[after, ["open", "high", "low", "close"]] *= np.float32(0.88)
    out2, st2 = I.drop_misfiled_blocks(crash, 1.2)
    assert st2["dropped_misfiled"] == 0 and len(out2) == len(crash)


def test_drop_misfiled_blocks_ignores_levels_years_apart():
    a = full_day("2014-03-03", price=6500.0, step=0.0)
    b = full_day("2017-03-03", price=9000.0, step=0.0)                # next available day is three years later
    out, st = I.drop_misfiled_blocks(pd.concat([a, b], ignore_index=True), 1.2)
    assert st["dropped_misfiled"] == 0 and len(out) == 750


def test_trim_before_listing():
    df = pd.concat([full_day("2019-10-11"), full_day("2019-10-14")], ignore_index=True)
    out, n = I.trim_before_listing(df, pd.Timestamp("2019-10-14"))
    assert n == 375 and out["ts"].min() == pd.Timestamp("2019-10-14 09:15")
    same, n0 = I.trim_before_listing(df, None)
    assert n0 == 0 and len(same) == 750


# ---------------------------------------------------------------- holdout split and store layout

def test_split_holdout_boundary_is_end_of_day():
    df = pd.concat([bars("2021-12-31 15:27", 3), bars("2022-01-03 09:15", 2)], ignore_index=True)
    research, holdout = I.split_holdout(df, "2021-12-31")
    assert research["ts"].max() == pd.Timestamp("2021-12-31 15:29") and len(research) == 3
    assert holdout["ts"].min() == pd.Timestamp("2022-01-03 09:15") and len(holdout) == 2
    r2, h2 = I.split_holdout(df, "2021-12-31", start="2022-01-01")
    assert len(r2) == 0 and len(h2) == 2                              # `start` never moves rows into research
    r3, h3 = I.split_holdout(df, "2022-01-03")
    assert len(r3) == 5 and len(h3) == 0                              # a later `end` extends the research part


def test_write_split_layout_loads_through_store_and_keeps_holdout_apart(tmp_path):
    (tmp_path / "LOCK").write_text("2021-12-31")
    dup = bars("2022-01-03 09:15", 1, price=1.0)                      # a duplicate that exists only after the cut
    raw = pd.concat([full_day("2021-12-30"), full_day("2021-12-31"), full_day("2022-01-03"), dup], ignore_index=True)

    def prep(part):
        out, st = I.normalise(part)
        return out[I.COLS], {"src": st}

    info = I.write_split(raw, "TEST_1min.parquet", tmp_path, None, pd.Timestamp("2021-12-31"), prep)
    assert info["research"] == {"rows": 750, "first": "2021-12-30 09:15:00", "last": "2021-12-31 15:29:00", "days": 2}
    assert info["holdout"] == {"rows": 375, "first": "2022-01-03 09:15:00", "last": "2022-01-03 15:29:00"}
    assert info["cleaning"]["src"]["dropped_duplicate_ts"] == 0       # statistics describe the research rows only
    assert info["cleaning"]["src"]["rows_in"] == 750

    got = store.load_intraday("TEST", "1min", root=tmp_path)
    assert list(got.columns) == I.COLS and len(got) == 750
    assert got["ts"].max() == pd.Timestamp("2021-12-31 15:29")
    assert str(got["ts"].dtype).startswith("datetime64") and got["ts"].dt.tz is None
    assert all(str(got[c].dtype) == "float32" for c in I.COLS[1:])
    one_day = store.load_intraday("TEST", "1min", start="2021-12-31", end="2021-12-31", root=tmp_path)
    assert len(one_day) == 375

    hold = pd.read_parquet(tmp_path / "holdout" / "intraday" / "TEST_1min.parquet")
    assert hold["ts"].min() == pd.Timestamp("2022-01-03 09:15") and len(hold) == 375
    research_file = pd.read_parquet(tmp_path / "intraday" / "TEST_1min.parquet")
    assert research_file["ts"].max() < pd.Timestamp("2022-01-01")


def test_write_split_removes_stale_files_when_a_side_is_empty(tmp_path):
    end = pd.Timestamp("2021-12-31")
    I.write_split(pd.concat([full_day("2021-12-31"), full_day("2022-01-03")], ignore_index=True), "X_1min.parquet", tmp_path, None, end)
    assert (tmp_path / "holdout" / "intraday" / "X_1min.parquet").exists()
    info = I.write_split(full_day("2021-12-31"), "X_1min.parquet", tmp_path, None, end)
    assert info["holdout"] == {"rows": 0}
    assert not (tmp_path / "holdout" / "intraday" / "X_1min.parquet").exists()
    info = I.write_split(full_day("2022-01-03"), "X_1min.parquet", tmp_path, None, end)
    assert info["research"] == {"rows": 0} and not (tmp_path / "intraday" / "X_1min.parquet").exists()


def test_build_stock_trims_prelisting_rows_and_marks_missing_volume(tmp_path):
    raw = pd.concat([full_day("2019-10-11"), full_day("2019-10-14"), full_day("2022-01-03")], ignore_index=True)
    info = I.build_stock("IRCTC", raw, "hf_tiru8055", tmp_path, None, pd.Timestamp("2021-12-31"), False,
                         pd.Timestamp("2019-10-14"))
    assert info["dropped_before_listing"] == 375 and info["listing_date"] == "2019-10-14"
    assert info["research"]["first"] == "2019-10-14 09:15:00" and info["research"]["rows"] == 375
    got = store.load_intraday("IRCTC", root=tmp_path)
    assert got["volume"].isna().all()                                 # unknown volume is NaN, never 0


def test_option_cleaning_and_locked_loader(tmp_path):
    (tmp_path / "LOCK").write_text("2021-12-31")
    exp = pd.Timestamp("2022-01-06")
    rows = []
    for t in ["2021-12-31 09:15", "2021-12-31 09:16", "2022-01-03 09:15", "2022-01-07 09:15", "2021-12-31 08:00"]:
        for right, px in (("CE", 120.0), ("PE", 95.0)):
            rows.append([pd.Timestamp(t), exp, 17300.0, right, px, px + 1, px - 1, px, 50.0, 1000.0])
    o = pd.DataFrame(rows, columns=I.OPT_COLS)
    o = pd.concat([o, o.iloc[[0]]], ignore_index=True)                # an exact repeat
    cleaned, st = I.clean_options(o)
    assert st["dropped_duplicate_rows"] == 1 and st["dropped_outside_session"] == 2 and st["dropped_bad"] == 2
    assert not cleaned.duplicated(["ts", "strike", "right"]).any()
    assert cleaned["ts"].max() == pd.Timestamp("2022-01-03 09:15")    # the row stamped after expiry is gone

    info = I.write_split(o, "options/NIFTY_1min/2022-01-06.parquet", tmp_path, None, pd.Timestamp("2021-12-31"), I.clean_options)
    assert info["research"]["rows"] == 4 and info["holdout"]["rows"] == 2
    assert I.list_option_expiries("NIFTY", root=tmp_path) == [exp]
    chain = I.load_option_chain("NIFTY", "2022-01-06", root=tmp_path)
    assert len(chain) == 4 and chain["ts"].max() < pd.Timestamp("2022-01-01")
    assert list(chain.columns) == I.OPT_COLS


# ---------------------------------------------------------------- derived figures

def test_resample_is_anchored_at_open_and_never_invents_buckets():
    day = full_day("2021-06-01", step=1.0)
    five = I.resample_bars(day, 5)
    assert len(five) == 75 and five["ts"].iloc[0] == pd.Timestamp("2021-06-01 09:15")
    assert five["ts"].iloc[-1] == pd.Timestamp("2021-06-01 15:25")
    first = day.iloc[:5]
    assert five["open"].iloc[0] == first["open"].iloc[0] and five["close"].iloc[0] == first["close"].iloc[-1]
    assert five["high"].iloc[0] == first["high"].max() and five["low"].iloc[0] == first["low"].min()
    assert five["volume"].iloc[0] == 50.0
    holes = day[(day["ts"] < "2021-06-01 10:00") | (day["ts"] >= "2021-06-01 10:30")]
    got = I.resample_bars(holes, 15)
    assert pd.Timestamp("2021-06-01 10:00") not in set(got["ts"]) and pd.Timestamp("2021-06-01 10:15") not in set(got["ts"])
    assert len(got) == 25 - 2
    nov = day.assign(volume=np.float32("nan"))
    assert I.resample_bars(nov, 5)["volume"].isna().all()             # unknown volume stays unknown


def test_bar_quality_counts():
    d1, d2 = full_day("2021-06-01"), full_day("2021-06-03").iloc[:300]      # Wednesday 2 June has no bars
    df = pd.concat([d1, d2], ignore_index=True)
    df.loc[10, "close"] = df.loc[9, "close"] * 1.05                          # one 5 % jump (and back)
    df.loc[10, "high"] = df.loc[10, "close"]
    q = I.bar_quality(df, 0.03)
    assert q["rows"] == 675 and q["days"] == 2 and q["days_full_375"] == 1 and q["days_lt_370"] == 1
    assert q["bars_per_day_min"] == 300 and q["weekdays_without_bars"] == 1
    assert q["duplicate_ts"] == 0 and q["strictly_increasing"] and q["outside_session"] == 0
    assert q["bars_abs_return_gt_0.03"] == 2
    assert q["bar_completeness"] == pytest.approx(675 / 750, abs=1e-5)
    assert q["volume_nan_share"] == 0.0
    dup = pd.concat([df, df.iloc[[5]]], ignore_index=True)
    assert I.bar_quality(dup)["strictly_increasing"] is False and I.bar_quality(dup)["duplicate_ts"] == 1


def test_daily_comparison_flags_missing_days_and_bad_levels():
    intr = I.daily_from_bars(pd.concat([full_day("2021-06-01", price=100.0, step=0.0),
                                        full_day("2021-06-03", price=110.0, step=0.0)], ignore_index=True))
    assert intr.loc["2021-06-01", "bars"] == 375 and intr.loc["2021-06-01", "high"] == pytest.approx(100.5)
    official = pd.DataFrame({"open": [100.0, 105.0, 110.0], "high": [100.5, 106.0, 112.0],
                             "low": [99.5, 104.0, 109.5], "close": [100.2, 105.0, 110.2]},
                            index=pd.to_datetime(["2021-06-01", "2021-06-02", "2021-06-03"]))
    c = I.compare_daily(intr, official)
    assert c["official_days_missing_intraday"] == ["2021-06-02"] and c["common_days"] == 2
    assert c["low"]["within_tol_share"] == 1.0
    assert c["high"]["within_tol_share"] == 0.5                       # 110.5 vs 112.0 on the second day
    assert c["high"]["days_beyond_1pct"] == ["2021-06-03"]


def test_compare_bars_on_common_timestamps():
    a = bars("2021-06-01 09:15", 10)
    b = a.iloc[2:].copy()
    b.loc[b.index[0], "close"] *= 1.01
    c = I.compare_bars(a, b)
    assert c["common_bars"] == 8 and c["only_first"] == 2 and c["only_second"] == 0
    assert c["close"]["bars_beyond_0.5pct"] == 1 and c["open"]["identical_share"] == 1.0


# ---------------------------------------------------------------- download selection (no network)

def test_file_selection_respects_end_date():
    end = pd.Timestamp("2021-12-31")
    tv = [("1min/2017/NIFTY50_1min_2017.csv", 1), ("1min/2021/NIFTY50_1min_2021.csv", 1),
          ("1min/2022/NIFTY50_1min_2022.csv", 1), ("1min/2026/NIFTY50_1min_2026-09.csv", 1), ("README.md", 1)]
    assert [p for p, _ in I._sel_technovus(tv, end)] == [tv[0][0], tv[1][0]]
    assert len(I._sel_technovus(tv, pd.Timestamp("2022-06-30"))) == 3          # extending the range picks up 2022
    tm = [("index/NIFTY.parquet", 1), ("index/SENSEX.parquet", 1), ("options/NIFTY/2021-12-30.parquet", 1),
          ("options/NIFTY/2022-01-06.parquet", 1), ("options/NIFTY/2022-06-30.parquet", 1),
          ("options/SENSEX/2021-12-30.parquet", 1), ("stocks_options/SBIN/2021-12-30.parquet", 1)]
    assert [p for p, _ in I._sel_trademarkk(tm, end)] == [tm[0][0], tm[2][0], tm[3][0]]
    ae = [("2015/JAN/NIFTY.txt", 1), ("2015/JAN/NIFTY_F1.txt", 1), ("2015/JAN/CNX-IT.txt", 1),
          ("2016/AUG/NIFTY[Conflict].txt", 1), ("2017/AUG/01AUG/01AUG/ACC.txt", 1), ("2018/APR/02APR/02APR/INDIAVIX.txt", 1)]
    assert [p for p, _ in I._sel_aeron(ae, end)] == [ae[0][0], ae[1][0], ae[5][0]]
    assert I._sel_aeron(ae, pd.Timestamp("2014-12-31")) == []


def test_download_urls_quote_awkward_paths():
    u = I.github_raw_url("o/r", "main", "Nifty 100 stocks/Data/INDIA VIX_minute.csv")
    assert u == "https://raw.githubusercontent.com/o/r/main/Nifty%20100%20stocks/Data/INDIA%20VIX_minute.csv"
    assert I.hf_url("a/b", "options/NIFTY/2021-12-30.parquet").endswith("/resolve/main/options/NIFTY/2021-12-30.parquet")


def test_default_end_comes_from_lock_file(tmp_path):
    assert I.default_end(tmp_path) == pd.Timestamp(I.DEFAULT_END)
    (tmp_path / "LOCK").write_text("2020-06-30\n")
    assert I.default_end(tmp_path) == pd.Timestamp("2020-06-30")
