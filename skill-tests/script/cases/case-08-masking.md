---
title: 前端筆記
tags: [前端, CSS, 排版]
summary: 這行frontmatter刻意不加空格，應該整段跳過
---

# 前端排版筆記

## 自動加空格

CSS Text Module Level 4 的 [`text-spacing`](https://www.w3.org/TR/css-text-4/#text-spacing-property) 和 Microsoft 的 [`-ms-text-autospace`](https://msdn.microsoft.com/library/ms531164(v=vs.85).aspx) 可以實現自動為中英文之間增加空白。這一行的連結目標帶了成對括號，遮罩必須整段吃掉。

一般連結不受影響，例如 [pangu.js](https://github.com/vinta/pangu.js) 與 [官方文件](https://leancloud.cn/docs/)。

裸露的網址同樣要遮，像 https://example.com/中文path?q=測試 這種寫法。

自動連結的形式是 <https://example.com/foo> 這樣。

## 程式碼

行內程式碼的內容豁免，例如 `const 變數名 = "值"` 與 `margin:0 auto` 都不該被檢查。

```javascript
// 這段程式碼裡的中文comment不該被檢查
const 設定 = { 名稱: "測試", 數量: 10 };
console.log(`共${設定.數量}筆`);
```

~~~python
# 波浪號圍欄一樣要跳過
資料 = {"鍵": "值10筆"}
~~~

縮排四格的程式碼區塊也一樣：

    function 測試() {
      return "中文String不檢查";
    }

## HTML

行內的 HTML 標籤屬性不檢查，例如 <span class="highlight-中文">重點</span> 與 <img src="/圖片/banner.png" alt="橫幅圖1張">。

## 產品名詞

豆瓣FM 是官方定義的寫法，整體豁免規則一與規則二，不必補空格。

## 結語

以上每一種寫法都應該安靜通過，一項違規都不該出現。
