from monitors.penboard import PenboardMonitor


def main() -> None:
    monitor = PenboardMonitor()

    print("Fetching Penboard What's New ...")

    items = monitor.fetch()

    print(f"\nParsed items: {len(items)}")

    for item in items[:5]:
        print("\n" + "=" * 60)
        print(f"ID:          {item.item_id}")
        print(f"Title:       {item.title}")
        print(f"Price:       {item.price} {item.currency}")
        print(f"Condition:   {item.condition}")
        print(f"Year:        {item.year}")
        print(f"URL:         {item.url}")
        print(f"Image:       {item.image_url}")
        print(f"Description: {item.description}")


if __name__ == "__main__":
    main()
