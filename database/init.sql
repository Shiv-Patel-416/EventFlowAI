-- EventFlow AI — PostgreSQL Schema
-- Database initialization script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'officer' CHECK (role IN ('admin', 'officer', 'analyst', 'viewer')),
    police_station VARCHAR(200),
    zone VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- EVENTS TABLE
-- ============================================
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(50) UNIQUE,
    event_type VARCHAR(20) NOT NULL CHECK (event_type IN ('planned', 'unplanned')),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    end_latitude DOUBLE PRECISION,
    end_longitude DOUBLE PRECISION,
    address TEXT,
    end_address TEXT,
    event_cause VARCHAR(50) NOT NULL,
    requires_road_closure BOOLEAN DEFAULT FALSE,
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'closed')),
    priority VARCHAR(10) DEFAULT 'Low' CHECK (priority IN ('High', 'Low')),
    corridor VARCHAR(200),
    zone VARCHAR(100),
    junction VARCHAR(200),
    police_station VARCHAR(200),
    description TEXT,
    veh_type VARCHAR(50),
    veh_no VARCHAR(50),
    gba_identifier VARCHAR(200),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_start_datetime ON events(start_datetime);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_event_cause ON events(event_cause);
CREATE INDEX idx_events_corridor ON events(corridor);
CREATE INDEX idx_events_zone ON events(zone);
CREATE INDEX idx_events_location ON events(latitude, longitude);
CREATE INDEX idx_events_status_active ON events(status) WHERE status = 'active';

-- ============================================
-- PREDICTIONS TABLE
-- ============================================
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    severity_score DOUBLE PRECISION NOT NULL,
    severity_label VARCHAR(20),
    closure_probability DOUBLE PRECISION NOT NULL,
    estimated_duration_hours DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    feature_vector JSONB,
    model_version VARCHAR(20) DEFAULT 'v1.0.0',
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_predictions_event_id ON predictions(event_id);
CREATE INDEX idx_predictions_severity ON predictions(severity_score);

-- ============================================
-- RESOURCES TABLE
-- ============================================
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES predictions(id),
    traffic_police INTEGER DEFAULT 0,
    barricades INTEGER DEFAULT 0,
    checkpoints INTEGER DEFAULT 0,
    emergency_units INTEGER DEFAULT 0,
    total_cost_estimate DOUBLE PRECISION,
    optimization_status VARCHAR(20) DEFAULT 'pending',
    deployment_plan JSONB,
    planned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deployed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_resources_event_id ON resources(event_id);

-- ============================================
-- DIVERSIONS TABLE
-- ============================================
CREATE TABLE diversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES predictions(id),
    primary_route JSONB,
    alt_route_1 JSONB,
    alt_route_2 JSONB,
    primary_distance_km DOUBLE PRECISION,
    primary_duration_min DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'proposed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_diversions_event_id ON diversions(event_id);

-- ============================================
-- FEEDBACK TABLE
-- ============================================
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES predictions(id),
    submitted_by UUID REFERENCES users(id),
    actual_severity DOUBLE PRECISION,
    actual_duration_hours DOUBLE PRECISION,
    actual_road_closure BOOLEAN,
    actual_police_used INTEGER,
    actual_barricades_used INTEGER,
    officer_notes TEXT,
    prediction_accuracy DOUBLE PRECISION,
    resource_efficiency DOUBLE PRECISION,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_event_id ON feedback(event_id);

-- ============================================
-- ANALYTICS TABLE
-- ============================================
CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_date DATE NOT NULL,
    zone VARCHAR(100),
    corridor VARCHAR(200),
    total_events INTEGER DEFAULT 0,
    avg_severity DOUBLE PRECISION,
    avg_resolution_time DOUBLE PRECISION,
    prediction_accuracy DOUBLE PRECISION,
    closure_accuracy DOUBLE PRECISION,
    resource_utilization JSONB,
    event_cause_breakdown JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_analytics_date ON analytics(report_date);
CREATE INDEX idx_analytics_zone ON analytics(zone);

-- ============================================
-- DEFAULT ADMIN USER
-- ============================================
INSERT INTO users (username, email, password_hash, full_name, role, police_station, zone)
VALUES (
    'admin',
    'admin@eventflow.ai',
    '$2b$12$LJ3m4ys4uz0Gy8W5kOZqPeaFOPkGMz6N5jGNvKhCxFI2Dl1WS4HWm',  -- admin123
    'System Administrator',
    'admin',
    'Central HQ',
    'All Zones'
);

INSERT INTO users (username, email, password_hash, full_name, role, police_station, zone)
VALUES (
    'officer1',
    'officer@eventflow.ai',
    '$2b$12$LJ3m4ys4uz0Gy8W5kOZqPeaFOPkGMz6N5jGNvKhCxFI2Dl1WS4HWm',  -- admin123
    'Traffic Officer',
    'officer',
    'Cubbon Park',
    'Central Zone 2'
);
