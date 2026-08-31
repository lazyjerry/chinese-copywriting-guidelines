# 雲端儲存服務導覽

LeanCloud 提供的資料儲存服務圍繞 `AVObject` 進行設計，每個 `AVObject` 都包含與 JSON 相容的 key-value 資料。資料本身是 schema-free 的，不需要事先宣告欄位，直接設定對應的鍵值即可。

## 傳輸與容量

我家的光纖入屋寬頻有 10 Gbps，機房那台伺服器的 SSD 一共有 20 TB。實測從台北機房下載一份 512 MB 的備份檔，平均耗時 4 秒，換算下來大約是 128 MB 的每秒吞吐量。

新款筆電的螢幕寬 2560 px，色準經過原廠校正，色域覆蓋率達 98%，開蓋角度最大 135°，放在桌上使用相當舒適。

## 計價方式

免費方案每月提供 1 GB 儲存空間與 10 萬次 API 請求，超出的部分按量計費。上個月我的專案總共花了 5000 元，其中八成是圖片儲存的費用。

## 開發體驗

官方提供 JavaScript、Swift、Kotlin 三種 SDK，文件寫得相當清楚。我們的客戶有 GitHub、Foursquare、Microsoft Corporation、Google、Facebook, Inc.。團隊裡需要一位熟悉 TypeScript、HTML5，至少理解一種框架（如 React、Next.js）的前端開發者。

賈伯斯那句話是怎麼說的？「Stay hungry, stay foolish.」做工具的人大概都懂這種心情。推薦你閱讀 *Hackers & Painters: Big Ideas from the Computer Age*，非常地有趣。

嗨！你知道嘛？今天前台的小妹跟我說「喵」了哎！核磁共振成像（NMRI）是什麼原理都不知道？JFGI！

早期文件放在 [官方網站](https://leancloud.cn/) 與 [pangu.js](https://github.com/vinta/pangu.js)，兩邊的說明都值得一讀。
