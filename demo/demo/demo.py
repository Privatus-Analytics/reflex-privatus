"""A small app for trying reflex-privatus while you develop it."""

import reflex as rx

from reflex_privatus import privatus_analytics, track


class State(rx.State):
    joined: bool = False

    @rx.event
    def join(self):
        self.joined = True
        # An event handler can return the tracking call too.
        return track("Newsletter signup", {"source": "demo"})


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("reflex-privatus demo"),
            rx.button("Buy the pro plan", on_click=track("Purchase", {"plan": "pro"}, revenue=49, currency="USD")),
            rx.button("Join the newsletter", on_click=State.join),
            rx.cond(State.joined, rx.text("Thanks for joining.")),
            rx.link("About page", href="/about"),
            align="center",
        ),
        height="100vh",
    )


def about() -> rx.Component:
    return rx.center(rx.link("Back home", href="/"), height="100vh")


app = rx.App(
    head_components=[
        # Use your own site id. Visits from localhost are not counted.
        privatus_analytics("pa_DEMO123", modules=["engage", "auto", "vitals", "clicks", "ask"]),
    ],
)
app.add_page(index)
app.add_page(about, route="/about")
