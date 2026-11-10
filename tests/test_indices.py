"""Tests for quant.data.indices. No network: sources are inline fixtures and
the HTTP session is replaced by a fake."""
import gzip
import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from quant.data import indices as ix
from quant.data import store

DAILY_HEADER = ("Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,Closing Index Value,"
                "Points Change,Change(%),Volume,Turnover (Rs. Cr.),P/E,P/B,Div Yield\n")

# Real rows from ind_close_all_23032020.csv (trimmed), plus a made-up
# valueless row to exercise the "no close" path.
DAILY_2020 = DAILY_HEADER + (
    "Nifty 50,23-03-2020,7945.7,8159.25,7583.6,7610.25,-1135.2,-12.98,654151814,23891.9,17.15,2.17,2\n"
    "NIFTY Smallcap 100,23-03-2020,3543.25,3603.65,3368.2,3372.65,-512.6,-13.19,86089651,788.96,,1.14,2.1\n"
    "Nifty50 Dividend Points,23-03-2020,-,-,-,145.55,0.0,-,-,-,-,-,-\n"
    "Nifty Bank,23-03-2020,18311.3,18895.65,16791.05,16917.65,-3399.95,-16.73,307639369,7807.32,18.27,1.58,.57\n"
    "Nifty 1D Rate Index,23-03-2020,-,-,-,1885.1,0.25,0.01,-,-,-,-,-\n"
    "Empty Index,23-03-2020,-,-,-,-,-,-,-,-,-,-,-\n"
)

# Real rows from ind_close_all_21022012.csv: the names in use at the time.
DAILY_2012 = DAILY_HEADER + (
    "S&P CNX Nifty,21-02-2012,5561.9,5621.5,5561.75,5607.15,42.85,.77,231132126,8169.38,19.64,3.16,1.41\n"
    "CNX Nifty Junior,21-02-2012,10828,10926.15,10821.9,10883.05,54.95,.51,122248595,2327.63,16.42,2.37,1.42\n"
    "CNX Finance,21-02-2012,-,-,-,4509.05,29.58,.66,44469419,2447.47,19.07,2.99,1.18\n"
    "S&P ESG India,21-02-2012,-,-,-,3974.92,37.54,.95,-,-,-,-,-\n"
)


# ---------------------------------------------------------------- names

def test_canon_maps_every_historical_name_to_the_official_one():
    assert ix.canon("S&P CNX Nifty") == "NIFTY 50"
    assert ix.canon("CNX Nifty") == "NIFTY 50"
    assert ix.canon("Nifty 50") == "NIFTY 50"
    assert ix.canon("CNX Nifty Junior") == "NIFTY NEXT 50"
    assert ix.canon("CNX Midcap") == ix.canon("Nifty Free Float Midcap 100") == ix.canon("NIFTY Midcap 100") == "NIFTY MIDCAP 100"
    assert ix.canon("CNX Finance") == "NIFTY FINANCIAL SERVICES"
    assert ix.canon("GSECBM NSE Index") == "NIFTY 10 YR BENCHMARK G-SEC"
    assert ix.canon("GSEC10 NSE Index") == "NIFTY 8-13 YR G-SEC"
    assert ix.canon("India VIX") == "INDIA VIX"


def test_canon_normalises_spacing_case_and_dashes_and_keeps_unknown_names():
    assert ix.canon("  NIFTY Alpha   Low–Volatility 30 ") == "NIFTY ALPHA LOW-VOLATILITY 30"
    assert ix.canon("Nifty200 Momentum 30") == "NIFTY200 MOMENTUM 30"
    assert ix.canon("S&P ESG India") == "S&P ESG INDIA"          # discontinued, no official successor


def test_alias_table_is_well_formed():
    for old, new in ix.ALIASES.items():
        assert old == ix.squash(old) and new == ix.squash(new)
        assert new not in ix.ALIASES, f"alias chain through {new}"
    # every index the project asked for is reachable under its official name
    assert not set(ix.WANTED) & set(ix.ALIASES)


def test_slug_is_filesystem_safe_and_distinguishes_similar_names():
    a, b = ix.slug("NIFTY 10 YR BENCHMARK G-SEC"), ix.slug("NIFTY 10 YR BENCHMARK G-SEC (CLEAN PRICE)")
    assert a == "NIFTY_10_YR_BENCHMARK_G_SEC" and a != b
    assert ix.slug("Nifty REITs & InvITs 90:10") == "NIFTY_REITS_INVITS_90_10"


# ---------------------------------------------------------------- numbers and dates

def test_to_float():
    assert ix.to_float("1,234.50") == 1234.5
    assert ix.to_float(".57") == 0.57
    assert ix.to_float(" 8159.25 ") == 8159.25
    for blank in ("-", "", "  ", None, "NA"):
        assert np.isnan(ix.to_float(blank))
    with pytest.raises(ValueError):
        ix.to_float("<html>")


def test_parse_date_formats():
    assert ix._parse_date("23-03-2020") == pd.Timestamp("2020-03-23")
    assert ix._parse_date("31 Mar 2020") == pd.Timestamp("2020-03-31")
    assert ix._parse_date("03-Jan-2011") == pd.Timestamp("2011-01-03")
    with pytest.raises(ValueError):
        ix._parse_date("2020/03/23x")


# ---------------------------------------------------------------- daily file

def test_parse_daily_csv_values_and_blanks():
    df = ix.parse_daily_csv(DAILY_2020).set_index("name")
    assert list(df.index) == ["NIFTY 50", "NIFTY SMALLCAP 100", "NIFTY50 DIVIDEND POINTS", "NIFTY BANK",
                              "NIFTY 1D RATE INDEX"]                 # the row without a close is dropped
    n = df.loc["NIFTY 50"]
    assert n["date"] == pd.Timestamp("2020-03-23") and n["raw_name"] == "Nifty 50"
    assert (n["open"], n["high"], n["low"], n["close"]) == (7945.7, 8159.25, 7583.6, 7610.25)
    assert (n["pe"], n["pb"], n["dy"]) == (17.15, 2.17, 2.0)
    assert n["volume"] == 654151814 and n["turnover"] == 23891.9
    assert np.isnan(df.loc["NIFTY SMALLCAP 100", "pe"]) and df.loc["NIFTY SMALLCAP 100", "pb"] == 1.14
    d = df.loc["NIFTY50 DIVIDEND POINTS"]
    assert d["close"] == 145.55 and d[["open", "high", "low", "pe", "pb", "dy", "volume"]].isna().all()
    assert df.loc["NIFTY BANK", "dy"] == 0.57                        # ".57" in the file


def test_parse_daily_csv_old_names():
    df = ix.parse_daily_csv(DAILY_2012)
    assert list(df["name"]) == ["NIFTY 50", "NIFTY NEXT 50", "NIFTY FINANCIAL SERVICES", "S&P ESG INDIA"]
    assert list(df["raw_name"]) == ["S&P CNX Nifty", "CNX Nifty Junior", "CNX Finance", "S&P ESG India"]
    assert df.loc[0, "close"] == 5607.15 and (df["date"] == pd.Timestamp("2012-02-21")).all()


def test_parse_daily_csv_duplicate_rows():
    # ind_close_all_08022013.csv prints "CNX Alpha Index" twice with different
    # values (one row is another index, mislabelled): neither can be trusted.
    # ind_close_all_15092014.csv repeats one row verbatim: keep one copy.
    text = DAILY_HEADER + (
        "CNX Alpha Index,08-02-2013,-,-,-,4713.18,-51.9,-1.09,-,-,23.07,3.6,.65\n"
        "CNX Alpha Index,08-02-2013,-,-,-,1572.9,-17.6,-1.11,-,-,22.39,.96,1.18\n"
        "GSEC10 NSE Index,08-02-2013,-,-,-,1258.1,1.1,.09,-,-,-,-,-\n"
        "GSEC10 NSE Index,08-02-2013,-,-,-,1258.1,1.1,.09,-,-,-,-,-\n"
        "CNX Nifty,08-02-2013,5927.5,5946.9,5886.2,5903.5,-35.3,-.59,1,2,18.3,3.1,1.4\n")
    df = ix.parse_daily_csv(text)
    assert list(df["name"]) == ["NIFTY 8-13 YR G-SEC", "NIFTY 50"]
    assert df.attrs["conflicts"] == ["NIFTY ALPHA 50"]


def test_parse_daily_csv_rejects_other_content():
    with pytest.raises(ValueError):
        ix.parse_daily_csv("<!DOCTYPE html><html><title>Error 404</title></html>")
    with pytest.raises(ValueError):
        ix.parse_daily_csv("")


def test_daily_url_and_cache_path(tmp_path):
    assert ix.DAILY_URL.format(d=date(2020, 3, 23)).endswith("/content/indices/ind_close_all_23032020.csv")
    assert ix.daily_path(tmp_path, date(2020, 3, 23)) == tmp_path / "daily" / "2020" / "ind_close_all_23032020.csv"


# ---------------------------------------------------------------- niftyindices

NI_PRICE = [  # real rows, newest first as the site returns them
    {"RequestNumber": "His1", "Index Name": "", "INDEX_NAME": "Nifty 50", "HistoricalDate": "24 Mar 2020",
     "OPEN": "7848.30", "HIGH": "8036.95", "LOW": "7511.10", "CLOSE": "7801.05"},
    {"RequestNumber": "His1", "Index Name": "", "INDEX_NAME": "Nifty 50", "HistoricalDate": "23 Mar 2020",
     "OPEN": "7945.70", "HIGH": "8159.25", "LOW": "7583.60", "CLOSE": "7610.25"},
]
NI_PRICE_CLOSE_ONLY = [
    {"RequestNumber": "His2", "Index Name": "", "INDEX_NAME": "Nifty200 Momentum 30",
     "HistoricalDate": "31 Mar 2020", "OPEN": "-", "HIGH": "-", "LOW": "-", "CLOSE": "9252.38"}]
NI_TRI = [
    {"RequestNumber": "TRI1", "Index Name": "Nifty 50", "Date": "31 Mar 2020", "TotalReturnsIndex": "12105.66",
     "NTR_Value": "11131.48"},
    {"RequestNumber": "TRI1", "Index Name": "Nifty 50", "Date": "30 Mar 2020", "TotalReturnsIndex": "11659.76",
     "NTR_Value": "10721.46"}]
NI_PEPB = [
    {"RequestNumber": "pepb1", "Index Name": "Nifty 50", "pe": "17.15", "pb": "2.17", "divYield": "2.00",
     "DATE": "23 Mar 2020"}]


def test_parse_ni_price():
    df = ix.parse_ni("price", NI_PRICE)
    assert list(df.index) == [pd.Timestamp("2020-03-23"), pd.Timestamp("2020-03-24")]     # sorted ascending
    assert df.loc["2020-03-23"].to_dict() == {"open": 7945.7, "high": 8159.25, "low": 7583.6, "close": 7610.25}
    c = ix.parse_ni("price", NI_PRICE_CLOSE_ONLY)
    assert c["close"].iloc[0] == 9252.38 and c[["open", "high", "low"]].isna().all().all()


def test_parse_ni_tri_and_valuation():
    t = ix.parse_ni("tri", NI_TRI)
    assert list(t.columns) == ["tri"] and t.loc["2020-03-31", "tri"] == 12105.66 and len(t) == 2
    v = ix.parse_ni("pepb", NI_PEPB)
    assert v.loc["2020-03-23"].to_dict() == {"pe": 17.15, "pb": 2.17, "dy": 2.0}


def test_parse_ni_drops_valueless_rows_and_repeated_dates():
    rows = NI_TRI + [{"Date": "27 Mar 2020", "TotalReturnsIndex": "-"}, dict(NI_TRI[0])]
    t = ix.parse_ni("tri", rows)
    assert len(t) == 2 and t.index.is_unique
    assert ix.parse_ni("price", []).empty


def test_decode_ni():
    assert ix.decode_ni(json.dumps(NI_PEPB)) == NI_PEPB
    assert ix.decode_ni(json.dumps({"d": json.dumps(NI_PEPB)})) == NI_PEPB       # the site's older envelope
    assert ix.decode_ni("[]") == []
    with pytest.raises(ValueError):
        ix.decode_ni("<!DOCTYPE html><html><title>Error 404</title></html>")     # served with HTTP 200
    with pytest.raises(ValueError):
        ix.decode_ni('{"Message": "error"}')


def test_ni_blocks_have_fixed_boundaries():
    b = ix.ni_blocks(date(2003, 1, 1), date(2021, 12, 31))
    assert b == [(date(2003, 1, 1), date(2004, 12, 31)), (date(2005, 1, 1), date(2009, 12, 31)),
                 (date(2010, 1, 1), date(2014, 12, 31)), (date(2015, 1, 1), date(2019, 12, 31)),
                 (date(2020, 1, 1), date(2021, 12, 31))]
    later = ix.ni_blocks(date(2003, 1, 1), date(2026, 10, 30))
    assert later[:4] == b[:4]                      # finished windows keep their cache key
    assert later[4:] == [(date(2020, 1, 1), date(2024, 12, 31)), (date(2025, 1, 1), date(2026, 10, 30))]
    assert ix.ni_blocks(date(2020, 3, 23), date(2020, 3, 23)) == [(date(2020, 3, 23), date(2020, 3, 23))]
    assert ix.ni_blocks(date(2021, 1, 1), date(2020, 1, 1)) == []
    for s, e in later:                              # contiguous, no overlap
        assert s <= e
    assert all(later[i][1] + pd.Timedelta(days=1) == later[i + 1][0] for i in range(len(later) - 1))


def test_ni_body_matches_what_the_site_sends():
    body = json.loads(ix.ni_body("NIFTY FIN SERVICE", "NIFTY FINANCIAL SERVICES", date(2003, 1, 1), date(2021, 12, 31)))
    assert body == {"cinfo": "{'name':'NIFTY FIN SERVICE','startDate':'01-Jan-2003','endDate':'31-Dec-2021',"
                             "'indexName':'NIFTY FINANCIAL SERVICES'}"}


def test_trading_names_lookup():
    tn = ix.trading_names([
        {"Trading_Index_Name": "Nifty Fin Service", "Index_long_name": "Nifty Financial Services"},
        {"Trading_Index_Name": "NIFTY SMLCAP 250", "Index_long_name": "NIFTY Smallcap 250"},
        {"Trading_Index_Name": "Nifty 50", "Index_long_name": "Nifty 50"}])
    assert ix.request_name("NIFTY FINANCIAL SERVICES", tn) == "NIFTY FIN SERVICE"
    assert ix.request_name("NIFTY SMALLCAP  250", tn) == "NIFTY SMLCAP 250"       # whitespace-insensitive
    assert ix.request_name("NIFTY 50", tn) == "NIFTY 50"
    assert ix.request_name("INDIA VIX", tn) == "INDIA VIX"                        # unmapped: sent as is


# ---------------------------------------------------------------- assembly

def _dates(*d):
    return pd.DatetimeIndex(list(d), name="date")


def test_to_wide():
    long = ix.parse_daily_csv(DAILY_2020)
    w = ix.to_wide(long, "pe")
    assert list(w.columns) == ["NIFTY 50", "NIFTY BANK"]            # indices without a P/E get no column
    assert w.index.name == "date" and w.loc["2020-03-23", "NIFTY 50"] == 17.15
    assert ix.to_wide(long.iloc[:0], "close").empty


def test_merge_sources_keeps_primary_and_only_fills_holes():
    a = pd.DataFrame({"X": [1.0, np.nan, 3.0], "Y": [np.nan, np.nan, 9.0]}, index=_dates("2020-01-01", "2020-01-02", "2020-01-03"))
    b = pd.DataFrame({"X": [1.5, 2.0], "Z": [7.0, np.nan]}, index=_dates("2020-01-01", "2020-01-02"))
    m = ix.merge_sources(a, b)
    assert m["X"].tolist() == [1.0, 2.0, 3.0]                       # primary wins, hole filled
    assert m["Y"].isna().tolist() == [True, True, False]            # nothing invented
    assert m["Z"].isna().tolist() == [False, True, True] and m.index.name == "date"


def test_longest_gap_and_missing_days():
    s = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0], index=_dates("2020-01-01", "2020-01-02", "2020-01-03", "2020-01-10", "2020-01-13"))
    assert ix.longest_gap(s) == (8, "2020-01-02")
    assert ix.missing_days(s) == 1
    assert ix.longest_gap(s.iloc[:1]) == (0, None) and ix.missing_days(s * np.nan) == 0


def test_continuous_from():
    d = pd.date_range("2020-01-01", periods=12)
    back_issue = np.array([1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1], bool)       # one early appearance, then live
    assert ix.continuous_from(back_issue, d) == pd.Timestamp("2020-01-09")
    discontinued = np.array([1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0], bool)
    assert ix.continuous_from(discontinued, d) == pd.Timestamp("2020-01-01")
    assert ix.continuous_from(np.zeros(12, bool), d) is None


def _fixture_sources():
    """Three trading days. niftyindices has NIFTY 50 for all three and the
    rate index for two plus a Sunday; the daily file has the middle day."""
    d1, d2, d3, sun = (pd.Timestamp(x) for x in ("2020-03-20", "2020-03-23", "2020-03-24", "2020-03-22"))
    price = {
        "NIFTY 50": pd.DataFrame({"open": [8284.45, 7945.7, 7848.3], "high": [8883.0, 8159.25, 8036.95],
                                  "low": [8178.2, 7583.6, 7511.1], "close": [8745.45, 7610.25, 7801.05]},
                                 index=[d1, d2, d3]),
        "NIFTY 1D RATE INDEX": pd.DataFrame({"open": np.nan, "high": np.nan, "low": np.nan,
                                             "close": [1884.6, 1884.9, 1885.4]}, index=[d1, sun, d3]),
        "INDIA VIX": pd.DataFrame({"open": [70.0], "high": [86.0], "low": [66.0], "close": [71.99]}, index=[d2]),
    }
    tri = {"NIFTY 50": pd.DataFrame({"tri": [12300.5, 10704.0, 10972.4]}, index=[d1, d2, d3])}
    pepb = {"NIFTY 50": pd.DataFrame({"pe": [19.72, 17.15, 17.58], "pb": [2.49, 2.17, 2.22],
                                      "dy": [1.74, 2.0, 1.95]}, index=[d1, d2, d3])}
    daily = ix.parse_daily_csv(DAILY_2020)
    cats = {"NIFTY 50": "Equity / Broad Market Indices", "NIFTY 1D RATE INDEX": "Fixed Income / Money Market",
            "INDIA VIX": "Volatility"}
    return {"price": price, "tri": tri, "pepb": pepb}, daily, cats


def test_assemble_layout_calendar_and_sources():
    ni, daily, cats = _fixture_sources()
    wide, meta = ix.assemble(ni, daily, cats, date(2020, 1, 1), date(2020, 12, 31))
    close = wide["close"]
    # calendar = NIFTY 50 days; the Sunday row of the rate index is dropped, not shifted
    assert list(close.index) == list(_dates("2020-03-20", "2020-03-23", "2020-03-24")) and close.index.name == "date"
    assert meta["calendar"]["days"] == 3 and meta["calendar"]["dropped_off_calendar"]["close"]["cells"] == 1
    for f in ix.FIELDS:
        assert (wide[f].dtypes == "float32").all() and wide[f].index.equals(close.index)
        assert list(wide[f].columns) == sorted(wide[f].columns)
    # niftyindices value kept, the daily file fills the hole on the 23rd and adds its own indices
    assert close["NIFTY 50"].tolist() == pytest.approx([8745.45, 7610.25, 7801.05])
    assert close["NIFTY 1D RATE INDEX"].tolist() == pytest.approx([1884.6, 1885.1, 1885.4])
    assert np.isnan(close["NIFTY BANK"].iloc[0]) and close["NIFTY BANK"].iloc[1] == pytest.approx(16917.65)
    assert wide["volume"]["NIFTY 50"].iloc[1] == pytest.approx(654151814, rel=1e-6)
    assert "NIFTY50 DIVIDEND POINTS" not in wide["open"]              # all-empty columns are not written
    # total return: from the endpoint for equity, a copy of close for the fixed-income index, none for VIX
    assert wide["tri"]["NIFTY 50"].tolist() == pytest.approx([12300.5, 10704.0, 10972.4])
    assert wide["tri"]["NIFTY 1D RATE INDEX"].equals(close["NIFTY 1D RATE INDEX"])
    assert "INDIA VIX" not in wide["tri"]
    m = meta["indices"]
    assert m["NIFTY 50"]["fields"]["close"] == {"first": "2020-03-20", "last": "2020-03-24", "n": 3,
                                                "n_niftyindices": 3, "n_daily_file": 0, "source": "niftyindices"}
    assert m["NIFTY 1D RATE INDEX"]["fields"]["close"]["source"] == "niftyindices+daily_file"
    assert m["NIFTY 1D RATE INDEX"]["fields"]["tri"]["source"].startswith("copy of close")
    assert m["NIFTY BANK"]["fields"]["close"]["source"] == "daily_file"
    assert m["NIFTY BANK"]["category"].startswith("not listed")
    assert m["NIFTY 50"]["daily_file_names"] == ["Nifty 50"]
    assert meta["shapes"]["close"] == [3, close.shape[1]]
    # the two sources agree on the one day both have
    assert meta["source_agreement"]["close"]["cells_compared"] == 1
    assert meta["source_agreement"]["close"]["cells_differ"] == 0


def test_assemble_reports_disagreement_between_sources():
    ni, daily, cats = _fixture_sources()
    ni["price"]["NIFTY 50"].loc[pd.Timestamp("2020-03-23"), "close"] = 7700.0
    wide, meta = ix.assemble(ni, daily, cats, date(2020, 1, 1), date(2020, 12, 31))
    ag = meta["source_agreement"]["close"]
    assert ag["cells_differ"] == 1 and ag["worst"]["NIFTY 50"]["max_abs"] == pytest.approx(89.75)
    assert wide["close"]["NIFTY 50"].iloc[1] == pytest.approx(7700.0)          # primary source is kept


def test_assemble_clips_to_the_requested_range():
    ni, daily, cats = _fixture_sources()
    wide, meta = ix.assemble(ni, daily, cats, date(2020, 3, 21), date(2020, 3, 23))
    assert list(wide["close"].index) == [pd.Timestamp("2020-03-23")]
    assert meta["calendar"]["first"] == meta["calendar"]["last"] == "2020-03-23"


# ---------------------------------------------------------------- holdout guard

def test_check_end_refuses_dates_after_the_lock(tmp_path, monkeypatch):
    monkeypatch.delenv("QUANT_UNLOCK_HOLDOUT", raising=False)
    (tmp_path / "LOCK").write_text("2021-12-31\n")
    ix.check_end(date(2021, 12, 31), tmp_path)
    with pytest.raises(SystemExit, match="holdout"):
        ix.check_end(date(2022, 1, 3), tmp_path)
    with pytest.raises(SystemExit, match="holdout"):
        ix.build(date(2003, 1, 1), date(2022, 6, 30), root=tmp_path, offline=True)
    monkeypatch.setenv("QUANT_UNLOCK_HOLDOUT", "1")
    ix.check_end(date(2022, 1, 3), tmp_path)


# ---------------------------------------------------------------- download layer, with a fake session

class FakeResponse:
    def __init__(self, status=200, body=b""):
        self.status_code, self.content = status, body
        self.text = body.decode("utf-8", "replace")


class FakeSession:
    """Answers GET for daily files and POST for niftyindices from dicts; counts calls."""
    def __init__(self, daily=None, ni=None):
        self.daily, self.ni, self.calls = daily or {}, ni or {}, []

    def get(self, url, **kw):
        self.calls.append(url)
        key = url.rsplit("_", 1)[1][:8]
        return FakeResponse(200, self.daily[key].encode()) if key in self.daily else FakeResponse(404, b"<html>404</html>")

    def post(self, url, data=None, **kw):
        self.calls.append(url)
        cinfo = json.loads(data)["cinfo"]
        for (endpoint, name), rows in self.ni.items():
            if url.endswith(endpoint) and f"'name':'{name}'" in cinfo:
                return FakeResponse(200, json.dumps(rows).encode())
        return FakeResponse(200, b"[]")


@pytest.fixture
def fake(monkeypatch):
    s = FakeSession()
    monkeypatch.setattr(ix, "_session", lambda: s)
    monkeypatch.setattr(ix.time, "sleep", lambda *_: None)
    return s


def test_download_daily_is_incremental_and_remembers_absent_days(tmp_path, fake):
    fake.daily = {"23032020": DAILY_2020}
    st = ix.download_daily(tmp_path, date(2020, 3, 21), date(2020, 3, 24), log=lambda *_: None)
    assert (st["requested"], st["ok"], st["absent"], st["failed"], st["files"]) == (4, 1, 3, [], 1)
    assert ix.daily_path(tmp_path, date(2020, 3, 23)).read_text() == DAILY_2020
    assert json.loads((tmp_path / "daily" / "absent.json").read_text()) == ["2020-03-21", "2020-03-22", "2020-03-24"]
    n = len(fake.calls)
    st = ix.download_daily(tmp_path, date(2020, 3, 21), date(2020, 3, 24), log=lambda *_: None)
    assert st["requested"] == 0 and len(fake.calls) == n                 # nothing is asked for twice
    fake.daily["24032020"] = DAILY_2020.replace("23-03-2020", "24-03-2020")
    st = ix.download_daily(tmp_path, date(2020, 3, 21), date(2020, 3, 24), recheck={date(2020, 3, 24)}, log=lambda *_: None)
    assert st["requested"] == 1 and st["ok"] == 1 and st["files"] == 2   # a known trading day is retried
    assert "2020-03-24" not in json.loads((tmp_path / "daily" / "absent.json").read_text())


def test_download_daily_never_asks_before_the_first_file(tmp_path, fake):
    st = ix.download_daily(tmp_path, date(2012, 2, 17), date(2012, 2, 21), log=lambda *_: None)
    assert st["requested"] == 1 and fake.calls[0].endswith("ind_close_all_21022012.csv")


def test_fetch_daily_rejects_an_error_page_served_with_status_200(tmp_path, fake):
    fake.daily = {"23032020": "<html>Access Denied</html>"}
    with pytest.raises(RuntimeError, match="unexpected body"):
        ix.fetch_daily(tmp_path, date(2020, 3, 23))
    assert not ix.daily_path(tmp_path, date(2020, 3, 23)).exists()


def test_read_daily_flags_a_file_holding_another_days_rows(tmp_path):
    p = ix.daily_path(tmp_path, date(2020, 3, 24))
    p.parent.mkdir(parents=True)
    p.write_text(DAILY_2020)                                           # rows dated the 23rd in the file of the 24th
    long, problems = ix.read_daily(tmp_path, date(2020, 3, 1), date(2020, 3, 31))
    assert long.empty and problems and problems[0][0] == "2020-03-24"


def test_fetch_ni_caches_and_discards_rows_outside_the_window(tmp_path, fake):
    late = {"RequestNumber": "x", "Index Name": "Nifty 50", "Date": "03 Jan 2022", "TotalReturnsIndex": "25000.00"}
    fake.ni = {("getTotalReturnIndexString", "NIFTY 50"): [late] + NI_TRI}
    rows = ix.fetch_ni(tmp_path, "tri", "NIFTY 50", "NIFTY 50", date(2020, 1, 1), date(2021, 12, 31))
    assert [r["Date"] for r in rows] == ["31 Mar 2020", "30 Mar 2020"]           # the 2022 row never reaches disk
    p = ix.ni_path(tmp_path, "tri", "NIFTY 50", date(2020, 1, 1), date(2021, 12, 31))
    stored = json.loads(gzip.decompress(p.read_bytes()))
    assert stored["rows"] == rows and "2022" not in json.dumps(stored["rows"]) and "RequestNumber" not in rows[0]
    n = len(fake.calls)
    assert ix.fetch_ni(tmp_path, "tri", "NIFTY 50", "NIFTY 50", date(2020, 1, 1), date(2021, 12, 31)) == rows
    assert len(fake.calls) == n                                                    # second call is served from disk
    with pytest.raises(FileNotFoundError):
        ix.fetch_ni(tmp_path, "tri", "NIFTY 500", "NIFTY 500", date(2020, 1, 1), date(2021, 12, 31), offline=True)


def test_download_ni_retries_under_the_official_name(tmp_path, fake):
    # the valuation endpoint answers only to the short name, the price endpoint to either
    cat = {"indices": {"NIFTY 50": "Equity / Broad Market Indices", "NIFTY SMALLCAP 250": "Equity / Broad Market Indices"},
           "trading_names": {"NIFTY50": "NIFTY 50", "NIFTYSMALLCAP250": "NIFTY SMLCAP 250"}}
    fake.ni = {("getHistoricaldatatabletoString", "NIFTY 50"): NI_PRICE,
               ("getTotalReturnIndexString", "NIFTY 50"): NI_TRI,
               ("getpepbHistoricaldataDBtoString", "NIFTY 50"): NI_PEPB,
               ("getHistoricaldatatabletoString", "NIFTY SMALLCAP 250"): NI_PRICE_CLOSE_ONLY}
    out = ix.download_ni(tmp_path, cat, date(2020, 1, 1), date(2020, 12, 31), log=lambda *_: None)
    assert out["failed"] == []
    assert set(out["frames"]["price"]) == {"NIFTY 50", "NIFTY SMALLCAP 250"}
    assert set(out["frames"]["tri"]) == {"NIFTY 50"} and set(out["frames"]["pepb"]) == {"NIFTY 50"}
    assert out["frames"]["price"]["NIFTY 50"].loc["2020-03-23", "close"] == 7610.25
    assert not any("INDIA VIX" in k for k in out["frames"]["tri"])


# ---------------------------------------------------------------- end to end, offline

def test_build_offline_and_load_through_store(tmp_path, fake, monkeypatch):
    monkeypatch.delenv("QUANT_UNLOCK_HOLDOUT", raising=False)
    (tmp_path / "LOCK").write_text("2021-12-31\n")
    raw = tmp_path / "raw" / "index"
    cat = {"indices": {"NIFTY 50": "Equity / Broad Market Indices"}, "trading_names": {"NIFTY50": "NIFTY 50"}}
    (raw / "niftyindices").mkdir(parents=True)
    (raw / "niftyindices" / "catalogue.json").write_text(json.dumps(cat))
    fake.daily = {"23032020": DAILY_2020}
    fake.ni = {("getHistoricaldatatabletoString", "NIFTY 50"): NI_PRICE,
               ("getTotalReturnIndexString", "NIFTY 50"): NI_TRI,
               ("getpepbHistoricaldataDBtoString", "NIFTY 50"): NI_PEPB}
    meta = ix.build(date(2020, 3, 1), date(2020, 3, 31), root=tmp_path, log=lambda *_: None)
    assert meta["download"]["niftyindices_failed"] == [] and meta["download"]["daily"]["files"] == 1
    assert meta["download"]["trading_days_without_daily_file"] == ["2020-03-24"]

    n = len(fake.calls)                                    # a second, offline build makes no request at all
    ix.build(date(2020, 3, 1), date(2020, 3, 31), root=tmp_path, offline=True, log=lambda *_: None)
    assert len(fake.calls) == n

    close = store.load_index("close", root=tmp_path)
    assert isinstance(close.index, pd.DatetimeIndex) and close.index.name == "date"
    assert list(close.index) == [pd.Timestamp("2020-03-23"), pd.Timestamp("2020-03-24")]
    assert close.loc["2020-03-23", "NIFTY 50"] == pytest.approx(7610.25)
    assert close.loc["2020-03-23", "NIFTY BANK"] == pytest.approx(16917.65)       # from the daily file
    assert (close.dtypes == "float32").all()
    assert store.load_index("pe", root=tmp_path).loc["2020-03-23", "NIFTY 50"] == pytest.approx(17.15)
    assert store.load_index("low", start="2020-03-24", root=tmp_path)["NIFTY 50"].tolist() == pytest.approx([7511.10])
    assert store.load_index("tri", root=tmp_path).empty or "NIFTY 50" in store.load_index("tri", root=tmp_path)
    on_disk = json.loads((tmp_path / "index" / "meta.json").read_text())
    assert on_disk["indices"]["NIFTY 50"]["fields"]["close"]["last"] == "2020-03-24"
    assert set(on_disk["sources"]) == {"niftyindices", "daily_file"}

    res = {r["check"]: r for r in ix.validate(tmp_path, log=lambda *_: None)}
    assert res["NIFTY 50 close on well-known dates"]["pass"]                      # 2020-03-23 = 7610.25
    assert res["no row after the requested end / holdout lock"]["pass"]
    assert not res["every requested index is present in close"]["pass"]           # the fixture has two indices
