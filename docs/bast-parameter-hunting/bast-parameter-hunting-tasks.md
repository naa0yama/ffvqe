# エンコーダーパラメータ検証タスク

## 目標

- **VMAF harmonic_mean**: 93.0以上
- **圧縮率**: できるだけ高く
- **処理時間**: 実用的な範囲内
- **対象映像**: Anime (3本), Nature (3本)

---

## コーデック別フレーム構造の理解

### H.264 (AVC) のフレーム構造

**従来型の3フレーム構造**:

- **I-Frame (Intra)**: キーフレーム、単独で復号可能
- **P-Frame (Predicted)**: 前方参照のみ(過去のフレームから予測)
- **B-Frame (Bi-directional)**: 前後両方向から参照(過去と未来のフレームから予測)

```text
I --- P --- B --- B --- P --- B --- B --- I
^     ^     ^     ^     ^     ^     ^     ^
|     |     └─┬───┘     |     └─┬───┘     |
|     └───────┴─────────┘       └─────────┘
```

- **既存データ例**: `I/P/B: 30.0 / 2654.5 / 1380.0` (libx264)
- **`-bf` の意味**: P と P の間に入る B フレームの最大数
- **`-refs` の意味**: 動き推定で参照するフレーム数

### HEVC (H.265) のフレーム構造

**H.264 と基本的に同じだが、より高度**:

- I/P/B の概念は同じ
- **GPB (Generalized P/B Frame)**: P フレームと B フレームを統一的に扱う拡張機能
- B フレームのピラミッド構造がより洗練されている

```text
I --- B --- B --- B --- B --- B --- B --- B --- I
      └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘
        └─────┴─────┴─────┴─────┴─────┘
         (階層的なBフレーム参照構造)
```

**Intel QSV の HEVC エンコーダーの特徴**:

- **GPB モード** (`-gpb 1`, デフォルト): P フレームを全て B フレームとして扱う
  - 既存データ例: `I/P/B: 15.0 / 0.0 / 3582.0` ← **P が 0 なのはこのため**
  - 参照の柔軟性向上、圧縮効率改善
- **従来モード** (`-gpb 0`): P と B を分離

### AV1 のフレーム構造

**I/P/B という概念を使用しない**:

AV1 は従来の I/P/B フレームとは全く異なる設計：

1. **Key Frame**: 独立して復号可能(I-Frame に相当)
2. **Inter Frame**: 他のフレームを参照(P/B に相当するが異なる)
3. **Altref (Alternative Reference) フレーム**: 未来のフレームを事前エンコードして参照に使用

```text
K --- [Altref hidden] --- Inter --- Inter --- Inter --- K
      ↑                   ↓         ↓         ↓
      └───────────────────┴─────────┴─────────┘
```

- **既存データ例**: `I/P/B: 23.0 / 3573.5 / 0.0` (av1_qsv)
- **B-Frame が 0**: これは**正常**(AV1 には B-Frame が存在しない)
- **`-bf` オプション**: **AV1 では無効**(指定しても無視される)
- **Altref フレーム**: エンコーダーが自動的に最適な構造を決定

### コーデック別対応表

| コーデック   | I-Frame |  P-Frame  | B-Frame | 特殊フレーム | `-bf` の効果                  | `-refs` の意味          |
| :----------- | :-----: | :-------: | :-----: | :----------- | :---------------------------- | :---------------------- |
| **H.264**    |    ✓    |     ✓     |    ✓    | -            | P間のBフレーム最大数          | 参照フレーム数          |
| **HEVC**     |    ✓    |     ✓     |    ✓    | GPB          | P間のBフレーム最大数          | 参照フレーム数          |
| **AV1**      | ✓ (Key) | ✓ (Inter) |    ✗    | Altref       | **無効**                      | 参照フレーム数(最大7) |
| **h264_qsv** |    ✓    |     ✓     |    ✓    | -            | P間のBフレーム最大数 (最大16) | 参照フレーム数 (最大16) |
| **hevc_qsv** |    ✓    |     △     |    ✓    | GPB          | Bフレーム制御 (最大15)        | 参照フレーム数          |
| **av1_qsv**  | ✓ (Key) | ✓ (Inter) |    ✗    | Altref       | **無効**                      | 参照フレーム数 (最大7)  |

---

## libx264 - CRF モード

### 基本情報(libx264-basic-info)

- **フレーム構造**: 従来の I/P/B 構造を使用
- **既存フレーム比率**: `I/P/B: 30.0 / 2654.5 / 1380.0`
- **既存ベスト**: `-crf 23 -g 250 -bf 9 -refs 15`

### パラメーター詳細(libx264-parameter-details)

| パラメーター | デフォルト | 最小値 | 最大値 |    推奨範囲     | 説明                                                                              |
| :----------- | :--------: | :----: | :----: | :-------------: | :-------------------------------------------------------------------------------- |
| **-crf**     |     23     |   0    |   51   |      18-28      | 品質パラメーター。低いほど高品質・大容量。±6で約2倍/半分のビットレート            |
| **-g**       |    250     |   1    |   -    |     120-300     | GOP サイズ(キーフレーム間隔)。30fps で 250 = 約8.3秒                            |
| **-bf**      |     3      |   0    |   16   |      2-15       | 連続B-Frameの最大数。多いほど圧縮率向上、処理時間増                               |
| **-refs**    |     3      |   1    |   16   |      4-15       | 参照フレーム数。多いほど画質向上、処理時間増。5以上で効果微減                     |
| **-preset**  |   medium   |   -    |   -    | medium-veryslow | エンコード速度プリセット(ultrafast/veryfast/faster/medium/slow/slower/veryslow) |

**x264-params 高度なパラメーター:**

| パラメーター     | デフォルト |  範囲   | 説明                                                 |
| :--------------- | :--------: | :-----: | :--------------------------------------------------- |
| **trellis**      |     1      |   0-2   | トレリス量子化。2で最高品質、処理時間増              |
| **aq-mode**      |     1      |   0-3   | 適応的量子化モード。2が推奨(分散ベース)            |
| **aq-strength**  |    1.0     | 0.0-3.0 | 適応的量子化強度。1.0-1.2が推奨                      |
| **rc-lookahead** |     40     |  0-250  | レート制御先読みフレーム数。多いほどビット配分最適化 |
| **me**           |    hex     |    -    | 動き推定アルゴリズム(dia/hex/umh/esa/tesa)         |
| **psy-rd**       |  1.0,0.0   | 0.0-2.0 | 心理視覚最適化(RD,RDOQ)                            |

### Phase 1: CRF値探査(libx264-0001-crf)

**範囲**: 18-28

```yaml
outfile:
    base:
        - type: Anime
          option: ""
        - type: Nature
          option: ""
    options:
        - -crf 20
        - -crf 21
        - -crf 22
        - -crf 23
        - -crf 24
        - -crf 25
        - -crf 26
        - -crf 27
        - -crf 28

```

**目的**: VMAF 93前後を達成するCRF値を特定
**結果**:
    - Anime -crf 26
    - Nature -crf 24

### Phase 2: GOP サイズ(libx264-0002-gop)

**範囲**: 120, 150, 180, 210, 240, 250, 270, 300

```yaml
outfile:
    base:
        - type: Anime
          option: -crf 26
        - type: Nature
          option: -crf 24
    options:
        - -g 250
        - -g 270
        - -g 300

```

**目的**: 圧縮率と画質のバランスが良いGOPサイズを特定
**結果**: GOP はシークに依存しデフォルトの 250 でも 8.3秒のため変更しない。 300 との比較は 30kb 程度しかなかった

### Phase 3: B-Frame 数(libx264-0003-bf-refs)

**範囲**: 2, 3, 4, 5, 6, 8, 10, 12, 15

```yaml
# for bf in $(seq 1 16); do for refs in $(seq 1 16); do echo "          - -bf ${bf} -refs ${refs}"; done; done

outfile:
    base:
        - type: Anime
          option: -crf 26
        - type: Nature
          option: -crf 24

    options:
        - -bf {1..16} -refs {1..16}
```

**目的**: 圧縮効率を高めるB-Frame数を特定
**結果**: `-bf 15 -refs 14`

### Phase 4: プリセット(libx264-0005-preset)

**選択肢**: fast, medium, slow, slower, veryslow

```yaml
presets:
    - ultrafast
    - veryfast
    - faster
    - medium
    - slower
    - veryslow

```

**目的**: 処理時間と画質のバランスを確認
**結果**: `medium` が無難、 `veryslow` にすることで 59MB 削減できるが 215 余分にエンコード時間がかかる vmaf も -0.02 程度の劣化になる

### Phase 5: x264opts 高度なオプション(libx264-0006-x264-params)

```yaml
outfile:
  options:
    # AQ最適化
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=1:aq-strength=1.0
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=2:aq-strength=1.0
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=3:aq-strength=1.0
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=2:aq-strength=0.8
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=2:aq-strength=1.2

    # 心理視覚最適化(psy-rdは2つの値をカンマで区切る)
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params psy-rd=0.8,0.0
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params psy-rd=1.0,0.0
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params psy-rd=1.2,0.0
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params psy-rd=1.0,0.15

    # 先読みフレーム数
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params rc-lookahead=40
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params rc-lookahead=60
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params rc-lookahead=80

    # 動き推定
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params me=umh
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params me=esa

    # トレリス量子化
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params trellis=2

    # 複合最適化(複数パラメータはコロンで区切り、psy-rdの値内はカンマ)
    - -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=2:aq-strength=1.0:psy-rd=1.0,0.15:rc-lookahead=60
```

**目的**: 微細な画質改善と圧縮率向上
**結果**: `-x264-params aq-mode=2:aq-strength=1.2` を採用

- `aq-mode=2:aq-strength=1.2`
  - 適応的量子化 (Adaptive Quantization)
  - 複雑度に基づく適応的なビット配分

---

## libx265 - CRF モード

### 基本情報(libx265-basic-info)

- **フレーム構造**: 従来の I/P/B 構造を使用(H.264 より高度)
- **既存ベスト**: `-crf 27 (Anime)`, `-crf 23 (Nature)`

### パラメーター詳細(libx265-parameter-details)

| パラメーター | デフォルト | 最小値 | 最大値 |    推奨範囲     | 説明                                                                              |
| :----------- | :--------: | :----: | :----: | :-------------: | :-------------------------------------------------------------------------------- |
| **-crf**     |     28     |   0    |   51   |      20-32      | 品質パラメーター。x264より約+4が同等品質。±6で約2倍/半分のビットレート            |
| **-g**       |    250     |   1    |   -    |     120-300     | GOP サイズ(キーフレーム間隔)。30fps で 250 = 約8.3秒                            |
| **-bf**      |     4      |   0    |   16   |      2-12       | 連続B-Frameの最大数。多いほど圧縮率向上、処理時間増                               |
| **-refs**    |     1      |   1    |   16   |       1-6       | 参照フレーム数。**HEVC仕様制限: B-pyramid有効時は最大6**                          |
| **-preset**  |   medium   |   -    |   -    | medium-veryslow | エンコード速度プリセット(ultrafast/veryfast/faster/medium/slow/slower/veryslow) |

**HEVC 仕様による refs 制限:**

| 条件                             | 最大 refs 値 | 説明                                     |
| :------------------------------- | :----------: | :--------------------------------------- |
| **B-pyramid 有効(デフォルト)** |    **6**     | 全プリセットでデフォルト有効             |
| B-frames 有効、B-pyramid 無効    |      7       | `no-b-pyramid=1` 指定時                  |
| HEVC 仕様の絶対上限              |      8       | 準拠ストリームの上限                     |
| libx265 ソフトウェア制限         |      16      | `allow-non-conformance=1` で非準拠許可時 |

**重要: refs と bf の制限事項**

```text
エラー例1 (refs 超過):
x265 [warning]: level 5 detected, but NumPocTotalCurr (total references) is non-compliant
x265 [info]: non-conformant bitstreams not allowed (--allow-non-conformance)
[libx265] Cannot open libx265 encoder.

エラー例2 (rc-lookahead 不足):
x265 [error]: Lookahead depth must be greater than the max consecutive bframe count
[libx265] Cannot open libx265 encoder.
```

**refs の制限:**

- **推奨: `-refs 6` 以下**(B-pyramid 有効時、デフォルト)
- `-refs 7` や `-refs 8` を使用する場合は `-x265-params no-b-pyramid=1` が必要(圧縮効率低下のため非推奨)
- `-refs 9` 以上は HEVC 仕様違反のため**必ずエラー**

**bf と rc-lookahead の関係:**

- **必須条件: `rc-lookahead > bf`**
- ultrafast プリセット(rc-lookahead=5): `-bf 4` まで
- veryfast プリセット(rc-lookahead=10): `-bf 9` まで
- medium 以上(rc-lookahead=40): `-bf 39` まで(実用上制限なし)
- 明示的に指定する場合: `-x265-params rc-lookahead=10` (bf より大きい値)

**推奨設定:**

- **高速エンコード**: `-preset veryfast -bf 9 -refs 6`
- **バランス型**: `-preset medium -bf 9 -refs 6`(推奨)
- **高品質**: `-preset slow -bf 9 -refs 6`

**x265-params 高度なパラメーター:**

| パラメーター     | デフォルト |   範囲   | 説明                                                                 |
| :--------------- | :--------: | :------: | :------------------------------------------------------------------- |
| **rc-lookahead** |     40     |  5-250   | レート制御先読みフレーム数。**bf より大きい値が必須**                |
| **b-pyramid**    |    有効    |   0/1    | B-Frameを参照フレームとして使用。デフォルト有効、無効化で refs 最大7 |
| **rd**           |     3      |   0-6    | RD最適化レベル。高いほど品質向上、処理時間増                         |
| **rdoq-level**   |     0      |   0-2    | 量子化RD最適化。2で最高品質                                          |
| **aq-mode**      |     2      |   0-4    | 適応的量子化モード。3が推奨(エッジベース)                          |
| **aq-strength**  |    1.0     | 0.0-3.0  | 適応的量子化強度                                                     |
| **psy-rd**       |    2.0     | 0.0-5.0  | 心理視覚RD最適化                                                     |
| **psy-rdoq**     |    0.0     | 0.0-50.0 | 心理視覚RDOQ最適化                                                   |
| **rect**         |    無効    |   0/1    | 矩形予測ユニット有効化                                               |
| **amp**          |    無効    |   0/1    | 非対称動き予測有効化                                                 |

### Phase 1: CRF値探査(libx265-0001-crf)

**範囲**: 20-32

```yaml
outfile:
    base:
        - type: Anime
          option: ""
        - type: Nature
          option: ""
    options:
        - -crf 20
        - -crf 21
        - -crf 22
        - -crf 23
        - -crf 24
        - -crf 25
        - -crf 26
        - -crf 27
        - -crf 28
        - -crf 29
        - -crf 30
        - -crf 31
        - -crf 32
```

**目的**: VMAF 93前後を達成するCRF値を特定
**結果**:

- Anime `-crf 27`
- Nature `-crf 24`

### Phase 2: B-Frame 数, 参照フレーム数(libx265-0002-bf-refs)

**範囲**: bf 1-16, refs 1-6
**結果**: `-bf 8 -refs 6` がバランスが良い、 `-bf 8-16 -refs 6` は圧縮率は変わらないが実行時間が伸びる傾向
**注意**: B-pyramid 有効時(デフォルト)は **最大 6** まで

```yaml
# for bf in $(seq 1 16); do for refs in $(seq 1 6); do echo "          - -crf 27 -bf ${bf} -refs ${refs}"; done; done

outfile:
    base:
        - type: Anime
          option: -crf 27
        - type: Nature
          option: -crf 24
    options:
    - -bf {1..16} -refs {1..6}

```

### Phase 3: x265-params 高度なオプション(libx265-0003-x265-params)

無指定か `-x265-params psy-rd=1.5:psy-rdoq=0.0` が良い。ファイルサイズはデフォルトと比較で 2% しか変わらない

```yaml
outfile:
  options:
    # AQ最適化
    - -x265-params aq-mode=1:aq-strength=1.0
    - -x265-params aq-mode=2:aq-strength=1.0
    - -x265-params aq-mode=3:aq-strength=1.0
    - -x265-params aq-mode=4:aq-strength=1.0
    - -bf [最適値] -refs [最適値] -x265-params aq-mode=1:aq-strength=1.0
    - -bf [最適値] -refs [最適値] -x265-params aq-mode=2:aq-strength=1.0
    - -bf [最適値] -refs [最適値] -x265-params aq-mode=3:aq-strength=1.0
    - -bf [最適値] -refs [最適値] -x265-params aq-mode=4:aq-strength=1.0

    # 心理視覚最適化
    - -x265-params psy-rd=1.5:psy-rdoq=0.0
    - -x265-params psy-rd=2.0:psy-rdoq=0.0
    - -x265-params psy-rd=2.5:psy-rdoq=0.0
    - -x265-params psy-rd=2.0:psy-rdoq=1.0
    - -bf [最適値] -refs [最適値] -x265-params psy-rd=1.5:psy-rdoq=0.0
    - -bf [最適値] -refs [最適値] -x265-params psy-rd=2.0:psy-rdoq=0.0
    - -bf [最適値] -refs [最適値] -x265-params psy-rd=2.5:psy-rdoq=0.0
    - -bf [最適値] -refs [最適値] -x265-params psy-rd=2.0:psy-rdoq=1.0

    # RD最適化
    - -x265-params rd=3
    - -x265-params rd=4
    - -x265-params rd=5
    - -x265-params rd=6
    - -bf [最適値] -refs [最適値] -x265-params rd=3
    - -bf [最適値] -refs [最適値] -x265-params rd=4
    - -bf [最適値] -refs [最適値] -x265-params rd=5
    - -bf [最適値] -refs [最適値] -x265-params rd=6

    # RDOQ
    - -x265-params rdoq-level=1
    - -x265-params rdoq-level=2
    - -bf [最適値] -refs [最適値] -x265-params rdoq-level=1
    - -bf [最適値] -refs [最適値] -x265-params rdoq-level=2

    # 予測モード
    - -x265-params rect=1
    - -x265-params amp=1
    - -x265-params rect=1:amp=1
    - -bf [最適値] -refs [最適値] -x265-params rect=1
    - -bf [最適値] -refs [最適値] -x265-params amp=1
    - -bf [最適値] -refs [最適値] -x265-params rect=1:amp=1

    # 複合最適化
    - -x265-params aq-mode=3:aq-strength=1.0:psy-rd=2.0:psy-rdoq=1.0:rd=4:rdoq-level=2
    - -bf [最適値] -refs [最適値] -x265-params aq-mode=3:aq-strength=1.0:psy-rd=2.0:psy-rdoq=1.0:rd=4:rdoq-level=2
```

`-x265-params aq-mode=3:aq-strength=1.0:psy-rd=2.0:psy-rdoq=1.0:rd=4:rdoq-level=2` が良い結果

## libsvtav1 - CRF モード

### 基本情報(libsvtav1-basic-info)

- **フレーム構造**: AV1独自の構造(I/P/B ではなく Key/Inter + Altref)
- **既存フレーム比率**: `I/P/B: 23.0 / 3574.0 / 0.0` ← **B-Frame は存在しない**
- **既存ベスト**: `-crf 31`, `-crf 35`
- **重要**: `-bf` オプションは**無効**(AV1 には B-Frame が存在しない)

### パラメーター詳細(libsvtav1-parameter-details)

| パラメーター | デフォルト | 最小値 | 最大値 | 推奨範囲 | 説明                                                           |
| :----------- | :--------: | :----: | :----: | :------: | :------------------------------------------------------------- |
| **-crf**     |     35     |   0    |   63   |  25-40   | 品質パラメーター。x264/x265より値域が広く、約+10が同等品質     |
| **-preset**  |     5      |   0    |   13   |   4-6    | エンコード速度プリセット。**低いほど高品質・低速**(x264と逆) |
| **-g**       |    自動    |   1    |   -    | 120-300  | GOP サイズ(キーフレーム間隔)。指定なしで自動最適化           |
| **-bf**      |    N/A     |   -    |   -    |    -     | **AV1には存在しない**。指定しても無視される                    |
| **-refs**    |     1      |   1    |   7    |   1-7    | 参照フレーム数。AV1仕様では最大7                               |

**プリセット特性(数値が小さいほど高品質):**

|  Preset   | 特性                   | 推奨用途                     |
| :-------: | :--------------------- | :--------------------------- |
|  **0-2**  | 最高品質、非常に低速   | アーカイブ、最終配信マスター |
|  **3-4**  | 高品質、低速           | 高品質配信                   |
|  **5-6**  | バランス型(推奨)     | 一般的な配信                 |
|  **7-9**  | 高速、品質低下         | リアルタイムエンコード       |
| **10-13** | 最高速、大幅な品質低下 | テスト用途のみ               |

**svtav1-params 高度なパラメーター:**

| パラメーター            | デフォルト | 範囲  | 説明                                       |
| :---------------------- | :--------: | :---: | :----------------------------------------- |
| **tune**                |     1      |  0-2  | チューニングモード(0:VQ, 1:PSNR, 2:SSIM) |
| **hierarchical-levels** |     4      |  3-5  | Altref階層レベル。高いほど圧縮効率向上     |
| **film-grain**          |     0      | 0-50  | フィルムグレイン合成強度                   |
| **film-grain-denoise**  |     0      |  0/1  | フィルムグレイン＋ノイズ除去               |
| **enable-qm**           |     0      |  0/1  | 量子化マトリックス有効化                   |
| **qm-min**              |     8      | 0-15  | 量子化マトリックス最小値                   |
| **qm-max**              |     15     | 0-15  | 量子化マトリックス最大値                   |
| **enable-dlf**          |     1      |  0-2  | デブロッキングループフィルター             |
| **cdef-level**          |     -1     | -1-5  | CDEF(制約付き方向性強調フィルター)レベル |
| **enable-restoration**  |     1      |  0/1  | ループ復元フィルター                       |
| **tile-rows**           |     0      |  0-6  | タイル行数(並列処理)                     |
| **tile-columns**        |     0      |  0-6  | タイル列数(並列処理)                     |

### Phase 1: CRF値探査(libsvtav1-0001-crf)

**範囲**: 25-45
**結果**:

Anime: `-crf 43`
Nature: `-crf 32`

```yaml
outfile:
    base:
        - type: Anime
          option: ""
        - type: Nature
          option: ""
    options:
        - -crf {25..45}

```

**目的**: VMAF 93前後を達成するCRF値を特定

### Phase 2: GOP サイズ(libsvtav1-0002-gop)

**範囲**: 120, 150, 180, 210, 240, 270, 300
**結果**: `-g 270`

```yaml
outfile:
  options:
    - -g 120
    - -g 150
    - -g 180
    - -g 210
    - -g 240
    - -g 270
    - -g 300
```

### Phase 3: 参照フレーム数(libsvtav1-0003-refs)

**範囲**: 1-7
**結果**: どの値を設定しても score が変わらないため無指定の方がよい

```yaml
outfile:
  options:
    - -refs 1
    - -refs 2
    - -refs 3
    - -refs 4
    - -refs 5
    - -refs 6
    - -refs 7
```

### Phase 4: プリセット(libsvtav1-0004-preset)

**範囲**: 3, 4, 5, 6, 7, 8, 9 (低いほど高品質だが処理時間増)
**結果**: `-preset 6` が最適

```yaml
    presets:
    - '1'
    - '2'
    - '3'
    - '4'
    - '5'
    - '6'
    - '7'
    - '8'
    - '9'
    - '10'
    infile:
        option: ''
```

**目的**: 処理時間と画質のバランスを確認

### Phase 5: svtav1-params 高度なオプション(libsvtav1-0005-svtav1-params)

```yaml
outfile:
  options:
    # チューニングモード
    - -svtav1-params tune=0
    - -svtav1-params tune=1
    - -svtav1-params tune=2

    # 階層的予測レベル(Altref制御)
    - -svtav1-params hierarchical-levels=3
    - -svtav1-params hierarchical-levels=4
    - -svtav1-params hierarchical-levels=5

    # フィルムグレイン
    - -svtav1-params film-grain=10
    - -svtav1-params film-grain=20
    - -svtav1-params film-grain=30
    - -svtav1-params film-grain-denoise=1

    # 量子化マトリックス
    - -svtav1-params enable-qm=1:qm-min=0:qm-max=15
    - -svtav1-params enable-qm=1:qm-min=0:qm-max=10
    - -svtav1-params enable-qm=1:qm-min=5:qm-max=15

    # フィルタ設定
    - -svtav1-params enable-dlf=2
    - -svtav1-params cdef-level=0
    - -svtav1-params cdef-level=3
    - -svtav1-params cdef-level=5
    - -svtav1-params enable-restoration=0
    - -svtav1-params enable-restoration=1

    # タイル設定(並列処理)
    - -svtav1-params tile-rows=1:tile-columns=1
    - -svtav1-params tile-rows=2:tile-columns=2

    # 複合最適化
    - -svtav1-params tune=0:hierarchical-levels=4:enable-qm=1:qm-min=0:qm-max=15:enable-dlf=2:cdef-level=5

```

**目的**: Altref フレームと階層的予測の最適化
**結果**: `-svtav1-params enable-qm=1:qm-min=0:qm-max=10` がベスト `-svtav1-params tune=2` が score 的には良いが、 vmaf_min が 4pt 低く filesize も 2% しか変わらないのでバランスを見て上記がよい

## h264_qsv - CQP モード

### 基本情報(h264-qsv-cqp-basic-info)

- **フレーム構造**: 従来の I/P/B 構造を使用
- **既存フレーム比率**: `I/P/B: 15.0 / 225.0 / 3357.0` ← **B-Frame が約90%**
- **既存ベスト**: `-q:v 22 -bf 15 -refs 8`
- **ソースコード**: `libavcodec/qsvenc_h264.c`

### パラメーター詳細(h264-qsv-cqp-parameter-details)

| パラメーター | デフォルト | 最小値 | 最大値 |      推奨範囲      | Intel SDK    | 説明                                                  |
| :----------- | :--------: | :----: | :----: | :----------------: | :----------- | :---------------------------------------------------- |
| **-q:v**     |     -      |   0    |   51   |       18-28        | QPI/QPP/QPB  | CQP(固定QP)。低いほど高品質。I/P/Bで自動調整される  |
| **-g**       |     -1     |   1    |   -    |      120-300       | GopPicSize   | GOP サイズ(キーフレーム間隔)                        |
| **-bf**      |     -1     |   0    |   16   |        8-16        | GopRefDist-1 | 連続B-Frameの最大数。**QSVでは処理時間変わらず**      |
| **-refs**    |     0      |   0    |   16   |        4-16        | NumRefFrame  | 参照フレーム数。**QSVでは処理時間変わらず**           |
| **-preset**  |   medium   |   1    |   7    |    veryslow推奨    | TargetUsage  | エンコード速度プリセット。**QSVでは処理時間ほぼ同じ** |
| **-profile** |    high    |   -    |   -    | baseline/main/high | CodecProfile | baseline(66), main(77), high(100)                     |

**QP値の自動調整(CQPモード):**

| フレームタイプ | QP計算式                             | デフォルトオフセット |
| :------------- | :----------------------------------- | :------------------: |
| **I-Frame**    | `q:v × 0.8` (0-51にクリップ)         |          0           |
| **P-Frame**    | `q:v` (0-51にクリップ)               |          +2          |
| **B-Frame**    | `q:v × 1.25 + 1.25` (0-51にクリップ) |          +4          |

**QSV 高度なパラメーター:**

| パラメーター                | デフォルト | 範囲  | Intel SDK            | 説明                                                     |
| :-------------------------- | :--------: | :---: | :------------------- | :------------------------------------------------------- |
| **adaptive_i**              |     0      |  0/1  | AdaptiveI            | アダプティブI-Frame配置                                  |
| **adaptive_b**              |     0      |  0/1  | AdaptiveB            | アダプティブB-Frame配置                                  |
| **b_strategy**              |     0      |  0/1  | BRefType             | B-Frame戦略最適化                                        |
| **rdo**                     |     0      |  0/1  | RateDistortionOpt    | Rate Distortion最適化                                    |
| **scenario**                |     0      |  0-8  | ScenarioInfo         | シナリオヒント(0:default, 3:gaming, 4:remote-gaming)   |
| **mbbrc**                   |     0      |  0/1  | MBBRC                | マクロブロックレベルBRC                                  |
| **cavlc**                   |     0      |  0/1  | CAVLC                | CAVLC有効(デフォルトはCABAC)                           |
| **idr_interval**            |     0      |  0-   | IdrInterval          | IDR間隔                                                  |
| **dblk_idc**                |     0      |  0-2  | DisableDeblockingIdc | デブロッキング無効(0:有効, 1:無効, 2:スライス境界無効) |
| **max_dec_frame_buffering** |     0      | 0-16  | MaxDecFrameBuffering | DPBサイズ                                                |
| **aud**                     |     0      |  0/1  | AUD                  | Access Unit Delimiter挿入                                |
| **repeat_pps**              |     0      |  0/1  | RepeatPPS            | PPS繰り返し                                              |

**Look-ahead パラメーター(LA-ICQモード用):**

| パラメーター                | デフォルト |      範囲      | Intel SDK      | 説明                             |
| :-------------------------- | :--------: | :------------: | :------------- | :------------------------------- |
| **look_ahead**              |     0      |      0/1       | LookAhead      | Look-ahead有効化(h264_qsv専用) |
| **look_ahead_depth**        |     0      |     0-100      | LookAheadDepth | 先読みフレーム数                 |
| **look_ahead_downsampling** |    auto    | auto/off/2x/4x | LookAheadDS    | 先読み時のダウンサンプリング     |

### Phase 1: QP値探査(h264-qsv-cqp-0001-qp)

**範囲**: 18-28

```yaml
outfile:
    base:
        - type: Anime
          option: ""
        - type: Nature
          option: ""
    options:
    - -q:v 18
    - -q:v 19
    - -q:v 20
    - -q:v 21
    - -q:v 22
    - -q:v 23
    - -q:v 24
    - -q:v 25
    - -q:v 26
    - -q:v 27
    - -q:v 28
```

**目的**: VMAF 93前後を達成するQP値を特定
**結果**: Anime `-q:v 26`, Natrue `-q:v 22` を採用

### Phase 2: B-Frame、参照フレーム数(h264-qsv-cqp-0002-bf-refs)

```yaml
# for bf in $(seq 1 16); do for refs in $(seq 1 16); do echo "          - -q:v 27 -bf ${bf} -refs ${refs}"; done; done

outfile:
    base:
        - type: Anime
        option: '-q:v 26'
        - type: Nature
        option: '-q:v 22'
    options:
        - -bf 1 -refs 1
        - -bf 16 -refs 16
```

**HWEnc特性**: 処理時間は変わらないため最大値まで試す
**結果**: `-bf 4 -refs 7` が最適

### Phase 3: QSV高度なオプション(h264-qsv-cqp-0003-qsv-params)

```yaml
outfile:
  options:
    # アダプティブフレーム配置
    - -bf [最適値] -refs [最適値] -adaptive_i 1
    - -bf [最適値] -refs [最適値] -adaptive_b 1
    - -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1

    # B-Frame戦略
    - -bf [最適値] -refs [最適値] -b_strategy 1

    # RDO
    - -bf [最適値] -refs [最適値] -rdo 1

    # シナリオヒント
    - -bf [最適値] -refs [最適値] -scenario 3
    - -bf [最適値] -refs [最適値] -scenario 4

    # 複合最適化
    - -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1 -b_strategy 1 -rdo 1
```

**結果**: 付けないほうが良い

---

## h264_qsv - ICQ モード

### 基本情報(h264-qsv-icq-basic-info)

- **フレーム構造**: 従来の I/P/B 構造を使用
- **既存ベスト**: `-global_quality 25 -bf 15 -refs 8`
- **ソースコード**: `libavcodec/qsvenc_h264.c`
- **対応Profile**: baseline(66), main(77), high(100)
- **対応Preset**: veryslow(1) ~ veryfast(7)

### パラメーター詳細(h264-qsv-icq-parameter-details)

| パラメーター        | デフォルト | 最小値 | 最大値 |      推奨範囲      | Intel SDK    | 説明                                                    |
| :------------------ | :--------: | :----: | :----: | :----------------: | :----------- | :------------------------------------------------------ |
| **-global_quality** |     -      |   1    |   51   |       20-32        | ICQQuality   | ICQ品質値。低いほど高品質。フレーム間で品質を一定に保つ |
| **-g**              |     -1     |   1    |   -    |      120-300       | GopPicSize   | GOP サイズ(キーフレーム間隔)                          |
| **-bf**             |     -1     |   0    |   16   |        8-16        | GopRefDist-1 | 連続B-Frameの最大数。**QSVでは処理時間変わらず**        |
| **-refs**           |     0      |   0    |   16   |        4-16        | NumRefFrame  | 参照フレーム数。**QSVでは処理時間変わらず**             |
| **-preset**         |   medium   |   1    |   7    |    veryslow推奨    | TargetUsage  | エンコード速度プリセット。**QSVでは処理時間ほぼ同じ**   |
| **-profile**        |    high    |   -    |   -    | baseline/main/high | CodecProfile | baseline(66), main(77), high(100)                       |

**ICQ vs CQP:**

| モード  | 特徴                     | ビットレート変動 | 品質             | 推奨用途           |
| :------ | :----------------------- | :--------------: | :--------------- | :----------------- |
| **CQP** | 固定QP                   |      大きい      | フレーム間で変動 | テスト、比較用     |
| **ICQ** | インテリジェント品質制御 |      中程度      | フレーム間で一定 | **推奨：一般配信** |

**QSV 高度なパラメーター:**

| パラメーター     | デフォルト | 範囲  | Intel SDK            | 説明                              |
| :--------------- | :--------: | :---: | :------------------- | :-------------------------------- |
| **mbbrc**        |     0      |  0/1  | MBBRC                | マクロブロックレベルBRC。品質向上 |
| **adaptive_i**   |     0      |  0/1  | AdaptiveI            | アダプティブI-Frame配置           |
| **adaptive_b**   |     0      |  0/1  | AdaptiveB            | アダプティブB-Frame配置           |
| **b_strategy**   |     0      |  0/1  | BRefType             | B-Frame戦略最適化                 |
| **rdo**          |     0      |  0/1  | RateDistortionOpt    | Rate Distortion最適化             |
| **scenario**     |     0      |  0-8  | ScenarioInfo         | シナリオヒント                    |
| **cavlc**        |     0      |  0/1  | CAVLC                | CAVLC有効(デフォルトはCABAC)    |
| **idr_interval** |     0      |  0-   | IdrInterval          | IDR間隔                           |
| **dblk_idc**     |     0      |  0-2  | DisableDeblockingIdc | デブロッキング無効                |

### Phase 1: Quality値探査(h264-qsv-icq-0001-quality)

**範囲**: 20-32

```yaml
    outfile:
        base:
            - type: Anime
              option: ""
            - type: Nature
              option: ""
    options:
        - -global_quality 20
        - -global_quality 21
        - -global_quality 22
        - -global_quality 23
        - -global_quality 24
        - -global_quality 25
        - -global_quality 26
        - -global_quality 27
        - -global_quality 28
        - -global_quality 29
        - -global_quality 30
        - -global_quality 31
        - -global_quality 32
```

**目的**: VMAF 93前後を達成するQuality値を特定
**結果**: Anime `-global_quality 29`, Natrue `-global_quality 26`

### Phase 2: B-Frame, refs (h264-qsv-icq-0002-bf-refs)

```yaml
outfile:
    base:
        - type: Anime
          option: -global_quality 29
        - type: Nature
          option: -global_quality 26
    options:
        - -bf {1..16} -refs {1..16}

```

**結果**: `-bf 4 -refs 15` がバランスが良い

### Phase 3: QSV高度なオプション(h264-qsv-icq-0003-qsv-params)

```yaml
outfile:
  options:
    # MBBRC(マクロブロックレベルBRC)
    - -bf [最適値] -refs [最適値] -mbbrc 1

    # アダプティブフレーム配置
    - -bf [最適値] -refs [最適値] -adaptive_i 1
    - -bf [最適値] -refs [最適値] -adaptive_b 1
    - -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1

    # RDO
    - -bf [最適値] -refs [最適値] -rdo 1

    # 複合最適化
    - -bf [最適値] -refs [最適値] -mbbrc 1 -adaptive_i 1 -adaptive_b 1 -rdo 1
```

**結果**: `-adaptive_i 1 -adaptive_b 1` がよい

---

## h264_qsv - LA-ICQ モード

### 基本情報(h264-qsv-la-icq-basic-info)

- **フレーム構造**: 従来の I/P/B 構造を使用
- **既存ベスト**: `-global_quality 25 -look_ahead 1 -bf 15 -refs 8`
- **ソースコード**: `libavcodec/qsvenc_h264.c`
- **対応Profile**: baseline(66), main(77), high(100)
- **対応Preset**: veryslow(1) ~ veryfast(7)
- **特徴**: Look-ahead機能はh264_qsv専用(hevc_qsv/av1_qsvでは非対応)

### パラメーター詳細(h264-qsv-la-icq-parameter-details)

| パラメーター                 | デフォルト | 最小値 | 最大値 |      推奨範囲      | Intel SDK      | 説明                                             |
| :--------------------------- | :--------: | :----: | :----: | :----------------: | :------------- | :----------------------------------------------- |
| **-global_quality**          |     -      |   1    |   51   |       20-32        | ICQQuality     | LA-ICQ品質値。低いほど高品質                     |
| **-look_ahead**              |     0      |   0    |   1    |         1          | LookAhead      | Look-ahead有効化。**LA-ICQには必須**             |
| **-look_ahead_depth**        |     0      |   0    |  100   |       40-100       | LookAheadDepth | 先読みフレーム数。多いほどビット配分最適化       |
| **-look_ahead_downsampling** |    auto    |   -    |   -    |   auto/off/2x/4x   | LookAheadDS    | 先読み時のダウンサンプリング                     |
| **-g**                       |     -1     |   1    |   -    |      120-300       | GopPicSize     | GOP サイズ(キーフレーム間隔)                   |
| **-bf**                      |     -1     |   0    |   16   |        8-16        | GopRefDist-1   | 連続B-Frameの最大数。**QSVでは処理時間変わらず** |
| **-refs**                    |     0      |   0    |   16   |        4-16        | NumRefFrame    | 参照フレーム数。**QSVでは処理時間変わらず**      |
| **-preset**                  |   medium   |   1    |   7    |    veryslow推奨    | TargetUsage    | エンコード速度プリセット                         |
| **-profile**                 |    high    |   -    |   -    | baseline/main/high | CodecProfile   | baseline(66), main(77), high(100)                |

**モード比較:**

| モード     | Look-ahead | 特徴             | ビット配分 | 品質   | 推奨用途             |
| :--------- | :--------: | :--------------- | :--------: | :----- | :------------------- |
| **CQP**    |     ✗      | 固定QP           |     ✗      | 変動大 | テスト用             |
| **ICQ**    |     ✗      | 品質一定制御     |     ○      | 一定   | 一般配信             |
| **LA-ICQ** |     ✓      | 先読み＋品質制御 |     ◎      | 最適   | **推奨：高品質配信** |

**QSV 高度なパラメーター:**

| パラメーター   | デフォルト | 範囲  | Intel SDK         | 説明                           |
| :------------- | :--------: | :---: | :---------------- | :----------------------------- |
| **adaptive_i** |     0      |  0/1  | AdaptiveI         | アダプティブI-Frame配置        |
| **adaptive_b** |     0      |  0/1  | AdaptiveB         | アダプティブB-Frame配置        |
| **b_strategy** |     0      |  0/1  | BRefType          | B-Frame戦略最適化              |
| **rdo**        |     0      |  0/1  | RateDistortionOpt | Rate Distortion最適化          |
| **mbbrc**      |     0      |  0/1  | MBBRC             | マクロブロックレベルBRC        |
| **scenario**   |     0      |  0-8  | ScenarioInfo      | シナリオヒント                 |
| **cavlc**      |     0      |  0/1  | CAVLC             | CAVLC有効(デフォルトはCABAC) |

### Phase 1: Quality値探査(h264-qsv-la-icq-0001-quality)

**範囲**: 20-32

```yaml
outfile:
    base:
        - type: Anime
          option: ""
        - type: Nature
          option: ""
  options:
    - -global_quality 20 -look_ahead 1
    - -global_quality 21 -look_ahead 1
    - -global_quality 22 -look_ahead 1
    - -global_quality 23 -look_ahead 1
    - -global_quality 24 -look_ahead 1
    - -global_quality 25 -look_ahead 1
    - -global_quality 26 -look_ahead 1
    - -global_quality 27 -look_ahead 1
    - -global_quality 28 -look_ahead 1
    - -global_quality 29 -look_ahead 1
    - -global_quality 30 -look_ahead 1
    - -global_quality 31 -look_ahead 1
    - -global_quality 32 -look_ahead 1
```

**目的**: VMAF 93前後を達成するQuality値を特定

### Phase 2: Look-ahead Depth(h264-qsv-la-icq-0002-la-depth)

**範囲**: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100

```yaml
outfile:
    base:
        - type: Anime
          option: -global_quality 29 -look_ahead 1
        - type: Nature
          option: -global_quality 26 -look_ahead 1
    options:
        - -look_ahead_depth 10
        - -look_ahead_depth 20
        - -look_ahead_depth 30
        - -look_ahead_depth 40
        - -look_ahead_depth 50
        - -look_ahead_depth 60
        - -look_ahead_depth 70
        - -look_ahead_depth 80
        - -look_ahead_depth 90
        - -look_ahead_depth 100
```

**目的**: 先読みフレーム数と画質の関係を確認
**結果**: 効果なし preset で設定済み?

### Phase 3: B-Frame 数(最大負荷テスト)(h264-qsv-la-icq-0003-bf-refs)

**範囲**: 4, 6, 8, 10, 12, 14, 16

```yaml
# for bf in $(seq 1 16); do for refs in $(seq 1 16); do echo "          - -bf ${bf} -refs ${refs}"; done; done

outfile:
    base:
        - type: Anime
          option: -global_quality 29 -look_ahead 1
        - type: Nature
          option: -global_quality 26 -look_ahead 1
    options:
        - -bf {1..16} -refs {1..16}

```

**結果**: `-bf 4 -refs 8`

### Phase 4: QSV高度なオプション(h264-qsv-la-icq-0004-qsv-params)

```yaml
outfile:
  options:
    # アダプティブフレーム配置
    - -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1
    - -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -adaptive_b 1
    - -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1

    # RDO
    - -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -rdo 1

    # 複合最適化
    - -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1 -rdo 1
```

**結果**: `-bf 4 -refs 8 -adaptive_b 1`

---

## hevc_qsv - CQP モード

### 基本情報(hevc-qsv-cqp-basic-info)

- **ソースコード**: `libavcodec/qsvenc_hevc.c`
- **対応Profile**: main(1), main10(2), mainsp(3), rext(4), scc(9)
- **対応Preset**: veryslow(1) ~ veryfast(7)
- **フレーム構造**: GPB モード使用(P-Frame を B-Frame として扱う)
- **既存フレーム比率**: `I/P/B: 15.0 / 0.0 / 3582.0` ← **P が 0 = GPB モード**
- **既存ベスト**: `-q:v 20 -bf 15 -refs 8 -vf vpp_qsv=format=p010le`
- **特徴**: hevc_qsvはh264_qsvのlook_ahead非対応。look_ahead_depthはextbrc=1時のみ有効

### パラメーター詳細(hevc-qsv-cqp-parameter-details)

| パラメーター                  | デフォルト | 最小値 | 最大値 |  推奨範囲   | Intel SDK    | 説明                                            |
| :---------------------------- | :--------: | :----: | :----: | :---------: | :----------- | :---------------------------------------------- |
| **-q:v**                      |     -      |   0    |   51   |    18-28    | QPI/QPP/QPB  | CQP(固定QP)。低いほど高品質                   |
| **-gpb**                      |     1      |   0    |   1    |    1推奨    | GPB          | GPBモード。1でP-FrameをB-Frameとして扱う        |
| **-vf vpp_qsv=format=p010le** |     -      |   -    |   -    |    推奨     | -            | 10bit エンコード。画質向上、ファイルサイズ微増  |
| **-profile**                  |    main    |   -    |   -    | main/main10 | CodecProfile | main(1), main10(2), mainsp(3), rext(4), scc(9)  |
| **-tier**                     |    main    |   -    |   -    |  main/high  | Tier         | HEVCティア                                      |
| **-g**                        |    248     |   1    |   -    |   120-300   | GopPicSize   | GOP サイズ(キーフレーム間隔)                  |
| **-bf**                       |     -1     |   0    | **15** |    8-15     | GopRefDist-1 | 連続B-Frameの最大数。**最大15**(h264_qsvは16) |
| **-refs**                     |     0      |   0    |   16   |    4-12     | NumRefFrame  | 参照フレーム数。**QSVでは処理時間変わらず**     |

**GPB モードの効果:**

|  GPB  | P-Frame | B-Frame | 特徴                       | 圧縮効率 | 推奨  |
| :---: | :-----: | :-----: | :------------------------- | :------: | :---: |
| **1** |    0    |  多い   | P-FrameをB-Frameとして扱う |   高い   |   ◎   |
| **0** |  有り   |  有り   | 従来のP/B分離              |   標準   |   -   |

**QSV 高度なパラメーター:**

| パラメーター       | デフォルト | 範囲  | Intel SDK            | 説明                                       |
| :----------------- | :--------: | :---: | :------------------- | :----------------------------------------- |
| **tile_cols**      |     0      |  0-   | NumTileCols          | タイル列数(並列処理)                     |
| **tile_rows**      |     0      |  0-   | NumTileRows          | タイル行数(並列処理)                     |
| **rdo**            |     0      |  0/1  | RateDistortionOpt    | Rate Distortion最適化                      |
| **transform_skip** |     0      |  0/1  | TransformSkip        | 変換スキップモード有効化                   |
| **adaptive_i**     |     0      |  0/1  | AdaptiveI            | アダプティブI-Frame配置                    |
| **adaptive_b**     |     0      |  0/1  | AdaptiveB            | アダプティブB-Frame配置                    |
| **p_strategy**     |     0      |  0-2  | PRefType             | P-pyramid (0:default, 1:simple, 2:pyramid) |
| **b_strategy**     |     0      |  0/1  | BRefType             | B-Frame戦略                                |
| **dblk_idc**       |     0      |  0-2  | DisableDeblockingIdc | デブロッキング無効                         |
| **idr_interval**   |     0      |  0-   | IdrInterval          | IDR間隔                                    |
| **aud**            |     0      |  0/1  | AUD                  | Access Unit Delimiter挿入                  |
| **pic_timing_sei** |     0      |  0/1  | PicTimingSEI         | タイミングSEI挿入                          |

**Extended BRC パラメーター(ICQモード用):**

| パラメーター         | デフォルト | 範囲  | Intel SDK      | 説明                                 |
| :------------------- | :--------: | :---: | :------------- | :----------------------------------- |
| **extbrc**           |     0      |  0/1  | ExtBRC         | 拡張BRC有効化                        |
| **look_ahead_depth** |     0      | 0-100 | LookAheadDepth | 先読みフレーム数(extbrc時のみ有効) |
| **mbbrc**            |     0      |  0/1  | MBBRC          | マクロブロックレベルBRC              |

### Phase 1: QP値探査(hevc-qsv-cqp-0001-qp)

**範囲**: 18-28

```yaml
outfile:
  options:
    - -q:v 18
    - -q:v 19
    - -q:v 20
    - -q:v 21
    - -q:v 22
    - -q:v 23
    - -q:v 24
    - -q:v 25
    - -q:v 26
    - -q:v 27
    - -q:v 28
```

**目的**: VMAF 93前後を達成するQP値を特定
**結果**: Anime `-q:v 25`, Nature `-q:v 21`

### Phase 2: GPB モードの比較(hevc-qsv-cqp-0002-gpb)

```yaml
outfile:
  options:
    # GPBモード無効(従来のP/B分離)
    - -gpb 0

    # GPBモード有効(デフォルト、Pを全てBとして扱う)
    - -gpb 1
```

**目的**: GPB モードの圧縮効率と画質への影響を確認
**結果**: `-gpb 1` の方が良い

**予想される結果**:

- `-gpb 0`: P-Frame と B-Frame が分離される
- `-gpb 1`: P-Frame = 0, B-Frame が増える(既存データと一致)

### Phase 3: 10bit対応テスト(hevc-qsv-cqp-0003-10bit)

```yaml
outfile:
  options:
    - -vf vpp_qsv=format=p010le
```

**目的**: 10bit エンコードの画質向上効果を確認
**結果**: 10bit は測定出来ず

### Phase 4: B-Frame 数(最大負荷テスト)(hevc-qsv-cqp-0004-bf-refs)

**範囲**: 8, 10, 12, 14, 15

```yaml
# for bf in $(seq 1 16); do for refs in $(seq 1 16); do echo "          - -bf ${bf} -refs ${refs}"; done; done

outfile:
    base:
        - type: Anime
          option: -global_quality 29 -look_ahead 1
        - type: Nature
          option: -global_quality 26 -look_ahead 1
    options:
        - -bf {1..16} -refs {1..16}

```

**結果**: `-bf 6 -refs 3`

### Phase 5: QSV高度なオプション(hevc-qsv-cqp-0005-qsv-params)

```yaml
outfile:
  options:
    # タイル設定
    - -bf [最適値] -refs [最適値] -tile_cols 2
    - -bf [最適値] -refs [最適値] -tile_rows 2
    - -bf [最適値] -refs [最適値] -tile_cols 2 -tile_rows 2

    # RDO
    - -bf [最適値] -refs [最適値] -rdo 1

    # 変換スキップ
    - -bf [最適値] -refs [最適値] -transform_skip 1

    # 複合最適化
    - -bf [最適値] -refs [最適値] -rdo 1 -transform_skip 1
```

**結果**: `-bf 6 -refs 3` のみでよい

---

## hevc_qsv - ICQ モード

### 基本情報(hevcqsv-icq-basic-info)

- **ソースコード**: `libavcodec/qsvenc_hevc.c`
- **対応Profile**: main(1), main10(2), mainsp(3), rext(4), scc(9)
- **対応Preset**: veryslow(1) ~ veryfast(7)
- **フレーム構造**: GPB モード使用(P-Frame を B-Frame として扱う)
- **既存フレーム比率**: `I/P/B: 15.0 / 0.0 / 3582.0` ← **P が 0 = GPB モード**
- **既存ベスト**: `-global_quality 21 -bf 15 -refs 8 -vf vpp_qsv=format=p010le`
- **特徴**: hevc_qsvはh264_qsvのlook_ahead非対応。look_ahead_depthはextbrc=1時のみ有効

### パラメーター詳細(hevc-qsv-icq-parameter-details)

| パラメーター                  | デフォルト | 最小値 | 最大値 |  推奨範囲   | Intel SDK    | 説明                                           |
| :---------------------------- | :--------: | :----: | :----: | :---------: | :----------- | :--------------------------------------------- |
| **-global_quality**           |     -      |   1    |   51   |    18-28    | ICQQuality   | ICQ品質値。低いほど高品質                      |
| **-gpb**                      |     1      |   0    |   1    |    1推奨    | GPB (ExtCO3) | GPBモード。1でP-FrameをB-Frameとして扱う       |
| **-vf vpp_qsv=format=p010le** |     -      |   -    |   -    |    推奨     | FourCC       | 10bit エンコード。画質向上、ファイルサイズ微増 |
| **-profile**                  |    main    |   -    |   -    | main/main10 | CodecProfile | HEVCプロファイル。10bit時はmain10              |
| **-g**                        |     -1     |   1    |   -    |   120-300   | GopPicSize   | GOP サイズ(キーフレーム間隔)                 |
| **-bf**                       |     -1     |   0    |   15   |    8-15     | GopRefDist-1 | 連続B-Frameの最大数。**hevc_qsvは最大15**      |
| **-refs**                     |     0      |   1    |   16   |    4-12     | NumRefFrame  | 参照フレーム数。**QSVでは処理時間変わらず**    |

**QSV 高度なパラメーター:**

| パラメーター         | デフォルト |  範囲  | Intel SDK          | 説明                                   |
| :------------------- | :--------: | :----: | :----------------- | :------------------------------------- |
| **extbrc**           |     0      |  0/1   | ExtBRC (ExtCO2)    | Extended BRC。品質制御改善             |
| **look_ahead_depth** |     0      | 20-100 | LookAheadDepth     | 先読みフレーム数(extbrc=1時のみ有効) |
| **mbbrc**            |     0      |  0/1   | MBBRC (ExtCO2)     | マクロブロックレベルBRC                |
| **tile_cols**        |     0      |  0-20  | NumTileColumns     | タイル列数(並列処理)                 |
| **tile_rows**        |     0      |  0-22  | NumTileRows        | タイル行数(並列処理)                 |
| **rdo**              |     0      |  0/1   | -                  | Rate Distortion最適化                  |
| **adaptive_i**       |     0      |  0/1   | AdaptiveI (ExtCO2) | アダプティブI-Frame配置                |
| **adaptive_b**       |     0      |  0/1   | AdaptiveB (ExtCO2) | アダプティブB-Frame配置                |

### Phase 1: Quality値探査(hevc-qsv-icq-0001-quality)

**範囲**: 18-28

```yaml
outfile:
    base:
        - type: Anime
          option: ""
        - type: Nature
          option: ""
    options:
    - -global_quality 18
    - -global_quality 19
    - -global_quality 20
    - -global_quality 21
    - -global_quality 22
    - -global_quality 23
    - -global_quality 24
    - -global_quality 25
    - -global_quality 26
    - -global_quality 27
    - -global_quality 28

```

**目的**: VMAF 93前後を達成するQuality値を特定
**結果**: Anime `-global_quality 28`, Natrue `-global_quality 22`

### Phase 2: GPB モードの比較(hevc-qsv-icq-0002-gpb)

```yaml
outfile:
  options:
    # GPBモード無効(従来のP/B分離)
    - -gpb 0

    # GPBモード有効(デフォルト、Pを全てBとして扱う)
    - -gpb 1
```

**目的**: GPB モードの圧縮効率と画質への影響を確認
**結果**: `-gpb 1`

### Phase 3: 10bit対応テスト(hevc-qsv-icq-0003-10bit)

```yaml
outfile:
  options:
    - -vf vpp_qsv=format=p010le
```

**結果**: 10Bit にしたほうが良い

### Phase 4: B-Frame 数(最大負荷テスト)(hevc-qsv-icq-0004-bf)

```yaml
# for bf in $(seq 1 15); do for refs in $(seq 1 15); do echo "          - -bf ${bf} -refs ${refs}"; done; done

outfile:
  options:
    - -bf {1..15} -refs {1..15}
```

**結果**: `-bf 2 -refs 6`

### Phase 6: GOP サイズ(hevc-qsv-icq-0006-gop)

**範囲**: 120, 180, 240, 248, 300

```yaml
outfile:
  options:
    - -g 120
    - -g 180
    - -g 240
    - -g 248
    - -g 300
```

**結果**: 変化無し

### Phase 8: QSV高度なオプション(hevc-qsv-icq-0008-qsv-params)

```yaml
outfile:
  options:
    # Extended BRC
    - -extbrc 1

    # Look-ahead depth(extbrc有効時のみ)
    - -extbrc 1 -look_ahead_depth 20
    - -extbrc 1 -look_ahead_depth 40
    - -extbrc 1 -look_ahead_depth 60
    - -extbrc 1 -look_ahead_depth 80
    - -extbrc 1 -look_ahead_depth 100

    # MBBRC
    - -mbbrc 1

    # タイル設定
    - -tile_cols 2 -tile_rows 2

    # RDO
    - -rdo 1

    # アダプティブフレーム配置
    - -adaptive_i 1 -adaptive_b 1

    # 複合最適化
    - -extbrc 1 -look_ahead_depth 60 -mbbrc 1 -rdo 1 -adaptive_i 1 -adaptive_b 1
```

**結果**:

### Phase 9: 総当たり最終検証(hevc-qsv-icq-0009-final)

---

## av1_qsv - CQP モード

### 基本情報(av1-qsv-cqp-basic-info)

- **ソースコード**: `libavcodec/qsvenc_av1.c`
- **対応Profile**: main(1)のみ
- **対応Preset**: veryslow(1) ~ veryfast(7)
- **フレーム構造**: AV1独自の構造(I/P/B ではなく Key/Inter + Altref)
- **既存フレーム比率**: `I/P/B: 15.0 / 3582.0 / 0.0` ← **B-Frame は存在しない**
- **既存ベスト**: `-q:v 53 -vf vpp_qsv=format=p010le`
- **重要**: `-bf` オプションは**無効**(AV1 には B-Frame が存在しない)
- **特徴**: av1_qsvは多くのオプションが非対応(rdo, mbbrc, max_qp_*, scenario等)。-refs最大7

### パラメーター詳細(av1-qsv-cqp-parameter-details)

| パラメーター                  | デフォルト | 最小値 | 最大値 | 推奨範囲 | Intel SDK    | 説明                                           |
| :---------------------------- | :--------: | :----: | :----: | :------: | :----------- | :--------------------------------------------- |
| **-q:v**                      |     -      |   0    |  255   |  45-80   | QPI          | CQP(固定QP)。低いほど高品質。AV1は値域が広い |
| **-vf vpp_qsv=format=p010le** |     -      |   -    |   -    |   推奨   | -            | 10bit エンコード。AV1では10bit推奨             |
| **-profile**                  |    main    |   -    |   -    |   main   | CodecProfile | main(1)のみ対応                                |
| **-g**                        |     -1     |   1    |   -    | 120-300  | GopPicSize   | GOP サイズ(キーフレーム間隔)                 |
| **-bf**                       |    N/A     |   -    |   -    |    -     | -            | **AV1には存在しない**。指定しても無視される    |
| **-refs**                     |     0      |   0    | **7**  |   1-7    | NumRefFrame  | 参照フレーム数。**AV1仕様では最大7**           |

**AV1 QSV の制限事項:**

av1_qsv は h264_qsv/hevc_qsv と比較してオプションが限定的です：

| 機能カテゴリ                     | 対応状況 | 備考   |
| :------------------------------- | :------: | :----- |
| QP制御 (max_qp_*, min_qp_*)      |    ❌     | 非対応 |
| RDO (rdo)                        |    ❌     | 非対応 |
| MBBRC (mbbrc)                    |    ❌     | 非対応 |
| シナリオ (scenario)              |    ❌     | 非対応 |
| AVBR (avbr_*)                    |    ❌     | 非対応 |
| スキップフレーム (skip_frame)    |    ❌     | 非対応 |
| イントラリフレッシュ (int_ref_*) |    ❌     | 非対応 |
| デブロッキング (dblk_idc)        |    ❌     | 非対応 |
| P-pyramid (p_strategy)           |    ❌     | 非対応 |
| IDR間隔 (idr_interval)           |    ❌     | 非対応 |

**QSV 高度なパラメーター(対応するもの):**

| パラメーター         | デフォルト | 範囲  | Intel SDK      | 説明                                         |
| :------------------- | :--------: | :---: | :------------- | :------------------------------------------- |
| **tile_cols**        |     0      |  0-   | NumTileCols    | タイル列数(並列処理)                       |
| **tile_rows**        |     0      |  0-   | NumTileRows    | タイル行数(並列処理)                       |
| **adaptive_i**       |     0      |  0/1  | AdaptiveI      | アダプティブKeyFrame配置                     |
| **adaptive_b**       |     0      |  0/1  | AdaptiveB      | アダプティブInter-Frame配置                  |
| **b_strategy**       |     0      |  0/1  | BRefType       | B-Frame戦略(AV1のAltrefフレーム制御に影響) |
| **extbrc**           |     0      |  0/1  | ExtBRC         | 拡張BRC有効化                                |
| **look_ahead_depth** |     0      | 0-100 | LookAheadDepth | 先読みフレーム数(extbrc時のみ有効)         |
| **low_delay_brc**    |     0      |  0/1  | LowDelayBRC    | 低遅延BRC                                    |
| **max_frame_size**   |     0      |  0-   | MaxFrameSize   | 最大フレームサイズ                           |

### Phase 1: QP値探査(av1-qsv-cqp-0001-qp)

**範囲**: 45-80

```yaml
outfile:
  options:
    - -q:v 45
    - -q:v 48
    - -q:v 50
    - -q:v 53
    - -q:v 55
    - -q:v 58
    - -q:v 60
    - -q:v 63
    - -q:v 65
    - -q:v 68
    - -q:v 70
    - -q:v 73
    - -q:v 75
    - -q:v 78
    - -q:v 80
```

**目的**: VMAF 93前後を達成するQP値を特定

### Phase 2: 10bit対応テスト(av1-qsv-cqp-0002-10bit)

```yaml
outfile:
  options:
    - -q:v [最適値]
    - -q:v [最適値] -vf vpp_qsv=format=p010le
```

### Phase 3: GOP サイズ(av1-qsv-cqp-0003-gop)

**範囲**: 120, 180, 240, 248, 300

```yaml
outfile:
  options:
    - -q:v [最適値] -vf vpp_qsv=format=p010le -g 120
    - -q:v [最適値] -vf vpp_qsv=format=p010le -g 180
    - -q:v [最適値] -vf vpp_qsv=format=p010le -g 240
    - -q:v [最適値] -vf vpp_qsv=format=p010le -g 248
    - -q:v [最適値] -vf vpp_qsv=format=p010le -g 300
```

### Phase 4: QSV高度なオプション(av1-qsv-cqp-0004-qsv-params)

```yaml
outfile:
  options:
    # タイル設定(並列処理)
    - -q:v [最適値] -vf vpp_qsv=format=p010le -tile_cols 1
    - -q:v [最適値] -vf vpp_qsv=format=p010le -tile_rows 1
    - -q:v [最適値] -vf vpp_qsv=format=p010le -tile_cols 2
    - -q:v [最適値] -vf vpp_qsv=format=p010le -tile_rows 2
    - -q:v [最適値] -vf vpp_qsv=format=p010le -tile_cols 2 -tile_rows 2
    - -q:v [最適値] -vf vpp_qsv=format=p010le -tile_cols 4 -tile_rows 4

    # アダプティブフレーム配置
    - -q:v [最適値] -vf vpp_qsv=format=p010le -adaptive_i 1
    - -q:v [最適値] -vf vpp_qsv=format=p010le -adaptive_b 1
    - -q:v [最適値] -vf vpp_qsv=format=p010le -adaptive_i 1 -adaptive_b 1

    # 複合最適化
    - -q:v [最適値] -vf vpp_qsv=format=p010le -tile_cols 2 -tile_rows 2 -adaptive_i 1 -adaptive_b 1
```

**注意**: AV1 には B-Frame が存在しないため、`-bf` オプションは指定しない

### Phase 5: 総当たり最終検証(av1-qsv-cqp-0005-final)

---

## av1_qsv - ICQ モード

### 基本情報(av1-qsv-icq-basic-info)

- **ソースコード**: `libavcodec/qsvenc_av1.c`
- **対応Profile**: main(1)のみ
- **対応Preset**: veryslow(1) ~ veryfast(7)
- **フレーム構造**: AV1独自の構造(I/P/B ではなく Key/Inter + Altref)
- **既存フレーム比率**: `I/P/B: 15.0 / 3582.0 / 0.0` ← **B-Frame は存在しない**
- **既存ベスト**: `-global_quality 24 -vf vpp_qsv=format=p010le`
- **重要**: `-bf` オプションは**無効**(AV1 には B-Frame が存在しない)
- **特徴**: av1_qsvは多くのオプションが非対応(rdo, mbbrc, max_qp_*, scenario等)。-refs最大7

### パラメーター詳細(av1-qsv-icq-parameter-details)

| パラメーター                  | デフォルト | 最小値 | 最大値 | 推奨範囲 | Intel SDK    | 説明                                        |
| :---------------------------- | :--------: | :----: | :----: | :------: | :----------- | :------------------------------------------ |
| **-global_quality**           |     -      |   1    |   51   |  20-32   | ICQQuality   | ICQ品質値。低いほど高品質                   |
| **-vf vpp_qsv=format=p010le** |     -      |   -    |   -    |   推奨   | -            | 10bit エンコード。AV1では10bit推奨          |
| **-profile**                  |    main    |   -    |   -    |   main   | CodecProfile | main(1)のみ対応                             |
| **-g**                        |     -1     |   1    |   -    | 120-300  | GopPicSize   | GOP サイズ(キーフレーム間隔)              |
| **-bf**                       |    N/A     |   -    |   -    |    -     | -            | **AV1には存在しない**。指定しても無視される |
| **-refs**                     |     0      |   0    | **7**  |   1-7    | NumRefFrame  | 参照フレーム数。**AV1仕様では最大7**        |

**QSV 高度なパラメーター(対応するもの):**

| パラメーター         | デフォルト | 範囲  | Intel SDK      | 説明                                         |
| :------------------- | :--------: | :---: | :------------- | :------------------------------------------- |
| **extbrc**           |     0      |  0/1  | ExtBRC         | Extended BRC。品質制御改善                   |
| **look_ahead_depth** |     0      | 0-100 | LookAheadDepth | 先読みフレーム数(extbrc=1時のみ有効)       |
| **tile_cols**        |     0      |  0-   | NumTileCols    | タイル列数(並列処理)                       |
| **tile_rows**        |     0      |  0-   | NumTileRows    | タイル行数(並列処理)                       |
| **adaptive_i**       |     0      |  0/1  | AdaptiveI      | アダプティブKeyFrame配置                     |
| **adaptive_b**       |     0      |  0/1  | AdaptiveB      | アダプティブInter-Frame配置                  |
| **b_strategy**       |     0      |  0/1  | BRefType       | B-Frame戦略(AV1のAltrefフレーム制御に影響) |
| **low_delay_brc**    |     0      |  0/1  | LowDelayBRC    | 低遅延BRC                                    |
| **max_frame_size**   |     0      |  0-   | MaxFrameSize   | 最大フレームサイズ                           |

**非対応オプション(av1_qsv固有の制限):**

CQPモードと同様、以下のオプションは av1_qsv では非対応です：

- QP制御 (max_qp_*, min_qp_*)
- RDO (rdo)
- MBBRC (mbbrc)
- シナリオ (scenario)
- AVBR (avbr_*)
- イントラリフレッシュ (int_ref_*)
- デブロッキング (dblk_idc)
- P-pyramid (p_strategy)

### Phase 1: Quality値探査(av1-qsv-icq-0001-quality)

**範囲**: 20-32

```yaml
outfile:
  options:
    - -global_quality 20
    - -global_quality 21
    - -global_quality 22
    - -global_quality 23
    - -global_quality 24
    - -global_quality 25
    - -global_quality 26
    - -global_quality 27
    - -global_quality 28
    - -global_quality 29
    - -global_quality 30
    - -global_quality 31
    - -global_quality 32
```

**目的**: VMAF 93前後を達成するQuality値を特定

### Phase 2: 10bit対応テスト(av1-qsv-icq-0002-10bit)

```yaml
outfile:
  options:
    - -global_quality [最適値]
    - -global_quality [最適値] -vf vpp_qsv=format=p010le
```

### Phase 3: GOP サイズ(av1-qsv-icq-0003-gop)

**範囲**: 120, 180, 240, 248, 300

```yaml
outfile:
  options:
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -g 120
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -g 180
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -g 240
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -g 248
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -g 300
```

### Phase 4: Extended BRC と Look-ahead(av1-qsv-icq-0004-extbrc)

```yaml
outfile:
  options:
    # Extended BRC
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1

    # Look-ahead depth(extbrc有効時のみ)
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 20
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 40
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 60
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 80
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 100
```

### Phase 5: QSV高度なオプション(av1-qsv-icq-0005-qsv-params)

```yaml
outfile:
  options:
    # タイル設定(並列処理)
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -tile_cols 1
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -tile_rows 1
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -tile_cols 2
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -tile_rows 2
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -tile_cols 2 -tile_rows 2
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -tile_cols 4 -tile_rows 4

    # アダプティブフレーム配置
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -adaptive_i 1
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -adaptive_b 1
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -adaptive_i 1 -adaptive_b 1

    # 複合最適化
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 60 -tile_cols 2 -tile_rows 2 -adaptive_i 1 -adaptive_b 1
```

**注意**: AV1 には B-Frame が存在しないため、`-bf` オプションは指定しない

### Phase 6: 総当たり最終検証(av1-qsv-icq-0006-final)

---

## 検証実行の推奨手順

### 1. Phase 1 から順次実行

各エンコーダーの Phase 1 から順番に実行し、最適値を特定してから次のフェーズへ進む。

### 2. VMAF 目標値の確認

- **VMAF harmonic_mean**: 93.0 以上
- **VMAF mean**: 93.0 以上
- **SSIM mean**: 0.99 以上

### 3. 圧縮率の評価

- **compress_rate**: 低いほど高圧縮(目標: 0.7以下)
- **bitrate**: 低いほど良い

### 4. 処理時間の考慮

- **ソフトウェアエンコード**: 処理時間と画質のバランスを考慮
- **ハードウェアエンコード(QSV)**: 処理時間はほぼ一定のため最大負荷設定を積極的に試す

### 5. フレーム構造の確認

エンコード後、`ffprobe` または結果の `I/P/B frames` を確認：

- **H.264**: I/P/B の比率を確認
- **HEVC (GPB=1)**: P が 0、B が増加していることを確認
- **AV1**: B が 0 であることを確認(正常)

### 6. 結果の記録

各フェーズの最適値を記録し、次のフェーズで使用する。最終的に全パラメータの組み合わせで総当たり検証を実施。

---

## 注意事項

### libx265 (HEVC) の制限事項

#### **refs の制限**

- **B-pyramid 有効時(デフォルト)**: 最大 **6** まで
- **B-pyramid 無効時**: 最大 **7** まで(`-x265-params no-b-pyramid=1`)
- **HEVC 仕様**: 絶対上限 **8**
- **違反時のエラー**: `NumPocTotalCurr (total references) is non-compliant`

#### **bf と rc-lookahead の関係**

- **必須条件**: `rc-lookahead > bf`
- **ultrafast**: rc-lookahead=5 のため `-bf 4` まで
- **veryfast**: rc-lookahead=10 のため `-bf 9` まで
- **medium 以上**: rc-lookahead=40 のため実用上制限なし
- **違反時のエラー**: `Lookahead depth must be greater than the max consecutive bframe count`

#### **推奨設定**

- 高速: `-preset veryfast -bf 9 -refs 6`
- バランス: `-preset medium -bf 9 -refs 6` ★推奨
- 高品質: `-preset slow -bf 9 -refs 6`

### AV1 エンコーダーの特性

- **B-Frame は存在しない**: `-bf` オプションは無視される
- **Altref フレーム**: エンコーダーが自動的に最適な構造を決定
- **階層的予測**: `hierarchical-levels` パラメータで制御可能(libsvtav1)
- **refs の上限**: AV1 仕様では最大 **7** まで

### HEVC QSV の GPB モード

- **デフォルトで有効**: P-Frame を B-Frame として扱う
- **圧縮効率向上**: 参照の柔軟性が増す
- **無効化**: `-gpb 0` で従来の P/B 分離モードに切り替え可能

### HWEnc (QSV) の特性

- **処理時間がほぼ一定**: プリセットや負荷を変えても処理時間はほとんど変わらない
- **最大負荷設定推奨**: `-bf 16` (H.264), `-refs 16` (H.264), `-look_ahead_depth 100` などの最大値を積極的に試す
- **タイル並列処理**: `-tile_cols`, `-tile_rows` で並列処理を有効化できる(HEVC/AV1のみ)

#### コーデック別パラメーター制限(ソースコード検証済み)

| パラメーター          |  h264_qsv  |   hevc_qsv   |   av1_qsv    | 備考                              |
| --------------------- | :--------: | :----------: | :----------: | --------------------------------- |
| **-bf** (B-frames)    |    0-16    |   0-**15**   |    ❌ 無効    | hevc_qsvは最大15、av1_qsvは非対応 |
| **-refs**             |    0-16    |     0-16     |   0-**7**    | av1_qsvはAV1仕様制限              |
| **-g** (GOP)          | default:-1 | default:248  |  default:-1  |                                   |
| **rdo**               |     ✅      |      ✅       |      ❌       |                                   |
| **mbbrc**             |     ✅      |      ✅       |      ❌       |                                   |
| **max_qp_*/min_qp_*** |     ✅      |      ✅       |      ❌       |                                   |
| **scenario**          |     ✅      |      ✅       |      ❌       |                                   |
| **avbr_***            |     ✅      |      ✅       |      ❌       |                                   |
| **int_ref_***         |     ✅      |      ✅       |      ❌       |                                   |
| **dblk_idc**          |     ✅      |      ✅       |      ❌       |                                   |
| **p_strategy**        |     ✅      |      ✅       |      ❌       |                                   |
| **look_ahead**        |     ✅      |      ❌       |      ❌       | h264_qsv専用                      |
| **look_ahead_depth**  |     ✅      | ✅ (extbrc時) | ✅ (extbrc時) |                                   |
| **tile_cols/rows**    |     ❌      |      ✅       |      ✅       |                                   |
| **gpb**               |     ❌      |      ✅       |      ❌       | HEVC専用                          |
| **tier**              |     ❌      |      ✅       |      ❌       | HEVC専用                          |
| **cavlc**             |     ✅      |      ❌       |      ❌       | H.264専用                         |

#### ソースコード参照

- **ffmpeg**: `libavcodec/qsvenc.h`, `qsvenc.c`, `qsvenc_h264.c`, `qsvenc_hevc.c`, `qsvenc_av1.c`
- **Intel VPL**: `api/vpl/mfxstructures.h` (mfxExtCodingOption2, mfxExtCodingOption3)

### ソフトウェアエンコードの特性

- **処理時間と画質のトレードオフ**: プリセットや参照フレーム数で大きく変わる
- **細かいチューニングが可能**: `*-params` で詳細な制御が可能

### 総当たり検証の実施タイミング

Phase 1-6で最適値が特定できたら、それらの組み合わせで総当たり検証を実施し、最終的な最適パラメータを決定する。
