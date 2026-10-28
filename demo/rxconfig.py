import reflex as rx

config = rx.Config(
    app_name="demo",
    plugins=[rx.plugins.RadixThemesPlugin()],
    disable_plugins=[rx.plugins.SitemapPlugin],
)
