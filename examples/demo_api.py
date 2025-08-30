"""
Typed‑builder demo showcasing all components (except Image) with data binding.
Run:
  uv run examples/demo_api.py
Output written to out/demo_api.png
"""

from quadre.api import (
    render,
    doc,
    Title,
    Text,
    KPI,
    Table,
    Progress,
    StatusBadge,
    Row,
    Column,
    Grid,
    Spacer,
    dref,
)


def main() -> None:
    data = {
        "perf": {
            "title": "Revenue",
            "value": "1 293 €",
            "delta": {"pct": 12, "vs": "MoM"},
        },
        "perf2": {
            "title": "Orders",
            "value": "12 345",
            "delta": {"pct": -4, "vs": "MoM"},
        },
        "perf3": {
            "title": "Conversion",
            "value": "3.4%",
            "delta": {"pct": 1.2, "vs": "WoW"},
        },
        "table": {
            "headers": ["Product", "Price", "Features", "Rating", "Market Share"],
            "rows": [
                ["Product A", "€299", "Advanced", "4.8/5", "35.2%"],
                ["Product B", "€199", "Standard", "4.2/5", "28.7%"],
                ["Product C", "€399", "Premium", "4.9/5", "21.5%"],
                ["Product D", "€149", "Basic", "3.9/5", "14.6%"],
            ],
        },
        "progress": {"upload": 0.72, "download": 0.35, "error": 0.1},
    }

    d = doc(
        Title("Demo API"),
        Text("All Components").font("heading"),
        # KPI Row with a fixed-width label and 3 KPIs, grouped in a soft panel
        Row()
        .gap(12)
        .padding(16)
        .add(
            Text("KPIs").font("heading").no_grow(),
            KPI(
                title=dref("$.perf.title"),
                value=dref("$.perf.value"),
                delta=dref("$.perf.delta"),
            ).grow(1),
            KPI(
                title=dref("$.perf2.title"),
                value=dref("$.perf2.value"),
                delta=dref("$.perf2.delta"),
            ).grow(1),
            KPI(
                title=dref("$.perf3.title"),
                value=dref("$.perf3.value"),
                delta=dref("$.perf3.delta"),
            ).grow(1),
        ),
        Spacer(12),
        # Table driven by data
        Table.from_payload(dref("$.table")).props(style={"use_alternating_rows": True}),
        Spacer(12),
        Text("Progress & Status").font("heading"),
        # Mixed content row: left column with progress bars, right column with status badges
        Row()
        .gap(12)
        .padding(16)
        .add(
            Column()
            .gap(10)
            .add(
                Progress(value=dref("$.progress.upload"), label="Upload").bar_height(
                    18
                ),
                Progress(
                    value=dref("$.progress.download"), label="Download"
                ).bar_height(18),
                Progress(value=dref("$.progress.error"), label="Error").bar_height(18),
            )
            .grow(1),
            Column()
            .gap(8)
            .add(
                StatusBadge("OK").variant("success"),
                StatusBadge("Warning").variant("warning"),
                StatusBadge("Failed").variant("destructive"),
                StatusBadge("Queued").variant("secondary"),
            )
            .grow(0),
        ),
        Spacer(12),
        Text("Grid of badges").font("heading"),
        Grid()
        .columns(3)
        .gap(12)
        .padding(16)
        .bg_fill("muted")
        .bg_radius(12)
        .bg_outline("border")
        .bg_outline_width(2)
        .shadow()
        .add(
            StatusBadge("Build").variant("secondary"),
            StatusBadge("Test").variant("success"),
            StatusBadge("Deploy").variant("warning"),
            StatusBadge("SLA").variant("outline"),
            StatusBadge("Red").variant("destructive"),
            StatusBadge("Green").variant("success"),
        ),
        data=data,
        canvas={
            "height": "auto",
            "padding": 24,
            "gap": 16,
            "bottom_margin": 24,
            # Supersampling + sharpen for crisper text
            "scale": 2.0,
            "downscale": True,
            "sharpen": 0.35,
        },
        # Subtle background lift for the whole page
        theme={"colors": {"background": "#f8fafc", "border": "#e5e7eb"}},
    ).to_dict()

    render(d, path="out/demo_api.png")


if __name__ == "__main__":
    main()
