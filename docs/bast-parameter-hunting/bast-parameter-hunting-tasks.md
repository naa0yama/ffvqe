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
- **P-Frame (Predicted)**: 前方参照のみ（過去のフレームから予測）
- **B-Frame (Bi-directional)**: 前後両方向から参照（過去と未来のフレームから予測）

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

1. **Key Frame**: 独立して復号可能（I-Frame に相当）
2. **Inter Frame**: 他のフレームを参照（P/B に相当するが異なる）
3. **Altref (Alternative Reference) フレーム**: 未来のフレームを事前エンコードして参照に使用

```text
K --- [Altref hidden] --- Inter --- Inter --- Inter --- K
      ↑                   ↓         ↓         ↓
      └───────────────────┴─────────┴─────────┘
```

- **既存データ例**: `I/P/B: 23.0 / 3573.5 / 0.0` (av1_qsv)
- **B-Frame が 0**: これは**正常**（AV1 には B-Frame が存在しない）
- **`-bf` オプション**: **AV1 では無効**（指定しても無視される）
- **Altref フレーム**: エンコーダーが自動的に最適な構造を決定

### コーデック別対応表

| コーデック   | I-Frame |  P-Frame  | B-Frame | 特殊フレーム | `-bf` の効果                  | `-refs` の意味          |
| :----------- | :-----: | :-------: | :-----: | :----------- | :---------------------------- | :---------------------- |
| **H.264**    |    ✓    |     ✓     |    ✓    | -            | P間のBフレーム最大数          | 参照フレーム数          |
| **HEVC**     |    ✓    |     ✓     |    ✓    | GPB          | P間のBフレーム最大数          | 参照フレーム数          |
| **AV1**      | ✓ (Key) | ✓ (Inter) |    ✗    | Altref       | **無効**                      | 参照フレーム数（最大7） |
| **h264_qsv** |    ✓    |     ✓     |    ✓    | -            | P間のBフレーム最大数 (最大16) | 参照フレーム数 (最大16) |
| **hevc_qsv** |    ✓    |     △     |    ✓    | GPB          | Bフレーム制御                 | 参照フレーム数          |
| **av1_qsv**  | ✓ (Key) | ✓ (Inter) |    ✗    | Altref       | **無効**                      | 参照フレーム数          |

---

## libx264 - CRF モード

### 基本情報

- **フレーム構造**: 従来の I/P/B 構造を使用
- **既存フレーム比率**: `I/P/B: 30.0 / 2654.5 / 1380.0`
- **デフォルトGOP**: 250
- **デフォルトB-Frame**: 3
- **デフォルトRefs**: 4
- **既存ベスト**: `-crf 23`

### Phase 1: CRF値探査

**範囲**: 18-28

```yaml
outfile:
  options:
    - -crf 18
    - -crf 19
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
- Nature -crf 23

### Phase 2: GOP サイズ

**範囲**: 120, 150, 180, 210, 240, 250, 270, 300

```yaml
outfile:
  options:
    - -crf [最適値] -g 120
    - -crf [最適値] -g 150
    - -crf [最適値] -g 180
    - -crf [最適値] -g 210
    - -crf [最適値] -g 240
    - -crf [最適値] -g 250
    - -crf [最適値] -g 270
    - -crf [最適値] -g 300
```

**目的**: 圧縮率と画質のバランスが良いGOPサイズを特定

**結果**: GOP はシークに依存しデフォルトの 250 でも 8.3秒のため変更しない。 300 との比較は 30kb 程度しかなかった

### Phase 3: B-Frame 数

**範囲**: 2, 3, 4, 5, 6, 8, 10, 12, 15

```yaml
outfile:
  options:
    - -crf [最適値] -g [最適値] -bf 2
    - -crf [最適値] -g [最適値] -bf 3
    - -crf [最適値] -g [最適値] -bf 4
    - -crf [最適値] -g [最適値] -bf 5
    - -crf [最適値] -g [最適値] -bf 6
    - -crf [最適値] -g [最適値] -bf 8
    - -crf [最適値] -g [最適値] -bf 10
    - -crf [最適値] -g [最適値] -bf 12
    - -crf [最適値] -g [最適値] -bf 15
```

**目的**: 圧縮効率を高めるB-Frame数を特定
**結果**: `-bf 9` が最も良い、 10-14 もデータによってはあるが vmaf が微減するバランスがよい

### Phase 4: 参照フレーム数

**範囲**: 1, 2, 3, 4, 5, 6, 8, 10, 12

```yaml
outfile:
  options:
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 1
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 2
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 3
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 4
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 5
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 6
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 8
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 10
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 12
```

**目的**: 画質向上と処理時間のバランスを取る
**結果**: `-refs 15` が最も良い、エンコード時間がかかるが...

### Phase 5: プリセット

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

### Phase 6: x264opts 高度なオプション

```yaml
outfile:
  options:
    # AQ最適化
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=1:aq-strength=1.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=2:aq-strength=1.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=3:aq-strength=1.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=2:aq-strength=0.8
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=2:aq-strength=1.2

    # 心理視覚最適化（psy-rdは2つの値をカンマで区切る）
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params psy-rd=0.8,0.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params psy-rd=1.0,0.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params psy-rd=1.2,0.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params psy-rd=1.0,0.15

    # 先読みフレーム数
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params rc-lookahead=40
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params rc-lookahead=60
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params rc-lookahead=80

    # 動き推定
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params me=umh
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params me=esa

    # トレリス量子化
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params trellis=2

    # 複合最適化（複数パラメータはコロンで区切り、psy-rdの値内はカンマ）
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x264-params aq-mode=2:aq-strength=1.0:psy-rd=1.0,0.15:rc-lookahead=60
```

**目的**: 微細な画質改善と圧縮率向上
**結果**: `-x264-params trellis=2:aq-mode=2:aq-strength=1.2:rc-lookahead=40` を採用

- `trellis=2`
  - トレリス最適化により、量子化誤差を最小化
  - Rate-Distortion最適化のより精密な実装
- `aq-mode=2:aq-strength=1.0`
  - 適応的量子化 (Adaptive Quantization)
  - 複雑度に基づく適応的なビット配分
- `rc-lookahead`
  - 先読みフレーム数を増やしてビット配分を最適化
  - シーン変化の予測精度向上
  - ビット配分の最適化

### Phase 7: 総当たり最終検証

Phase 1-6で特定した最適パラメータの組み合わせを総当たりで検証

---

## libx265 - CRF モード

### 基本情報

- **フレーム構造**: 従来の I/P/B 構造を使用（H.264 より高度）
- **デフォルトGOP**: 250
- **デフォルトB-Frame**: 3
- **デフォルトRefs**: 1
- **既存ベスト**: `-crf 23`, `-crf 28`

### Phase 1: CRF値探査

**範囲**: 20-32

```yaml
outfile:
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

### Phase 2: GOP サイズ

**範囲**: 120, 150, 180, 210, 240, 250, 270, 300

```yaml
outfile:
  options:
    - -crf [最適値] -g 120
    - -crf [最適値] -g 150
    - -crf [最適値] -g 180
    - -crf [最適値] -g 210
    - -crf [最適値] -g 240
    - -crf [最適値] -g 250
    - -crf [最適値] -g 270
    - -crf [最適値] -g 300
```

### Phase 3: B-Frame 数

**範囲**: 2, 3, 4, 5, 6, 8, 10, 12, 15

```yaml
outfile:
  options:
    - -crf [最適値] -g [最適値] -bf 2
    - -crf [最適値] -g [最適値] -bf 3
    - -crf [最適値] -g [最適値] -bf 4
    - -crf [最適値] -g [最適値] -bf 5
    - -crf [最適値] -g [最適値] -bf 6
    - -crf [最適値] -g [最適値] -bf 8
    - -crf [最適値] -g [最適値] -bf 10
    - -crf [最適値] -g [最適値] -bf 12
    - -crf [最適値] -g [最適値] -bf 15
```

### Phase 4: 参照フレーム数

**範囲**: 1, 2, 3, 4, 5, 6

```yaml
outfile:
  options:
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 1
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 2
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 3
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 4
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 5
    - -crf [最適値] -g [最適値] -bf [最適値] -refs 6
```

### Phase 5: プリセット

**選択肢**: fast, medium, slow, slower, veryslow

```yaml
presets:
  - fast
  - medium
  - slow
  - slower
  - veryslow
```

### Phase 6: x265-params 高度なオプション

```yaml
outfile:
  options:
    # AQ最適化
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params aq-mode=1:aq-strength=1.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params aq-mode=2:aq-strength=1.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params aq-mode=3:aq-strength=1.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params aq-mode=4:aq-strength=1.0

    # 心理視覚最適化
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params psy-rd=1.5:psy-rdoq=0.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params psy-rd=2.0:psy-rdoq=0.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params psy-rd=2.5:psy-rdoq=0.0
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params psy-rd=2.0:psy-rdoq=1.0

    # RD最適化
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params rd=3
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params rd=4
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params rd=5
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params rd=6

    # RDOQ
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params rdoq-level=1
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params rdoq-level=2

    # 予測モード
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params rect=1
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params amp=1
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params rect=1:amp=1

    # 複合最適化
    - -crf [最適値] -g [最適値] -bf [最適値] -refs [最適値] -x265-params aq-mode=3:aq-strength=1.0:psy-rd=2.0:psy-rdoq=1.0:rd=4:rdoq-level=2
```

### Phase 7: 総当たり最終検証

---

## libsvtav1 - CRF モード

### 基本情報

- **フレーム構造**: AV1独自の構造（I/P/B ではなく Key/Inter + Altref）
- **既存フレーム比率**: `I/P/B: 23.0 / 3574.0 / 0.0` ← **B-Frame は存在しない**
- **デフォルトGOP**: 161 (自動)
- **デフォルトRefs**: 1
- **デフォルトPreset**: -2 (未設定)
- **既存ベスト**: `-crf 31`, `-crf 35`
- **重要**: `-bf` オプションは**無効**（AV1 には B-Frame が存在しない）

### Phase 1: CRF値探査

**範囲**: 25-40

```yaml
outfile:
  options:
    - -crf 25
    - -crf 26
    - -crf 27
    - -crf 28
    - -crf 29
    - -crf 30
    - -crf 31
    - -crf 32
    - -crf 33
    - -crf 34
    - -crf 35
    - -crf 36
    - -crf 37
    - -crf 38
    - -crf 39
    - -crf 40
```

**目的**: VMAF 93前後を達成するCRF値を特定

### Phase 2: プリセット

**範囲**: 3, 4, 5, 6, 7, 8, 9 (低いほど高品質だが処理時間増)

```yaml
outfile:
  options:
    - -crf [最適値] -preset 3
    - -crf [最適値] -preset 4
    - -crf [最適値] -preset 5
    - -crf [最適値] -preset 6
    - -crf [最適値] -preset 7
    - -crf [最適値] -preset 8
    - -crf [最適値] -preset 9
```

**目的**: 処理時間と画質のバランスを確認

### Phase 3: GOP サイズ

**範囲**: 120, 150, 180, 210, 240, 270, 300

```yaml
outfile:
  options:
    - -crf [最適値] -preset [最適値] -g 120
    - -crf [最適値] -preset [最適値] -g 150
    - -crf [最適値] -preset [最適値] -g 180
    - -crf [最適値] -preset [最適値] -g 210
    - -crf [最適値] -preset [最適値] -g 240
    - -crf [最適値] -preset [最適値] -g 270
    - -crf [最適値] -preset [最適値] -g 300
```

### Phase 4: svtav1-params 高度なオプション

```yaml
outfile:
  options:
    # チューニングモード
    - -crf [最適値] -preset [最適値] -svtav1-params tune=0
    - -crf [最適値] -preset [最適値] -svtav1-params tune=1
    - -crf [最適値] -preset [最適値] -svtav1-params tune=2

    # 階層的予測レベル（Altref制御）
    - -crf [最適値] -preset [最適値] -svtav1-params hierarchical-levels=3
    - -crf [最適値] -preset [最適値] -svtav1-params hierarchical-levels=4
    - -crf [最適値] -preset [最適値] -svtav1-params hierarchical-levels=5

    # フィルムグレイン
    - -crf [最適値] -preset [最適値] -svtav1-params film-grain=10
    - -crf [最適値] -preset [最適値] -svtav1-params film-grain=20
    - -crf [最適値] -preset [最適値] -svtav1-params film-grain=30
    - -crf [最適値] -preset [最適値] -svtav1-params film-grain-denoise=1

    # 量子化マトリックス
    - -crf [最適値] -preset [最適値] -svtav1-params enable-qm=1:qm-min=0:qm-max=15
    - -crf [最適値] -preset [最適値] -svtav1-params enable-qm=1:qm-min=0:qm-max=10
    - -crf [最適値] -preset [最適値] -svtav1-params enable-qm=1:qm-min=5:qm-max=15

    # フィルタ設定
    - -crf [最適値] -preset [最適値] -svtav1-params enable-dlf=2
    - -crf [最適値] -preset [最適値] -svtav1-params cdef-level=0
    - -crf [最適値] -preset [最適値] -svtav1-params cdef-level=3
    - -crf [最適値] -preset [最適値] -svtav1-params cdef-level=5
    - -crf [最適値] -preset [最適値] -svtav1-params enable-restoration=0
    - -crf [最適値] -preset [最適値] -svtav1-params enable-restoration=1

    # タイル設定（並列処理）
    - -crf [最適値] -preset [最適値] -svtav1-params tile-rows=1:tile-columns=1
    - -crf [最適値] -preset [最適値] -svtav1-params tile-rows=2:tile-columns=2

    # 複合最適化
    - -crf [最適値] -preset [最適値] -svtav1-params tune=0:hierarchical-levels=4:enable-qm=1:qm-min=0:qm-max=15:enable-dlf=2:cdef-level=5
```

**目的**: Altref フレームと階層的予測の最適化

### Phase 5: 総当たり最終検証

---

## h264_qsv - CQP モード

### 基本情報

- **フレーム構造**: 従来の I/P/B 構造を使用
- **既存フレーム比率**: `I/P/B: 15.0 / 225.0 / 3357.0` ← **B-Frame が約90%**
- **デフォルトGOP**: 256
- **デフォルトB-Frame**: 2
- **デフォルトRefs**: 3
- **デフォルトPreset**: 0 (未設定)
- **既存ベスト**: `-q:v 22 -bf 15 -refs 8`

### Phase 1: QP値探査

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

### Phase 2: B-Frame 数（最大負荷テスト）

**範囲**: 8, 10, 12, 14, 15, 16

```yaml
outfile:
  options:
    - -q:v [最適値] -bf 8
    - -q:v [最適値] -bf 10
    - -q:v [最適値] -bf 12
    - -q:v [最適値] -bf 14
    - -q:v [最適値] -bf 15
    - -q:v [最適値] -bf 16
```

**HWEnc特性**: 処理時間は変わらないため最大値まで試す

### Phase 3: 参照フレーム数（最大負荷テスト）

**範囲**: 4, 6, 8, 10, 12, 14, 16

```yaml
outfile:
  options:
    - -q:v [最適値] -bf [最適値] -refs 4
    - -q:v [最適値] -bf [最適値] -refs 6
    - -q:v [最適値] -bf [最適値] -refs 8
    - -q:v [最適値] -bf [最適値] -refs 10
    - -q:v [最適値] -bf [最適値] -refs 12
    - -q:v [最適値] -bf [最適値] -refs 14
    - -q:v [最適値] -bf [最適値] -refs 16
```

**HWEnc特性**: 処理時間は変わらないため最大値まで試す

### Phase 4: GOP サイズ

**範囲**: 120, 180, 240, 256, 300

```yaml
outfile:
  options:
    - -q:v [最適値] -bf [最適値] -refs [最適値] -g 120
    - -q:v [最適値] -bf [最適値] -refs [最適値] -g 180
    - -q:v [最適値] -bf [最適値] -refs [最適値] -g 240
    - -q:v [最適値] -bf [最適値] -refs [最適値] -g 256
    - -q:v [最適値] -bf [最適値] -refs [最適値] -g 300
```

### Phase 5: プリセット（HWEncでは効果限定的）

**選択肢**: veryslow, slower, slow, medium

```yaml
presets:
  - veryslow
  - slower
  - slow
  - medium
```

**注意**: QSVでは処理時間がほぼ変わらないため、通常は veryslow 推奨

### Phase 6: QSV高度なオプション

```yaml
outfile:
  options:
    # アダプティブフレーム配置
    - -q:v [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1
    - -q:v [最適値] -bf [最適値] -refs [最適値] -adaptive_b 1
    - -q:v [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1

    # B-Frame戦略
    - -q:v [最適値] -bf [最適値] -refs [最適値] -b_strategy 1

    # RDO
    - -q:v [最適値] -bf [最適値] -refs [最適値] -rdo 1

    # シナリオヒント
    - -q:v [最適値] -bf [最適値] -refs [最適値] -scenario 3
    - -q:v [最適値] -bf [最適値] -refs [最適値] -scenario 4

    # 複合最適化
    - -q:v [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1 -b_strategy 1 -rdo 1
```

### Phase 7: 総当たり最終検証

---

## h264_qsv - ICQ モード

### 基本情報

- **フレーム構造**: 従来の I/P/B 構造を使用
- **デフォルトGOP**: 256
- **デフォルトB-Frame**: 2
- **デフォルトRefs**: 3
- **既存ベスト**: `-global_quality 25 -bf 15 -refs 8`

### Phase 1: Quality値探査

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

### Phase 2: B-Frame 数（最大負荷テスト）

**範囲**: 8, 10, 12, 14, 15, 16

```yaml
outfile:
  options:
    - -global_quality [最適値] -bf 8
    - -global_quality [最適値] -bf 10
    - -global_quality [最適値] -bf 12
    - -global_quality [最適値] -bf 14
    - -global_quality [最適値] -bf 15
    - -global_quality [最適値] -bf 16
```

### Phase 3: 参照フレーム数（最大負荷テスト）

**範囲**: 4, 6, 8, 10, 12, 14, 16

```yaml
outfile:
  options:
    - -global_quality [最適値] -bf [最適値] -refs 4
    - -global_quality [最適値] -bf [最適値] -refs 6
    - -global_quality [最適値] -bf [最適値] -refs 8
    - -global_quality [最適値] -bf [最適値] -refs 10
    - -global_quality [最適値] -bf [最適値] -refs 12
    - -global_quality [最適値] -bf [最適値] -refs 14
    - -global_quality [最適値] -bf [最適値] -refs 16
```

### Phase 4: GOP サイズ

**範囲**: 120, 180, 240, 256, 300

```yaml
outfile:
  options:
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -g 120
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -g 180
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -g 240
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -g 256
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -g 300
```

### Phase 5: QSV高度なオプション

```yaml
outfile:
  options:
    # MBBRC（マクロブロックレベルBRC）
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -mbbrc 1

    # アダプティブフレーム配置
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -adaptive_b 1
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1

    # RDO
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -rdo 1

    # 複合最適化
    - -global_quality [最適値] -bf [最適値] -refs [最適値] -mbbrc 1 -adaptive_i 1 -adaptive_b 1 -rdo 1
```

### Phase 6: 総当たり最終検証

---

## h264_qsv - LA-ICQ モード

### 基本情報

- **フレーム構造**: 従来の I/P/B 構造を使用
- **デフォルトGOP**: 256
- **デフォルトB-Frame**: 2
- **デフォルトRefs**: 3
- **デフォルトLook-ahead**: false
- **デフォルトLook-ahead Depth**: 0
- **既存ベスト**: `-global_quality 25 -look_ahead 1 -bf 15 -refs 8`

### Phase 1: Quality値探査

**範囲**: 20-32

```yaml
outfile:
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

### Phase 2: Look-ahead Depth

**範囲**: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100

```yaml
outfile:
  options:
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 10
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 20
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 30
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 40
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 50
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 60
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 70
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 80
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 90
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth 100
```

**目的**: 先読みフレーム数と画質の関係を確認

### Phase 3: Look-ahead Downsampling

**選択肢**: off, 2x, 4x

```yaml
outfile:
  options:
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -look_ahead_downsampling off
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -look_ahead_downsampling 2x
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -look_ahead_downsampling 4x
```

**目的**: ダウンサンプリングの画質への影響を確認

### Phase 4: B-Frame 数（最大負荷テスト）

**範囲**: 8, 10, 12, 14, 15, 16

```yaml
outfile:
  options:
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf 8
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf 10
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf 12
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf 14
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf 15
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf 16
```

### Phase 5: 参照フレーム数（最大負荷テスト）

**範囲**: 4, 6, 8, 10, 12, 14, 16

```yaml
outfile:
  options:
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs 4
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs 6
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs 8
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs 10
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs 12
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs 14
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs 16
```

### Phase 6: GOP サイズ

**範囲**: 120, 180, 240, 256, 300

```yaml
outfile:
  options:
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -g 120
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -g 180
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -g 240
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -g 256
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -g 300
```

### Phase 7: QSV高度なオプション

```yaml
outfile:
  options:
    # アダプティブフレーム配置
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -adaptive_b 1
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1

    # RDO
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -rdo 1

    # 複合最適化
    - -global_quality [最適値] -look_ahead 1 -look_ahead_depth [最適値] -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1 -rdo 1
```

### Phase 8: 総当たり最終検証

---

## hevc_qsv - CQP モード

### 基本情報

- **フレーム構造**: GPB モード使用（P-Frame を B-Frame として扱う）
- **既存フレーム比率**: `I/P/B: 15.0 / 0.0 / 3582.0` ← **P が 0 = GPB モード**
- **デフォルトGOP**: 248
- **デフォルトB-Frame**: 3
- **デフォルトRefs**: 1
- **デフォルトGPB**: true
- **既存ベスト**: `-q:v 20 -bf 15 -refs 8 -vf vpp_qsv=format=p010le`

### Phase 1: QP値探査

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

### Phase 2: GPB モードの比較

```yaml
outfile:
  options:
    # GPBモード無効（従来のP/B分離）
    - -q:v [最適値] -gpb 0

    # GPBモード有効（デフォルト、Pを全てBとして扱う）
    - -q:v [最適値] -gpb 1
```

**目的**: GPB モードの圧縮効率と画質への影響を確認

**予想される結果**:

- `-gpb 0`: P-Frame と B-Frame が分離される
- `-gpb 1`: P-Frame = 0, B-Frame が増える（既存データと一致）

### Phase 3: 10bit対応テスト

```yaml
outfile:
  options:
    - -q:v [最適値] -gpb [最適値]
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le
    - -q:v [最適値] -gpb [最適値] -profile main10
    - -q:v [最適値] -gpb [最適値] -profile main10 -vf vpp_qsv=format=p010le
```

**目的**: 10bit エンコードの画質向上効果を確認

### Phase 4: B-Frame 数（最大負荷テスト）

**範囲**: 8, 10, 12, 14, 15, 16

```yaml
outfile:
  options:
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 8
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 10
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 12
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 14
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 15
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 16
```

### Phase 5: 参照フレーム数（最大負荷テスト）

**範囲**: 2, 4, 6, 8, 10, 12

```yaml
outfile:
  options:
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 2
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 4
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 6
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 8
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 10
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 12
```

### Phase 6: GOP サイズ

**範囲**: 120, 180, 240, 248, 300

```yaml
outfile:
  options:
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 120
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 180
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 240
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 248
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 300
```

### Phase 7: QSV高度なオプション

```yaml
outfile:
  options:
    # タイル設定
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -tile_cols 2
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -tile_rows 2
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -tile_cols 2 -tile_rows 2

    # RDO
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -rdo 1

    # 変換スキップ
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -transform_skip 1

    # 複合最適化
    - -q:v [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -rdo 1 -transform_skip 1
```

### Phase 8: 総当たり最終検証

---

## hevc_qsv - ICQ モード

### 基本情報

- **フレーム構造**: GPB モード使用（P-Frame を B-Frame として扱う）
- **既存フレーム比率**: `I/P/B: 15.0 / 0.0 / 3582.0` ← **P が 0 = GPB モード**
- **デフォルトGOP**: 248
- **デフォルトB-Frame**: 3
- **デフォルトRefs**: 1
- **デフォルトGPB**: true
- **既存ベスト**: `-global_quality 21 -bf 15 -refs 8 -vf vpp_qsv=format=p010le`

### Phase 1: Quality値探査

**範囲**: 18-28

```yaml
outfile:
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

### Phase 2: GPB モードの比較

```yaml
outfile:
  options:
    # GPBモード無効（従来のP/B分離）
    - -global_quality [最適値] -gpb 0

    # GPBモード有効（デフォルト、Pを全てBとして扱う）
    - -global_quality [最適値] -gpb 1
```

**目的**: GPB モードの圧縮効率と画質への影響を確認

### Phase 3: 10bit対応テスト

```yaml
outfile:
  options:
    - -global_quality [最適値] -gpb [最適値]
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le
    - -global_quality [最適値] -gpb [最適値] -profile main10
    - -global_quality [最適値] -gpb [最適値] -profile main10 -vf vpp_qsv=format=p010le
```

### Phase 4: B-Frame 数（最大負荷テスト）

**範囲**: 8, 10, 12, 14, 15, 16

```yaml
outfile:
  options:
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 8
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 10
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 12
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 14
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 15
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf 16
```

### Phase 5: 参照フレーム数（最大負荷テスト）

**範囲**: 2, 4, 6, 8, 10, 12

```yaml
outfile:
  options:
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 2
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 4
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 6
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 8
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 10
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs 12
```

### Phase 6: GOP サイズ

**範囲**: 120, 180, 240, 248, 300

```yaml
outfile:
  options:
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 120
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 180
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 240
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 248
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -g 300
```

### Phase 7: Extended BRC と Look-ahead

```yaml
outfile:
  options:
    # Extended BRC
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -extbrc 1

    # Look-ahead depth（extbrc有効時のみ）
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -extbrc 1 -look_ahead_depth 20
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -extbrc 1 -look_ahead_depth 40
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -extbrc 1 -look_ahead_depth 60
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -extbrc 1 -look_ahead_depth 80
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -extbrc 1 -look_ahead_depth 100
```

### Phase 8: QSV高度なオプション

```yaml
outfile:
  options:
    # MBBRC
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -mbbrc 1

    # タイル設定
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -tile_cols 2 -tile_rows 2

    # RDO
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -rdo 1

    # アダプティブフレーム配置
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -adaptive_i 1 -adaptive_b 1

    # 複合最適化
    - -global_quality [最適値] -gpb [最適値] -vf vpp_qsv=format=p010le -bf [最適値] -refs [最適値] -extbrc 1 -look_ahead_depth 60 -mbbrc 1 -rdo 1 -adaptive_i 1 -adaptive_b 1
```

### Phase 9: 総当たり最終検証

---

## av1_qsv - CQP モード

### 基本情報

- **フレーム構造**: AV1独自の構造（I/P/B ではなく Key/Inter + Altref）
- **既存フレーム比率**: `I/P/B: 15.0 / 3582.0 / 0.0` ← **B-Frame は存在しない**
- **デフォルトGOP**: 248
- **デフォルトB-Frame**: 0（存在しない）
- **デフォルトRefs**: 1
- **既存ベスト**: `-q:v 53 -vf vpp_qsv=format=p010le`
- **重要**: `-bf` オプションは**無効**（AV1 には B-Frame が存在しない）

### Phase 1: QP値探査

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

### Phase 2: 10bit対応テスト

```yaml
outfile:
  options:
    - -q:v [最適値]
    - -q:v [最適値] -vf vpp_qsv=format=p010le
```

### Phase 3: GOP サイズ

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

### Phase 4: QSV高度なオプション

```yaml
outfile:
  options:
    # タイル設定（並列処理）
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

### Phase 5: 総当たり最終検証

---

## av1_qsv - ICQ モード

### 基本情報

- **フレーム構造**: AV1独自の構造（I/P/B ではなく Key/Inter + Altref）
- **既存フレーム比率**: `I/P/B: 15.0 / 3582.0 / 0.0` ← **B-Frame は存在しない**
- **デフォルトGOP**: 248
- **デフォルトB-Frame**: 0（存在しない）
- **デフォルトRefs**: 1
- **既存ベスト**: `-global_quality 24 -vf vpp_qsv=format=p010le`
- **重要**: `-bf` オプションは**無効**（AV1 には B-Frame が存在しない）

### Phase 1: Quality値探査

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

### Phase 2: 10bit対応テスト

```yaml
outfile:
  options:
    - -global_quality [最適値]
    - -global_quality [最適値] -vf vpp_qsv=format=p010le
```

### Phase 3: GOP サイズ

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

### Phase 4: Extended BRC と Look-ahead

```yaml
outfile:
  options:
    # Extended BRC
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1

    # Look-ahead depth（extbrc有効時のみ）
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 20
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 40
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 60
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 80
    - -global_quality [最適値] -vf vpp_qsv=format=p010le -extbrc 1 -look_ahead_depth 100
```

### Phase 5: QSV高度なオプション

```yaml
outfile:
  options:
    # タイル設定（並列処理）
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

### Phase 6: 総当たり最終検証

---

## 検証実行の推奨手順

### 1. Phase 1 から順次実行

各エンコーダーの Phase 1 から順番に実行し、最適値を特定してから次のフェーズへ進む。

### 2. VMAF 目標値の確認

- **VMAF harmonic_mean**: 93.0 以上
- **VMAF mean**: 93.0 以上
- **SSIM mean**: 0.99 以上

### 3. 圧縮率の評価

- **compress_rate**: 低いほど高圧縮（目標: 0.7以下）
- **bitrate**: 低いほど良い

### 4. 処理時間の考慮

- **ソフトウェアエンコード**: 処理時間と画質のバランスを考慮
- **ハードウェアエンコード（QSV）**: 処理時間はほぼ一定のため最大負荷設定を積極的に試す

### 5. フレーム構造の確認

エンコード後、`ffprobe` または結果の `I/P/B frames` を確認：

- **H.264**: I/P/B の比率を確認
- **HEVC (GPB=1)**: P が 0、B が増加していることを確認
- **AV1**: B が 0 であることを確認（正常）

### 6. 結果の記録

各フェーズの最適値を記録し、次のフェーズで使用する。最終的に全パラメータの組み合わせで総当たり検証を実施。

---

## 注意事項

### AV1 エンコーダーの特性

- **B-Frame は存在しない**: `-bf` オプションは無視される
- **Altref フレーム**: エンコーダーが自動的に最適な構造を決定
- **階層的予測**: `hierarchical-levels` パラメータで制御可能（libsvtav1）

### HEVC QSV の GPB モード

- **デフォルトで有効**: P-Frame を B-Frame として扱う
- **圧縮効率向上**: 参照の柔軟性が増す
- **無効化**: `-gpb 0` で従来の P/B 分離モードに切り替え可能

### HWEnc (QSV) の特性

- **処理時間がほぼ一定**: プリセットや負荷を変えても処理時間はほとんど変わらない
- **最大負荷設定推奨**: `-bf 16`, `-refs 16`, `-look_ahead_depth 100` などの最大値を積極的に試す
- **タイル並列処理**: `-tile_cols`, `-tile_rows` で並列処理を有効化できる

### ソフトウェアエンコードの特性

- **処理時間と画質のトレードオフ**: プリセットや参照フレーム数で大きく変わる
- **細かいチューニングが可能**: `*-params` で詳細な制御が可能

### 総当たり検証の実施タイミング

Phase 1-6で最適値が特定できたら、それらの組み合わせで総当たり検証を実施し、最終的な最適パラメータを決定する。
