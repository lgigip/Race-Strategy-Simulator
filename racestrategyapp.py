import streamlit as st
from dataclasses import dataclass, asdict
from typing import Dict, List
import random

TIRES = {"Soft": (-5, 2), "Medium": (-3, 1), "Hard": (-1, 0.5), "Wet": (-2, 1)}
PUSH  = {1: (0, -1, -1), 2: (-2, 1, 1), 3: (-4, 2, 2)}
WEATHER = ["Dry","Hot","Rain","Safety Car"]

BASE_LAP = 90
PIT_PENALTY = 25
WEAR_LIMIT = 10

@dataclass
class TeamState:
    name: str
    total: float = 0.0
    wear: float = 0.0
    fuel: float = 0.0
    must_pit: bool = False
    tire: str = "Medium"
    push: int = 2

def lap_time(team: TeamState, weather: str, pit: bool):
    t_delta, t_wear = TIRES[team.tire]
    p_delta, w_delta, f_delta = PUSH[team.push]

    # Weather effects
    weather_pen = 0
    wear_bonus = 0
    push_effect_allowed = True

    if weather == "Rain":
        if team.tire != "Wet":
            weather_pen += 8
            team.wear += 1
    if weather == "Hot":
        team.wear += 0.5
    if weather == "Safety Car":
        weather_pen += 5
        push_effect_allowed = False

    lap = BASE_LAP + t_delta + weather_pen
    if push_effect_allowed:
        lap += p_delta

    # Pit stop
    if pit:
        lap += PIT_PENALTY
        team.wear = 0
        team.fuel = 0
        team.must_pit = False
    else:
        team.wear += t_wear + w_delta
        team.fuel += f_delta
        team.wear = max(team.wear, 0)
        team.fuel = max(team.fuel, 0)
        if team.wear >= WEAR_LIMIT or team.fuel >= WEAR_LIMIT:
            team.must_pit = True

    team.total += lap
    return lap

st.title("Race Engineers — Strategy Simulator")
laps = st.session_state.get("laps", 10)
st.sidebar.header("Race Control")
laps = st.sidebar.slider("Race length (laps)", 5, 15, laps)
st.session_state["laps"] = laps

# Init teams
if "teams" not in st.session_state:
    st.session_state.teams: Dict[str, TeamState] = {
        "Rapid Racers": TeamState("Rapid Racers"),
        "Turbo Titans": TeamState("Turbo Titans"),
        "Blaze Brigade": TeamState("Blaze Brigade"),
        "Dynamo Drivers": TeamState("Dynamo Drivers")
    }
if "lap" not in st.session_state:
    st.session_state.lap = 1

teams = st.session_state.teams
lap_num = st.session_state.lap

if lap_num <= laps:
    st.subheader(f"Lap {lap_num}")
    weather = st.selectbox("Weather", WEATHER, index=0)
    cols = st.columns(len(teams))
    pits: Dict[str,bool] = {}
    for i,(name,team) in enumerate(teams.items()):
        with cols[i]:
            st.markdown(f"### {name}")
            team.tire = st.selectbox("Tire", list(TIRES.keys()), index=list(TIRES).index(team.tire), key=f"tire_{name}_{lap_num}")
            team.push = st.slider("Push", 1, 3, team.push, key=f"push_{name}_{lap_num}")
            pits[name] = st.checkbox("Pit this lap?", value=team.must_pit, key=f"pit_{name}_{lap_num}")
            st.caption(f"Wear: {team.wear:.1f}  |  Fuel: {team.fuel:.1f}  |  {'MUST PIT' if team.must_pit else ''}")

    if st.button("Run Lap"):
        results: List[tuple] = []
        for name,team in teams.items():
            t = lap_time(team, weather, pits[name])
            results.append((name, t, team.total, team.wear, team.fuel, team.must_pit))
        st.session_state.lap += 1
        st.success(f"Lap {lap_num} complete.")
        st.table(
            [{"Team":n,"Lap Time (s)":round(t,1),"Total (s)":round(tt,1),"Wear":round(w,1),"Fuel":round(f,1),"MustPit":mp}
             for (n,t,tt,w,f,mp) in sorted(results, key=lambda x: x[2])]
        )
else:
    st.header("Results")
    final = sorted([(n, t.total) for n,t in teams.items()], key=lambda x:x[1])
    st.table([{"Pos":i+1,"Team":n,"Total (s)":round(T,1)} for i,(n,T) in enumerate(final)])
    if st.button("Reset Race"):
        for t in teams.values():
            t.total = t.wear = t.fuel = 0
            t.must_pit = False
            t.tire = "Medium"; t.push = 2
        st.session_state.lap = 1
