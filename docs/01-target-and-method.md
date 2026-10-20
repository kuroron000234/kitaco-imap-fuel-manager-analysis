# 1. 解析対象と解析方法

## 1.1 対象

| 項目 | 値 |
|---|---|
| 製品 | KITACO i-Map（燃調コントローラ）と、i-Map 専用の PC インターフェイスケーブル（品番 763-0500900） |
| 配布ページ | <https://www.kitaco.co.jp/imap> の「I-MAP FUEL MANAGER」 |
| 配布ファイル | `i-Map.zip`（9,617,598 bytes） |
| `i-Map.zip` の SHA-256 | `2ee03e5451aacdd6ae2f258d0e628258779cee50503b8cc5c8592cd2e4037266` |

### `i-Map.zip` の中身

| ファイル | サイズ (bytes) | zip 内の日付 | 内容 |
|---|---:|---|---|
| `Fuel_manager.exe` | 130,560 | 2015-01-06 | 本体 |
| `dotnetfx35setup.exe` | 2,959,376 | 2008-09-12 | Microsoft .NET Framework 3.5 のオンラインインストーラ |
| `CP210x_VCP_Windows.zip` | 3,837,952 | 2014-08-11 | Silicon Labs CP210x 仮想 COM ポートのドライバ |
| `Fuel Manager 取扱説明書.pdf` | 2,840,889 | 2014-09-24 | 取扱説明書。zip 内のファイル名は Shift_JIS なので、展開には `unzip -O CP932` などを使う |

取扱説明書（zip 同梱版）の SHA-256 は `8dcedddbd129cf21f9ee488ce857f1b8d6c0031c5ea70a64858a845ae077ffcb` です。公式サイトで単体配布されている `FuelManager.pdf` は 2,841,105 bytes で、同梱版とはバイト単位で一致しません。

### `Fuel_manager.exe`

| 項目 | 値 |
|---|---|
| SHA-256 | `23b5b5a17e62fc32d977fd025618b943b0d1ef343b5db28d96c9c1ee02cf156a` |
| 形式 | PE32 (x86) の .NET (CLI) アセンブリ。IL のみ（AnyCPU） |
| メタデータのバージョン | `v2.0.50727`（CLR 2.0 系。.NET Framework 2.0〜3.5 で動く） |
| アセンブリ名とバージョン | `fuel_manager` 1.0.0.0（画面上の表記は `Version  1.02`） |
| モジュール MVID | `35638f50-f45c-4f34-998c-ea42f6dc84af` |
| 厳密名署名 | なし |
| 著作権表示（文字列リテラル） | `(C) 2009 KITACO Co.,LTD All Rights Reserved.` |
| 難読化 | なし。型名、メソッド名、フィールド名はすべて元のまま残っている |

### 参照しているアセンブリ

| アセンブリ | バージョン |
|---|---|
| mscorlib | 2.0.0.0 |
| Microsoft.VisualBasic | 8.0.0.0（VB 2005 のランタイム） |
| System | 2.0.0.0（`System.IO.Ports.SerialPort` を含む） |
| System.Windows.Forms | 2.0.0.0 |
| System.Drawing | 2.0.0.0 |

### メタデータの規模

| テーブル | 行数 |
|---|---:|
| TypeDef | 13 |
| MethodDef | 263 |
| Field | 132 |
| MemberRef | 309 |
| ManifestResource | 4 |
| 呼び出し命令（call / callvirt / newobj）の総数 | 2,199 |
| `ldstr` で読み込まれる文字列リテラル | 126 |

## 1.2 解析手順

すべて静的解析です。対象のプログラムは一度も実行していません。

1. 公式サイトから `i-Map.zip` をダウンロードし、ほかのファイルと混ざらない専用のディレクトリに展開した。
2. REA の `inspect_managed_artifact` で PE/CLI ヘッダとメタデータを調べた。
   - 判定結果は `managed` / `cil`。メタデータは欠けなく読めた（`complete`）。
   - Evidence ID: `ev_2f2cb4c454c8376d76001fbb89e05bfa55188800341cfca1db6ba646264ee581`
3. REA の `inspect_managed_members` で、型、メソッド、呼び出し関係、文字列リテラルを抽出した。
   - Evidence ID: `ev_d3c4ef766f912320bf9339cb78f05c8d958c9aec2e330b87779437b1b012b1fd`
4. ILSpy（ilspycmd 11.1.0）で C# のプロジェクトとしてデコンパイルした。メインフォーム `fuel_manager.fuel_manage` は約 3,900 行になった。
5. デコンパイル結果を取扱説明書（特に 23〜37 ページの操作説明と画面写真）と突き合わせた。
6. 公式サイトで配布されている `.fmp` マップを1つ取得し（`125cc_STD_GPR_TYPE1-2_CAM.zip`）、ファイル形式の推定が正しいか確かめた。

Evidence ID は、解析した環境の REA セッションの中で付いた識別子です。記録として載せています。

### 再現用のコマンド

```bash
mkdir imap && unzip -O CP932 i-Map.zip -d imap
rea inspect-managed-artifact imap/i-Map/Fuel_manager.exe --json > artifact.json
rea inspect-managed-members  imap/i-Map/Fuel_manager.exe --json > members.json
ilspycmd -p -o src imap/i-Map/Fuel_manager.exe
```

## 1.3 行っていないこと

- `Fuel_manager.exe` を実行しての動作確認（Windows 上での確認）
- i-Map 実機との通信、シリアル通信の傍受（シリアルモニタやロジックアナライザを使うもの）
- i-Map 本体のファームウェアの解析
- PC インターフェイスケーブルの分解やピン配置の調査

このため、本体側の動作は PC ソフトの実装から推測するしかありません。各文書の【推測】【不明】は、この制約によるものです。

## 1.4 参照したその他の資料

| 資料 | 入手元 | 使い道 |
|---|---|---|
| i-Map カプラーオン SET 取扱説明書（グロム JC61 用、Ver3 763-1432120 / Ver4 763-1432130） | <https://www.kitaco.co.jp/storage/product/763-1432120~30.pdf> | DIP スイッチとマップ番号の対応、補正のかかり方、本体の配線（[3 章](03-map-data-and-fmp-format.md)、[4 章](04-serial-protocol.md)、[7 章](07-pc-interface-cable.md)） |
| i-map カプラーオン SET 取扱説明書（ズーマー FI 用 763-1135100、PCX150 用 763-1441100） | <https://www.kitaco.co.jp/storage/product/763-1135100.pdf>、<https://www.kitaco.co.jp/storage/product/763-1441100.pdf> | 本体のカプラ（110 型 6P）と配線 |
| 純正 PC インターフェイスケーブルの写真 | 2026 年 10 月にフリマアプリで公開されていた中古品の出品写真（6 枚） | ケーブルとカプラの構造（[7 章](07-pc-interface-cable.md)） |
| データロガー用ソフト `Loger.EXE`（33,164,339 bytes、SHA-256 `4db60565e6ac184a84f901a190e848e2d12ce35a31092025ffd6d493766bec99`） | <https://www.kitaco.co.jp/imap> の「データロガー」 | 同じ会社の別製品用ソフトとの比較（[8 章](08-development-traces.md)） |
