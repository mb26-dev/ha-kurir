/*
 * Kurir card - parcel tracking card for the Kurir integration.
 * type: custom:kurir-card
 */
const KURIR_CARD_VERSION = "0.1.0";

const KURIR_STEPS = ["Ordered", "Packed", "Shipped", "Delivered"];

const KURIR_LOOK = {
  pending: { c: "#9e9e9e", i: "mdi:cart-outline", t: "Pending" },
  packed: { c: "#b388ff", i: "mdi:package-variant-closed", t: "Packed" },
  in_transit: { c: "#00bcd4", i: "mdi:truck-delivery", t: "In transit" },
  out_for_delivery: { c: "#f9a825", i: "mdi:truck-fast", t: "Out for delivery" },
  failed_attempt: { c: "#f44336", i: "mdi:alert-circle-outline", t: "Attempt failed" },
  delivered: { c: "#4caf50", i: "mdi:package-variant-closed-check", t: "Delivered" },
  returned: { c: "#ff7043", i: "mdi:keyboard-return", t: "Returned" },
  unknown: { c: "#9e9e9e", i: "mdi:package-variant", t: "Unknown" },
};

const kurirEsc = (s) =>
  String(s === undefined || s === null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

class KurirCard extends HTMLElement {
  setConfig(config) {
    this._config = {
      title: "Parcels",
      show_delivered: true,
      show_history: true,
      max_items: 20,
      ...config,
    };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._open = this._open || new Set();
  }

  static getStubConfig(hass) {
    const ent = Object.keys(hass.states).find((e) => e.startsWith("sensor.") && Array.isArray(hass.states[e].attributes.parcels) && hass.states[e].attributes.counts);
    return { entity: ent || "sensor.kurir_parcels_on_the_way" };
  }

  getCardSize() {
    return 4;
  }

  _entity() {
    if (this._config.entity) return this._config.entity;
    return Object.keys(this._hass.states).find((e) => e.startsWith("sensor.") && Array.isArray(this._hass.states[e].attributes.parcels) && this._hass.states[e].attributes.counts);
  }

  set hass(hass) {
    this._hass = hass;
    const ent = this._entity();
    const st = ent ? hass.states[ent] : undefined;
    const key = st ? st.last_updated + JSON.stringify(st.attributes.parcels || []).length : "none";
    if (key === this._lastKey) return;
    this._lastKey = key;
    this._render(st);
  }

  _time(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return kurirEsc(iso);
    const lang = (this._hass && this._hass.locale && this._hass.locale.language) || undefined;
    return d.toLocaleString(lang, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  }

  _bar(step, L) {
    const warn = L.c === KURIR_LOOK.failed_attempt.c || L.c === KURIR_LOOK.out_for_delivery.c;
    const seg = [1, 2, 3, 4]
      .map((i) => {
        const bg = i > step ? "var(--divider-color, rgba(127,127,127,.25))" : i < step && warn ? KURIR_LOOK.in_transit.c : L.c;
        const glow = i === step && L.c === KURIR_LOOK.failed_attempt.c ? `box-shadow:0 0 6px ${L.c};` : "";
        return `<div class="seg" style="background:${bg};${glow}"></div>`;
      })
      .join("");
    const lab = KURIR_STEPS.map((s, i) => {
      const col = i + 1 === step ? L.c : i + 1 < step ? "var(--secondary-text-color)" : "var(--disabled-text-color, #888)";
      return `<span style="color:${col};text-align:${i === 0 ? "left" : i === 3 ? "right" : "center"}">${s}</span>`;
    }).join("");
    return `<div class="bar">${seg}</div><div class="labels">${lab}</div>`;
  }

  _render(st) {
    const root = this.shadowRoot;
    if (!root) return;
    const cfg = this._config;
    if (!st) {
      root.innerHTML = `<ha-card header="${kurirEsc(cfg.title)}"><div class="empty" style="padding:16px">Kurir sensor not found. Set <code>entity</code> in the card config.</div></ha-card>`;
      return;
    }
    let rows = (st.attributes.parcels || []).slice();
    if (!cfg.show_delivered) rows = rows.filter((r) => r.status !== "delivered");
    rows = rows.slice(0, cfg.max_items);
    const counts = st.attributes.counts || {};
    const onWay = (counts.in_transit || 0) + (counts.failed_attempt || 0);
    const tiles = [
      ["mdi:package-variant-closed", (counts.pending || 0) + (counts.packed || 0), "Waiting", KURIR_LOOK.packed.c],
      ["mdi:truck-delivery", onWay, "On the way", KURIR_LOOK.in_transit.c],
      ["mdi:truck-fast", counts.out_for_delivery || 0, "Out for delivery", KURIR_LOOK.out_for_delivery.c],
      ["mdi:package-variant-closed-check", counts.delivered || 0, "Delivered", KURIR_LOOK.delivered.c],
    ]
      .map(
        ([icon, n, label, c]) => `
        <div class="tile" style="background:${c}1f;border-color:${c}66;${n === 0 ? "opacity:.45;" : ""}">
          <ha-icon icon="${icon}" style="color:${c}"></ha-icon>
          <span class="num" style="color:${c}">${n}</span>
          <span class="lbl" style="color:${c}">${label}</span>
        </div>`
      )
      .join("");

    const items = rows
      .map((r) => {
        const L = KURIR_LOOK[r.status] || KURIR_LOOK.unknown;
        const open = this._open.has(r.tracking_number);
        const evLine = r.event
          ? `<div class="ev" style="color:${L.c}"><ha-icon icon="${L.i}" style="color:${L.c}"></ha-icon>${kurirEsc(r.event)}${r.location ? " · " + kurirEsc(r.location) : ""}<span class="muted"> · ${this._time(r.time)}</span></div>`
          : `<div class="ev muted">Waiting for the first scan</div>`;
        const hist =
          cfg.show_history && Array.isArray(r.events) && r.events.length > 1
            ? `<div class="histtoggle" data-tn="${kurirEsc(r.tracking_number)}">${open ? "▾" : "▸"} Tracking history (${r.events.length})</div>` +
              (open
                ? `<div class="hist">${r.events
                    .map(
                      (e, i) =>
                        `<div class="hrow${i ? "" : " first"}"><span class="ht">${this._time(e.time)}</span><span>${kurirEsc(e.event)}${e.location ? " · " + kurirEsc(e.location) : ""}</span></div>`
                    )
                    .join("")}</div>`
                : "")
            : "";
        return `
        <div class="item">
          <div class="dot" style="background:${L.c}1f"><ha-icon icon="${L.i}" style="color:${L.c}"></ha-icon></div>
          <div class="body">
            <div class="name">${kurirEsc(r.name)}</div>
            <div class="meta">${kurirEsc(r.carrier_name || r.carrier)} · <span class="mono">${kurirEsc(r.tracking_number)}</span></div>
            ${evLine}
            ${this._bar(r.step || 1, L)}
            ${hist}
          </div>
          <div class="chip" style="color:${L.c};background:${L.c}22;border-color:${L.c}66">${L.t}</div>
        </div>`;
      })
      .join("");

    const warn = st.attributes.flash_blocked
      ? `<div class="warn">Flash Express is blocking automated requests right now; Flash parcels keep their last status${st.attributes.etrackings_used_this_month !== null && st.attributes.etrackings_used_this_month !== undefined ? " (eTrackings fallback active)" : ""}.</div>`
      : "";

    root.innerHTML = `
      <style>
        ha-card { padding: 14px 16px; }
        .head { display:flex; align-items:center; gap:10px; margin-bottom:12px; }
        .head ha-icon { --mdc-icon-size: 26px; color: var(--primary-color); }
        .title { font-size: 17px; font-weight: 700; color: var(--primary-text-color); }
        .tiles { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:8px; }
        .tile { display:flex; flex-direction:column; align-items:center; gap:2px; padding:10px 2px 8px; border-radius:14px; border:1px solid; min-width:0; }
        .tile ha-icon { --mdc-icon-size: 20px; }
        .num { font-size: 22px; font-weight: 900; line-height: 1.1; }
        .lbl { font-size: 9px; font-weight: 700; text-align:center; line-height:1.15; text-transform: uppercase; }
        .item { display:flex; align-items:flex-start; gap:10px; padding:10px 0; border-bottom:1px solid var(--divider-color, rgba(127,127,127,.2)); }
        .item:last-child { border-bottom: none; }
        .dot { flex:0 0 30px; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; }
        .dot ha-icon { --mdc-icon-size: 17px; }
        .body { flex:1 1 auto; min-width:0; }
        .name { font-size:13px; font-weight:700; color: var(--primary-text-color); line-height:1.3; overflow-wrap:anywhere; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
        .meta { font-size:10px; color: var(--secondary-text-color); margin-top:2px; overflow-wrap:anywhere; }
        .mono { font-family: monospace; }
        .ev { font-size:12px; font-weight:700; margin-top:5px; line-height:1.3; overflow-wrap:anywhere; }
        .ev ha-icon { --mdc-icon-size: 12px; vertical-align:-1px; margin-right:3px; }
        .muted { color: var(--secondary-text-color); font-weight: 400; }
        .bar { display:flex; gap:4px; margin-top:7px; }
        .seg { flex:1 1 0; height:5px; border-radius:3px; }
        .labels { display:flex; gap:4px; margin-top:3px; }
        .labels span { flex:1 1 0; min-width:0; font-size:9px; font-weight:700; white-space:nowrap; }
        .chip { flex:0 0 auto; font-size:9px; font-weight:700; border:1px solid; border-radius:8px; padding:2px 7px; white-space:nowrap; text-transform:uppercase; }
        .histtoggle { font-size:10px; color: var(--secondary-text-color); margin-top:6px; cursor:pointer; user-select:none; }
        .hist { margin-top:3px; padding-left:6px; border-left:2px solid var(--divider-color, rgba(127,127,127,.25)); }
        .hrow { display:flex; gap:8px; font-size:10px; line-height:1.35; padding:2px 0; color: var(--secondary-text-color); }
        .hrow.first { color: var(--primary-text-color); }
        .ht { flex:0 0 74px; white-space:nowrap; }
        .warn { font-size:11px; color:#f9a825; margin-top:10px; }
        .empty { font-size:12px; color: var(--secondary-text-color); padding: 14px 0 2px; }
        .list { margin-top: 8px; }
      </style>
      <ha-card>
        <div class="head"><ha-icon icon="mdi:truck-fast"></ha-icon><div class="title">${kurirEsc(cfg.title)}</div></div>
        <div class="tiles">${tiles}</div>
        <div class="list">${items || '<div class="empty">No parcels tracked. Use the kurir.add_parcel action to add one.</div>'}</div>
        ${warn}
      </ha-card>`;

    root.querySelectorAll(".histtoggle").forEach((el) =>
      el.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const tn = el.getAttribute("data-tn");
        if (this._open.has(tn)) this._open.delete(tn);
        else this._open.add(tn);
        this._lastKey = undefined;
        this._render(st);
      })
    );
  }
}

if (!customElements.get("kurir-card")) {
  customElements.define("kurir-card", KurirCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "kurir-card",
    name: "Kurir parcel card",
    description: "Live parcel tracking from the Kurir integration (Flash Express, Shopee Express).",
    preview: false,
    documentationURL: "https://github.com/mb26-dev/ha-kurir",
  });
  console.info(`%c KURIR-CARD %c ${KURIR_CARD_VERSION} `, "color:#fff;background:#00bcd4;font-weight:700", "color:#00bcd4");
}
