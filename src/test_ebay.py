from monitors.ebay import EbayMonitor


def main() -> None:
    mock_api_item = {
        "itemId": "v1|123456789|0",
        "title": "Vintage Soennecken 111 Extra Fountain Pen",
        "itemWebUrl": "https://www.ebay.de/itm/123456789",
        "price": {
            "value": "149.00",
            "currency": "EUR",
        },
        "condition": "Used",
        "itemLocation": {
            "country": "DE",
        },
        "image": {
            "imageUrl": "https://example.com/soennecken.jpg",
        },
    }

    item = EbayMonitor.parse_item(mock_api_item)

    print(f"ID:        {item.item_id}")
    print(f"Title:     {item.title}")
    print(f"Price:     {item.price} {item.currency}")
    print(f"Condition: {item.condition}")
    print(f"Location:  {item.location}")
    print(f"URL:       {item.url}")


if __name__ == "__main__":
    main()
