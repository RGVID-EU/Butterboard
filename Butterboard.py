#!/usr/bin/env python3
# Copyright © 2019-2020
#     Aleks-Daniel Jakimenko-Aleksejev <alex.jakimenko@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pcbnew
import math

# TODO This code works fine but it needs heavy refactoring.


class ButterboardPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Butterboard generator"
        self.category = "Prototyping"
        self.description = "This plugin generates a useful prototyping board"

    def Run(self):
        generate()


print("adding ButterboardPlugin")

ButterboardPlugin().register()

print("done adding ButterboardPlugin")


def mm(size_in_mm):
    # return pcbnew.FromMM(size_in_mm) # TODO it crashes
    return size_in_mm * 1000000


def deg(angle_in_deg):
    return angle_in_deg * 10


# Distance between two points of an area. Should be a very small value
AREA_STEP_EVERY = mm(0.02)
COPPER_STEP_EVERY = mm(0.01)
# Gap for solder points
GAP = mm(0.2)
# Gap between vertical rails
GAP_SPLIT = mm(0.2)

BORDER_ROUND_RADIUS  = mm(  1)
# it will make sure that the board is at least of that size
BORDER_UPSIZE_WIDTH  = mm(100)
BORDER_UPSIZE_HEIGHT = mm( 50)

MAIN_HOLE_COUNT_X = 38
MAIN_HOLE_COUNT_Y = 18

MAIN_HOLE_SHIFT      = mm(2.54)
MAIN_HOLE_SIZE       = mm(1.20)
MAIN_HOLE_DRILL_SIZE = mm(0.80)

AUX_HOLE_SIZE       = mm(0.80)
AUX_HOLE_DRILL_SIZE = mm(0.40)

CLEARANCE      = mm(0.2) # TODO not fully implemented yet
AREA_CLEARANCE = mm(0.1)
AREA_THICKNESS = mm(0.1)

TEXT_SIZE_NUMBER_TWEAK = 0.8
TEXT_SIZE_LETTER_TWEAK = 1.25 # letter size is based on the number size
# / 2 so that 2 characters can fit
TEXT_SIZE_NUMBER = int((MAIN_HOLE_SHIFT - MAIN_HOLE_SIZE) * TEXT_SIZE_NUMBER_TWEAK / 2)
TEXT_SIZE_LETTER = TEXT_SIZE_NUMBER * TEXT_SIZE_LETTER_TWEAK
TEXT_THICKNESS = TEXT_SIZE_NUMBER / 4

# Number of coppers layers
# 2 and 4 layer boards are supported
COPPER_LAYERS = 2
# COPPER_LAYERS = 4

# assuming there is enough space
TEXT_LEFT   = "https://github.com/RGVID-EU/Butterboard"
TEXT_MIDDLE = "Butterboard v1.0.0"
TEXT_RIGHT  = "Butterboard is licensed under GNU AGPLv3"
TEXT_SIZE_INFO      = mm(0.8)
TEXT_THICKNESS_INFO = mm(0.125)
# spacing between edge cuts
TEXT_INFO_HORIZONTAL_SPACING = mm(2.5)
TEXT_INFO_VERTICAL_SPACING   = mm(0.5)

# hacks and stuff
AREA_OVERLAP = mm(0.1) # to ensure connection of pads


def hole_pad(board, module, size, drill_size, pos, net,
             pad_type="round"): # round|first_half|second_half
    pad = pcbnew.D_PAD(module)
    pad.SetSize(size)
    pad.SetDrillSize(drill_size)

    # pad.SetPos0(pos) # don't do this, pcbnew will freak out after save/open
    pad.SetPosition(pos)

    if    net == ensure_net(board, "VCC") \
       or net == ensure_net(board, "GND") \
       or net == 0:
        # thru-holes
        pad.SetAttribute(pcbnew.PAD_ATTRIB_STANDARD)
        pad.SetLayerSet(pad.StandardMask())
        if net == ensure_net(board, "VCC"):
            pad.SetShape(pcbnew.PAD_SHAPE_RECT)
            pad.SetOrientation(deg(45))
        else:
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    else:
        # bridge pads
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)

        if pad_type == "round":
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        else:
            pad.SetShape(pcbnew.PAD_SHAPE_CUSTOM)
            r = int(size.GetWidth() / 2)
            inverter = 1
            if pad_type == "first_half":
                inverter = -1

            hack_shift = int(r / 2)
            gap = int(GAP / 2) * inverter
            pad.SetPosition(pcbnew.wxPoint(pos.x, pos.y + hack_shift * inverter + gap))
            module.SetPosition(pcbnew.wxPoint(module.GetPosition().x,
                                              module.GetPosition().y + gap)) # XXX yet another hack
            pad.SetSize(pcbnew.wxSize(int(r * 0.9), int(r * 0.9))) # base shape (a tad smaller)
            # ^ base shape size can't be 0 because 3d view asserts != 0
            # ^ base shape size can't be 1 because somehow you'll end up with no copper
            # ^ base shape size can't be small because KiCad will find a way to break apart

            points = pcbnew.wxPoint_Vector()
            points.append(pcbnew.wxPoint(-r, -hack_shift * inverter))
            for x in range(-r + int(COPPER_STEP_EVERY), +r, int(COPPER_STEP_EVERY)):
                # y = sqrt(r**2 - x**2)
                points.append(pcbnew.wxPoint(x, (int(math.sqrt(r**2 - x**2)) - hack_shift) * inverter))
            points.append(pcbnew.wxPoint(+r, -hack_shift * inverter))
            pad.AddPrimitive(points, 0) # 0 thickness = filled

        layer_set = pad.SMDMask().RemoveLayer(board.GetLayerID("F.Paste"))
        if "_B" in board.GetNetsByNetcode()[net].GetNetname():
            # XXX we should be flipping the module, not the pad
            pad.SetLayerSet(pcbnew.FlipLayerMask(layer_set))
            pad.Rotate(pos, 90 * 10)
        else:
            pad.SetLayerSet(layer_set)
            pad.Rotate(pos, 0)

    pad.SetPadName("0")
    pad.SetNet(board.GetNetsByNetcode()[net])
    module.Add(pad)


def hole_module(board, size, drill_size, pos, net, pad_type="round"):
    pos = pcbnew.wxPoint(pos[0], pos[1])
    main_hole_size_wx = pcbnew.wxSize(size, size)
    main_hole_drill_size_wx = pcbnew.wxSize(drill_size, drill_size)
    module = pcbnew.MODULE(board)
    module.SetPosition(pos)
    hole_pad(board, module, main_hole_size_wx, main_hole_drill_size_wx,
             pos, net, pad_type)
    board.Add(module)


def connect_area(board, width, start, end, net, squareish, endcaps, layer):
    net_textname = board.GetNetsByNetcode()[net].GetNetname()
    powernet = False
    if net_textname == "GND" or net_textname == "VCC":
        powernet = True
        squareish = False # always not squarish even if you ask for it

    distance = (end[0] - start[0], end[1] - start[1])
    magnitude = math.sqrt(distance[0] ** 2 + distance[1] ** 2)

    steps = int(magnitude / AREA_STEP_EVERY)
    step = (distance[0] / steps, distance[1] / steps)
    magnitude_per_step = magnitude / steps
    hole_size = AUX_HOLE_SIZE # endcap pad size
    if net_textname == "VCC":
        hole_size = math.sqrt(AUX_HOLE_SIZE ** 2 * 2)
    obstacle_size = AUX_HOLE_SIZE
    if squareish:
        obstacle_size = math.sqrt(AUX_HOLE_SIZE ** 2 * 2)
    #if not powernet:
    #    hole_size = AUX_HOLE_SIZE + GAP
    steps_to_ensure_connection = hole_size / 2 / magnitude_per_step

    # rotate 90 degrees counterclockwise and normalize
    normal = (distance[1] / magnitude, -distance[0] / magnitude)

    #gap_shift = (GAP * distance[0] / magnitude, GAP * distance[1] / magnitude)

    extrasteps_endcap = 0

    def fx(s, gap=False):
        fixed_tweak = 1.75
        variable_tweak = 0.6
        second_tweak = 3.5
        second_range = 0.35
        overlap_steps = int(AREA_OVERLAP / magnitude_per_step)
        y = 1 * math.cos(float(s) / steps * math.pi * 4) * width / 2 * variable_tweak \
            + width / 2 * fixed_tweak
        y_sin = y
        if    (endcaps == "full_first_half"  or not gap) and s < 0 \
           or (endcaps == "full_second_half" or not gap) and s > steps: # circle
            if s > steps:
                s -= steps
            endcap_radius = fx(0)
            # y = sqrt(r**2 - x**2)
            return math.sqrt((1**2 - (s / extrasteps_endcap)**2)) * endcap_radius
        if gap: # half of the area
            y = -GAP_SPLIT / 2
            if s < steps / 2:
                y = -magnitude_per_step * (s - steps_to_ensure_connection)
            else:
                y = -magnitude_per_step * (steps - s - steps_to_ensure_connection)
            if y > hole_size / 2:
                y = -y + hole_size
            #elif s > steps - steps_to_ensure_connection:
            #    y = GAP_SPLIT + magnitude_per_step * (steps - s)
            if 0 < s and s < steps:
                y = max(-GAP_SPLIT / 2, y)

            obstacle_half = obstacle_size / 2 + CLEARANCE
            obstacle_steps = obstacle_half / magnitude_per_step
            steps_tweak = 1
            if    endcaps == "full_first_half"  and s < steps / 2 \
               or endcaps == "full_second_half" and s > steps / 2:
                y = -obstacle_half
                if squareish:
                    y *= 0.145
                else:
                    steps_tweak = 0.8
                    y *= 0.45 / steps_tweak

            obstacle_steps *= steps_tweak

            if steps / 2 - obstacle_steps < s and s < steps / 2 + obstacle_steps:
                slope_coef = (obstacle_half + y) / obstacle_half / steps_tweak
                y = slope_coef * abs(s - steps / 2) * magnitude_per_step - (obstacle_size / 2 + CLEARANCE)

            if endcaps == "full_first_half" and 0 <= s and s < steps / 2 - obstacle_steps:
                amount = s / (steps / 2 - obstacle_steps) # ease into the circle
                amount *= amount
                return y * amount + y_sin * (1 - amount)

            if endcaps == "full_second_half" and steps / 2 + obstacle_steps < s and s <= steps:
                amount = (steps - s) / (steps / 2 - obstacle_steps) # ease into the circle
                amount *= amount
                return y * amount + y_sin * (1 - amount)
            return y
        if not squareish: # tweak for the square holes
            return y
        if s == int(steps / 2):
            return width / 2 * second_tweak
        if second_range * steps < s and s < (1 - second_range) * steps:
            return None

        return y

    #extrasteps = int((fx(0) + GAP / 2) / AREA_STEP_EVERY) # rounded endcaps
    extrasteps_endcap = int(  fx(0, gap=False) / AREA_STEP_EVERY) # rounded endcaps
    extrasteps_gap    = int(           GAP / 2 / AREA_STEP_EVERY) # gap for split pads

    if powernet: # no gap for powernets
        extrasteps_gap = -int(mm(0.1) / AREA_STEP_EVERY) # slight overlap

    extrasteps_start = 0
    extrasteps_end   = 0
    # TODO remove copy-paste
    if "first_half" in endcaps or endcaps == "both":
        if "full_first_half" == endcaps:
            extrasteps_start = extrasteps_endcap
        else:
            if net_textname == "VCC":
                extrasteps_start = int(extrasteps_endcap * 0.95)
            else:
                extrasteps_start = int(extrasteps_endcap * 0.89)
    else:
        extrasteps_start = -extrasteps_gap
    if "second_half" in endcaps or endcaps == "both":
        if "full_second_half" == endcaps:
            extrasteps_end = extrasteps_endcap
        else:
            if net_textname == "VCC":
                extrasteps_end = int(extrasteps_endcap * 0.95)
            else:
                extrasteps_end = int(extrasteps_endcap * 0.89)
    else:
        extrasteps_end   = -extrasteps_gap

    zone_container = board.InsertArea(net, 0, layer,
                                      int(start[0] - step[0] * extrasteps_start),
                                      int(start[1] - step[1] * extrasteps_start),
                                      pcbnew.ZONE_CONTAINER.DIAGONAL_EDGE)

    shape_poly_set = zone_container.Outline()

    for s in range(-extrasteps_start, steps + 1 + extrasteps_end):
        gap = (COPPER_LAYERS < 4 and powernet)
        y = fx(s, gap=gap)
        if y is None:
            continue

        shape_poly_set.Append(int(start[0] + step[0] * s + y * normal[0]),
                              int(start[1] + step[1] * s + y * normal[1]))

    # We add one step to make sure that the pad is within the zone
    shape_poly_set.Append(int(end[0] + step[0] * extrasteps_end),
                          int(end[1] + step[1] * extrasteps_end))

    for s in reversed(range(-extrasteps_start, steps + 1 + extrasteps_end)):
        gap = (COPPER_LAYERS < 4 and not powernet)
        y = fx(s, gap=gap)
        if y is None:
            continue

        shape_poly_set.Append(int(start[0] + step[0] * s - y * normal[0]),
                              int(start[1] + step[1] * s - y * normal[1]))

    zone_container.Hatch()
    zone_container.SetZoneClearance(int(AREA_CLEARANCE))
    zone_container.SetMinThickness(int(AREA_THICKNESS))
    zone_container.SetPadConnection(pcbnew.PAD_ZONE_CONN_FULL) # full = solid
    zone_container.SetThermalReliefGap(int(mm(0.2)))
    zone_container.SetThermalReliefCopperBridge(int(mm(0.3)))
    zone_container.SetCornerSmoothingType(pcbnew.ZONE_SETTINGS.SMOOTHING_FILLET)
    zone_container.SetCornerRadius(int(mm(0.4)))

    shape_poly_set.Simplify(pcbnew.SHAPE_POLY_SET.PM_STRICTLY_SIMPLE) # PM_FAST or PM_STRICTLY_SIMPLE
    #if "full_" in endcaps:
    #    zone_container.SetPriority(2)
    #else:
    #    zone_container.SetPriority(1)


def power_plane(board, net, x1, y1, x2, y2):
    if board.GetNetsByNetcode()[net].GetNetname() == "GND":
        layer = board.GetLayerID("In1.Cu")
    else:
        layer = board.GetLayerID("In2.Cu")

    zone_container = board.InsertArea(net, 0, layer,
                                      int(x1), int(y1),
                                      pcbnew.ZONE_CONTAINER.DIAGONAL_EDGE)

    shape_poly_set = zone_container.Outline()

    shape_poly_set.Append(int(x2), int(y1))
    shape_poly_set.Append(int(x2), int(y2))
    shape_poly_set.Append(int(x1), int(y2))

    zone_container.Hatch()
    zone_container.SetZoneClearance(int(mm(0.1)))
    zone_container.SetMinThickness(int(mm(0.1)))
    zone_container.SetPadConnection(pcbnew.PAD_ZONE_CONN_THERMAL)
    zone_container.SetThermalReliefGap(int(mm(0.4)))
    zone_container.SetThermalReliefCopperBridge(int(mm(0.5)))


def generate_text_hint(board, text, width, height, thickness, x, y):
    txt = pcbnew.TEXTE_PCB(board)
    txt.SetText(text)
    txt.SetPosition(pcbnew.wxPoint(int(x), int(y)))
    txt.SetHorizJustify(pcbnew.GR_TEXT_HJUSTIFY_CENTER)
    txt.SetTextSize(pcbnew.wxSize(int(width), int(height)))
    txt.SetThickness(int(thickness))
    return txt


def text_hint(board, text, width, height, thickness, x, y):
    txt_t = generate_text_hint(board, text, width, height, thickness, x, y)
    txt_b = generate_text_hint(board, text, width, height, thickness, x, y)
    txt_t.SetLayer(board.GetLayerID("F.SilkS"))
    txt_b.SetLayer(board.GetLayerID("F.SilkS"))  # not "B.SilkS" cuz flip takes care of that
    txt_b.Flip(pcbnew.wxPoint(x, y))
    board.Add(txt_t)
    board.Add(txt_b)


def line(board, layer, x1, y1, x2, y2):
    seg1 = pcbnew.DRAWSEGMENT(board)
    seg1.SetStart(pcbnew.wxPoint(x1, y1))
    seg1.SetEnd(  pcbnew.wxPoint(x2, y2))
    seg1.SetLayer(layer)
    board.Add(seg1)


def arc(board, layer, x1, y1, x2, y2):
    seg1 = pcbnew.DRAWSEGMENT(board)
    seg1.SetShape(pcbnew.S_ARC)
    seg1.SetArcStart(pcbnew.wxPoint(x1, y1))
    seg1.SetCenter(  pcbnew.wxPoint(x2, y2))
    seg1.SetAngle(deg(90))
    seg1.SetLayer(layer)
    board.Add(seg1)


def border(board, width, height, center_x, center_y):
    layer = board.GetLayerID("Edge.Cuts")

    x1 = center_x -  width / 2
    y1 = center_y - height / 2
    x2 = center_x +  width / 2
    y2 = center_y + height / 2

    r = BORDER_ROUND_RADIUS

    # edge cuts
    line(board, layer, x1 + r, y1,     x2 - r, y1    )  # top
    line(board, layer, x1 + r, y2,     x2 - r, y2    )  # bottom
    line(board, layer, x1,     y1 + r, x1,     y2 - r)  # left
    line(board, layer, x2,     y1 + r, x2,     y2 - r)  # right

    arc( board, layer, x1    , y1 + r, x1 + r, y1 + r)  # top-left
    arc( board, layer, x2 - r, y1    , x2 - r, y1 + r)  # top-right
    arc( board, layer, x2    , y2 - r, x2 - r, y2 - r)  # bottom-right
    arc( board, layer, x1 + r, y2    , x1 + r, y2 - r)  # bottom-left

    # helpful text
    text_stuff = []
    text_stuff.append(generate_text_hint(board, TEXT_LEFT, TEXT_SIZE_INFO,
                                         TEXT_SIZE_INFO, TEXT_THICKNESS_INFO,
                                         x1 + TEXT_INFO_HORIZONTAL_SPACING, y2 - TEXT_INFO_VERTICAL_SPACING))
    text_stuff.append(generate_text_hint(board, TEXT_MIDDLE, TEXT_SIZE_INFO,
                                         TEXT_SIZE_INFO, TEXT_THICKNESS_INFO,
                                         center_x,                          y2 - TEXT_INFO_VERTICAL_SPACING))
    text_stuff.append(generate_text_hint(board, TEXT_RIGHT, TEXT_SIZE_INFO,
                                         TEXT_SIZE_INFO, TEXT_THICKNESS_INFO,
                                         x2 - TEXT_INFO_HORIZONTAL_SPACING, y2 - TEXT_INFO_VERTICAL_SPACING))

    text_stuff[0].SetHorizJustify(pcbnew.GR_TEXT_HJUSTIFY_LEFT)
    text_stuff[1].SetHorizJustify(pcbnew.GR_TEXT_HJUSTIFY_CENTER)
    text_stuff[2].SetHorizJustify(pcbnew.GR_TEXT_HJUSTIFY_RIGHT)
    for text in text_stuff:
        text.SetVertJustify(pcbnew.GR_TEXT_VJUSTIFY_BOTTOM)
        text.SetLayer(board.GetLayerID("F.SilkS"))
        board.Add(text)


    if COPPER_LAYERS >= 4:
        # power planes
        power_plane(board, ensure_net(board, "VCC"),
                    x1 - mm(10), y1 - mm(10),
                    x2 + mm(10), y2 + mm(10))
        power_plane(board, ensure_net(board, "GND"),
                    x1 - mm(15), y1 - mm(15),
                    x2 + mm(15), y2 + mm(15))

    # origin
    board.SetAuxOrigin(pcbnew.wxPoint(int(x1), int(y1)))


def ensure_net(board, net_name):
    net = pcbnew.NETINFO_ITEM(board, net_name)
    board.Add(net)
    return net.GetNet() # luckily, it makes sure there are no duplicates


def generate():
    print("Generating Butterboard")
    board = pcbnew.GetBoard()

    # This is hard to find but may be useful:
    #board.GetNetClasses().Add(pcbnew.NETCLASSPTR("helloworld"))
    #board.SynchronizeNetsAndNetClasses()
    #board.Add(pcbnew.NETCLASSPTR("hello"))

    if board.GetCopperLayerCount() < COPPER_LAYERS:
        board.SetCopperLayerCount(COPPER_LAYERS)

    # main holes
    for x in range(MAIN_HOLE_COUNT_X):
        for y in range(MAIN_HOLE_COUNT_Y):
            hole_module(board,
                        MAIN_HOLE_SIZE, MAIN_HOLE_DRILL_SIZE,
                        (x * MAIN_HOLE_SHIFT,
                         y * MAIN_HOLE_SHIFT),
                        0)

    # text hints
    for x in range(MAIN_HOLE_COUNT_X + 1):
        for y in range(MAIN_HOLE_COUNT_Y):
            text_hint(board, str(chr(ord("A") + y)),
                      TEXT_SIZE_LETTER, TEXT_SIZE_LETTER, TEXT_THICKNESS,
                      (x - 0.5) * MAIN_HOLE_SHIFT, y * MAIN_HOLE_SHIFT)
    for x in range(MAIN_HOLE_COUNT_X):
        for y in range(MAIN_HOLE_COUNT_Y + 1):
            text_hint(board, "%02d" % (x,),
                      TEXT_SIZE_NUMBER, TEXT_SIZE_NUMBER, TEXT_THICKNESS,
                      x * MAIN_HOLE_SHIFT, (y - 0.5) * MAIN_HOLE_SHIFT)

    # auxiliary pads
    for x in range(MAIN_HOLE_COUNT_X + 1):
        for y in range(MAIN_HOLE_COUNT_Y + 1):
            pad_types = ("round",)
            if (x + y) % 2 == 0:
                if y % 2 == 0:
                    nets = ("GND",)
                else:
                    nets = ("VCC",)
            else:
                nets = ("AUX_%02d_T" % (x,),
                        "AUX_%02d_B" % (y,),)


            for net in nets:
                pad_types = ("first_half", "second_half")
                if net.endswith("_B"):
                    if x <= 1 or MAIN_HOLE_COUNT_X - 1 <= x:
                        pad_types = ("round",)
                if net.endswith("_T"):
                    if y <= 1 or MAIN_HOLE_COUNT_Y - 1 <= y:
                        pad_types = ("round",)

                for pad_type in pad_types:
                    actual_net = net
                    if net.endswith("_T"):
                        if pad_type == "second_half" or y <= 1:
                            actual_net += "_%02d" % (y // 2 + 1,)
                        else:
                            actual_net += "_%02d" % (y // 2 + 0,)
                    if net.endswith("_B"):
                        if pad_type == "second_half" or x <= 1:
                            actual_net += "_%02d" % (x // 2 + 1,)
                        else:
                            actual_net += "_%02d" % (x // 2 + 0,)
                    hole_module(board, AUX_HOLE_SIZE, AUX_HOLE_DRILL_SIZE,
                                ((x - 0.5) * MAIN_HOLE_SHIFT,
                                 (y - 0.5) * MAIN_HOLE_SHIFT),
                                ensure_net(board, actual_net), pad_type)

            # sinusoidal copper pours
            if COPPER_LAYERS >= 4 and (actual_net == "GND" or actual_net == "VCC"):
                continue
            if y <= MAIN_HOLE_COUNT_Y - 2:
                endcap = "none"
                if y == 0:
                    endcap = "full_first_half"
                elif y == 1:
                    endcap = "first_half"
                if y == MAIN_HOLE_COUNT_Y - 2:
                    endcap = "full_second_half"
                elif y == MAIN_HOLE_COUNT_Y - 3:
                    endcap = "second_half"

                actual_net = nets[0]
                if actual_net != "GND" and actual_net != "VCC":
                    actual_net += "_%02d" % (y // 2 + 1,)
                connect_area(board, AUX_HOLE_SIZE,
                             ((x - 0.5) * MAIN_HOLE_SHIFT,
                              (y - 0.5) * MAIN_HOLE_SHIFT),
                             ((x - 0.5) * MAIN_HOLE_SHIFT,
                              (y + 1.5) * MAIN_HOLE_SHIFT),
                             ensure_net(board, actual_net),
                             y % 2 == 0, endcap,
                             board.GetLayerID("F.Cu"))

            if x <= MAIN_HOLE_COUNT_X - 2:
                endcap = "none"
                if x == 0:
                    endcap = "full_first_half"
                elif x == 1:
                    endcap = "first_half"
                if x == MAIN_HOLE_COUNT_X - 2:
                    endcap = "full_second_half"
                elif x == MAIN_HOLE_COUNT_X - 3:
                    endcap = "second_half"

                if len(nets) > 1:
                    actual_net = nets[1]
                else:
                    actual_net = nets[0]
                if actual_net != "GND" and actual_net != "VCC":
                    actual_net += "_%02d" % (x // 2 + 1,)
                connect_area(board, AUX_HOLE_SIZE,
                             ((x - 0.5) * MAIN_HOLE_SHIFT,
                              (y - 0.5) * MAIN_HOLE_SHIFT),
                             ((x + 1.5) * MAIN_HOLE_SHIFT,
                              (y - 0.5) * MAIN_HOLE_SHIFT),
                             ensure_net(board, actual_net),
                             x % 2 == 0, endcap,
                             board.GetLayerID("B.Cu"))

    border(board,
           max(BORDER_UPSIZE_WIDTH,  MAIN_HOLE_SHIFT * (MAIN_HOLE_COUNT_X + 1)),
           max(BORDER_UPSIZE_HEIGHT, MAIN_HOLE_SHIFT * (MAIN_HOLE_COUNT_Y + 1)),
           (MAIN_HOLE_COUNT_X - 1) * MAIN_HOLE_SHIFT / 2,
           (MAIN_HOLE_COUNT_Y - 1) * MAIN_HOLE_SHIFT / 2)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.Refresh()
    print("Done generating Butterboard")
