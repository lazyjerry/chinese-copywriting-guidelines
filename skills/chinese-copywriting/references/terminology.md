# 名詞與單位規範

規則 9（專有名詞使用正確的大小寫）與規則 10（不要使用不道地的縮寫）的判定依據，另含補掃時要先過的白名單。

**這是一份規範，不是一張窮舉表。** 主體是判定方法；底下的分領域對照表只是例示。查不到某個詞不代表它寫錯了，回判定順序重新走一遍。

檢查腳本不讀這份文件，只有模型讀。腳本頂端的 `EXCEPTION_TERMS` 是另一回事，兩邊各自維護。

## 判定順序

逐筆候選都照這個順序走，命中就停：

1. **白名單** — 命中豁免類就不報；命中認可類就依該欄的指示補報。
2. **分領域對照表** — 先判文件屬哪個領域，只套該領域的表。跨領域文件取交集，兩張表衝突時從寬，也就是不報。
3. **可指認的官方來源** — 能講出這個詞的官方寫法出自哪裡（官網、規格書、廠商文件）才算數。
4. **都不命中就不報。**

## 三級結論

| 結論 | 條件 | 處置 |
| --- | --- | --- |
| 違規 | 有明確官方寫法，原文明確違反 | 進違規清單，可依處置方式修正 |
| 建議 | 有把握但屬風格取捨，或屬表外新名詞 | 進違規清單但標「建議」，一律不自動修 |
| 不報 | 沒把握 | 不列入清單 |

**寧可漏報，不可誤糾。** 誤糾一個專業術語，讀者會失去對整份報告的信任，代價遠高於漏掉一條。拿不準就歸「不報」。

## 白名單

分兩類，**意義相反，不可混用**：豁免類是「別動它」，認可類是「這是單位，去補規則 3」。

### 豁免類：命中則不報

這樣寫是對的。

| 分類 | 內容 |
| --- | --- |
| 通用技術縮寫 | API、URL、URI、HTTP、HTTPS、HTML、CSS、SQL、JSON、XML、YAML、SDK、CLI、GUI、IDE、CI/CD、DNS、TLS、SSH、VPN、RAM、CPU、GPU、SSD、USB、K8s |
| 醫學 | MRI、CT、PET、ICU、ECG、EEG、CPR、BMI、DNA、RNA、PCR、HbA1c |
| 金融 | IPO、ETF、APR、ROI、GDP、CPI、EPS、P/E、M&A、KYC、AML |
| 學術與出版 | DOI、ISBN、ISSN、IRB、PDF、arXiv、et al. |
| 工程與製造 | CAD、CNC、PCB、IoT、OEM、ODM、QA、QC、SOP |
| 產品官方寫法 | 官方定義即為無空格或特殊大小寫的名詞，例如「豆瓣FM」、eBay、iPhone、macOS |
| 引用與商標 | 引述原文、法律條文、商標既定樣式，一律照原樣保留 |

縮寫是否「不道地」看它在該領域是否為公認寫法，不看它有幾個字母。`K8s` 在雲原生領域是公認縮寫，`Ts` 在任何領域都不是。

### 認可類：命中則據以補報

這是合法單位，寫法沒問題，但**數字與單位之間仍要空格**，依規則 3 補報。

腳本的 `UNITS` 只收 23 個常見單位，以下是它抓不到、補掃要自己認的：

| 領域 | 單位 |
| --- | --- |
| 資訊與儲存 | kHz、ms、μs、ns、GiB、MiB、TiB、KiB、Mbps 以外的 kbps／Tbps、IOPS |
| 電子與電力 | mAh、Ah、W、kW、mW、V、mV、kV、A、mA、Ω、dB、dBm、Hz 系列的 kHz／THz |
| 半導體與材料 | nm、μm、Å、mil |
| 物理與化學 | kPa、MPa、bar、mol、mmol、kJ、J、cal、N、Pa、K |
| 醫學 | mmHg、mg/dL、mmol/L、mEq/L、IU、μg、ng、bpm |
| 金融 | bps（基點，與網路速率的 bps 不同，看上下文） |
| 日常 | kcal、ha、坪、℃（帶溫標時數字與符號之間留白，`25 °C` 是正確寫法） |

單字母單位（`s`、`m`、`A`、`K`、`W` 單獨出現時）**刻意不報**——`the 90s`、`3m` 這類英文會被大量誤判。只有在上下文明確是量測值時才列，且標「建議」。

### 單位與英文寫法的重疊

檢查腳本的 `--units` 帶進來的單位命中一律標 `low`，要在裁決步驟逐筆判。原因是「數字緊接英文」這個形狀，單位跟產品代號、規格名、俗寫長得一模一樣：

| 寫法 | 看起來像 | 實際是 | 該不該補空格 |
| --- | --- | --- | --- |
| `5G` | 5 高斯 | 行動網路制式 | 不該 |
| `4K` | 4 克耳文 | 螢幕解析度 | 不該 |
| `3in1` | 3 英吋 | 三合一配方 | 不該 |
| `2T` | 2 特斯拉 | 口語的 `2TB` | 不該 |
| `3bar` | — | 胎壓 3 巴 | 該 |
| `65W` | — | 功率 65 瓦 | 該 |
| `24h` | — | 24 小時 | 該 |

判準照這個順序走：

1. **這個數字後面接的東西，換成中文唸得出量詞嗎？** 「三巴」「六十五瓦」唸得出來，「五高斯的網路」唸不出來。
2. **前後文有沒有量測語境？** 出現「輸出」「容量」「壓力」「待機」這類詞，多半真的是量測值；出現「支援」「制式」「規格」「配方」多半是代號。
3. **這個寫法在該領域是不是既定名稱？** `5G`、`4K`、`Wi-Fi 6` 是名稱，名稱不拆。
4. **拿不準就 drop**，理由寫「無法確定是量測值或產品代號」。

代號類命中要 drop，不要改寫成別的形式——`5G` 不是排版問題，改成 `5 G` 反而是錯的。

## 分領域對照表

以下每張表都是例示，**非窮舉**。查不到不等於寫錯，回判定順序。

### 軟體開發

| 正確寫法 | 常見錯寫 |
| --- | --- |
| GitHub | Github、github、GITHUB、gitHub |
| GitLab | Gitlab、gitlab |
| JavaScript | Javascript、javascript、JS 當正式名稱用時 |
| TypeScript | Typescript、typescript |
| Node.js | NodeJS、nodejs、Node.JS |
| npm | NPM、Npm |
| PostgreSQL | Postgresql、postgreSQL |
| MySQL | MySql、mysql |
| SQLite | Sqlite、sqlite |
| Kubernetes | KUbernetes、kubernetes 當句首以外時 |
| Docker | docker 當句首以外時 |
| nginx | Nginx（官方一律小寫） |
| Redis | redis |
| GraphQL | GraphQl、Graphql |
| Markdown | MarkDown、markdown |
| Python | python |
| Rust | rust |
| PHP | Php、php |
| Laravel | laravel |
| Vue.js | VueJS、vuejs |
| React | ReactJS 當正式名稱用時 |
| Next.js | NextJS、nextjs |
| Tailwind CSS | TailwindCSS、tailwind |
| WordPress | Wordpress、wordpress |
| Cloudflare | CloudFlare |
| macOS | MacOS、Mac OS、MACOS |
| iOS | IOS、Ios |
| Wi-Fi | WiFi、wifi、Wifi |
| Microsoft Corporation | MicroSoft Corporation、microsoft corporation |
| Foursquare | FourSquare、foursquare |
| Facebook, Inc. | FaceBook, Inc.、facebook, inc. |
| Google | google、GOOGLE |

不道地的縮寫，一律展開：

| 不道地 | 應寫成 |
| --- | --- |
| Ts | TypeScript |
| Js | JavaScript |
| h5 | HTML5 |
| RJS | React |
| nextjs | Next.js |
| FED | 前端開發者 |
| `前端er`、`後端er` | 前端開發者、後端開發者 |

### 硬體與電子

| 正確寫法 | 常見錯寫 |
| --- | --- |
| Wi-Fi 6E | WiFi 6E、wifi6e |
| Bluetooth | BlueTooth、bluetooth |
| Thunderbolt | ThunderBolt |
| NVMe | NVME、nvme |
| Arduino | arduino |
| Raspberry Pi | RaspberryPi、樹莓派 Pi |
| MacBook Pro | Macbook Pro、macbook pro |

### 醫學與生技

| 正確寫法 | 常見錯寫 |
| --- | --- |
| COVID-19 | Covid-19、covid19 |
| SARS-CoV-2 | Sars-Cov-2 |
| mRNA | MRNA、m-RNA |
| CRISPR-Cas9 | Crispr-cas9 |
| PubMed | Pubmed、pubmed |
| WHO | Who（作為組織縮寫時全大寫） |

藥品名與學名的大小寫慣例（商品名首字大寫、學名全小寫）屬專業規範，**不確定一律不報**。

### 金融

| 正確寫法 | 常見錯寫 |
| --- | --- |
| NASDAQ | Nasdaq 在正式文件中、nasdaq |
| S&P 500 | S&P500、SP500 |
| Bitcoin／BTC | bitcoin 作為專有名詞時 |
| Visa | VISA（官方寫法為 Visa） |
| Mastercard | MasterCard（2016 年後官方改為 Mastercard） |
| PayPal | Paypal、paypal |

### 學術與出版

| 正確寫法 | 常見錯寫 |
| --- | --- |
| LaTeX | Latex、latex |
| BibTeX | Bibtex |
| ORCID | Orcid |
| Scopus | SCOPUS |
| Creative Commons | creative commons |

### 設計

| 正確寫法 | 常見錯寫 |
| --- | --- |
| Figma | figma、FIGMA |
| Sketch | sketch 作為軟體名時 |
| Adobe Photoshop | PhotoShop、photoshop |
| InDesign | Indesign |
| Material Design | material design |

## 引用參考

依這份規範判出的違規，引用參考一律指回上游規則：

- 大小寫問題寫 `專有名詞使用正確的大小寫 L166-L198`
- 縮寫問題寫 `不要使用不道地的縮寫 L200-L208`
- 認可類單位補報的空格問題寫 `數字與單位之間需要增加空格 L52-L74`

行號查 [rules.md](rules.md) 的規則索引，不要自行推算。

## 擴充規範

新增條目要附官方來源與所屬領域，寫進對應的那張表；沒有領域歸屬的不收。既有條目的引用參考只增不改。

補掃時判出的表外名詞，在報告末尾的「可補進規範的候選」列出來，附來源，由使用者決定要不要收進這份文件。
