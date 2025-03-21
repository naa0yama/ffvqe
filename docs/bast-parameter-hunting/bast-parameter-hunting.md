# Bast parameter hunting

h264_qsv, hevc_qsv, av1_qsv のエンコードパラメータで容量が小さく、 VMAF が優れているパラメータを模索する方法。

## Environment

|        |                                           |
| :----- | :---------------------------------------- |
| CPU    | 64 x AMD EPYC 7551P 32-Core Processor     |
| M/B    | Supermicro H11SSL-i                       |
| Memory | 8 x 32GB DDR4-2133                        |
| SSD    | 2x Intel 2.5inch 480GB D3-S4510 ZFS Miror |
| GPU    | Sparkle Intel Arc A310 ELF 4GB SA310E-4G  |

### VM

Proxmox VE の仮想マシンに PCIE パススルーし、計測している VMAF の算出は CPU で処理するため 60 Core 割り当てているので注意

|                 |             |
| :-------------- | :---------- |
| CPU             | 60 Core     |
| Memory          | 32GB        |
| BIOS            | OVMF        |
| Machine         | q35         |
| SCSI Controller | VirtIO SCSI |

## 現状のベスト

|                 |  File size |   bitrate | encode time | compress_rate | MSSIM |   VMAF min/mean | GOP   | bf   | refs | I/P/B frames           | options                                                     |
| :-------------- | ---------: | --------: | ----------: | ------------: | ----: | --------------: | :---- | :--- | :--- | :--------------------- | :---------------------------------------------------------- |
| libx264         | 94,385.908 | 6,292.776 |      40.209 |         0.617 | 0.998 | 85.469 / 94.831 | 250.0 | 3.0  | 4.0  | 30.0 / 2654.5 / 1380.0 | -crf 23                                                     |
| libx265         | 88,267.994 | 5,884.813 |     160.378 |         0.651 | 0.997 | 83.206 / 94.555 | 250.0 | 3.0  | 1.0  | 21.5 / 2036.0 / 2231.0 | -crf 23                                                     |
| libx265         | 42,769.258 | 2,851.418 |      132.84 |         0.832 | 0.994 | 73.278 / 89.803 | 250.0 | 3.0  | 1.0  | 21.5 / 2036.0 / 2231.0 | -crf 28                                                     |
| libsvtav1       | 64,850.455 | 4,323.608 |      86.170 |         0.745 | 0.997 | 83.326 / 94.639 | 161.0 | 0.0  | 1.0  | 23.0 / 3573.5 / 0.0    | -crf 31                                                     |
| libsvtav1       | 45,813.643 | 3,054.433 |      85.297 |         0.820 | 0.996 | 80.339 / 93.243 | 161.0 | 0.0  | 1.0  | 23.0 / 3573.5 / 0.0    | -crf 35                                                     |
|                 |            |           |             |               |       |                 |       |      |      |                        |                                                             |
| h264_qsv LA-ICQ | 80,026.906 | 5,334.941 |      12.104 |         0.689 | 0.996 | 82.038 / 95.711 | 256.0 | 3.0  | 3.0  | 15.0 / 899.0 / 2683.0  | -global_quality 25 -look_ahead 1                            |
|                 | 70,052.759 | 4,670.035 |      12.913 |         0.727 | 0.996 | 79.411 / 94.773 | 256.0 | 5.0  | 8.0  | 15.0 / 225.0 / 3357.0  | -global_quality 25 -look_ahead 1 -bf 15 -refs 8             |
| hevc_qsv ICQ    | 58,740.902 | 3,915.939 |      13.359 |         0.772 | 0.997 | 81.685 / 95.556 | 248.0 | 5.0  | 1.0  | 15.0 / 0.0 / 3582.0    | -global_quality 21 -bf 15 -refs 8                           |
|                 | 57,403.106 | 3,826.759 |      13.384 |         0.777 | 0.997 | 81.586 / 95.704 | 248.0 | 5.0  | 1.0  | 15.0 / 0.0 / 3582.0    | -global_quality 21 -bf 15 -refs 8 -vf vpp_qsv=format=p010le |
| av1_qsv ICQ     | 69,171.718 | 4,611.312 |      12.597 |         0.730 | 0.997 | 82.761 / 95.985 | 248.0 | 0.0  | 1.0  | 15.0 / 3582.0 / 0.0    | -global_quality 24                                          |
|                 | 70,849.782 | 4,723.186 |      12.628 |         0.723 | 0.997 |  83.577 / 96.34 | 248.0 | 0.0  | 1.0  | 15.0 / 3582.0 / 0.0    | -global_quality 24 -vf vpp_qsv=format=p010le                |

### h264_qsv best

```bash
ffmpeg -y -threads 4 -hide_banner -ignore_unknown -fflags +discardcorrupt+genpts -analyzeduration 30M -probesize 100M \
    -hwaccel_output_format qsv \
    -map 0:v -hwaccel qsv -c:v mpeg2_qsv -i base.mkv \
    -c:v h264_qsv -preset:v veryslow \
    -global_quality 25 -look_ahead 1 -aspect 16:9 -bf 15 -refs 8 \
    -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 -max_muxing_queue_size 4000 \
    -movflags faststart -f mkv \
    -map 0:a -c:a libopus -b:a 128k -ar 48k -ac 2 \
    \
    out.mkv

```

### hevc_qsv best

hevc_qsv はファイルサイズの削減更に進み、画質を落とさず容量削減が可能。
また、 10-Bit カラーの Main10 にも対応するためグラデーションなど状況でも問題ない。

```bash

```

### av1_qsv best

## 画質探索の極意

私の知識で、簡単に動画ファイルの圧縮について記述します。  
[FFmpeg](https://www.ffmpeg.org) を利用します、 Windows などでは [HandBrake](https://handbrake.fr) など GUI で優れたエンコードソフトウェアがありますが、私の環境では Linux を主に利用しており、 Linux/Windows で同じ設定を利用出来ないと品質を維持して利用することが出来ません。  

「動画の圧縮」と一言で言っても方法が多く、広義の方法として言われる事が多いため実現したい事を定義する。世の中には地上波放送を録画して楽しむ文化がある。総称として DTV が用いられるため以下はそうする。 DTV は地上波放送を録画する関係で MPEG-2 のコーディックで配信されてくる音声、映像データを保存するため約 7GB/時間の容量を必要とする。  
そのため、アニメやドラマを全録するような利用をすると2600番組/年程度録画することになり、単純な容量計算では 18TB 程度必要になる。これでは毎年高額な大容量 HDD を買い足す運用になり維持管理が難しいため映像を圧縮して容量を削減するのが目的である。

映像を圧縮するには codec を指定する、今回は Intel QSV を利用するため h264, HEVC, AV1 に対応しており圧縮率は h264 -> HEVC -> AV1 の順番でよくなり秒間あたりの Bitrate が削減できるため動画全体として容量を圧縮できる。一方、圧縮時間は圧縮率が高い codec になるほど時間がかかるため AV1 が最も優れているが、処理時間とトレードオフになる事もある。

エンコードすると多少なりとも映像は劣化する。がそれを定量的に確認する術がなく、「なんか画質悪くなった」というようなケースがあったんではなかろうか。そのため今回は結構なパターンを検証することもあり [VMAF](https://github.com/Netflix/vmaf) を利用したスコアを確認する。 VMAF のスコアは 1080p をベースに算出され、 0-100 での数値で表記される。 全フレームの平均が採用されるが、最低値を確認する方法として `min` も存在するこれは フレームに対して記録された最低値のため容易に 0 が記録される事がある。オプションを設定することで 調和平均(`harmonic_mean`) を確認することができる。のでこちらを利用する。

テストの目標は調和平均 VMAF 93 以上、容量はできるだけ小さくを目標にする。  
アニメ 1話 200MB 以下、1クオーター 500GB 前後になるようにしたい。  

* q(Constant Quantizer): エンコード時に出る `q=XX.X` の数値で `-global_quality` に合わせて前後する。
  * `libx264` の `-crf 23` は `q=29.0` となる
  * LA-ICQ で合わせるなら `-global_quality 25` が同等となる。
* qp(Quantization Parameter): 固定品質パラメータ、各 Frame の最低値設定などで利用する

## Global

※詳細は、各パラメーターに譲るがが抜粋

| type     | option                                    | `<default>, <>`           | Description                                                                       |
| :------- | :---------------------------------------- | :------------------------ | :-------------------------------------------------------------------------------- |
| Global   | `-y`                                      |                           | 確認せずに上書きする                                                              |
|          | `-threads 4`                              | `<cpu core>*1.5`          | FFmpeg のスレッド数を指定、試験環境は VMAF の関係で超多コア(60 Core)のため指定    |
|          | `-hide_banner`                            |                           | バナーを非教示に                                                                  |
|          | `-ignore_unknown`                         |                           | 不明コーデックをコピーしない                                                      |
|          | `-fflags +discardcorrupt+genpts`          |                           | 破損パケットを破棄(`+discardcorrupt`), DTS が存在する場合は PTS を生成(`+genpts`) |
|          | `-analyzeduration 30M`                    | 5M us(5秒)                | 映像解析時間を指定 (μs 単位)                                                      |
|          | `-probesize 100M`                         | 5MB                       | 映像解析容量の上限                                                                |
|          |                                           |                           |                                                                                   |
|          |                                           |                           |                                                                                   |
|          |                                           |                           |                                                                                   |
| Hardware | `-hwaccel_output_format qsv`              |                           | 出力フォーマットを Hardware QSV にする                                            |
|          |                                           |                           |                                                                                   |
| Input    | `-hwaccel qsv -c:v mpeg2_qsv -i base.mkv` |                           | Intel QSV の decoder を指定し Input を読み込む                                    |
|          | `-map 0:v`                                |                           | 映像を input からマッピング                                                       |
|          | `-c:v h264_qsv`                           |                           |                                                                                   |
|          | `-preset:v veryslow`                      |                           | preset                                                                            |
|          | `-global_quality 25 -look_ahead 1`        |                           | LA-ICQ でエンコードする                                                           |
|          | `-look_ahead_depth 60`                    | 0, 0-100                  | 先行読み込みフレームを 60 枚(約2秒)にする                                         |
|          | `-look_ahead_downsampling off`            | unknown, (auto,off,2x,4x) | 先行読み込み時にダウンサンプリングをしない                                        |
|          | `-g`                                      | 256                       | GOP長、Iフレーム間の距離                                                          |
|          | `-bf 16`                                  | 2                         | I-Frame と P-Frame 間の B-Frame の数                                              |
|          | `-refs 9`                                 | 3                         | B-Frame 動き補正を考慮する参照フレーム数                                          |
|          | `-b_strategy 1`                           | `-1`, 0, 1                | B-Frame を 参照 B-Frame として使用することを制御します。                          |
|          | `-aspect:v 16:9`                          |                           | アスペクト比を 16:9 に設定                                                        |
|          | `-movflags faststart`                     |                           | メタデータをファイルの先頭にする                                                  |
|          | `-tag:v hvc1`                             |                           | Apple 製品で再生出来ないため `hvc1` 方式であることを明示する (HEVC の時のみ)      |
|          | `-f mkv`                                  |                           | ファイルフォーマットは MKV にする                                                 |
|          |                                           |                           |                                                                                   |
| Audio    | `-c:a aac`                                |                           | AAC に変換                                                                        |
|          | `-ar 48000`                               |                           | サンプリングレート 48kHz                                                          |
|          | `-ab 256k`                                |                           | ビットレート 256kbps                                                              |
|          | `-bsf:a aac_adtstoasc`                    |                           | MPEG-2 から MPEG-4 に変更するオプション                                           |

* [FFmpeg Codecs Documentation](https://ffmpeg.org/ffmpeg-codecs.html#Global-Options-_002d_003e-MSDK-Options)
* [HWAccelIntro – FFmpeg](https://trac.ffmpeg.org/wiki/HWAccelIntro)
* [Hardware/QuickSync – FFmpeg](https://trac.ffmpeg.org/wiki/Hardware/QuickSync)
* [Hardware/VAAPI – FFmpeg](https://trac.ffmpeg.org/wiki/Hardware/VAAPI)

```bash
$ ffmpeg -loglevel debug -i base.mkv -c:v h264_qsv -global_quality 25 -look_ahead 1 -preset veryslow -f null -

[h264_qsv @ 0x6003e69b3bc0] Initialized an internal MFX session using hardware accelerated implementation
[h264_qsv @ 0x6003e69b3bc0] Using the intelligent constant quality with lookahead (LA_ICQ) ratecontrol method
[h264_qsv @ 0x6003e69b3bc0] profile: avc high; level: 40
[h264_qsv @ 0x6003e69b3bc0] GopPicSize: 256; GopRefDist: 4; GopOptFlag: closed; IdrInterval: 0
[h264_qsv @ 0x6003e69b3bc0] TargetUsage: 1; RateControlMethod: ICQ
[h264_qsv @ 0x6003e69b3bc0] ICQQuality: 25
[h264_qsv @ 0x6003e69b3bc0] NumSlice: 1; NumRefFrame: 3
[h264_qsv @ 0x6003e69b3bc0] RateDistortionOpt: OFF
[h264_qsv @ 0x6003e69b3bc0] RecoveryPointSEI: OFF
[h264_qsv @ 0x6003e69b3bc0] VDENC: ON
[h264_qsv @ 0x6003e69b3bc0] Entropy coding: CABAC; MaxDecFrameBuffering: 3
[h264_qsv @ 0x6003e69b3bc0] NalHrdConformance: OFF; SingleSeiNalUnit: ON; VuiVclHrdParameters: OFF VuiNalHrdParameters: OFF
[h264_qsv @ 0x6003e69b3bc0] FrameRateExtD: 1001; FrameRateExtN: 30000
[h264_qsv @ 0x6003e69b3bc0] IntRefType: 0; IntRefCycleSize: 0; IntRefQPDelta: 0
[h264_qsv @ 0x6003e69b3bc0] MaxFrameSize: 783360; MaxSliceSize: 0
[h264_qsv @ 0x6003e69b3bc0] BitrateLimit: OFF; MBBRC: ON; ExtBRC: OFF
[h264_qsv @ 0x6003e69b3bc0] Trellis: auto
[h264_qsv @ 0x6003e69b3bc0] RepeatPPS: OFF; NumMbPerSlice: 0; LookAheadDS: 2x
[h264_qsv @ 0x6003e69b3bc0] AdaptiveI: OFF; AdaptiveB: OFF; BRefType:pyramid
[h264_qsv @ 0x6003e69b3bc0] MinQPI: 0; MaxQPI: 0; MinQPP: 0; MaxQPP: 0; MinQPB: 0; MaxQPB: 0
[h264_qsv @ 0x6003e69b3bc0] DisableDeblockingIdc: 0
[h264_qsv @ 0x6003e69b3bc0] SkipFrame: no_skip
[h264_qsv @ 0x6003e69b3bc0] PRefType: default
[h264_qsv @ 0x6003e69b3bc0] TransformSkip: unknown
[h264_qsv @ 0x6003e69b3bc0] IntRefCycleDist: 0
[h264_qsv @ 0x6003e69b3bc0] LowDelayBRC: OFF
[h264_qsv @ 0x6003e69b3bc0] MaxFrameSizeI: 0; MaxFrameSizeP: 0
[h264_qsv @ 0x6003e69b3bc0] ScenarioInfo: 0

```

## Encode type

Intel QSV では下記のエンコードモードに対応している

* CQP (Constant Quantization Parameter)
  * **Intel QSV での h264_qsv, hevc_qsv, av1_qsv のデフォルトモード**
  * 一定品質を維持する設定のため、単調なシーンでは過剰、複雑なシーンではビットレート不足となる
* ICQ (Intelligent Constant Quality)
  * このモードは画質を一定に保ちながら、シーンの複雑さに応じてビットレートを調整します。
* LA-ICQ (Look-Ahead Intelligent Constant Quality)
  * `hevc_qsv`, `av1_qsv` では 2025/02 現在では LA_ICQ の実装はない
    * [[Bug]: VA_RC_ICQ not available in AV1 encoder on DG2 · Issue #1597 · intel/media-driver](https://github.com/intel/media-driver/issues/1597)
  * 先読み解析により画質制御がされ適切なビットレートを割り当てることで、画質と容量のバランスを取ります

libx265 でおなじみ CRF(Constant Rate Factor) は Intel QSV には存在しない  
画質は、 LA-ICQ が最も良く ICQ、CQP、VBR の順になる

## 条件

* q / CRF は手元の環境でテストし VMAF min/mean が下限 70/93 を超えるパラメーターを採用する
* [Encode Features for Intel® Discrete Graphics](https://www.intel.com/content/www/us/en/docs/onevpl/developer-reference-media-intel-hardware/1-0/features-and-formats.html#ENCODE-DISCRETE)
* MSSIM(Mean SSIM / 構造的類似性) 画像の類似性を計測する値、1に近いほうが元画像に近い
* [VMAF - Video Multi-Method Assessment Fusion](https://github.com/Netflix/vmaf/tree/master)
  * Netflix が配信映像の主観的品質評価を目的に開発したライブラリー
  * 機械学習を利用して人間の映像品質の識別を教師データとして学習しているため、人間の知覚に近い
  * 0-100 で算出され一般に 93-96 は元映像の見分けが付かず、 95 以上はオリジナルより余剰容量(Bitrate)となる
    * スコア差 2 は人間では見分けが付かず、3を超えると知覚が鋭敏な人は気づく (18人のテストで半分が気づく)
    * 93.00 付近で複数値がある場合は compress_rate が ±0.03 以内なら VMAF mean がより高い方を選択
* `-threads`
  * 通常の利用では指定なしでも問題ないが、今回のテストでは 60Core のマシンを利用しているため実利用の環境に合わせ 4Core で制限をかける

* HW encode
  * `-preset`
    * HW encode になるとどの `-preset` を使っても実行時間の差はわずかであるため一番処理に時間がかかる `veryslow` を採用する

## ベースデータ

ベースデータは各 codec の基準値として採用する値  
この値から + / - どちらに触れたかで映像の向上を確認する

| codev       | BRC modes     | BBB / Nature | q / CRF |  File size |   bitrate | encode time | compress_rate | MSSIM | VMAF min/mean | Options<br>GOP,b-frame, refs     |
| :---------- | :------------ | :----------: | ------: | ---------: | --------: | ----------: | ------------: | ----: | ------------: | :------------------------------- |
| `libx264`   |               |              |         |            |           |             |               |       |               | **GOP: 250, -bf 2, -refs 4**     |
|             | CRF (default) |    Anime     |     *23 | 112,452.17 |  7,497.69 |       40.22 |          0.53 |  1.00 | 86.33 / 93.94 | -crf 23                          |
|             |               |    Nature    |     *23 |  76,319.65 |  5,087.87 |       38.96 |          0.70 |  1.00 | 84.61 / 95.73 | -crf 23                          |
|             |               |    Anime     |      25 |  56,118.49 |  3,741.16 |       38.65 |          0.78 |  1.00 | 81.63 / 94.15 | -crf 25                          |
|             |               |    Nature    |      23 | 112,452.17 |  7,497.69 |       40.22 |          0.53 |  1.00 | 86.33 / 93.94 | -crf 23                          |
|             |               |              |         |            |           |             |               |       |               |                                  |
| `libx265`   |               |              |         |            |           |             |               |       |               | **GOP: 250, -bf 2, -refs 1**     |
|             | CRF (default) |    Anime     |     *28 |  34,688.58 |  2,312.45 |      124.71 |          0.87 |  0.99 | 73.77 / 91.94 | -crf 28                          |
|             |               |    Nature    |     *28 |  50,849.93 |  3,390.39 |      136.81 |          0.80 |  0.99 | 72.79 / 87.67 | -crf 28                          |
|             |               |    Anime     |      26 |  46,893.31 |  3,126.05 |      132.49 |          0.82 |  1.00 | 77.80 / 93.85 | -crf 26                          |
|             |               |    Nature    |      23 | 104,671.72 |  6,978.93 |      169.79 |          0.58 |  1.00 | 83.36 / 93.26 | -crf 23                          |
|             |               |              |         |            |           |             |               |       |               |                                  |
| `libsvtav1` |               |              |         |            |           |             |               |       |               | **GOP: 161, -bf 0, -refs 1**     |
|             | CRF (default) |    Anime     |     *35 |  57,952.24 |  3,863.93 |       95.13 |          0.77 |  1.00 | 79.77 / 91.31 | -crf 35                          |
|             |               |    Nature    |     *35 |  33,675.05 |  2,244.93 |       70.58 |          0.87 |  1.00 | 80.91 / 95.17 | -crf 35                          |
|             |               |    Anime     |      39 |  23,106.44 |  1,540.40 |       68.27 |          0.91 |  1.00 | 78.50 / 93.94 | -crf 39                          |
|             |               |    Nature    |      31 |  80,498.38 |  5,367.18 |       96.56 |          0.68 |  1.00 | 82.93 / 93.11 | -crf 31                          |
|             |               |              |         |            |           |             |               |       |               |                                  |
| `h264_qsv`  |               |              |         |            |           |             |               |       |               | **GOP: 256, -bf 2, -refs 3**     |
|             | CQP (default) |    Anime     |     *23 | 100,540.38 |  6,703.47 |       11.15 |          0.60 |  1.00 | 82.89 / 92.96 | -q:v 23                          |
|             |               |    Nature    |     *23 |  71,430.68 |  4,761.92 |       11.86 |          0.72 |  1.00 | 80.79 / 95.35 | -q:v 23                          |
|             |               |    Anime     |      25 |  54,695.31 |  3,646.26 |       11.79 |          0.79 |  1.00 | 77.61 / 93.98 | -q:v 25                          |
|             |               |    Nature    |      22 | 120,176.71 |  8,012.71 |       11.22 |          0.52 |  1.00 | 85.33 / 94.22 | -q:v 22                          |
|             |               |              |         |            |           |             |               |       |               |                                  |
|             | ICQ           |    Anime     |     *23 |  74,324.41 |  4,955.54 |       11.29 |          0.70 |  0.99 | 79.67 / 90.52 | -global_quality 28               |
|             |               |    Nature    |     *23 |  52,720.14 |  3,514.56 |       12.01 |          0.79 |  0.99 | 75.71 / 93.38 | -global_quality 28               |
|             |               |    Anime     |      27 |  60,482.05 |  4,032.00 |       12.04 |          0.76 |  1.00 | 78.03 / 94.26 | -global_quality 27               |
|             |               |    Nature    |      25 | 110,673.65 |  7,379.10 |        11.4 |          0.56 |  1.00 | 84.82 / 93.58 | -global_quality 25               |
|             |               |              |         |            |           |             |               |       |               |                                  |
|             | LA_ICQ        |    Anime     |     *23 | 104,642.45 |  6,975.94 |       12.18 |          0.59 |  1.00 | 85.20 / 96.74 | -global_quality 23 -look_ahead 1 |
|             |               |    Nature    |     *23 | 142,290.08 |  9,487.11 |       11.48 |          0.43 |  1.00 | 87.05 / 95.04 | -global_quality 23 -look_ahead 1 |
|             |               |    Anime     |      27 |  60,482.05 |  4,032.00 |       12.04 |          0.76 |  1.00 | 78.03 / 94.26 | -global_quality 27 -look_ahead 1 |
|             |               |    Nature    |      25 | 110,673.65 |  7,379.10 |       11.39 |          0.56 |  1.00 | 84.82 / 93.58 | -global_quality 25 -look_ahead 1 |
|             |               |              |         |            |           |             |               |       |               |                                  |
| `hevc_qsv`  |               |              |         |            |           |             |               |       |               | **GOP: 248, -bf 3, -refs 1**     |
|             | CQP (default) |    Anime     |     *28 |  29,635.19 |  1,975.91 |       12.38 |          0.88 |  0.99 | 61.78 / 82.21 | -q:v 28                          |
|             |               |    Nature    |     *28 |  17,267.83 |  1,151.17 |       12.48 |          0.93 |  0.99 | 68.94 / 88.55 | -q:v 28                          |
|             |               |    Anime     |      23 |  39,296.54 |  2,619.70 |       12.51 |          0.85 |  1.00 | 79.27 / 94.23 | -q:v 23                          |
|             |               |    Nature    |      20 | 105,332.47 |  7,022.98 |       12.39 |          0.58 |  1.00 | 84.19 / 93.74 | -q:v 20                          |
|             |               |              |         |            |           |             |               |       |               |                                  |
|             | ICQ           |    Anime     |     *28 |  26,025.18 |  1,734.99 |       13.28 |          0.90 |  0.99 | 76.45 / 92.40 | -global_quality 28               |
|             |               |    Nature    |     *28 |  48,349.48 |  3,223.67 |       13.18 |          0.81 |  0.99 | 72.69 / 87.86 | -global_quality 28               |
|             |               |    Anime     |      26 |  37,815.20 |  2,520.95 |       13.29 |          0.85 |  1.00 | 79.74 / 94.27 | -global_quality 26               |
|             |               |    Nature    |      21 |  98,495.21 |  6,567.11 |       13.21 |          0.61 |  1.00 | 83.24 / 93.08 | -global_quality 21               |
|             |               |              |         |            |           |             |               |       |               |                                  |
| `av1_qsv`   |               |              |         |            |           |             |               |       |               | **GOP: 248, -bf 0, -refs 1**     |
|             | CQP (default) |    Anime     |     *35 | 127,181.15 |  8,478.54 |       12.01 |          0.50 |  1.00 | 87.52 / 97.55 | -q:v 28                          |
|             |               |    Nature    |     *35 | 179,775.76 | 11,986.45 |       11.98 |          0.27 |  1.00 | 89.45 / 95.90 | -q:v 28                          |
|             |               |    Anime     |      78 |  40,589.02 |  2,705.86 |       11.95 |          0.84 |  1.00 | 77.60 / 93.96 | -q:v 78                          |
|             |               |    Nature    |      53 | 110,504.13 |  7,367.80 |       11.94 |          0.56 |  1.00 | 85.23 / 93.58 | -q:v 53                          |
|             |               |              |         |            |           |             |               |       |               |                                  |
|             | ICQ           |    Anime     |     *35 |   9,883.26 |    658.89 |       12.48 |          0.96 |  0.99 | 55.96 / 81.36 | -global_quality 35               |
|             |               |    Nature    |     *35 |  16,930.02 |  1,128.80 |       12.32 |          0.93 |  0.98 | 48.48 / 73.41 | -global_quality 35               |
|             |               |    Anime     |      26 |  46,445.72 |  3,096.28 |       12.70 |          0.82 |  1.00 | 79.17 / 94.34 | -global_quality 26               |
|             |               |    Nature    |      24 | 107,178.63 |  7,146.07 |       12.71 |          0.57 |  1.00 | 84.42 / 93.37 | -global_quality 24               |

## テストの順番

### h264_qsv tests

* CQP / ICQ / LA-ICQ をテスト、設定値を決定
  * LA-ICQ を採用
  * ベースラインから `-global_quality 25 -look_ahead 1` でテストを開始
* 1. フレーム処理と適応型設定
  * **結果:** パラメータを変更しながら、調査したが指定なしが一番良い
  * `adaptive_i`: Iフレームの適応型配置を有効化
  * `adaptive_b`: Bフレームの適応型配置を有効化
  * `b_strategy`: Bフレームの選択戦略を有効化
* 1. 基本設定（プリセットとシナリオ）
  * `-scenario`
    * **結果:** 全く変化なし
* 1. レートコントロールと品質
  * `-look_ahead_depth`: フレーム数での先読みの深さを設定
  * `-look_ahead_downsampling`: 先読み時にダウンスケーリングするか
    * **結果:** 全く変化なし
  * `-rdo`: Bitrate の極端な乱高下を最適化する
    * **結果:** 全く変化なし
  * `min_qp_i`, `max_qp_i`, `min_qp_p`, `max_qp_p`, `min_qp_b`, `max_qp_b`
    * LA-ICQ では自動的に設定されるため、変更しない
* 1. 画質とフィルタ
  * `dblk_idc`: デブロックフィルタ、ブロックノイズを軽減し、画質を改善します。
    * **結果:** 全く変化なし
* 1. GOP, B-Frame, Refs の選定
  * `-bf {2..20} -refs {1..20}` をテストした
    * * **結果:**
      * `-bf 15 -refs 8` を採用する、これによって平均で 12% 容量を削減できる(h264_qsv の場合)
      * 調査では `-bf 2 -refs 9` がもっと画質が良かった
      * `-refs 16` 以上は、品質が落ちる事がわかったので利用しない
      * `libx265` は最大で `-bf 15 -refs 8` であった
    * `-bf {2..20}` は緩やかに圧縮率が改善する
    * `-refs {1..20}`
      * `-refs 15` 以上はどの `-bf` でも品質が落ちる(VMAF min 34 など)

|                   |  File size |   bitrate | encode time | compress_rate | MSSIM |   VMAF min/mean | options                                         |
| :---------------- | ---------: | --------: | ----------: | ------------: | ----: | --------------: | :---------------------------------------------- |
| `h264_qsv` LA-ICQ | 80,026.906 | 5,334.941 |      12.104 |         0.689 | 0.996 | 82.038 / 95.711 | -global_quality 25 -look_ahead 1                |
|                   | 70,052.759 | 4,670.035 |      12.913 |         0.727 | 0.996 | 79.411 / 94.773 | -global_quality 25 -look_ahead 1 -bf 15 -refs 8 |

### hevc_qsv tests

* CQP / ICQ をテスト、設定値を決定
  * ICQ を採用
  * ベースラインから `-global_quality 21` でテストを開始
* 1. GOP サイズ、 B-Frame、参照フレーム数
  * **結果:**
  * `-bf 15 -refs 8` を採用
  * `-g 256` にしても 0.004% しか容量に変化が無いため、デフォルトの `-g 248` を採用する
* 1. Extended BRC と先読みフレーム数
  * `-extbrc 1 -look_ahead_depth {10..100}`
    * **結果:** 変化なし
  * `-rdo`: Bitrate の極端な乱高下を最適化する
    * **結果:** 変化なし
* 1. シナリオ
  * `-scenario`
    * **結果:** 全く変化なし
* 1. 画質とフィルタ
  * `dblk_idc`: デブロックフィルタ、ブロックノイズを軽減し、画質を改善します。
    * **結果:** VMAF min は改善するが VMAF mean が劣化するため、採用しない
* `-b_strategy`,`-adaptive_i`, `adaptive_b` 効果無し
* `-profile main10` やったほうがきれいになる

### av1_qsv tests

* CQP / ICQ をテスト、設定値を決定
  * ICQ を採用
  * ベースラインから `-global_quality 21` でテストを開始
* 1. GOP サイズ、 B-Frame、参照フレーム数
  * 設定しないほうが良い
* `-b_strategy`, `-adaptive_i`, `adaptive_b`
  * **結果:** 全く変化なし
* `-extbrc 1 -look_ahead_depth {10..100}`
  * **結果:** 全く変化なし
* `-profile main10` やったほうがきれいになる
