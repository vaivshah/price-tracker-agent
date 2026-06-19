---
name: price-check
description: >
  Look up the current price of a product. The user may provide a URL
  or a product name. Return structured JSON.
---

# Price Check

When the user asks about a product price:

1. If they gave a URL, use the browser to navigate to it.
2. If they gave a product name, search the web for it first.
3. Extract the product details and price information.
4. Return ONLY this JSON block (no other text):

```json
{
  "skill": "price-check",
  "product": {
    "name": "Sony WH-1000XM5",
    "brand": "Sony",
    "category": "electronics",
    "model_number": "WH-1000XM5"
  },
  "variant": {
    "variant_name": "Black",
    "attributes": {
      "color": "Black"
    }
  },
  "listings": [
    {
      "retailer": "amazon",
      "source_url": "https://amazon.com/dp/B0CXYZ...",
      "price": 278.00,
      "currency": "USD",
      "rating": 4.6,
      "rating_count": 12341,
      "availability": "in_stock"
    }
  ],
  "summary": "Sony WH-1000XM5: $278 on Amazon"
}
```

If you cannot find the price, return:
```json
{
  "skill": "price-check",
  "error": "Could not find pricing",
  "summary": "I couldn't find the price for that product."
}
```
