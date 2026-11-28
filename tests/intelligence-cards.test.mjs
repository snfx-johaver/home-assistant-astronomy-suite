import test from "node:test";
import assert from "node:assert/strict";
import {BUNDLES, loadBundleWithSandbox, makeHass, makeState as stateObject} from "./harness.mjs";

const makeState = (state, attributes = {}) => stateObject("sensor.fixture", state, attributes);

const {bindings} = loadBundleWithSandbox(BUNDLES.astronomy, [
  "ObservationPlannerCard", "ObservationPlannerEditor", "NightSkyHighlightsCard",
  "AstroLunarCard", "SolarActivityCard", "IssTrackerCard", "finiteValue", "renderSkyPath",
], sandbox => {
  sandbox.document.createElement = () => {
    let html = "";
    return {get innerHTML() {return html;}, set textContent(value) {
      html = String(value).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
    }};
  };
});

const entity = "sensor.astronomy_space_suite_observing_score";
const future = new Date(Date.now() + 3600000).toISOString();
const end = new Date(Date.now() + 7200000).toISOString();
const row = {time:future,scores:{stargazing:80,deep_sky:65,astrophotography:75},
  astronomical_darkness:true,sun_altitude:-25,cloud_cover:10,cloud_cover_low:10,
  cloud_cover_mid:5,cloud_cover_high:2,seeing_estimate:75,transparency_estimate:80,
  moon_interference:20,limiting_factor:"Moonlight"};

test("planner shows bounded forecast, best window and honest missing data", () => {
  const card = new bindings.ObservationPlannerCard();
  card.setConfig({});
  card.hass = makeHass({});
  assert.match(card.shadowRoot.innerHTML,/Forecast unavailable/);
  const state = makeState("80",{forecast:[row],windows:{stargazing:{start:future,end}},stale:true});
  card.hass = makeHass({[entity]:state});
  assert.match(card.shadowRoot.innerHTML,/Best viewing/);
  assert.match(card.shadowRoot.innerHTML,/Cached forecast/);
  assert.match(card.shadowRoot.innerHTML,/Seeing\*/);
  assert.doesNotMatch(card.shadowRoot.innerHTML,/NaN|undefined|Invalid Date/);
  card.hass = makeHass({[entity]:makeState("unknown",{forecast:[{time:future,scores:null},null,{time:"bad"}]})});
  assert.match(card.shadowRoot.innerHTML,/Forecast unavailable/);
  assert.doesNotMatch(card.shadowRoot.innerHTML,/NaN|undefined|Invalid Date/);
});

test("planner does not redraw or reparse forecast for unrelated HA changes", () => {
  const card = new bindings.ObservationPlannerCard();
  card.setConfig({});
  const state=makeState("80",{forecast:[row]});
  const first=makeHass({[entity]:state});
  card.hass=first;
  const rows=card._rows;
  let renders=0;
  card._render=()=>renders++;
  card.hass={...first,states:{...first.states,"sensor.unrelated":makeState("on")}};
  assert.equal(renders,0);
  assert.equal(card._rows,rows);
  card.hass={...first,states:{[entity]:makeState("75",{forecast:[row]})}};
  assert.equal(renders,1);
});

test("planner editor and YAML defaults have matching observing modes", () => {
  const editor=new bindings.ObservationPlannerEditor();
  editor.setConfig({});
  assert.deepEqual(editor._config,bindings.ObservationPlannerCard.getStubConfig());
  for(const field of ["entity","mode","hours","show_targets"]) assert.match(editor._editorTemplate(),new RegExp(`id="${field}"`));
  assert.match(editor._editorTemplate(),/deep_sky/);
  assert.match(editor._editorTemplate(),/astrophotography/);
});

test("event ribbon reuses eclipse reference and exposes local peak", () => {
  const card=new bindings.NightSkyHighlightsCard();
  card.setConfig({show_eclipses:false});
  card.hass=makeHass({"sensor.astronomy_space_suite_next_celestial_event":makeState("Geminids",{
    events:[{event_type:"meteor_shower",title:"Geminids",peak:future,end,
      visibility_from_location:"radiant_rises",altitude_at_peak:45,azimuth_at_peak:90,
      moon_interference:25,expected_rate:150,peak_estimate:true}],
  })});
  assert.match(card.shadowRoot.innerHTML,/Geminids/);
  assert.match(card.shadowRoot.innerHTML,/Radiant rises/);
  assert.match(card.shadowRoot.innerHTML,/Calendar estimate/);
  assert.doesNotMatch(card.shadowRoot.innerHTML,/NaN|undefined|Invalid Date/);
});

test("lunar card consumes real phase times without requiring another Moon integration", () => {
  const card=new bindings.AstroLunarCard();
  card.setConfig({moon_entity:"sensor.moon_phase"});
  card.hass=makeHass({"sensor.nasa_astronomy_ephemeris_moon_illumination_pct":makeState("50",{
    phase_longitude:90,illumination_pct:50,distance_km:380000,age_days:7.4,
    angular_diameter_arcmin:31.4,phases:[{title:"Full Moon",time:future,angle:180}],
    perigee:{time:future},apogee:{time:end},moonlight_impact:25,
  })});
  assert.match(card.shadowRoot.innerHTML,/380/);
  assert.match(card.shadowRoot.innerHTML,/Perigee/);
  assert.doesNotMatch(card.shadowRoot.innerHTML,/~\d+d|NaN|Invalid Date/);
});

test("solar forecast distinguishes local activity from unknown viewing conditions", () => {
  const card=new bindings.SolarActivityCard();
  card.setConfig(bindings.SolarActivityCard.getStubConfig());
  card.hass=makeHass({"sensor.astronomy_space_suite_space_weather_forecast":makeState("Elevated",{
    aurora:{time:future,probability:30},kp:[{time:future,kp:6,kind:"predicted"}],
    solar:{days:[{m_class_probability:20,x_class_probability:5,radiation_probability:1}]},
    solar_cycle:[
      {month:"2026-09",sunspots:55,solar_flux_sfu:120},
      {month:"2026-10",sunspots:45,solar_flux_sfu:108},
    ],
  })});
  assert.match(card.shadowRoot.innerHTML,/Viewing conditions unknown/);
  assert.match(card.shadowRoot.innerHTML,/Dashed: forecast/);
  assert.doesNotMatch(card.shadowRoot.innerHTML,/plausibly observable/);
  assert.match(card.shadowRoot.innerHTML,/Monthly observations/);
  assert.doesNotMatch(card.shadowRoot.innerHTML,/Purple:|Blue:/);
});

test("satellite mode bounds selection and preserves default ISS mode", () => {
  const card=new bindings.IssTrackerCard();
  card.setConfig({});
  assert.equal(card._entityId(),"sensor.astronomy_space_suite_iss_position");
  card.setConfig({mode:"satellites",satellite_entities:Array.from({length:20},(_,i)=>`sensor.satellite_${i}`)});
  assert.equal(card._satelliteEntities().length,8);
  card._selectedSatellite="sensor.satellite_1";
  assert.equal(card._entityId(),"sensor.satellite_1");
  card.setConfig({});
  assert.equal(card._entityId(),"sensor.astronomy_space_suite_iss_position");
  assert.equal(bindings.renderSkyPath([{altitude:NaN,azimuth:Infinity}]),"");
  assert.equal(bindings.finiteValue(null,0,100),null);
});

test("satellite forecast explains an empty pass window and daylight visibility", () => {
  const card=new bindings.IssTrackerCard();
  const host={innerHTML:""};
  card.shadowRoot.querySelector=selector=>selector===".iss-pass"?host:null;
  card.setConfig({show_map:false});
  const attributes={latitude:10,longitude:20,timestamp:Date.now()/1000,passes:[]};
  card.hass=makeHass({"sensor.astronomy_space_suite_iss_position":makeState("10,20",attributes)});
  assert.match(host.innerHTML,/No passes above 10°/);
  card.hass=makeHass({"sensor.astronomy_space_suite_iss_position":makeState("10,20",{
    ...attributes,passes:[{start:future,peak:future,end,observer_dark:false,sunlit:true,max_elevation:30,sky_path:[]}],
  })});
  assert.match(host.innerHTML,/Daylight pass/);
});
