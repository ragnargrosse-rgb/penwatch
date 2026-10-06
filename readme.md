# PenWatch

PenWatch is a personal, non-commercial notification tool for monitoring public marketplace posts for rare fountain pens and related collectibles.

## Purpose

PenWatch monitors new public submissions from selected sources and compares titles and post content against a small user-defined keyword watchlist.

The initial Reddit integration monitors public submissions in `r/Pen_Swap` for collecting-related keywords such as `Soennecken`.

When a matching submission is detected, PenWatch sends a private push notification to the owner containing the post title and a link to the original submission.

## Reddit integration

The Reddit integration is read-only.

PenWatch:

- reads new public submissions from configured subreddits;
- compares public post titles and text against a predefined keyword list;
- sends private notifications when a match is detected;
- stores submission identifiers to prevent duplicate notifications.

PenWatch does not:

- create posts or comments;
- vote;
- send Reddit messages;
- moderate content;
- access private Reddit data;
- profile Reddit users;
- redistribute Reddit data;
- use Reddit data for AI or machine-learning training.

## Operation

PenWatch runs as a private Python service on a small cloud server and is intended for use by a single collector.

API credentials, notification credentials and other secrets are stored locally on the server and are never committed to this repository.

## Status

Early development.

### Data access and Devvit

PenWatch requires limited read-only access to recent public submissions for its personal keyword-monitoring functionality.

The specific data requirements, data-minimization approach, and the functional limitation that prevents this use case from being implemented through Devvit's subreddit-installed event model are documented here:

[Reddit Data Access](docs/reddit-data-access.md)

The Reddit integration will not be activated unless appropriate Reddit API access has been granted.
