/*
 * Kurir card - parcel tracking card for the Kurir integration.
 * type: custom:kurir-card
 */
const KURIR_CARD_VERSION = "0.1.10";

// UI texts and courier event names per language. English is the source; the
// events are the English names produced by the integration (carriers.py).
const KURIR_I18N = {
  en: {
    steps: ["Ordered", "Packed", "Shipped", "Delivered"],
    state: { pending: "Pending", packed: "Packed", in_transit: "In transit", out_for_delivery: "Out for delivery", failed_attempt: "Attempt failed", delivered: "Delivered", returned: "Returned", unknown: "Unknown" },
    tiles: ["Waiting", "On the way", "Out for delivery", "Delivered"],
    title: "Parcels",
    first_scan: "Waiting for the first scan",
    history: "Tracking history",
    not_found: "Kurir sensor not found. Set <code>entity</code> in the card config.",
    empty: "No parcels tracked. Use the kurir.add_parcel action to add one.",
    flash_blocked: "Flash Express is blocking automated requests right now; Flash parcels keep their last status",
    fallback: " (eTrackings fallback active)",
    ev: {},
  },
  de: {
    steps: ["Bestellt", "Verpackt", "Versendet", "Zugestellt"],
    state: { pending: "Ausstehend", packed: "Verpackt", in_transit: "Unterwegs", out_for_delivery: "In Zustellung", failed_attempt: "Zustellung fehlgeschl.", delivered: "Zugestellt", returned: "Zurück", unknown: "Unbekannt" },
    tiles: ["Wartend", "Unterwegs", "In Zustellung", "Zugestellt"],
    title: "Pakete",
    first_scan: "Warte auf den ersten Scan",
    history: "Sendungsverlauf",
    not_found: "Kurir-Sensor nicht gefunden. Setze <code>entity</code> in der Kartenkonfiguration.",
    empty: "Keine Pakete. Füge eins mit der Aktion kurir.add_parcel hinzu.",
    flash_blocked: "Flash Express blockiert gerade automatische Abfragen; Flash-Pakete behalten ihren letzten Status",
    fallback: " (eTrackings-Ausweichweg aktiv)",
    ev: {
      "Arrived at hub": "Im Verteilzentrum angekommen",
      "Arrived at local hub": "Im Zustellstützpunkt angekommen",
      "Arrived at origin warehouse": "Im Absenderlager angekommen",
      "Arrived in destination country": "Im Zielland angekommen",
      "Back in transit": "Wieder unterwegs",
      "Cleared export customs": "Ausfuhrzoll erledigt",
      "Cleared import customs": "Einfuhrzoll erledigt",
      "Delivered": "Zugestellt",
      "Delivery attempt failed": "Zustellversuch fehlgeschlagen",
      "Delivery problem reported": "Zustellproblem gemeldet",
      "Departed hub": "Verteilzentrum verlassen",
      "Departed origin port": "Abgangshafen verlassen",
      "Departed origin warehouse": "Absenderlager verlassen",
      "Driver assigned": "Fahrer zugewiesen",
      "Handed to air forwarder": "An Luftfracht übergeben",
      "Handed to courier by seller": "Vom Verkäufer an den Kurier übergeben",
      "Handed to domestic courier": "An Inlandskurier übergeben",
      "Held at hub": "Im Verteilzentrum zurückgehalten",
      "In transit": "Unterwegs",
      "Label created, waiting for pickup": "Label erstellt, wartet auf Abholung",
      "Out for delivery": "In Zustellung",
      "Picked up by courier": "Vom Kurier abgeholt",
      "Returned to sender": "An Absender zurück",
    },
  },
  th: {
    steps: ["สั่งซื้อ", "แพ็ก", "จัดส่ง", "ได้รับ"],
    state: { pending: "รอดำเนินการ", packed: "แพ็กแล้ว", in_transit: "ระหว่างขนส่ง", out_for_delivery: "กำลังนำส่ง", failed_attempt: "นำส่งไม่สำเร็จ", delivered: "จัดส่งสำเร็จ", returned: "ตีกลับ", unknown: "ไม่ทราบ" },
    tiles: ["รอ", "ระหว่างทาง", "กำลังนำส่ง", "จัดส่งสำเร็จ"],
    title: "พัสดุ",
    first_scan: "รอการสแกนครั้งแรก",
    history: "ประวัติการขนส่ง",
    not_found: "ไม่พบเซนเซอร์ Kurir กำหนด <code>entity</code> ในการตั้งค่าการ์ด",
    empty: "ยังไม่มีพัสดุ ใช้ action kurir.add_parcel เพื่อเพิ่ม",
    flash_blocked: "ขณะนี้ Flash Express บล็อกคำขออัตโนมัติ พัสดุ Flash จะแสดงสถานะล่าสุด",
    fallback: " (ใช้ eTrackings สำรองอยู่)",
    ev: {
      "Arrived at hub": "ถึงศูนย์คัดแยก",
      "Arrived at local hub": "ถึงสาขาปลายทาง",
      "Arrived at origin warehouse": "ถึงคลังต้นทาง",
      "Arrived in destination country": "ถึงประเทศปลายทาง",
      "Back in transit": "กลับมาขนส่งอีกครั้ง",
      "Cleared export customs": "ผ่านพิธีการศุลกากรขาออก",
      "Cleared import customs": "ผ่านพิธีการศุลกากรขาเข้า",
      "Delivered": "จัดส่งสำเร็จ",
      "Delivery attempt failed": "นำส่งไม่สำเร็จ",
      "Delivery problem reported": "แจ้งปัญหาการจัดส่ง",
      "Departed hub": "ออกจากศูนย์คัดแยก",
      "Departed origin port": "ออกจากท่าต้นทาง",
      "Departed origin warehouse": "ออกจากคลังต้นทาง",
      "Driver assigned": "มอบหมายพนักงานส่งแล้ว",
      "Handed to air forwarder": "ส่งมอบให้สายการบินขนส่ง",
      "Handed to courier by seller": "ผู้ขายส่งมอบให้ขนส่งแล้ว",
      "Handed to domestic courier": "ส่งมอบให้ขนส่งในประเทศ",
      "Held at hub": "พักไว้ที่ศูนย์คัดแยก",
      "In transit": "ระหว่างขนส่ง",
      "Label created, waiting for pickup": "สร้างใบปะหน้าแล้ว รอเข้ารับ",
      "Out for delivery": "กำลังนำส่ง",
      "Picked up by courier": "ขนส่งเข้ารับพัสดุแล้ว",
      "Returned to sender": "ตีกลับถึงผู้ส่ง",
    },
  },
  vi: {
    steps: ["Đã đặt", "Đóng gói", "Đã gửi", "Đã giao"],
    state: { pending: "Đang chờ", packed: "Đã đóng gói", in_transit: "Đang vận chuyển", out_for_delivery: "Đang giao", failed_attempt: "Giao thất bại", delivered: "Đã giao", returned: "Hoàn trả", unknown: "Không rõ" },
    tiles: ["Đang chờ", "Trên đường", "Đang giao", "Đã giao"],
    title: "Bưu kiện",
    first_scan: "Đang chờ lần quét đầu tiên",
    history: "Lịch sử vận chuyển",
    not_found: "Không tìm thấy cảm biến Kurir. Đặt <code>entity</code> trong cấu hình thẻ.",
    empty: "Chưa có bưu kiện. Dùng hành động kurir.add_parcel để thêm.",
    flash_blocked: "Flash Express đang chặn truy vấn tự động; bưu kiện Flash giữ trạng thái gần nhất",
    fallback: " (đang dùng eTrackings dự phòng)",
    ev: {
      "Arrived at hub": "Đã đến kho phân loại",
      "Arrived at local hub": "Đã đến bưu cục giao hàng",
      "Arrived at origin warehouse": "Đã đến kho gửi",
      "Arrived in destination country": "Đã đến nước nhận",
      "Back in transit": "Tiếp tục vận chuyển",
      "Cleared export customs": "Đã thông quan xuất khẩu",
      "Cleared import customs": "Đã thông quan nhập khẩu",
      "Delivered": "Đã giao",
      "Delivery attempt failed": "Giao hàng thất bại",
      "Delivery problem reported": "Báo sự cố giao hàng",
      "Departed hub": "Đã rời kho phân loại",
      "Departed origin port": "Đã rời cảng đi",
      "Departed origin warehouse": "Đã rời kho gửi",
      "Driver assigned": "Đã phân công tài xế",
      "Handed to air forwarder": "Đã giao cho hãng hàng không",
      "Handed to courier by seller": "Người bán đã giao cho đơn vị vận chuyển",
      "Handed to domestic courier": "Đã giao cho đơn vị vận chuyển nội địa",
      "Held at hub": "Tạm giữ tại kho",
      "In transit": "Đang vận chuyển",
      "Label created, waiting for pickup": "Đã tạo vận đơn, chờ lấy hàng",
      "Out for delivery": "Đang giao hàng",
      "Picked up by courier": "Đã lấy hàng",
      "Returned to sender": "Đã hoàn trả người gửi",
    },
  },
  id: {
    steps: ["Dipesan", "Dikemas", "Dikirim", "Diterima"],
    state: { pending: "Menunggu", packed: "Dikemas", in_transit: "Dalam perjalanan", out_for_delivery: "Sedang diantar", failed_attempt: "Gagal antar", delivered: "Terkirim", returned: "Dikembalikan", unknown: "Tidak diketahui" },
    tiles: ["Menunggu", "Di jalan", "Sedang diantar", "Terkirim"],
    title: "Paket",
    first_scan: "Menunggu pemindaian pertama",
    history: "Riwayat pengiriman",
    not_found: "Sensor Kurir tidak ditemukan. Atur <code>entity</code> di konfigurasi kartu.",
    empty: "Belum ada paket. Gunakan aksi kurir.add_parcel untuk menambah.",
    flash_blocked: "Flash Express sedang memblokir permintaan otomatis; paket Flash tetap pada status terakhir",
    fallback: " (cadangan eTrackings aktif)",
    ev: {
      "Arrived at hub": "Tiba di hub",
      "Arrived at local hub": "Tiba di hub tujuan",
      "Arrived at origin warehouse": "Tiba di gudang asal",
      "Arrived in destination country": "Tiba di negara tujuan",
      "Back in transit": "Kembali dalam perjalanan",
      "Cleared export customs": "Lolos bea cukai ekspor",
      "Cleared import customs": "Lolos bea cukai impor",
      "Delivered": "Terkirim",
      "Delivery attempt failed": "Pengantaran gagal",
      "Delivery problem reported": "Masalah pengiriman dilaporkan",
      "Departed hub": "Berangkat dari hub",
      "Departed origin port": "Berangkat dari pelabuhan asal",
      "Departed origin warehouse": "Berangkat dari gudang asal",
      "Driver assigned": "Kurir ditugaskan",
      "Handed to air forwarder": "Diserahkan ke kargo udara",
      "Handed to courier by seller": "Diserahkan penjual ke kurir",
      "Handed to domestic courier": "Diserahkan ke kurir domestik",
      "Held at hub": "Ditahan di hub",
      "In transit": "Dalam perjalanan",
      "Label created, waiting for pickup": "Label dibuat, menunggu penjemputan",
      "Out for delivery": "Sedang diantar",
      "Picked up by courier": "Dijemput kurir",
      "Returned to sender": "Dikembalikan ke pengirim",
    },
  },
  ms: {
    steps: ["Dipesan", "Dibungkus", "Dihantar", "Diterima"],
    state: { pending: "Belum selesai", packed: "Dibungkus", in_transit: "Dalam transit", out_for_delivery: "Sedang dihantar", failed_attempt: "Gagal hantar", delivered: "Dihantar", returned: "Dikembalikan", unknown: "Tidak diketahui" },
    tiles: ["Menunggu", "Dalam perjalanan", "Sedang dihantar", "Dihantar"],
    title: "Bungkusan",
    first_scan: "Menunggu imbasan pertama",
    history: "Sejarah penjejakan",
    not_found: "Sensor Kurir tidak ditemui. Tetapkan <code>entity</code> dalam konfigurasi kad.",
    empty: "Tiada bungkusan. Gunakan tindakan kurir.add_parcel untuk menambah.",
    flash_blocked: "Flash Express sedang menyekat permintaan automatik; bungkusan Flash kekal pada status terakhir",
    fallback: " (sandaran eTrackings aktif)",
    ev: {
      "Arrived at hub": "Tiba di hab",
      "Arrived at local hub": "Tiba di hab tempatan",
      "Arrived at origin warehouse": "Tiba di gudang asal",
      "Arrived in destination country": "Tiba di negara destinasi",
      "Back in transit": "Kembali dalam transit",
      "Cleared export customs": "Lepas kastam eksport",
      "Cleared import customs": "Lepas kastam import",
      "Delivered": "Dihantar",
      "Delivery attempt failed": "Penghantaran gagal",
      "Delivery problem reported": "Masalah penghantaran dilaporkan",
      "Departed hub": "Berlepas dari hab",
      "Departed origin port": "Berlepas dari pelabuhan asal",
      "Departed origin warehouse": "Berlepas dari gudang asal",
      "Driver assigned": "Pemandu ditugaskan",
      "Handed to air forwarder": "Diserahkan kepada kargo udara",
      "Handed to courier by seller": "Diserahkan penjual kepada kurier",
      "Handed to domestic courier": "Diserahkan kepada kurier domestik",
      "Held at hub": "Ditahan di hab",
      "In transit": "Dalam transit",
      "Label created, waiting for pickup": "Label dicipta, menunggu pengambilan",
      "Out for delivery": "Sedang dihantar",
      "Picked up by courier": "Diambil oleh kurier",
      "Returned to sender": "Dikembalikan kepada pengirim",
    },
  },
  zh: {
    steps: ["已下单", "已打包", "已发货", "已签收"],
    state: { pending: "待处理", packed: "已打包", in_transit: "运输中", out_for_delivery: "派送中", failed_attempt: "派送失败", delivered: "已签收", returned: "已退回", unknown: "未知" },
    tiles: ["等待中", "运输中", "派送中", "已签收"],
    title: "包裹",
    first_scan: "等待首次扫描",
    history: "物流记录",
    not_found: "未找到 Kurir 传感器。请在卡片配置中设置 <code>entity</code>。",
    empty: "暂无包裹。使用 kurir.add_parcel 动作添加。",
    flash_blocked: "Flash Express 目前拦截自动查询；Flash 包裹保持最后状态",
    fallback: "（eTrackings 备用已启用）",
    ev: {
      "Arrived at hub": "到达转运中心",
      "Arrived at local hub": "到达派送网点",
      "Arrived at origin warehouse": "到达始发仓",
      "Arrived in destination country": "到达目的国",
      "Back in transit": "恢复运输",
      "Cleared export customs": "出口清关完成",
      "Cleared import customs": "进口清关完成",
      "Delivered": "已签收",
      "Delivery attempt failed": "派送失败",
      "Delivery problem reported": "派送异常",
      "Departed hub": "离开转运中心",
      "Departed origin port": "离开始发港",
      "Departed origin warehouse": "离开始发仓",
      "Driver assigned": "已分配派送员",
      "Handed to air forwarder": "交航空货运",
      "Handed to courier by seller": "卖家已交快递",
      "Handed to domestic courier": "交本地快递",
      "Held at hub": "滞留转运中心",
      "In transit": "运输中",
      "Label created, waiting for pickup": "已创建运单，等待揽收",
      "Out for delivery": "派送中",
      "Picked up by courier": "快递已揽收",
      "Returned to sender": "已退回寄件人",
    },
  },
};

const kurirLang = (hass) => {
  const raw = ((hass && hass.locale && hass.locale.language) || (hass && hass.language) || "en").toLowerCase();
  if (KURIR_I18N[raw]) return raw;
  const base = raw.split(/[-_]/)[0];
  return KURIR_I18N[base] ? base : "en";
};

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
    const key = kurirLang(hass) + (st ? st.last_updated + JSON.stringify(st.attributes.parcels || []).length : "none");
    if (key === this._lastKey) return;
    this._lastKey = key;
    this._render(st);
  }

  get _t() {
    return KURIR_I18N[kurirLang(this._hass)];
  }

  _ev(name) {
    const t = this._t;
    return (t.ev && t.ev[name]) || name;
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
    const lab = this._t.steps.map((s, i) => {
      const col = i + 1 === step ? L.c : i + 1 < step ? "var(--secondary-text-color)" : "var(--disabled-text-color, #888)";
      return `<span style="color:${col};text-align:${i === 0 ? "left" : i === 3 ? "right" : "center"}">${s}</span>`;
    }).join("");
    return `<div class="bar">${seg}</div><div class="labels">${lab}</div>`;
  }

  _render(st) {
    const root = this.shadowRoot;
    if (!root) return;
    const cfg = this._config;
    const T = this._t;
    const title = cfg.title !== undefined && cfg.title !== null ? cfg.title : T.title;
    if (!st) {
      root.innerHTML = `<ha-card header="${kurirEsc(title)}"><div class="empty" style="padding:16px">${T.not_found}</div></ha-card>`;
      return;
    }
    let rows = (st.attributes.parcels || []).slice();
    if (!cfg.show_delivered) rows = rows.filter((r) => r.status !== "delivered");
    rows = rows.slice(0, cfg.max_items);
    // counts are forced to whole numbers (they go into the markup)
    const rawCounts = st.attributes.counts || {};
    const counts = {};
    for (const k of Object.keys(rawCounts)) { const n = parseInt(rawCounts[k], 10); counts[k] = Number.isFinite(n) && n > 0 ? n : 0; }
    const onWay = (counts.in_transit || 0) + (counts.failed_attempt || 0);
    const tiles = [
      ["mdi:package-variant-closed", (counts.pending || 0) + (counts.packed || 0), T.tiles[0], KURIR_LOOK.packed.c],
      ["mdi:truck-delivery", onWay, T.tiles[1], KURIR_LOOK.in_transit.c],
      ["mdi:truck-fast", counts.out_for_delivery || 0, T.tiles[2], KURIR_LOOK.out_for_delivery.c],
      ["mdi:package-variant-closed-check", counts.delivered || 0, T.tiles[3], KURIR_LOOK.delivered.c],
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
          ? `<div class="ev" style="color:${L.c}"><ha-icon icon="${L.i}" style="color:${L.c}"></ha-icon>${kurirEsc(this._ev(r.event))}${r.location ? " · " + kurirEsc(r.location) : ""}<span class="muted"> · ${this._time(r.time)}</span></div>`
          : `<div class="ev muted">${kurirEsc(T.first_scan)}</div>`;
        const hist =
          cfg.show_history && Array.isArray(r.events) && r.events.length > 1
            ? `<div class="histtoggle" data-tn="${kurirEsc(r.tracking_number)}">${open ? "▾" : "▸"} ${kurirEsc(T.history)} (${r.events.length})</div>` +
              (open
                ? `<div class="hist">${r.events
                    .map(
                      (e, i) =>
                        `<div class="hrow${i ? "" : " first"}"><span class="ht">${this._time(e.time)}</span><span>${kurirEsc(this._ev(e.event))}${e.location ? " · " + kurirEsc(e.location) : ""}</span></div>`
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
          <div class="chip" style="color:${L.c};background:${L.c}22;border-color:${L.c}66">${kurirEsc(T.state[r.status] || T.state.unknown)}</div>
        </div>`;
      })
      .join("");

    const warn = st.attributes.flash_blocked
      ? `<div class="warn">${kurirEsc(T.flash_blocked)}${st.attributes.etrackings_used_this_month !== null && st.attributes.etrackings_used_this_month !== undefined ? kurirEsc(T.fallback) : ""}.</div>`
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
        <div class="head"><ha-icon icon="mdi:truck-fast"></ha-icon><div class="title">${kurirEsc(title)}</div></div>
        <div class="tiles">${tiles}</div>
        <div class="list">${items || `<div class="empty">${kurirEsc(T.empty)}</div>`}</div>
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
