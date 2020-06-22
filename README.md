# Butterboard

Tired of using wires? Butterboard is an enchanced perforated
prototyping board! Each main hole has a nearby GND and VCC connection,
as well as two vertical and two horizontal bus connections. GND and
VCC pads are already routed, the planes are evenly distributed across
the board via grid pattern. It was initially designed for 4-layer
boards, but later we realized that the same design can be easily
done on just 2 layers.

Butterboard is fully open-source, you are free to make your
modifications and produce it as long as you share your changes. The
board can be procedurally generated by running the script as a KiCad
plugin. Currently we only provide gerbers for 50x100mm boards. You can
generate other sizes yourself, but it is probably easier to just ask
us to generate a custom board for you.

## Photos

| Description | Photo |
|:-----------:|:-----:|
| Top side | ![top-fs8](https://user-images.githubusercontent.com/5507503/81975323-83f93c80-962f-11ea-94fd-49229816e784.png) |
| GND plane is routed to all small round pads | ![gnd-fs8](https://user-images.githubusercontent.com/5507503/81975324-852a6980-962f-11ea-81d8-7dcd8c14da9d.png) |
| VCC plane is routed to all square pads | ![vcc-fs8](https://user-images.githubusercontent.com/5507503/81975316-82c80f80-962f-11ea-813e-8740bb9c83b4.png) |
| Vertical bus lanes on the top side | ![buses_top-fs8](https://user-images.githubusercontent.com/5507503/81975326-86f42d00-962f-11ea-8d41-e54a4949bb60.png) |
| Bottom side| ![bottom-fs8](https://user-images.githubusercontent.com/5507503/81975369-94a9b280-962f-11ea-9ede-9023939d22a6.png) |
| Horizontal bus lanes on the bottom side | ![buses_bottom-fs8](https://user-images.githubusercontent.com/5507503/81975336-89568700-962f-11ea-93a6-90df35724544.png) |


## Getting the boards

You can get these boards from regular PCB manufacturers. It should
cost you less than 0.9$ per board for 20 boards (<18$).

### Making an order on JLCPCB

* Download [gerber files from the latest release](https://github.com/RGVID-EU/Butterboard/releases)
* Make an order https://jlcpcb.com/quote

When ordering, select these options:
* PCB Qty: 10
* Panel By JLCPCB: Yes (x: 2 50mm, y: 1 100mm)
* Edge rails: **no**

You will get 10 panels with two 50x100mm boards each (20 boards in
total). Total price with shipping will be different depending on your
location, but it should be around 18$ or less.


## Other projects

See also other protoboard projects:
* [ALio Proto Board](https://www.crowdsupply.com/aerd/alio-proto-board)
* [Arduino Based Hackable Prototyping Board](https://www.instructables.com/id/Arduino-based-hackable-prototyping-board/)
* [:CREATE Proto Board](https://www.kitronik.co.uk/5634-create-proto-board.html)
* [Do-it-yourself SMT prototyping board](http://www.pa3cor.nl/electronics/diy-smt-prototyping-board/)
* [Flower ProtoBoard](https://www.elecfreaks.com/store/blog/post/protoboard-revolution-flower-protoboard.html)
* [Perf+](https://www.kickstarter.com/projects/658903329/perf-the-perfboard-reinvented)
* [RoutaBoard](http://routaboard.com/)
* [The Ultimate Prototyping Board](https://www.kevindarrah.com/wiki/index.php?title=The_Ultimate_Prototyping_Board:)
* [Universal through-hole and SMD prototyping board](http://whitewing.co.uk/protoboard.html)
* Know more? Please tell us!

## License
```
Butterboard is a prototyping board on steroids.
Copyright © 2019-2020
    Aleks-Daniel Jakimenko-Aleksejev <alex.jakimenko@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
