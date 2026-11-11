# Sturdy sliding caliper-ruler

An original design in the spirit of the Craighill Metrolog, built to be much
stiffer than the thin Printables version in the parent folder. It is generated
by `generate.py`, so every dimension can be changed and the STL files rebuilt.

![Top view](preview_top.png)
![3D view](preview_iso.png)

## What changed for sturdiness

| | Printables version | This design |
| --- | --- | --- |
| Body | 30 × 230 × 5.4 mm | 34 × 200 × 12 mm |
| Material under the channel | thin | 4 mm solid floor |
| Slider | flat strip | 14–20 mm wide, 7.75 mm thick dovetail rail |
| Head and rail | — | one piece, no joint |
| Retention | 1.75 mm filament pin | printed spring tongue and stop in the body |
| Scales | metric only | cm and inch on the body, mm caliper scale on the rail |

- The rail is a 45° dovetail, so it cannot lift out of the body and has no
  side-to-side wobble.
- A spring tongue in the body floor pushes a bump into a groove under the
  rail. It gives steady sliding friction and is the end stop.
- At full opening (148 mm) 48 mm of rail is still inside the body.
- The big head corner is a 15 mm radius, usable as a 30 mm circle template.

## Files

| File | Size | Volume |
| --- | --- | --- |
| `sturdy_ruler_body.stl` | 34 × 200 × 12 mm | 55 cm³ |
| `sturdy_ruler_slider.stl` | 34 × 226 × 7.75 mm | 30 cm³ |

The slider is 226 mm long. It fits straight on a 235 mm or larger bed; on a
220 × 220 mm bed rotate it about 45°.

## Printing

- Both parts print flat exactly as exported, scale side up. No supports.
- 0.2 mm layers, 0.4 mm nozzle, 4 walls, 25–30 % infill.
- PETG is the better choice for the spring tongue; PLA works.
- Turn on elephant-foot compensation (about 0.15 mm) so the rail base slides
  freely.
- For readable scales, change filament colour for the last three layers
  (from 11.4 mm on the body and 7.2 mm on the slider), or rub paint or a wax
  crayon into the engraving and wipe the surface.

## Assembly

1. Push the rail tail into the open end of the body channel.
2. Keep pushing: the tail rides over the bump and the bump clicks into the
   groove. The slider now stops at 148 mm and cannot pull out.
3. To take it apart, turn the ruler over and pry the tip of the tongue
   (the end nearest the middle of the body) outward with a small
   screwdriver while pulling the slider.

## Use

- Ruler: centimetres on one edge, inches (1/16) on the other.
- Caliper: put the object between the head and the end of the body, then
  read the rail scale where the rail leaves the body.

## Tuning the fit

Edit the parameters at the top of `generate.py` and run it again
(`pip install manifold3d numpy matplotlib`, then `python3 generate.py`).

- Slides too tight: raise `SIDE_GAP` and `TAPER_GAP` by 0.05–0.1.
- Slides too loosely: raise `BUMP_TOP` by 0.1–0.2.
- Too much friction: lower `BUMP_TOP` by 0.1–0.2.

## Status

The geometry was checked in software only: both meshes are watertight, the
parts do not collide anywhere along the travel except the intended 0.4 mm
spring preload, and the stop engages at 148 mm. It has not been test printed,
so the first print may need the fit tuned as above.
