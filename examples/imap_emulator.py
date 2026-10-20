"""なりすまし i-Map（テスト用）。疑似端末（pty）の片側で、推定したプロトコルどおりに応答する。"""
import os
import threading
import tty


class FakeIMap:
    def __init__(self, cols, map_no=7):
        self.cols = [list(c) for c in cols]
        self.map_no = map_no
        self.log = []  # (向き, バイト列)
        self.master, slave = os.openpty()
        tty.setraw(slave)
        self.port = os.ttyname(slave)
        self._slave = slave  # 開いたままにしておく
        threading.Thread(target=self._serve, daemon=True).start()

    def _send(self, data):
        self.log.append(("I->PC", data))
        os.write(self.master, data)

    def _recv1(self):
        b = os.read(self.master, 1)
        self.log.append(("PC->I", b))
        return b

    def _serve(self):
        while True:
            cmd = self._recv1()
            if cmd == b"m":
                text = "\r\n".join(",".join(map(str, c)) for c in self.cols)
                self._send(bytes([self.map_no]) + text.encode("ascii") + b"/")
            elif cmd == b"s":
                self._send(b"r")
                new = []
                for c in range(30):
                    buf = bytearray()
                    while (b := self._recv1()) != b"/":
                        buf += b
                    vals = [int(v) for v in buf.decode("ascii").split(",") if v != ""]
                    assert len(vals) == 21, vals
                    new.append(vals)
                    if c != 29:
                        self._send(b"r")
                self.cols = new
