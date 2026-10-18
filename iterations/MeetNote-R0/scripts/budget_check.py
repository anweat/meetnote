from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
loads={'soc_ram':1.35,'wireless':.30,'camera_duty':.10,'fpga_clock_mics':.16,'storage':.15,'ui_rails':.10,'margin':.29}
watts=sum(loads.values());wh=3.7*2.5*.8*.88*.9;area=2*(.082*.118+.082*.029+.118*.029)
r={'evidence_level':'design calculation only, not measured','loads_W':loads,'total_load_W':watts,'usable_load_Wh':wh,'runtime_hours':wh/watts,'two_hour_max_load_W':wh/2,'battery_peak_A_at_3V3_85pct':6/(3.3*.85),'case_area_m2':area,'case_rise_C_h6_h10':[watts/.88/(h*area) for h in [6,10]],'debug_audio_2h_bytes':4*16000*3*7200,'opus_2h_bytes':32000/8*7200,'photos_bytes':120*4000000,'debug_total_with_15pct_bytes':(4*16000*3*7200+120*4000000)*1.15,'estimated_debug_meetings_20GB':int(20000000000/((4*16000*3*7200+120*4000000)*1.15)),'fpga_ring_theoretical_seconds':128*1024/(4*16000*3)}
(R/'verification/budget_calculations.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
