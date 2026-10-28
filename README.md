# reflex-privatus

**Real visitor numbers for your Reflex app. No cookies, no cookie pop-up, no bots.**

You want to know if people use your Reflex app. But Google Analytics uses
cookies, so in many countries you must show a cookie pop-up first (the box that
asks visitors to say yes to cookies). Many people click no, so they never show
up in your numbers. Bots add fake visits on top.

This package adds the Privatus Analytics script to your [Reflex](https://reflex.dev)
app with one line, and gives you a `track()` helper for button clicks and sales.
The script sets no cookies and keeps no IP addresses. Bots are filtered out
before they are counted.

So you see how many real people came, which pages they looked at and where they
came from, on one simple dashboard. A report comes to your inbox each week, and
you can set alerts for when traffic jumps or drops. And you don't need a cookie
pop-up for your analytics.

**Free plan, no card:** 10,000 events a month (an event is a page view or an action you track) on up to 3 sites. [Start free at privatusanalytics.com](https://privatusanalytics.com).

- **No cookies.** No cookies and no hidden IDs on your visitors' devices, and no IP
  addresses are kept. Laws differ by country, so check your own legal advice.
- **Real people, not bots.** Known bots, data centers and spam visits are left
  out on every plan.
- **Small and fast.** The script is about 3 KB when compressed.

## Requirements

* Python 3.10 or later.
* Reflex 0.9.12 or later.
* A Privatus Analytics site id (it starts with `pa_`). You find it under
  Site settings, Tracking.

## Install

```sh
pip install reflex-privatus
```

## Add the script

Put `privatus_analytics()` in your app's head components. It loads once, on
every page.

```python
import reflex as rx
from reflex_privatus import privatus_analytics

app = rx.App(
    head_components=[
        privatus_analytics("pa_YOURSITEID", modules=["engage", "auto", "vitals", "clicks", "ask"]),
    ],
)
```

This adds the same tag you would paste by hand:

```html
<script defer src="https://privatusstats.com/js/pa.js" data-site="pa_YOURSITEID" data-modules="engage,auto,vitals,clicks,ask"></script>
```

Reflex changes pages without a full reload. The script follows those changes
by itself, so every page view is counted.

You can leave out the site id and set it with an environment variable instead:

```sh
export PRIVATUS_SITE_ID=pa_YOURSITEID
```

When no site id is set, nothing is added and a warning is logged.

### Settings

| Argument | What it does |
|---|---|
| `site_id` | Your site id. Falls back to `PRIVATUS_SITE_ID`. |
| `modules` | Extra features: `engage` (time on page and scroll), `auto` (outbound links, downloads, form sends), `vitals` (Core Web Vitals), `clicks` (heatmaps), `ask` (short on-site surveys). Leave it out to get just `engage`. |
| `excluded_paths` | Pages never counted, like `["/admin/*"]`. |
| `domains` | Hostnames to count. Leave it out to count every host. |
| `spa` | How page changes are followed: `auto` (default), `history`, `hash` or `off`. |
| `manual` | `True` turns off the automatic page view. |
| `enabled` | `False` leaves the script out, for example in tests. |
| `script_host` | Only needed if you serve `pa.js` yourself. Falls back to `PRIVATUS_SCRIPT_HOST`. |
| `extra_attributes` | Any other `data-*` setting from the [tracker docs](https://privatusanalytics.com/docs). |

Visits from `localhost` are not counted, so local testing does not mix with
real numbers.

## Track events

Use `track()` as an event trigger:

```python
from reflex_privatus import track

rx.button("Sign up", on_click=track("Signup", {"plan": "pro"}))
```

Record money with `revenue` and `currency`:

```python
rx.button("Buy", on_click=track("Purchase", {"plan": "pro"}, revenue=49, currency="USD"))
```

Or return it from an event handler, after your own code runs:

```python
class State(rx.State):
    @rx.event
    def join(self):
        # ...save the sign-up
        return track("Newsletter signup")
```

Events run in the visitor's browser, never on your server. Calls made before the
script loads are queued, so none are lost. Create a goal for the event name in
your dashboard to see how often it happens and where those visitors came from.

Never put names, emails or other personal data in event details.

## Try the demo

```sh
pip install -e ".[test]"
cd demo
reflex run
```

## Develop

```sh
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

## Privacy

The tracker sets no cookies and uses no device ids. This package only loads it.
See the [privacy documentation](https://privatusanalytics.com/docs/privacy) for
what is collected.

If you have a privacy policy, it should say which tools handle your visitors' data. You can paste this:

> This website uses [Privatus Analytics](https://privatusanalytics.com/privacy-analytics) to count visits. It
> does not use cookies and does not follow you from one website to another. Your IP address is used for a moment
> to count visits and is never stored.

## License

MIT
