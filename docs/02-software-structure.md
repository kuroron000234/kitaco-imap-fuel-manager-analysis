# 2. ソフトウェアの内部構造

## 2.1 技術スタック

| 要素 | 内容 | 根拠 |
|---|---|---|
| 言語 | VB.NET | `Microsoft.VisualBasic` を参照している。`My` 名前空間（`MyApplication`、`MyComputer`、`MyProject`、`MySettings`）がある。例外処理に `ProjectData.SetProjectError` を使っている。型変換や比較に `Conversions.*` と `Operators.*` を使っている【観測】 |
| 開発環境 | Visual Studio 2005 世代 | `Microsoft.VisualBasic` 8.0.0.0 を参照しており、メタデータは v2.0.50727【観測】 |
| UI | Windows Forms | `System.Windows.Forms` 2.0 を参照【観測】 |
| シリアル通信 | `System.IO.Ports.SerialPort` | フォーム上のコンポーネント `SerialPort1`【観測】 |
| CSV の解析 | `Microsoft.VisualBasic.FileIO.TextFieldParser` | `ReadTextDataFile` の中で使用【観測】 |
| 描画 | `System.Drawing` で `PictureBox` に直接描いている | `Drawing_graph`【観測】 |

全体はメインフォーム1つでできた小さなアプリです。シリアル通信は UI スレッドの上で同期的に行っています。非同期処理やスレッドは使っていません【観測】。

## 2.2 型の一覧

| 型 | 種類 | 役割 |
|---|---|---|
| `fuel_manager.fuel_manage` | Form | メインウィンドウ。メソッド 196 個、フィールド 107 個で、ほぼすべての処理がここにある |
| `fuel_manager.Form2` | Form | バージョン情報ダイアログ（「Fuel Manager Information」）。ラベルのクリックハンドラは中身が空 |
| `fuel_manager.Form3` | Form | 中身が空のフォーム。どこからも参照されていない（使われていない） |
| `fuel_manager.My.*`（7個） | VB が自動生成 | アプリ起動、設定、リソースアクセス用の定型コード |
| `fuel_manager.My.Resources.Resources` | 自動生成 | リソースへのアクセス |

起動するフォームは `fuel_manage` です（`MyApplication.OnCreateMainForm`）【観測】。

## 2.3 画面構成

取扱説明書 25 ページの画面と、`InitializeComponent` の内容を対応させた表です。

| UI 部品 | フィールド名 | 表示 | 役割 |
|---|---|---|---|
| メニュー | `FileToolStripMenuItem` | File | Open / Save（`.fmp` の読み込みと保存） |
| メニュー | `COMToolStripMenuItem` | COM | COM1〜COM20 から手動で選ぶ |
| メニュー | `HELPToolStripMenuItem` | HELP | VERSION（Form2 の表示と非表示を切り替える） |
| ボタン | `Button3` | Single editing / Batch editing | 編集モードの切り替え |
| ボタン | `Button1` | Read | i-Map からマップを読み出す |
| ボタン | `Button2` | Write | i-Map にマップを書き込む |
| ラジオボタン | `RPM_edit_select` | RPM Edit | グラフ表示：選んだ回転数の列を、スロットル開度を横軸にして描く |
| ラジオボタン | `TPS_edit_select` | TPS Edit | グラフ表示：選んだスロットル開度の行を、回転数を横軸にして描く |
| ラジオボタン | `full_view` | 3D View | 3D 表示。グラフをクリックすると 10° ずつ回転する |
| ラベル | `Label1` | ファイル名、または `map_no_N` | 読み込んだファイル名か、読み出したマップ番号 |
| ラベル | `Label2` | `15000rpm` など | 現在のレブリミット |
| 表 | `dgv`（DataGridView） | 30 列 × 21 行 | マップの編集領域 |
| グラフ | `PictureBox1` | — | 補正値のグラフ |
| タイマー | `Timer1` | — | ウィンドウサイズが変わったらグラフを描き直す |
| ダイアログ | `Fuel_map`、`SaveFileDialog1` | — | `.fmp` を開く・保存する |

### 表のセルの色

| 色 | 意味 |
|---|---|
| `Aqua`（水色） | グラフに表示している列（RPM Edit）または行（TPS Edit） |
| `MediumSeaGreen`（緑） | Batch editing で選んだ範囲 |
| `Coral`（オレンジ） | レブリミットより上で、無効になる列 |
| `White` | 通常のセル |

グラフでは、編集中の最新の値が `Yellow`（黄色）、最後に読み込んだ時点の値が水色で描かれます【観測】【裏付け：取扱説明書 31〜34 ページ】。「編集前」の値は `map_dat` 配列に入っています。この配列が更新されるのは、ファイルや本体から読み込んだ（`ReadTextDataFile`）ときだけです。

## 2.4 主なメソッドと役割

| メソッド | 呼ばれるタイミング | 処理 |
|---|---|---|
| `Form1_Load` | 起動時 | 初期化（[2.6 節](#26-起動時の初期化)） |
| `OPenToolStripMenuItem_Click` | File → Open | 拡張子 `.fmp` だけ受け付けて `ReadTextDataFile` を呼ぶ |
| `ReadTextDataFile` | ファイルを開いたとき、本体から読み出したとき | CSV を解析して表に反映し、レブリミットを判定する |
| `SaveToolStripMenuItem_Click` | File → Save | 拡張子 `.fmp` だけ受け付けて `SAVETextDataFile` を呼ぶ |
| `SAVETextDataFile` | 保存するとき | 表の内容を `.fmp` に書き出す |
| `COM1`〜`COM20ToolStripMenuItem_Click` | COM メニュー | `Check_com` で全項目のチェックを外し、選んだ項目にチェックを付けて `PortName` を設定する |
| `Open_port` | Read / Write のとき、`PortName` が `"COM20"` なら | COM ポートを自動で探す（[4.2 節](04-serial-protocol.md#42-com-ポートの選び方)） |
| `Button1_Click` | Read | マップを読み出す（[4.4 節](04-serial-protocol.md#44-読み出し-read)） |
| `Button2_Click` | Write | マップを書き込む（[4.5 節](04-serial-protocol.md#45-書き込み-write)） |
| `Button3_Click` | 編集モードの切り替え | Single と Batch を切り替え、Batch の選択を解除する |
| `dgv_CellClick` | セルをクリックしたとき | Single なら表示中の列／行を更新し、Batch なら範囲を選ぶ |
| `dgv_Cellendedit` | セルの編集を確定したとき | 範囲チェックをして、Batch なら範囲内に一括で反映する |
| `dgv_CellDClick` | セルをダブルクリックしたとき | レブリミットを設定する |
| `paint_limit` | レブリミットが変わったとき | リミットより上の列をオレンジにする |
| `mod_verif` | 表示モードやセルの選択が変わったとき | 水色の強調表示を更新し、グラフを描き直す |
| `Drawing_graph` | いろいろな場面 | グラフ（2D / 3D）を描く |
| `PictureBox1_Click` | グラフをクリックしたとき | 3D 表示なら 10° 回転させる |
| `Timer1_Tick` | 定期的に | ウィンドウサイズが変わったら描き直す |
| `VERSIONToolStripMenuItem_Click` | HELP → VERSION | Form2 の表示と非表示を切り替える |

## 2.5 主な状態変数

| フィールド | 型 | 意味 |
|---|---|---|
| `rev_limit` | `short` | レブリミットの回転数（rpm） |
| `rpm_cell` | `short` | 有効な最後の列の番号（0 始まり）。`rev_limit = (rpm_cell + 1) * 500` |
| `rpm_cell_buf` | `short` | 前回の `rpm_cell`（`paint_limit` で色を戻すのに使う） |
| `map_dat` | `short[31,22]` | 最後に読み込んだときのマップ（表示値 −40〜+40）。グラフの「編集前」表示に使う |
| `check_buf_X/Y`、`check_dat`、`cell_check_cnt` | `short[]` / `short` | Batch editing で選んだ2つのセルの位置と値 |
| `start_x/y`、`loop_x/y` | `short` | Batch editing の範囲（始点と幅） |
| `mod_check` | `string` | 表示モード（`"rpm_mod"` / `"tps_mod"` / `"3d_mod"`） |
| `rpm`、`tps` | `int` | グラフに表示している列と行 |
| `lotate_deg` | `int` | 3D 表示の回転角 |
| `enshu_ritu` | `double` | 3.14159（「円周率」をローマ字にした名前） |
| `kijun_x/y` | `int` | 描画の基準座標（「基準」） |

`enshu_ritu`、`kijun`、`lotate`（rotate の誤記）といった変数名から、開発者は日本語話者だと考えられます【推測】。

## 2.6 起動時の初期化

`Form1_Load` では次の処理をします【観測】。

1. `SerialPort1.PortName = "COM20"`。この値を「ポート未設定」の目印に使っています（[5 章](05-quirks-and-bugs.md)）。
2. `RPM Edit` を選んだ状態にし、`mod_check = "rpm_mod"` にします。
3. `rev_limit = 15000`、`rpm_cell = 29` にします。
4. 表を 21 行にし、行見出しを `0%`〜`100%` にします。列見出し `500`〜`15000` はリソース（`.resx`）に定義されています。
5. 全セルを `0` にしてから、グラフを描きます。

## 2.7 編集処理

### Single editing（1セルずつ編集）

`dgv_Cellendedit` で確定時にチェックします【観測】。

| 条件 | 動作 |
|---|---|
| 値が +40 より大きい | 「Ran over setting range」と警告し、+40 にする |
| 値が −40 より小さい | 同じ警告を出し、−40 にする |
| 数値でない（例外が起きた） | 「Invalid key.」と警告し、0 にする |
| レブリミットより上の列のセル | 入力した値にかかわらず 0 にする |

### Batch editing（範囲を一括編集）

1. セルを2つクリックすると、その2つを対角とする長方形が緑になります。レブリミットより上の列でのクリックは無視されます【観測】。
2. どれか1つのセルに値を入れると、範囲チェック（−40〜+40、超えたら警告して丸める）のあと、長方形全体にその値が入ります。
3. 2つ選ぶ前に値を入れると、「Please choose two cells.」と警告し、セルを元の値に戻します。

### レブリミットの設定

`dgv_CellDClick` で、ダブルクリックしたセルの列 `X` を使って `rev_limit = (X + 1) * 500` にします。ただし 9000 rpm 未満になる場合は 9000 rpm（`rpm_cell = 17`）にします【観測】。上限は列の数で決まり、15000 rpm です。取扱説明書 35 ページにある「9000〜15000 rpm、500 rpm 刻み」と一致します【裏付け】。

リミットより上の列の値は、表の中ではそのまま残っています。保存や書き込みのときだけ `0` として出力されます。このため、リミットを上げ直すと前の値が表に戻ります【観測】。

## 2.8 メッセージの一覧

| メッセージ | タイトル | 出る場面 |
|---|---|---|
| `A wrong file has been selected.` | Warning | Open で拡張子が `.fmp` 以外のファイルを選んだ |
| `A wrong file has been chosen.` | Warning | Save で拡張子が `.fmp` 以外を指定した。または `.fmp` を解析中に `MalformedLineException` が起きた |
| `The error occurred while reading the file.` | Warning | `.fmp` の解析中にそれ以外の例外が起きた（数値でない、行や列が多すぎるなど） |
| `Communication device is not connected.` | Warning | 自動検出でポートが見つからなかった。または読み出し中に例外が起きた（タイムアウトや解析エラーも含む） |
| `Communication error` | Warning | 通信を始めようとしたらポートがすでに開いていた |
| `Read completed.` | Message | 読み出しが成功した |
| `Writing completed.` | Message | 書き込みが終わった |
| （例外のメッセージ） | Connection error | 書き込み中に例外が起きた |
| `Please choose two cells.` | Warning | Batch editing で範囲を選ぶ前に値を入れた |
| `Ran over setting range.` / `Ran over setting range` | Warning | 値が −40〜+40 の範囲を超えた（Batch と Single で末尾のピリオドの有無が違う） |
| `Invalid key.` | Warning | 数値以外を入力した |
