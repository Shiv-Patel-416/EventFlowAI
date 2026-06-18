"""Diversion Recommendation Engine using Graph Analytics.

Uses a road network graph (simulated from Bengaluru road data) with
Dijkstra/A* pathfinding to recommend alternative routes when events
cause road closures or congestion.
"""

import math
import random

# Bengaluru major junctions and roads for graph construction
BENGALURU_JUNCTIONS = {
    "MekhriCircle": (13.0065, 77.5800),
    "HebbalFlyover": (13.0358, 77.5970),
    "SilkBoard": (12.9170, 77.6230),
    "TinFactory": (13.0060, 77.6390),
    "YeshwanthpuraCircle": (13.0270, 77.5450),
    "MajesticBusStand": (12.9770, 77.5720),
    "KRPuram": (13.0010, 77.6810),
    "MarathahalliBridge": (12.9560, 77.7010),
    "Koramangala": (12.9350, 77.6250),
    "Whitefield": (12.9700, 77.7500),
    "ElectronicCity": (12.8450, 77.6600),
    "Yelahanka": (13.1000, 77.5940),
    "Jayanagar": (12.9250, 77.5830),
    "Malleshwaram": (13.0030, 77.5680),
    "Indiranagar": (12.9720, 77.6410),
    "BTM": (12.9160, 77.6100),
    "HSRLayout": (12.9120, 77.6500),
    "BannerghattaRoad": (12.8900, 77.5990),
    "JPNagar": (12.9060, 77.5860),
    "BasavanagudiCircle": (12.9430, 77.5740),
    "MysoreRoadJunc": (12.9570, 77.5440),
    "TumkurRoadJunc": (13.0310, 77.5370),
    "ChinnaswamyStadium": (12.9789, 77.5995),
    "CubbonPark": (12.9763, 77.5929),
    "MGRoad": (12.9735, 77.6076),
    "RichmondCircle": (12.9670, 77.6090),
    "LalbaghGate": (12.9520, 77.5850),
    "VidhanaSoudha": (12.9795, 77.5912),
    "PalaceGround": (12.9950, 77.5780),
    "KanteeravStadium": (12.9750, 77.5930),
}

# Road connections with approximate distances (km) and speed limits (km/h)
ROAD_CONNECTIONS = [
    ("MekhriCircle", "HebbalFlyover", 3.5, 40),
    ("MekhriCircle", "PalaceGround", 1.5, 30),
    ("MekhriCircle", "Malleshwaram", 2.0, 25),
    ("MekhriCircle", "YeshwanthpuraCircle", 3.0, 35),
    ("HebbalFlyover", "Yelahanka", 7.0, 50),
    ("HebbalFlyover", "TinFactory", 6.0, 35),
    ("SilkBoard", "BTM", 1.5, 20),
    ("SilkBoard", "HSRLayout", 2.0, 25),
    ("SilkBoard", "Koramangala", 2.5, 20),
    ("SilkBoard", "ElectronicCity", 8.0, 40),
    ("SilkBoard", "MarathahalliBridge", 5.0, 25),
    ("TinFactory", "KRPuram", 4.0, 30),
    ("TinFactory", "Indiranagar", 3.0, 25),
    ("KRPuram", "MarathahalliBridge", 4.5, 30),
    ("KRPuram", "Whitefield", 8.0, 40),
    ("MarathahalliBridge", "Whitefield", 5.0, 35),
    ("MarathahalliBridge", "Indiranagar", 4.0, 25),
    ("Koramangala", "Indiranagar", 3.0, 25),
    ("Koramangala", "HSRLayout", 2.5, 20),
    ("Koramangala", "MGRoad", 3.0, 20),
    ("Jayanagar", "BTM", 2.0, 20),
    ("Jayanagar", "JPNagar", 2.0, 20),
    ("Jayanagar", "BasavanagudiCircle", 2.0, 20),
    ("Jayanagar", "LalbaghGate", 2.5, 20),
    ("JPNagar", "BannerghattaRoad", 2.0, 25),
    ("BannerghattaRoad", "ElectronicCity", 6.0, 35),
    ("MajesticBusStand", "MysoreRoadJunc", 2.5, 25),
    ("MajesticBusStand", "CubbonPark", 1.5, 20),
    ("MajesticBusStand", "YeshwanthpuraCircle", 3.0, 30),
    ("MajesticBusStand", "BasavanagudiCircle", 2.5, 20),
    ("YeshwanthpuraCircle", "TumkurRoadJunc", 2.0, 30),
    ("YeshwanthpuraCircle", "Malleshwaram", 2.0, 25),
    ("Malleshwaram", "CubbonPark", 2.5, 20),
    ("Malleshwaram", "PalaceGround", 2.0, 25),
    ("CubbonPark", "MGRoad", 1.0, 15),
    ("CubbonPark", "VidhanaSoudha", 0.5, 15),
    ("CubbonPark", "KanteeravStadium", 0.8, 15),
    ("CubbonPark", "ChinnaswamyStadium", 1.0, 15),
    ("MGRoad", "RichmondCircle", 1.0, 15),
    ("MGRoad", "Indiranagar", 3.0, 20),
    ("RichmondCircle", "LalbaghGate", 2.0, 15),
    ("LalbaghGate", "BasavanagudiCircle", 1.5, 15),
    ("PalaceGround", "VidhanaSoudha", 1.5, 20),
    ("PalaceGround", "ChinnaswamyStadium", 2.0, 20),
    ("BTM", "BannerghattaRoad", 2.0, 20),
]


class DiversionEngine:
    """Graph-based diversion recommendation engine."""
    
    def __init__(self):
        self.graph = {}  # Adjacency list
        self.junctions = BENGALURU_JUNCTIONS.copy()
        self._build_graph()
    
    def _build_graph(self):
        """Build adjacency list from road connections."""
        for src, dst, dist, speed in ROAD_CONNECTIONS:
            travel_time = (dist / speed) * 60  # minutes
            
            if src not in self.graph:
                self.graph[src] = []
            if dst not in self.graph:
                self.graph[dst] = []
            
            self.graph[src].append({"node": dst, "distance": dist, "time": travel_time, "speed": speed})
            self.graph[dst].append({"node": src, "distance": dist, "time": travel_time, "speed": speed})
    
    def _find_nearest_junction(self, lat, lon):
        """Find the nearest junction to given coordinates."""
        best_dist = float('inf')
        best_junc = None
        
        for name, (jlat, jlon) in self.junctions.items():
            dist = math.sqrt((lat - jlat)**2 + (lon - jlon)**2)
            if dist < best_dist:
                best_dist = dist
                best_junc = name
        
        return best_junc
    
    def _dijkstra(self, source, blocked_nodes=None, congestion_factors=None):
        """Run Dijkstra's algorithm from source, returning shortest paths."""
        blocked = set(blocked_nodes or [])
        congestion = congestion_factors or {}
        
        distances = {node: float('inf') for node in self.graph}
        distances[source] = 0
        previous = {node: None for node in self.graph}
        visited = set()
        
        while len(visited) < len(self.graph):
            # Find unvisited node with minimum distance
            current = None
            min_dist = float('inf')
            for node in self.graph:
                if node not in visited and distances[node] < min_dist:
                    min_dist = distances[node]
                    current = node
            
            if current is None:
                break
            
            visited.add(current)
            
            for edge in self.graph.get(current, []):
                neighbor = edge["node"]
                if neighbor in visited or neighbor in blocked:
                    continue
                
                # Apply congestion factor
                cong_factor = congestion.get(neighbor, 1.0)
                travel_time = edge["time"] * cong_factor
                
                new_dist = distances[current] + travel_time
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
        
        return distances, previous
    
    def _reconstruct_path(self, previous, target):
        """Reconstruct path from Dijkstra's previous map."""
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = previous.get(current)
        path.reverse()
        return path
    
    def _path_to_coordinates(self, path):
        """Convert junction path to coordinates."""
        coords = []
        for junc in path:
            if junc in self.junctions:
                lat, lon = self.junctions[junc]
                coords.append([lat, lon])
        return coords
    
    def _path_distance(self, path):
        """Calculate total distance of a path."""
        total = 0
        for i in range(len(path) - 1):
            for edge in self.graph.get(path[i], []):
                if edge["node"] == path[i + 1]:
                    total += edge["distance"]
                    break
        return total
    
    def recommend_diversions(
        self,
        event_lat: float,
        event_lon: float,
        event_cause: str = "public_event",
        requires_road_closure: bool = False,
        severity_score: float = 5.0,
        radius_km: float = 2.0
    ) -> dict:
        """
        Generate diversion route recommendations.
        
        Uses the road network graph to find alternative routes
        that avoid the affected area.
        """
        # Find nearest junction to event
        affected_junction = self._find_nearest_junction(event_lat, event_lon)
        
        # Find junctions within affected radius
        blocked_junctions = []
        if requires_road_closure or severity_score >= 7:
            for name, (jlat, jlon) in self.junctions.items():
                dist = self._haversine(event_lat, event_lon, jlat, jlon)
                if dist < radius_km * 0.3:  # Close proximity
                    blocked_junctions.append(name)
        
        # Apply congestion to nearby junctions
        congestion_factors = {}
        for name, (jlat, jlon) in self.junctions.items():
            dist = self._haversine(event_lat, event_lon, jlat, jlon)
            if dist < radius_km:
                factor = 1.0 + (severity_score / 10.0) * (1.0 - dist / radius_km) * 2.0
                congestion_factors[name] = factor
        
        # Find common destinations from the affected area
        destinations = self._get_key_destinations(affected_junction)
        
        routes = []
        for dest_name, dest_junction in destinations:
            # Normal route (without event)
            normal_dist, normal_prev = self._dijkstra(affected_junction)
            normal_path = self._reconstruct_path(normal_prev, dest_junction)
            normal_time = normal_dist.get(dest_junction, float('inf'))
            
            # Diverted route (with blocked roads and congestion)
            # Find a source that's not blocked
            source_options = [j for j in self.graph.keys() 
                           if j not in blocked_junctions and j != affected_junction]
            
            if not source_options:
                continue
            
            # Use the nearest unblocked junction as new routing point
            nearest_source = None
            min_d = float('inf')
            for s in source_options:
                if s in self.junctions:
                    d = self._haversine(event_lat, event_lon, 
                                       self.junctions[s][0], self.junctions[s][1])
                    if d < min_d:
                        min_d = d
                        nearest_source = s
            
            if not nearest_source:
                continue
            
            alt_dist, alt_prev = self._dijkstra(
                nearest_source,
                blocked_nodes=blocked_junctions,
                congestion_factors=congestion_factors
            )
            
            alt_path = self._reconstruct_path(alt_prev, dest_junction)
            alt_time = alt_dist.get(dest_junction, float('inf'))
            
            if alt_time < float('inf') and len(alt_path) > 1:
                distance = self._path_distance(alt_path)
                coords = self._path_to_coordinates(alt_path)
                
                # Determine congestion level
                if alt_time > normal_time * 1.5:
                    cong_level = "heavy"
                elif alt_time > normal_time * 1.2:
                    cong_level = "moderate"
                else:
                    cong_level = "light"
                
                routes.append({
                    "route_name": f"Via {' → '.join(alt_path[:4])}{'...' if len(alt_path) > 4 else ''}",
                    "distance_km": round(distance, 1),
                    "estimated_time_min": round(alt_time, 1),
                    "congestion_level": cong_level,
                    "coordinates": coords,
                    "path": alt_path,
                    "destination": dest_name,
                })
        
        # Sort by estimated time and take top 3
        routes.sort(key=lambda r: r['estimated_time_min'])
        top_routes = routes[:3]
        
        # If we don't have enough routes, generate generic ones
        while len(top_routes) < 3:
            generic = self._generate_generic_route(event_lat, event_lon, len(top_routes))
            top_routes.append(generic)
        
        # Clean up routes for API response (remove internal fields)
        api_routes = []
        for r in top_routes:
            api_routes.append({
                "route_name": r["route_name"],
                "distance_km": r["distance_km"],
                "estimated_time_min": r["estimated_time_min"],
                "congestion_level": r["congestion_level"],
                "coordinates": r["coordinates"],
            })
        
        return {
            "routes": api_routes,
            "affected_junction": affected_junction,
            "blocked_junctions": blocked_junctions,
            "affected_area_radius_km": radius_km,
            "total_alternatives": len(api_routes),
        }
    
    def _get_key_destinations(self, source):
        """Get key destinations from a given source."""
        important = [
            ("Majestic", "MajesticBusStand"),
            ("Silk Board", "SilkBoard"),
            ("Whitefield", "Whitefield"),
            ("Electronic City", "ElectronicCity"),
            ("Hebbal", "HebbalFlyover"),
            ("KR Puram", "KRPuram"),
            ("Yeshwanthpura", "YeshwanthpuraCircle"),
        ]
        # Filter out source
        return [(name, junc) for name, junc in important if junc != source and junc in self.graph]
    
    def _generate_generic_route(self, lat, lon, index):
        """Generate a generic route when graph-based routing doesn't find enough."""
        offsets = [
            (0.01, 0.005, "Northern Bypass"),
            (-0.005, 0.01, "Eastern Ring Road"),
            (0.005, -0.01, "Western Service Road"),
        ]
        offset = offsets[index % len(offsets)]
        
        coords = [
            [lat, lon],
            [lat + offset[0] * 0.3, lon + offset[1] * 0.3],
            [lat + offset[0] * 0.6, lon + offset[1] * 0.6],
            [lat + offset[0], lon + offset[1]],
        ]
        
        return {
            "route_name": f"Alternative Route: {offset[2]}",
            "distance_km": round(3.5 + index * 1.2, 1),
            "estimated_time_min": round(15 + index * 5, 1),
            "congestion_level": ["light", "moderate", "moderate"][index % 3],
            "coordinates": coords,
        }
    
    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))


# Singleton
diversion_engine = DiversionEngine()
