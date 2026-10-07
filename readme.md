# PenWatch

PenWatch is a personal, non-commercial monitoring and notification service for rare fountain pens, writing instruments, and related collectibles.

It monitors publicly accessible marketplace, dealer, auction, and community listings for a small set of collector-defined search profiles and sends private notifications when a relevant new item is found.

PenWatch is operated by a single private collector and is not a commercial service.

---

## Reddit API reviewers

**If you are reviewing this repository in connection with a Reddit API access request, the relevant documentation is here:**

### [Reddit Data Access and API Use](docs/reddit-data-access.md)

The proposed Reddit integration has a narrow, read-only purpose:

> Monitor recent public submissions in selected collecting-related subreddits for a small set of predefined fountain-pen and collectible search terms and privately notify the owner when a matching public post appears.

### Reddit data PenWatch needs

PenWatch requires only the public submission data necessary for this matching process, such as:

- submission ID;
- subreddit;
- title;
- public self-text;
- permalink;
- submission timestamp.

The integration does not require private Reddit data.

### PenWatch will use Reddit data only to

- read recent public submissions from explicitly configured subreddits;
- compare those submissions against a small predefined collector watchlist;
- privately notify the single PenWatch user when a relevant item is detected;
- retain the minimum identifier/state information required to prevent duplicate notifications.

### PenWatch will not

- create posts or comments;
- vote;
- send Reddit messages;
- perform moderation actions;
- access private Reddit content;
- profile Reddit users;
- monitor individual Reddit users;
- redistribute or sell Reddit data;
- provide Reddit data to third parties;
- use Reddit data for advertising;
- use Reddit data for AI or machine-learning training.

The Reddit integration is **not currently active** and will not be activated unless appropriate Reddit API access has been granted.

The detailed data-access rationale, data-minimization approach, and the reason the use case cannot be implemented through Devvit's subreddit-installed event model are documented in:

**[docs/reddit-data-access.md](docs/reddit-data-access.md)**

---

## Purpose

Rare collectible writing instruments and related historical material are offered across many independent sources. Relevant items may appear infrequently and remain visible only for a limited period.

PenWatch automates the repetitive task of checking those public sources.

The architecture deliberately separates:

1. source-specific acquisition and parsing;
2. normalized item data;
3. collector-specific watchlist matching;
4. persistent deduplication state;
5. private push notifications.

A source integration therefore retrieves public listings, while the central watchlist logic determines whether an item is relevant.

---

## Current source integrations

| Source | Status | Coverage |
|---|---|---|
| Penboard | Operational | New and searchable existing inventory |
| MARTINI Auctions | Operational | Public auction inventory |
| Interpens | Operational | Public dealer inventory |
| VintagePens | Operational | Public feed/inventory |
| Catawiki | Operational / being extended | Paginated fountain-pen collection |
| eBay | Integration in progress | API credentials granted; implementation/testing pending |
| Reddit | Inactive / API access pending | Proposed read-only public submission monitoring |

### Penboard

The Penboard integration combines:

- the `What's New` inventory;
- searchable existing inventory for relevant manufacturers;
- locally performed watchlist matching;
- deduplication using Penboard item IDs.

Monitoring only `What's New` proved insufficient because relevant older inventory can remain available without appearing on that page.

The expanded parser is therefore designed to discover relevant items from the searchable inventory as well.

### MARTINI Auctions

PenWatch retrieves publicly available auction inventory and evaluates newly discovered items against the configured watchlists.

### Interpens

PenWatch monitors publicly accessible dealer inventory and evaluates newly discovered items against the configured watchlists.

### VintagePens

PenWatch monitors the available public feed/inventory and evaluates newly discovered items against the configured watchlists.

### Catawiki

The Catawiki integration currently:

- scans the public fountain-pen collection;
- follows pagination across the collection;
- determines the reported collection size dynamically;
- deduplicates lots using their item IDs;
- applies a delay between paginated requests.

Collection cards do not necessarily contain all information required for every PenWatch search.

For example, detailed nib information may only be present on the individual lot page.

The planned extension therefore follows a selective two-stage model:

1. retrieve the collection index;
2. identify potentially relevant lots;
3. retrieve detail pages only where additional information is required;
4. enrich the normalized searchable text;
5. perform final watchlist matching.

This approach is intended to minimize unnecessary requests.

### eBay

eBay API credentials have been granted and the source integration is currently being implemented.

The intended architecture is the same as for the other PenWatch sources:

    eBay API
        |
        v
    normalized listing data
        |
        v
    central watchlist matching
        |
        v
    persistent deduplication
        |
        v
    private ntfy notification

Credentials and secrets are stored outside the repository.

The eBay integration will be marked operational only after API retrieval, matching, deduplication, and notification behaviour have been tested successfully.

---

## Watchlists

PenWatch currently contains collector-defined searches for:

- Soennecken 111 / 222;
- Pelikan light tortoiseshell variants;
- Pelikan calendar 1987;
- Pelikan price list 30B;
- Pelikan Knickebein;
- Pelikan M800 Ocean Swirl;
- Pelikan fountain pens with `BBB` or `OBBB` nibs, independent of model.

Watchlists are independent of individual source integrations.

This means, for example, that a Pelikan BBB/OBBB search is not implemented separately for every marketplace. Each source instead provides normalized searchable item information to the central matching logic.

---

## Processing model

The general processing flow is:

    Public source / API
            |
            v
    Source-specific monitor
            |
            v
      Normalized item
            |
            v
      Watchlist matching
            |
            v
       SQLite state
            |
            v
    Private ntfy notification

---

## Persistent state and duplicate prevention

PenWatch uses SQLite to maintain state between monitoring cycles.

### `source_items`

Stores source items that have already been observed.

Once an item has been successfully evaluated, it is treated as known during subsequent monitoring cycles.

### `seen_items`

Stores source-item/watchlist combinations that have already generated a match.

This provides an additional safeguard against duplicate notifications.

Items are marked as processed only after the applicable watchlists have been evaluated successfully.

---

## Notifications

Relevant newly discovered items are sent privately to the collector through ntfy.

A notification can contain:

- a watchlist-specific title;
- item/listing title;
- matching information;
- a clickable link to the original public listing.

Notification credentials and configuration are supplied through environment variables and are not committed to the repository.

---

## Dry-run and regression testing

Source runners support dry-run operation.

A dry run can:

- retrieve live public source data;
- identify previously unknown items;
- execute the watchlist logic;
- display matches and diagnostic information.

It does not send notifications or modify persistent state.

Parser changes are additionally tested against known real-world items where possible. This helps detect situations where an HTTP request technically succeeds but the parser covers only part of the available inventory.

---

## Operation

PenWatch runs as a private Python service on a small Linux cloud server and is intended for a single collector.

Source-specific runners are executed periodically using systemd services and timers.

Secrets, API credentials, tokens, notification configuration, and other private configuration are stored locally and are never committed to this repository.

---

## Development and deployment

The Git repository is the source of truth.

Changes follow the general workflow:

    development working tree
            |
            v
    syntax / parser tests
            |
            v
        live dry-run
            |
            v
      regression test
            |
            v
       commit + push
            |
            v
    production deployment
            |
            v
    production verification

Direct production changes should be reconciled back into the repository so that the production server never becomes the only location containing the current implementation.

---

## Request behaviour and data minimization

PenWatch is designed to retrieve only the information reasonably necessary for its personal monitoring purpose.

Depending on the source, this includes:

- preferring public listing/search endpoints over unnecessary detail requests;
- deduplicating using stable source identifiers;
- applying delays between paginated HTTP requests where appropriate;
- retrieving detail pages selectively when listing data is insufficient;
- storing only the state required for matching and duplicate prevention.

PenWatch does not operate a public search service and does not redistribute collected marketplace data.

---

## Project status

### Operational

- Penboard
- MARTINI Auctions
- Interpens
- VintagePens
- Catawiki collection monitoring and pagination
- configurable watchlist matching
- SQLite state and duplicate prevention
- ntfy push notifications
- scheduled execution using systemd

### Integration in progress

- eBay API monitoring
- selective Catawiki detail-page enrichment

### Inactive / awaiting access

- Reddit public-submission monitoring

See **[Reddit Data Access and API Use](docs/reddit-data-access.md)** for the proposed Reddit integration.
