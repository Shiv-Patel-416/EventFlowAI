const pptxgen = require("pptxgenjs");
const fs = require('fs');

let pres = new pptxgen();

// Title Slide
let slide1 = pres.addSlide();
slide1.background = { color: "0B1020" };
slide1.addText("EventFlow AI", { x: 1.5, y: 1.5, w: "70%", h: 2, fontSize: 48, bold: true, color: "06B6D4", align: "center" });
slide1.addText("Traffic Intelligence & Orchestration Platform\nProactive, AI-driven urban mobility management", { x: 1.5, y: 3.5, w: "70%", h: 1, fontSize: 20, color: "FFFFFF", align: "center" });

// The Problem
let slide2 = pres.addSlide();
slide2.background = { color: "0B1020" };
slide2.addText("The Motive: The Problem", { x: 0.5, y: 0.5, w: "90%", h: 1, fontSize: 32, bold: true, color: "EF4444" });
slide2.addText([
    { text: "Current traffic management solutions are REACTIVE\n\n", options: { bullet: true } },
    { text: "Political rallies, festivals, sports events, construction activities, and sudden VIP movements create localized traffic breakdowns.\n\n", options: { bullet: true } },
    { text: "Police only respond to congestion AFTER it happens.", options: { bullet: true } }
], { x: 0.5, y: 1.5, w: "90%", h: 3, fontSize: 20, color: "FFFFFF" });

// The Solution
let slide3 = pres.addSlide();
slide3.background = { color: "0B1020" };
slide3.addText("The Solution: EventFlow AI", { x: 0.5, y: 0.5, w: "90%", h: 1, fontSize: 32, bold: true, color: "10B981" });
slide3.addText([
    { text: "A PROACTIVE full-stack intelligence platform\n\n", options: { bullet: true } },
    { text: "Fuses Machine Learning with Operations Research\n\n", options: { bullet: true } },
    { text: "Predicts traffic disruptions BEFORE they peak\n\n", options: { bullet: true } },
    { text: "Automatically calculates congestion severity, duration, and the exact resource deployment plan (Police & Barricades).", options: { bullet: true } }
], { x: 0.5, y: 1.5, w: "90%", h: 3, fontSize: 20, color: "FFFFFF" });

// Screenshot Helper
function addScreenshotSlide(title, imagePath, description, color) {
    let slide = pres.addSlide();
    slide.background = { color: "0B1020" };
    slide.addText(title, { x: 0.5, y: 0.5, w: "90%", h: 0.8, fontSize: 28, bold: true, color: color });
    
    if (fs.existsSync(imagePath)) {
        slide.addImage({ path: imagePath, x: 0.5, y: 1.5, w: 9, h: 3.5, sizing: { type: "contain", w: 9, h: 3.5 } });
    }
    
    slide.addText(description, { x: 0.5, y: 5.2, w: "90%", h: 0.5, fontSize: 16, color: "94A3B8" });
}

addScreenshotSlide("Command Center / Overview", "presentation/dashboard.png", "Real-time tracking of active incidents with high-level KPIs for city managers.", "3B82F6");
addScreenshotSlide("Geospatial Intel & Route Diversion", "presentation/map.png", "A*/Dijkstra algorithms calculate fastest alternative routes around incidents to prevent cascade jams.", "06B6D4");
addScreenshotSlide("AI Predictor (Impact Simulation)", "presentation/predictions.png", "XGBoost v3.0 calculates Severity Score, Est. Duration, and Resource Plan based on event parameters.", "A78BFA");
addScreenshotSlide("Jurisdiction Leaderboard & Analytics", "presentation/analytics.png", "Gamified tracking for Police Stations based on dynamic Efficiency Score.", "FACC15");

// Save the PPT
pres.writeFile({ fileName: "presentation/EventFlowAI_Pitch.pptx" }).then(() => {
    console.log("PPT generated!");
});
