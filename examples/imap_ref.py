"""i-Map 互換通信の参照実装（説明用）。純正 Fuel Manager v1.02 と同じバイト列を送る。"""
import time

import serial

BAUD = 38400
NUM_COLS, NUM_ROWS = 30, 21  # 回転数 500..15000rpm × スロットル開度 0..100%


def open_port(port):
    return serial.Serial(port, BAUD, bytesize=8, parity="N", stopbits=1, timeout=0.1)


def wait_for(s, token, timeout):
    """token（1 バイト）が来るまで待つ。ほかのバイトは読み捨てる（純正と同じ）。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.read(1) == token:
            return
    raise TimeoutError(f"{token!r} を {timeout} 秒待っても受信できなかった")


def parse_fmp_text(text):
    """.fmp と同じ形式のテキストを、30 列 × 21 個の生の値に変換する。"""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    cols = [[int(v) for v in ln.split(",")] for ln in lines]
    if len(cols) != NUM_COLS or any(len(c) != NUM_ROWS for c in cols):
        raise ValueError("30 行 × 21 値 の形式になっていない")
    return cols


def to_fmp_text(cols):
    """純正の保存処理と同じ形式（末尾に CRLF が 3 つ）で .fmp のテキストを作る。"""
    return "".join(",".join(map(str, c)) + "\r\n" for c in cols) + "\r\n\r\n"


def rev_limit(cols):
    for c, col in enumerate(cols):
        if 0 in col:
            return c * 500
    return 15000


def validate(cols):
    """書き込む前の検査。純正の UI では作れないデータを弾く。"""
    if len(cols) != NUM_COLS or any(len(c) != NUM_ROWS for c in cols):
        raise ValueError("30 列 × 21 値 が必要")
    zero = [all(v == 0 for v in col) for col in cols]
    for c, col in enumerate(cols):
        if zero[c]:
            continue
        if 0 in col:
            raise ValueError(f"列 {c}: 0 と 0 以外の値が混ざっている")
        if any(not 60 <= v <= 140 for v in col):
            raise ValueError(f"列 {c}: 60..140 の範囲外の値がある")
    first_zero = zero.index(True) if True in zero else NUM_COLS
    if not all(zero[first_zero:]):
        raise ValueError("全部 0 の列は、リミットより上にまとまっていなければならない")
    if first_zero < 18:
        raise ValueError("レブリミットは 9000rpm 以上でなければならない（純正 UI の制約）")


def read_map(port, first_timeout=20.0, idle_timeout=5.0):
    """戻り値は (マップ番号, 30 列 × 21 個の生の値)。"""
    with open_port(port) as s:
        s.reset_input_buffer()
        s.write(b"m")
        deadline = time.monotonic() + first_timeout
        map_no = None
        while map_no is None:
            if time.monotonic() > deadline:
                raise TimeoutError("'m' に対する応答がない")
            b = s.read(1)
            if b and b != b"\x00":
                map_no = b[0]  # 生のバイト値
        buf = bytearray()
        last_rx = time.monotonic()
        while b"/" not in buf:  # 純正は末尾の 1 文字しか見ないが、ここでは途中の "/" も検出する
            chunk = s.read(4096)
            if chunk:
                buf += chunk
                last_rx = time.monotonic()
            elif time.monotonic() - last_rx > idle_timeout:
                raise TimeoutError("マップデータの受信が途中で止まった")
        return map_no, parse_fmp_text(buf[: buf.index(b"/")].decode("ascii"))


def write_map(port, cols, ack_timeout=20.0):
    """ユーザーオリジナルマップ領域に書き込む。cols は 30 列 × 21 個の生の値。"""
    validate(cols)
    with open_port(port) as s:
        s.reset_input_buffer()
        s.write(b"s")
        wait_for(s, b"r", ack_timeout)
        for c, col in enumerate(cols):
            s.write(("".join(f"{v}," for v in col) + "/").encode("ascii"))
            s.flush()
            if c != NUM_COLS - 1:  # 純正は最後の列のあと応答を待たない
                wait_for(s, b"r", ack_timeout)
