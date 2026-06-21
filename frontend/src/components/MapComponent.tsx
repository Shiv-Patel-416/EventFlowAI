"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle, ZoomControl } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { eventService } from "@/lib/api";

// Suppress default icon path issue
delete (L.Icon.Default.prototype as any)._getIconUrl;

/* ── Marker Icons ───────────────────────────────────────────────── */
const createIcon = (color: string, glowColor: string, size: number = 22) =>
  L.divIcon({
    className: "",
    html: `
      <div style="position:relative;width:${size}px;height:${size}px;">
        <div style="
          position:absolute;inset:0;
          background:${glowColor};
          border-radius:50%;
          filter:blur(4px);
          opacity:0.7;
        "></div>
        <div style="
          position:absolute;inset:3px;
          background:radial-gradient(circle at 35% 35%, ${color}, ${glowColor});
          border-radius:50%;
          border:1.5px solid rgba(255,255,255,0.35);
          box-shadow:0 0 6px ${glowColor};
        "></div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2 + 2)],
  });

const ICONS = {
  critical: createIcon("#FF3B3B", "rgba(255,59,59,0.65)", 26),
  high:     createIcon("#FF8C42", "rgba(255,140,66,0.55)", 22),
  medium:   createIcon("#FFD93D", "rgba(255,217,61,0.45)", 20),
  low:      createIcon("#4DA8FF", "rgba(77,168,255,0.45)", 18),
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#FF3B3B",
  high:     "#FF8C42",
  medium:   "#FFD93D",
  low:      "#4DA8FF",
};

const SEVERITY_LABELS: Record<string, string> = {
  critical: "Critical",
  high:     "High",
  medium:   "Medium",
  low:      "Low",
};

/* ── Cause → base impact + base severity ────────────────────────── */
const CAUSE_META: Record<string, { baseImpact: number; baseSeverity: string }> = {
  // Critical-capable causes
  accident:           { baseImpact: 8.5, baseSeverity: "critical" },
  vip_movement:       { baseImpact: 9.0, baseSeverity: "critical" },
  protest:            { baseImpact: 8.8, baseSeverity: "critical" },
  // High causes
  tree_fall:          { baseImpact: 7.2, baseSeverity: "high" },
  water_logging:      { baseImpact: 6.5, baseSeverity: "high" },
  public_event:       { baseImpact: 7.8, baseSeverity: "high" },
  procession:         { baseImpact: 7.0, baseSeverity: "high" },
  construction:       { baseImpact: 5.8, baseSeverity: "high" },
  // Medium causes
  pot_holes:          { baseImpact: 4.0, baseSeverity: "medium" },
  road_conditions:    { baseImpact: 4.5, baseSeverity: "medium" },
  congestion:         { baseImpact: 5.2, baseSeverity: "medium" },
  fog_low_visibility: { baseImpact: 5.0, baseSeverity: "medium" },
  debris:             { baseImpact: 4.2, baseSeverity: "medium" },
  others:             { baseImpact: 3.8, baseSeverity: "medium" },
  // Low causes
  vehicle_breakdown:  { baseImpact: 3.0, baseSeverity: "low" },
  test_demo:          { baseImpact: 1.5, baseSeverity: "low" },
};

const SEVERITY_RANK: Record<string, number> = { low: 0, medium: 1, high: 2, critical: 3 };
const RANK_TO_SEVERITY = ["low", "medium", "high", "critical"];

function deriveSeverity(event: any): string {
  const apiPriority = (event.priority || "").toLowerCase();
  const cause = (event.event_cause || "").toLowerCase();
  const closure = event.requires_road_closure ?? false;
  const meta = CAUSE_META[cause] ?? { baseImpact: 4.0, baseSeverity: "medium" };

  let rank = SEVERITY_RANK[meta.baseSeverity] ?? 1;

  // Boost by +1 if API says High and cause is not already critical
  if (apiPriority === "high" && rank < 3) rank = Math.min(3, rank + 1);

  // Downgrade by -1 if API says Low and cause is not already low
  if (apiPriority === "low" && rank > 0) rank = Math.max(0, rank - 1);

  // Road closure always pushes at least to high
  if (closure && rank < 2) rank = 2;

  return RANK_TO_SEVERITY[rank];
}

function computeImpact(event: any): number {
  const cause = (event.event_cause || "").toLowerCase();
  const apiPriority = (event.priority || "").toLowerCase();
  const closure = event.requires_road_closure ?? false;
  const meta = CAUSE_META[cause] ?? { baseImpact: 4.0, baseSeverity: "medium" };

  let score = meta.baseImpact;

  if (apiPriority === "high") score += 1.0;
  if (apiPriority === "low") score -= 0.8;
  if (closure) score += 1.5;

  // Deterministic small variation per event
  const charCode = (event.id?.charCodeAt?.(event.id.length - 1) || 0);
  score += ((charCode % 10) - 5) * 0.15;

  return Math.round(Math.max(1, Math.min(10, score)) * 10) / 10;
}

/* ── Cluster icon factory ───────────────────────────────────────── */
const createClusterIcon = (cluster: any) => {
  const count = cluster.getChildCount();
  let size = 36;
  let bg = "rgba(77,168,255,0.8)";
  let border = "rgba(77,168,255,0.4)";

  if (count > 50) {
    size = 50; bg = "rgba(255,59,59,0.85)"; border = "rgba(255,59,59,0.4)";
  } else if (count > 20) {
    size = 44; bg = "rgba(255,140,66,0.85)"; border = "rgba(255,140,66,0.4)";
  } else if (count > 5) {
    size = 40; bg = "rgba(255,217,61,0.85)"; border = "rgba(255,217,61,0.4)";
  }

  return L.divIcon({
    html: `
      <div style="
        width:${size}px;height:${size}px;
        display:flex;align-items:center;justify-content:center;
        background:${bg};
        border:2px solid ${border};
        border-radius:50%;
        box-shadow:0 0 12px ${border}, inset 0 0 8px rgba(0,0,0,0.2);
        color:#fff;
        font-family:Inter,sans-serif;
        font-size:${count > 99 ? 11 : 13}px;
        font-weight:700;
        letter-spacing:-0.02em;
      ">${count}</div>
    `,
    className: "",
    iconSize: L.point(size, size),
  });
};

/* ── Main Component ─────────────────────────────────────────────── */
export default function MapComponent() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });

  useEffect(() => {
    async function fetchAllEvents() {
      try {
        const firstPage = await eventService.getEvents({ page_size: 100, status: "active" });
        const total = firstPage?.total ?? 0;
        let allEvents = firstPage?.events ?? [];

        if (total > 100) {
          const totalPages = Math.ceil(total / 100);
          const promises = [];
          for (let page = 2; page <= totalPages; page++) {
            promises.push(
              eventService.getEvents({ page_size: 100, page, status: "active" })
            );
          }
          const results = await Promise.all(promises);
          for (const result of results) {
            if (result?.events?.length) {
              allEvents = [...allEvents, ...result.events];
            }
          }
        }

        if (allEvents.length > 0) {
          setEvents(allEvents);
          // Compute stats
          const s = { total: allEvents.length, critical: 0, high: 0, medium: 0, low: 0 };
          allEvents.forEach((e: any) => {
            const sev = deriveSeverity(e);
            s[sev as keyof typeof s] = (s[sev as keyof typeof s] as number) + 1;
          });
          setStats(s);
        }
      } catch (err) {
        console.error("Failed to fetch events:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchAllEvents();
  }, []);

  return (
    <div style={{ position: "relative", height: "100%", width: "100%" }}>
      <MapContainer
        center={[12.9716, 77.5946]}
        zoom={12}
        style={{ height: "100%", width: "100%" }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        <ZoomControl position="bottomright" />

        <MarkerClusterGroup
          chunkedLoading
          maxClusterRadius={50}
          spiderfyOnMaxZoom
          showCoverageOnHover={false}
          iconCreateFunction={createClusterIcon}
        >
          {events.map(event => {
            const lat = event.latitude  ?? event.lat;
            const lng = event.longitude ?? event.lng;
            if (!lat || !lng) return null;

            const severity = deriveSeverity(event);
            const icon = ICONS[severity as keyof typeof ICONS] ?? ICONS.medium;
            const color = SEVERITY_COLORS[severity] ?? "#FFD93D";
            const cause = (event.event_cause ?? "Incident").replace(/_/g, " ");
            const zone  = event.address
              ? event.address.split(",").slice(0, 2).join(",").trim()
              : `${lat?.toFixed(4)}, ${lng?.toFixed(4)}`;
            const closure = event.requires_road_closure ?? false;
            const impact  = computeImpact(event);

            return (
              <Marker key={event.id} position={[lat, lng]} icon={icon}>
                <Popup>
                  <div style={{ fontFamily: "Inter, sans-serif", minWidth: "210px" }}>
                    {/* Header */}
                    <div style={{ display:"flex", alignItems:"center", gap:"8px", marginBottom:"10px" }}>
                      <div style={{ width:"10px", height:"10px", borderRadius:"50%", background:color, flexShrink:0, boxShadow:`0 0 8px ${color}` }}></div>
                      <strong style={{ fontSize:"13px", color:"#F1F5F9", textTransform:"capitalize" }}>{cause}</strong>
                    </div>

                    {/* Location */}
                    <p style={{ fontSize:"11px", color:"#64748B", marginBottom:"4px" }}>📍 {zone}</p>
                    {event.police_station && (
                      <p style={{ fontSize:"10px", color:"#475569", marginBottom:"8px" }}>🏢 {event.police_station}</p>
                    )}

                    {/* Severity + Impact row */}
                    <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"8px" }}>
                      <div>
                        <p style={{ fontSize:"10px", color:"#475569", marginBottom:"2px" }}>Severity</p>
                        <p style={{ fontSize:"12px", fontWeight:"600", color:color, textTransform:"capitalize" }}>{SEVERITY_LABELS[severity]}</p>
                      </div>
                      <div style={{ textAlign:"right" }}>
                        <p style={{ fontSize:"10px", color:"#475569", marginBottom:"2px" }}>Impact</p>
                        <p style={{ fontSize:"12px", fontWeight:"600", color:"#F1F5F9", fontFamily:"JetBrains Mono, monospace" }}>{impact}/10</p>
                      </div>
                    </div>

                    {/* Corridor */}
                    {event.corridor && event.corridor !== "Non-corridor" && (
                      <div style={{ padding:"4px 8px", background:"rgba(59,130,246,0.1)", borderRadius:"4px", border:"1px solid rgba(59,130,246,0.2)", fontSize:"10px", color:"#93C5FD", marginBottom:"6px" }}>
                        🛣️ {event.corridor}
                      </div>
                    )}

                    {/* Road closure */}
                    {closure && (
                      <div style={{ padding:"6px 10px", background:"rgba(255,59,59,0.12)", borderRadius:"6px", border:"1px solid rgba(255,59,59,0.25)", fontSize:"11px", color:"#FCA5A5", textAlign:"center" }}>
                        ⚠ Road Closure Active
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MarkerClusterGroup>

        {/* Road closure circles (outside cluster so they are always visible) */}
        {events.filter(e => e.requires_road_closure).map(event => {
          const lat = event.latitude ?? event.lat;
          const lng = event.longitude ?? event.lng;
          if (!lat || !lng) return null;
          const severity = deriveSeverity(event);
          const color = SEVERITY_COLORS[severity] ?? "#FF8C42";
          return (
            <Circle
              key={`closure-${event.id}`}
              center={[lat, lng]}
              radius={500}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.06, weight: 1.5, dashArray: "6,4" }}
            />
          );
        })}
      </MapContainer>

      {/* Floating stats badge */}
      {!loading && (
        <div style={{
          position: "absolute", top: 12, right: 12, zIndex: 1000,
          background: "rgba(15,23,42,0.85)", backdropFilter: "blur(12px)",
          border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12,
          padding: "10px 14px", display: "flex", gap: 14,
          fontFamily: "Inter, sans-serif",
        }}>
          <div style={{ textAlign: "center" }}>
            <p style={{ fontSize: 9, color: "#64748B", marginBottom: 2, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 }}>Total</p>
            <p style={{ fontSize: 16, fontWeight: 700, color: "#F1F5F9", fontFamily: "JetBrains Mono" }}>{stats.total}</p>
          </div>
          {(["critical", "high", "medium", "low"] as const).map(level => (
            <div key={level} style={{ textAlign: "center" }}>
              <p style={{ fontSize: 9, color: "#64748B", marginBottom: 2, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 }}>{level}</p>
              <p style={{ fontSize: 16, fontWeight: 700, color: SEVERITY_COLORS[level], fontFamily: "JetBrains Mono" }}>
                {stats[level as keyof typeof stats]}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
