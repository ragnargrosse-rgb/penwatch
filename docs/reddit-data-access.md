# Reddit Data Access – PenWatch

## Purpose

PenWatch is a personal, non-commercial notification tool for a single fountain-pen collector.

Its Reddit integration is intended to monitor new public submissions in r/Pen_Swap for a small private list of user-defined collecting keywords, for example "Soennecken".

When a new public submission matches one of these criteria, PenWatch sends a private notification to the user containing the post title and a link to the original Reddit submission.

PenWatch is not a commercial service and is not offered to third parties.

## Required Reddit functionality

The Reddit integration requires only limited read-only access:

1. Retrieve recent public submissions from r/Pen_Swap.
2. Read the public submission title and, where necessary, public post text.
3. Compare this content locally against a small private keyword watchlist.
4. Retain the Reddit submission ID locally to prevent duplicate notifications.
5. Link the user back to the original Reddit submission when a match occurs.

No other Reddit functionality is required.

## Why Devvit does not provide the required functionality

PenWatch is a user-controlled monitoring tool rather than a subreddit-installed application.

The user defines private individual search criteria and wants to monitor new public submissions in a subreddit that the user does not moderate.

Devvit provides event-driven functionality such as PostSubmit triggers for applications installed in a subreddit. This installation model does not satisfy PenWatch's core use case because the user is not a moderator of r/Pen_Swap and cannot install an application in that community.

The missing capability is therefore not push notification delivery itself.

The missing capability is the ability for an individual user to monitor new public submissions in a public subreddit that the user does not moderate, according to that user's own private criteria, without requiring the subreddit to install the application.

Requiring installation by the subreddit would fundamentally change PenWatch from a personal user tool into a community-installed application and would make its core personal monitoring functionality dependent on third-party moderator action.

## Data minimization

PenWatch is designed to process the minimum Reddit data necessary for this purpose.

It does not:

- create posts or comments;
- vote on Reddit content;
- send Reddit messages;
- perform moderation actions;
- access private Reddit data;
- build user profiles;
- monitor individual Reddit users;
- collect comments;
- redistribute Reddit content;
- sell or monetize Reddit data;
- use Reddit data for advertising;
- use Reddit data for AI or machine-learning training.

The application processes only recent public submissions required for keyword matching.

## Local storage

PenWatch stores only the minimum information required to prevent duplicate notifications and identify previously processed matches.

For a matched submission this may include:

- Reddit submission ID;
- watchlist identifier;
- submission title;
- Reddit submission URL;
- timestamp of first detection.

PenWatch does not maintain an archive of subreddit content.

## Access pattern

The application is intended for one user only.

It will access only the public subreddit r/Pen_Swap for the initial use case.

Requests will be made at a low frequency sufficient to identify newly submitted posts. The application does not require bulk access, historical data collection, or high-volume API usage.

## Architecture

The Reddit integration is read-only.

The processing flow is:

    Reddit public submissions
            |
            v
    PenWatch Reddit monitor
            |
            v
    Local keyword matching
            |
            v
    Duplicate check
            |
            v
    Private notification to the user

Keyword criteria remain private and are processed locally by PenWatch.

## Security

Reddit API credentials are stored as environment variables on the private application server and are not committed to the public source-code repository.

PenWatch follows a least-privilege approach and requests only the access necessary to retrieve public submissions for the stated personal use case.
