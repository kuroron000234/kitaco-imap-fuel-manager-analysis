"""なりすまし i-Map を相手に、読み出し → 書き込み → 読み戻しを通しで確かめる。

使い方: python test_roundtrip.py [公式配布の .fmp ファイル（省略可）]
必要なもの: Python 3.8 以上、pyserial、Linux または macOS（疑似端末を使うため）
"""
import sys
import time

import imap_ref as ref
from imap_emulator import FakeIMap

# 12000rpm リミット、2000〜3000rpm の 0〜10% を +10% にした説明用マップ
cols = [[100] * 21 for _ in range(24)] + [[0] * 21 for _ in range(6)]
for c in (3, 4, 5):
    cols[c][0:3] = [110, 110, 110]

dev = FakeIMap(cols, map_no=7)

map_no, got = ref.read_map(dev.port)
assert map_no == 7 and got == cols, "読み出した内容が一致しない"
assert ref.rev_limit(got) == 12000
print("読み出し OK: map_no", map_no, "rev_limit", ref.rev_limit(got))

new = [list(c) for c in got]
new[10] = [105] * 21                          # 5500rpm を全域 +5%
new[22:] = [[0] * 21 for _ in range(8)]       # リミットを 11000rpm に
ref.write_map(dev.port, new)

# 最後の列には応答がないので、なりすまし側が処理し終えるまで待つ
t0 = time.monotonic()
while dev.cols != new and time.monotonic() - t0 < 2:
    time.sleep(0.01)
assert dev.cols == new, "書き込んだ内容が一致しない"

_, back = ref.read_map(dev.port)
assert back == new and ref.rev_limit(back) == 11000
print("書き込みと読み戻し OK: rev_limit", ref.rev_limit(back))

for bad, label in [
    ([[100] * 21 for _ in range(10)] + [[0] * 21 for _ in range(20)], "リミット 5000rpm"),
    ([[141] + [100] * 20] + [list(c) for c in cols[1:]], "値 141"),
]:
    try:
        ref.validate(bad)
        raise SystemExit(f"{label} を検査で弾けなかった")
    except ValueError as e:
        print(f"検査 OK（{label}）:", e)

if len(sys.argv) > 1:
    with open(sys.argv[1], encoding="ascii") as f:
        official = ref.parse_fmp_text(f.read())
    ref.validate(official)
    print("公式 .fmp の解析 OK: rev_limit", ref.rev_limit(official))
