"""Reproduce preliminary budgets. Successful execution is NOT engineering release."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = json.loads((root / 'design_parameters.json').read_text())
b, t, d = p['battery'], p['thermal'], p['display']
energy = b['voltage_V'] * b['capacity_mAh'] / 1000 * b['age_factor'] * b['conversion_efficiency'] * b['reserve_factor']
envelopes = {}
for name, dims in p['envelopes_mm'].items():
    w, h, z = [v / 1000 for v in dims]
    area = 2 * (w*h + w*z + h*z)
    conductance = area * t['effective_area_fraction'] * t['h_W_m2K']
    rise = p['modes_W']['R1_meeting'] / b['conversion_efficiency'] / conductance
    envelopes[name] = {
        'bounding_box_volume_cm3': w*h*z*1e6,
        'box_area_m2_before_rounding': area,
        'estimated_average_rise_C': rise,
        'load_W_at_contact_target': (t['contact_target_C']-t['ambient_C'])*conductance*b['conversion_efficiency'],
        'thermal_screening': 'FAIL' if rise > t['contact_target_C']-t['ambient_C'] else 'ESTIMATE_ONLY',
        'old_70mm_carrier_fits_inner_width_with_1p8mm_walls': dims[0]-3.6 >= 70,
        'actual_assembly_status': 'R0 historical only; R1 NOT_CHECKED'
    }
report = {
    'evidence_level': 'local arithmetic and constraint checks; not hardware testing',
    'usable_Wh': energy,
    'runtime_h': {mode: energy/load for mode, load in p['modes_W'].items()},
    'max_average_load_W_for_2h': energy/2,
    'envelopes': envelopes,
    'display_frame_bytes': d['width_px']*d['height_px']*d['bits_per_pixel']//8,
    'display_10fps_payload_Mbps': d['width_px']*d['height_px']*d['bits_per_pixel']*10/1e6,
    'display_15fps_payload_Mbps': d['width_px']*d['height_px']*d['bits_per_pixel']*15/1e6,
    'display_assumed_effective_bus_Mbps': d['spi_MHz_assumption']*d['bus_efficiency_assumption'],
    'coarse_stack_without_camera_mm': sum([7.3,1.6,6,4,3.6,3]),
    'new_estimated_peak_battery_A': 7.25/(3.3*.85),
    '8h_schedule_energy_Wh_at_0p35W_idle': 7.5*.35+.5*3.4,
    '8h_schedule_energy_Wh_at_1W_idle': 7.5*1+.5*3.4,
    'cost_allocation_total_CNY_NOT_QUOTE': sum(p['budget_allocations_CNY_NOT_QUOTES'].values()),
    'release': 'BLOCKED: platform, thermal, assembly, quotes, electrical and hardware validation OPEN'
}
assert not p['fabrication_release']
assert 0 < b['conversion_efficiency'] <= 1
assert report['display_10fps_payload_Mbps'] < report['display_assumed_effective_bus_Mbps']
assert report['display_15fps_payload_Mbps'] > report['display_assumed_effective_bus_Mbps']
assert report['cost_allocation_total_CNY_NOT_QUOTE'] == 500
(root/'verification').mkdir(exist_ok=True)
(root/'verification/design_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
