from monitors.penboard import PenboardMonitor


def main() -> None:
    monitor = PenboardMonitor()

    print("Fetching Penboard What's New ...")

    items = monitor.fetch()

    print(f"\nParsed items: {len(items)}")

    for item in items[:5]:
        print("\n" + "=" * 60)
        print(f"ID:        {item.item_id}")
        print(f"Title:     {item.title}")
        print(f"Brand:     {item.brand}")
        print(f"Model:     {item.model}")
        print(f"Year:      {item.year}")
        print(f"Colour:    {item.colour}")
        print(f"Condition: {item.condition}")
        print(f"Nib:       {item.nib}")
        print(f"Price:     {item.price} {item.currency}")
        print(f"URL:       {item.url}")


if __name__ == "__main__":
    main()
