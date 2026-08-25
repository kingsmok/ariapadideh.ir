# درگاه‌های پرداخت — راهنمای کامل

این سند معماری، پیکربندی و جریان هر درگاه را توضیح می‌دهد. تمام مسیرها بر اساس مستندات رسمی هر سرویس پیاده شده‌اند.

## فهرست درگاه‌ها

| شناسه | سرویس | مستندات رسمی | حالت تست |
|---|---|---|---|
| `mock` | درگاه آزمایشی داخلی | — | همیشه تستی |
| `zarinpal` | زرین‌پال | payment.zarinpal.com/docs (PG v4) | sandbox.zarinpal.com |
| `idpay` | آی‌دی‌پی | idpay.ir/web-service/v1.1 | هدر `X-SANDBOX: 1` |
| `digipay` | دیجی‌پی | mydigipay.com/developers/docs/upg | uat.mydigipay.info |
| `snapppay` | اسنپ‌پی (اقساطی) | ارسال مستقیم به پذیرنده (محرمانه) | sandbox.snappymarket.ir |
| `sepah` | بانک سپه | PSP همکار سپه — الگوی استاندارد شاپرک | ندارد |

## فعال‌سازی

1. **.env یا پنل مدیریت** (تنظیمات → درگاه پرداخت) — پنل بر `.env` اولویت دارد:
   ```env
   ENABLED_PAYMENT_GATEWAYS=mock,zarinpal,sepah
   ```
   ترتیب = ترتیب نمایش به مشتری. درگاهی که کلیدش تنظیم نشده باشد به‌صورت خودکار از لیست حذف می‌شود (mock همیشه هست).

2. **واحد پول**: `PAYMENT_CURRENCY_UNIT=toman` (پیش‌فرض). همه درگاه‌های ایرانی ریالی‌اند؛ اگر مبالغ فروشگاه تومان باشد خودکار ×۱۰ می‌شود.

## جریان کلی پرداخت

```
checkout (فرم + انتخاب درگاه)
   → order ثبت می‌شود (pending) + PaymentTransaction(pending)
   → gateway.create_payment(order, callback_url)
       ├─ redirect ساده (زرین‌پال/آی‌دی‌پی/دیجی‌پی/اسنپ‌پی) → 302
       └─ redirect فرمی (سپه/شاپرک) → صفحه واسط /payment/redirect/<order> با auto-submit
   → مشتری در درگاه پرداخت می‌کند
   → کال‌بک /payment/callback/<order_number> (GET یا POST)
   → gateway.verify_payment(txn, callback_data)
       ├─ موفق → txn=success + tracking_code، order=confirmed/paid، ایمیل، خالی‌کردن سبد
       └─ ناموفق/لغو → txn=failed|cancelled، پیام خطا، امکان «پرداخت مجدد»
```

- تشخیص درگاه در کال‌بک از **تراکنش ثبت‌شده** انجام می‌شود نه ورودی کاربر (امنیتی).
- کال‌بک idempotent است؛ کال‌بک تکراری بعد از موفقیت تغییری ایجاد نمی‌کند.
- قبل از تأیید، «مبلغ» و «شناسه سفارش» با سفارش تطبیق داده می‌شوند (دیجی‌پی و سپه).

## جزئیات هر درگاه

### زرین‌پال (PG v4)
- **کلیدها**: `zarinpal_merchant_id` (UUID ۳۶ کاراکتری)، `zarinpal_sandbox`
- درخواست: `POST /pg/v4/payment/request.json` با `{merchant_id, amount(ریال), callback_url, description, metadata{mobile,email}}` → `data.code=100` + `authority`
- هدایت: `GET /pg/StartPay/{authority}`
- کال‌بک: `GET ?Authority=…&Status=OK|NOK`
- تأیید: `POST /pg/v4/payment/verify.json` → `code=100` (موفق) یا `101` (قبلاً تأییدشده) + `ref_id`
- Sandbox: با `zarinpal_sandbox=true` همه مسیرها به `sandbox.zarinpal.com` می‌روند.

### آی‌دی‌پی (v1.1)
- **کلیدها**: `idpay_api_key`، `idpay_sandbox`
- درخواست: `POST https://api.idpay.ir/v1.1/payment` با هدر `X-API-KEY` (+ `X-SANDBOX:1`) و `{order_id, amount(ریال), phone, mail, desc, callback}` → `{id, link}`
- کال‌بک: POST یا GET (بسته به تنظیم پنل آی‌دی‌پی) با `id / order_id / status` (2 = لغو)
- تأیید: `POST /v1.1/payment/verify` → `status=100|101` + `track_id`

### دیجی‌پی (UPG)
- **کلیدها**: `digipay_client_id`, `digipay_client_secret`, `digipay_username`, `digipay_password`, `digipay_sandbox`
- احراز هویت: `POST {base}/oauth/token` با هدر Basic (`client_id:client_secret`) و فرم `grant_type=password`
- تیکت: `POST {base}/tickets/business?type=11` با هدرهای `Agent: WEB` و `Digipay-Version: 2022-02-02` و `{cellNumber, amount(ریال), providerId(=شماره سفارش), callbackUrl}` → `redirectUrl`
  - صفحه دیجی‌پی خودش ابزار پرداخت را نشان می‌دهد (کیف پول / اعتباری BNPL / IPG).
- کال‌بک: `POST {amount, providerId, trackingCode, result: SUCCESS|FAILURE, type, rrn, isCredit}`
- تأیید: `POST {base}/purchases/verify?tracingCode=…&type=…` — **قبل از فراخوانی، amount و providerId با سفارش تطبیق داده می‌شود** (توصیه رسمی مستندات).
- پایه‌ها: عملیاتی `api.mydigipay.com/digipay/api` — تستی `uat.mydigipay.info/digipay/api`

### اسنپ‌پی (خرید اقساطی / BNPL)
- **کلیدها**: `snapppay_client_id`, `snapppay_client_secret`, `snapppay_username`, `snapppay_password`, `snapppay_sandbox`
- نکته: مستندات اسنپ‌پی به‌صورت PDF محرمانه به پذیرنده ارسال می‌شود؛ مسیرها بر پایه سرویس‌های شناخته‌شده پیاده شده و در صورت مغایرت با PDF خودتان، فقط کافی است آدرس‌ها در کلاس `SnappPayGateway` تنظیم شوند.
- احراز هویت: `POST {base}/api/online/v1/oauth/token` (Basic + password grant)
- درخواست: `POST {base}/api/online/payment/v1/token` با `{amount(ریال), telephone, postalAddress, invoiceNumber, returnUrl}` → `paymentToken` + `paymentPageUrl`
- کال‌بک: `POST {status, paymentToken}`
- تأیید: `POST …/payment/v1/verify` و سپس `…/payment/v1/settle` (بهترین تلاش)
- پایه‌ها: عملیاتی `payment.snapppay.ir` — تستی `sandbox.snappymarket.ir`
- سرویس‌های تکمیلی موجود در API و آماده توسعه بعدی: `revert`, `cancel`, `update`, `status`, `offer/v1/eligible`

### بانک سپه (الگوی استاندارد شاپرک)
- بانک سپه درگاه IPG مستقل ندارد و پذیرندگی آن از طریق شرکت‌های PSP همکار صادر می‌شود؛ این درایور با الگوی رایج «توکن شاپرک (سپهر)» پیاده شده که بیشتر PSPهای پذیرندهٔ سپه استفاده می‌کنند.
- **کلیدها**: `sepah_terminal_id`، و در صورت PSP متفاوت: `sepah_api_base`, `sepah_pay_base`
- توکن: `POST {api}/V1/PeymentApi/GetToken` با فرم `{terminalID, Amount(ریال، حداقل ۱٬۰۰۰), callbackURL, invoiceID(=شماره سفارش), CellNumber}` → `{Status:'0', Accesstoken}`
- هدایت کاربر: **POST فرم** به `{pay_base}` با `{TerminalID, token, getMethod:1}` — صفحه واسط `/payment/redirect/<order>` این فرم را خودکار submit می‌کند.
- کال‌بک: `POST {State, ResNum(=invoiceID), RefNum, TraceNo}` — `State=OK` یعنی پرداخت انجام شده
- تأیید: `POST {api}/V1/PeymentApi/Verify` با `{terminalID, refnum}` → `Status='0'` + مبلغ (تطبیق داده می‌شود)
- ⚠️ درگاه «سپهر» (`sepehr.shaparak.ir`) متعلق به **بانک صادرات** است؛ اگر پذیرندگی شما از PSP دیگری است فقط دو آدرس base را از پنل عوض کنید.

## رابط کاربری

- صفحه checkout زیر «پرداخت آنلاین» کارت‌های درگاه را با توضیح و نشان نشان می‌دهد (`rahsa-*`).
- صفحه سفارش برای پرداخت‌های ناتمام دکمه «پرداخت مجدد» دارد (`/order/<شماره>/pay`).
- صفحه `/order/<شماره>/card-payment` شماره کارت را از تنظیمات (`bank_card_number`) می‌خواند.

## تست

```bash
.venv/bin/python -m pytest tests/test_payment_gateways.py -q
```

پوشش: ساخت پرداخت و تأیید هر ۷ درایور (موفق/ناموفق/لغو/تطبیق مبلغ)، جریان کامل checkout→callback (زرین‌پال، سپه با هدایت فرمی)، پرداخت مجدد، دکمه خرید محصول و صفحه کارت‌به‌کارت. تمام تماس‌های HTTP ماک شده‌اند.
