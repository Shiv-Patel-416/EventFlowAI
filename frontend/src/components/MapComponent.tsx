"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle, ZoomControl } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { eventService } from "@/lib/api";

// Suppress default icon path issue
delete (L.Icon.Default.prototype as any)._getIconUrl;

// Premium custom SVG markers
const createPremiumIcon = (color: string, shadow: string) =>
  L.divIcon({
    className: "",
    html: `
      <div style="position:relative;width:32px;height:32px;">
        <div style="
          position:absolute;inset:0;
          background:${shadow};
          border-radius:50%;
          filter:blur(6px);
          animation:pulse 2s ease infinite;
        "></div>
        <div style="
          position:absolute;inset:4px;
          background:linear-gradient(135deg,${color},${shadow});
          border-radius:50%;
          border:2px solid rgba(255,255,255,0.25);
          box-shadow:0 0 12px ${shadow};
          display:flex;align-items:center;justify-content:center;
        ">
          <div style="width:6px;height:6px;background:white;border-radius:50%;opacity:0.9;"></div>
        </div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });

const ICONS = {
  critical: createPremiumIcon("#EF4444", "rgba(239,68,68,0.6)"),
  high:     createPremiumIcon("#FB923C", "rgba(251,146,60,0.6)"),
  medium:   createPremiumIcon("#FACC15", "rgba(250,204,21,0.5)"),
  low:      createPremiumIcon("#3B82F6", "rgba(59,130,246,0.5)"),
};

const MOCK_EVENTS = [
  { id: "1", latitude: 12.9176, longitude: 77.6234, event_cause: "Water Logging",     priority: "critical", zone: "Silk Board Junction",     closure: true,  impact: 9.1 },
  { id: "2", latitude: 12.9279, longitude: 77.6271, event_cause: "Vehicle Breakdown",  priority: "high",     zone: "Koramangala 6th Block",   closure: false, impact: 6.8 },
  { id: "3", latitude: 12.9730, longitude: 77.6016, event_cause: "Public Event",        priority: "high",     zone: "MG Road Junction",        closure: true,  impact: 7.4 },
  { id: "4", latitude: 12.9719, longitude: 77.6412, event_cause: "VIP Movement",        priority: "medium",   zone: "Indiranagar 100ft Road",  closure: false, impact: 4.7 },
  { id: "5", latitude: 13.0354, longitude: 77.5988, event_cause: "Tree Fall",           priority: "medium",   zone: "Hebbal Flyover",          closure: false, impact: 5.2 },
  { id: "6", latitude: 12.9698, longitude: 77.7499, event_cause: "Accident",            priority: "high",     zone: "Whitefield Main Road",    closure: true,  impact: 7.9 },
  { id: "7", latitude: 13.0083, longitude: 77.6953, event_cause: "Pot Holes",           priority: "low",      zone: "KR Puram Bridge",         closure: false, impact: 3.2 },
  { id: "8", latitude: 12.9258, longitude: 77.6771, event_cause: "Water Logging",     priority: "critical", zone: "Bellandur Junction",      closure: true,  impact: 8.7 },
];

const PRIORITY_COLORS: Record<string, string> = {
  critical: "#EF4444",
  high:     "#FB923C",
  medium:   "#FACC15",
  low:      "#3B82F6",
};

export default function MapComponent() {
  const [events, setEvents] = useState<any[]>(MOCK_EVENTS);

  useEffect(() => {
    eventService.getEvents({ page_size: 100, status: "active" })
      .then(data => { if (data?.events?.length) setEvents(data.events); })
      .catch(() => {/* use mock */});
  }, []);

  return (
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

      {events.map(event => {
        const lat = event.latitude  ?? event.lat;
        const lng = event.longitude ?? event.lng;
        const prio = event.priority?.toLowerCase() ?? "low";
        const icon = ICONS[prio as keyof typeof ICONS] ?? ICONS.low;
        const color = PRIORITY_COLORS[prio] ?? "#3B82F6";
        const cause = event.event_cause ?? event.cause ?? "Incident";
        const zone  = event.zone ?? `${lat?.toFixed(4)}, ${lng?.toFixed(4)}`;
        const closure = event.closure ?? event.requires_road_closure ?? false;
        const impact  = event.impact ?? "—";

        return (
          <div key={event.id}>
            <Marker position={[lat, lng]} icon={icon}>
              <Popup>
                <div style={{ fontFamily: "Inter, sans-serif", minWidth: "180px" }}>
                  <div style={{ display:"flex", alignItems:"center", gap:"8px", marginBottom:"10px" }}>
                    <div style={{ width:"10px", height:"10px", borderRadius:"50%", background:color, flexShrink:0, boxShadow:`0 0 8px ${color}` }}></div>
                    <strong style={{ fontSize:"13px", color:"#F1F5F9", textTransform:"capitalize" }}>{cause}</strong>
                  </div>
                  <p style={{ fontSize:"11px", color:"#64748B", marginBottom:"6px" }}>📍 {zone}</p>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"8px" }}>
                    <div>
                      <p style={{ fontSize:"10px", color:"#475569", marginBottom:"2px" }}>Priority</p>
                      <p style={{ fontSize:"12px", fontWeight:"600", color:color, textTransform:"capitalize" }}>{prio}</p>
                    </div>
                    <div style={{ textAlign:"right" }}>
                      <p style={{ fontSize:"10px", color:"#475569", marginBottom:"2px" }}>Impact</p>
                      <p style={{ fontSize:"12px", fontWeight:"600", color:"#F1F5F9", fontFamily:"JetBrains Mono, monospace" }}>{impact}/10</p>
                    </div>
                  </div>
                  {closure && (
                    <div style={{ padding:"6px 10px", background:"rgba(239,68,68,0.12)", borderRadius:"6px", border:"1px solid rgba(239,68,68,0.25)", fontSize:"11px", color:"#FCA5A5", textAlign:"center" }}>
                      ⚠ Road Closure Active
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>

            {closure && (
              <Circle
                center={[lat, lng]}
                radius={700}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.06, weight: 1.5, dashArray: "6,4" }}
              />
            )}
          </div>
        );
      })}
    </MapContainer>
  );
}
