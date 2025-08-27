from datetime import datetime
import os
import random
import shutil

cc_root = "./commands/resources/crowdcontrol"
cc_multiplier = int(os.environ.get("CC_MULTIPLIER", "1"))

current_threshold = 5000
threshold_modifier = 2500
threshold_tier_size = 3
total_bits = 0
total_adds = 0

def set_cc_multiplier(mult: int):
    global cc_multiplier
    if mult != 0:
        cc_multiplier = mult

#####################################################################################################
# Generic Shuffler Handling
#####################################################################################################
'''
Helper function to add more games to the shuffler.
'''
def add_next_game(count: int = 1) -> int:
    i = 0
    bizhawk_folder = "C:/Games/Bizhawk-2.9.1/bizhawk-shuffler-2"
    games_dir = os.fsencode(bizhawk_folder + "/games")
    extra_games_dir = os.fsencode(bizhawk_folder + "/extra-games")
    for file in os.listdir(extra_games_dir):
        src = os.path.join(extra_games_dir, file)
        dst = os.path.join(games_dir, file)
        shutil.copyfile(src, dst)
        os.remove(src)
        i += 1
        # don't copy more than "count" seeds at a time
        if i >= count:
            break
    return i

'''
Handle gift subs (treated as tier 1 monetary value in USD for simplicity).
'''
def handle_generic_cc_subs(subcnt: int, tier: int = 1):
    mult = 300 # $3 from tier 1's
    if tier == 2:
        mult = 500 # $5 from tier 2's
    elif tier == 3:
        mult = 1250 # $12.50 from tier 3's
    handle_generic_cc_bits(subcnt * mult)

'''
Handle generic shuffler and adding new games at bit milestones.
'''
def handle_generic_cc_bits(bits: int):
    global current_threshold
    global total_bits
    global total_adds
    total_bits += bits
    num_swaps = bits // 75
    if num_swaps >= 1:
        interval_swaps += (num_swaps - 1)
        print(f"[CC {datetime.now()}] Swapping {num_swaps} times")
        cc_file = f"{cc_root}/cc-shuffle.txt"
        # increment interval swaps if the file still exists (effectively two cheers in a <16ms window)
        if os.path.isfile(cc_file):
            interval_swaps += 1
        else:
            with open(cc_file, "w+") as f:
                f.write("Shuffle")

    while total_bits >= current_threshold:
        added_game_count = add_next_game()
        print(f"[CC {datetime.now()}] Adding {added_game_count} game(s)")
        total_bits -= current_threshold
        total_adds += 1
        if total_adds % threshold_tier_size == 0:
            current_threshold += threshold_modifier

#####################################################################################################
# PM64R CC Handlers
#####################################################################################################
# triggers on exact amounts of bits cheered
pm64_bit_values = {
    5:      "Set FP Max",
    10:     "Set HP Max",
    12:     "Add 10 Coins",
    16:     "Subtract 10 Coins",
    20:     "Set HP 1",
    25:     "Set HP 2",
    30:     "Disable Speedy Spin",  # 1 minute
    40:     "Berserker",            # 1 minute
    50:     "Random Pitch",         # 1 minute
    55:     "Set FP 0",
    69:     "Toggle Mirror Mode",
    75:     "Shuffle Current Seed", # change seed being played
    100:    "Slow Go",              # 1 minute
    200:    "Disable All Badges",
    220:    "Disable Heart Blocks", # 5 minutes
    250:    "Disable Save Blocks",  # 5 minutes
    300:    "Homeward Shroom",
    500:    "Interval Swap",        # change seed 10 times in 10 second intervals
    1000:   "Set Homeward Shroom"
}

# triggers on exact amounts of gift subs
pm64_sub_values = {
    1:  "Slow Go",          # 90 seconds
    5:  "OHKO Mode",        # 5-10 minutes (random)
    20: "Interval Swap",    # change seed 30 times in 10 second intervals
    50: "Poverty",          # 1hp, 0fp, 0 coins, 
                            # disable heart blocks for 10 minutes, 
                            # disable save blocks for 10 minutes, 
                            # slow go for 10 minutes, 
                            # ohko 10 minutes
    100: "Add Seeds"
}

# pm64r queue trackers
slowgo_queue        = 0
berserker_queue     = 0
random_pitch_queue  = 0
speedy_queue        = 0
heart_block_queue   = 0
save_block_queue    = 0
ohko_queue          = 0
interval_swaps      = 0
hs_interval_swaps   = 0

'''
Special handling for PM64R effects on gift subs.
'''
def handle_pm64_cc_subs(subcnt: int, tier: int = 1):
    global slowgo_queue
    global berserker_queue
    global random_pitch_queue
    global speedy_queue
    global heart_block_queue
    global save_block_queue
    global ohko_queue
    global interval_swaps
    global hs_interval_swaps

    if subcnt in pm64_sub_values:
        if pm64_sub_values[subcnt] == "Slow Go":
            slowgo_queue += 90
            print(f"[CC {datetime.now()}] Slow Go {slowgo_queue} seconds")
            with open(f"{cc_root}/pm64r-slowgo.txt", "w+") as f:
                f.write("YEP")
        elif pm64_sub_values[subcnt] == "OHKO Mode":
            ohko_queue += random.randint(300, 600)
            print(f"[CC {datetime.now()}] OHKO Mode {ohko_queue}")
            with open(f"{cc_root}/pm64r-ohko.txt", "w+") as f:
                f.write("eww")
        elif pm64_sub_values[subcnt] == "Interval Swap":
            interval_swaps += 29 # 30 including the current one
            hs_interval_swaps += 4
            print(f"[CC {datetime.now()}] Adding Interval Swaps {interval_swaps}")
            with open(f"{cc_root}/pm64r-set-homeward-shroom.txt", "w+") as f:
                f.write("oh no")
            with open(f"{cc_root}/cc-shuffle.txt", "w+") as f:
                f.write("Shuffle")
        elif pm64_sub_values[subcnt] == "Poverty":
            print(f"[CC {datetime.now()}] POVERTY")
            ohko_queue += 600
            slowgo_queue += 600
            heart_block_queue += 600
            save_block_queue += 600
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("1")
            with open(f"{cc_root}/pm64r-setfp.txt", "w+") as f:
                f.write("0")
            with open(f"{cc_root}/pm64r-addcoins.txt", "w+") as f:
                f.write("-999")
            with open(f"{cc_root}/pm64r-disable-heart-blocks.txt", "w+") as f:
                f.write("eww")
            with open(f"{cc_root}/pm64r-disable-save-blocks.txt", "w+") as f:
                f.write("eww")
            with open(f"{cc_root}/pm64r-slowgo.txt", "w+") as f:
                f.write("eww")
            with open(f"{cc_root}/pm64r-ohko.txt", "w+") as f:
                f.write("eww")
        elif pm64_sub_values[subcnt] == "Add Seeds":
            print(f"[CC {datetime.now()}] Adding 5 more seeds!")
            add_next_game(count=5)

'''
Special handling for PM64R effects on bits.
'''
def handle_pm64_cc_bits(bits: int):
    global cc_multiplier
    global slowgo_queue
    global berserker_queue
    global random_pitch_queue
    global speedy_queue
    global heart_block_queue
    global save_block_queue
    global ohko_queue
    global interval_swaps

    bits //= cc_multiplier
    if bits in pm64_bit_values:
        if pm64_bit_values[bits] == "Set FP Max":
            print(f"[CC {datetime.now()}] Set FP Max")
            with open(f"{cc_root}/pm64r-setfp.txt", "w+") as f:
                f.write("99")
        elif pm64_bit_values[bits] == "Set FP 0":
            print(f"[CC {datetime.now()}] Set FP 0")
            with open(f"{cc_root}/pm64r-setfp.txt", "w+") as f:
                f.write("0")
        elif pm64_bit_values[bits] == "Set HP Max":
            print(f"[CC {datetime.now()}] Set HP Max")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("99")
        elif pm64_bit_values[bits] == "Set HP 1":
            print(f"[CC {datetime.now()}] Set HP 1")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("1")
        elif pm64_bit_values[bits] == "Set HP 2":
            print(f"[CC {datetime.now()}] Set HP 2")
            with open(f"{cc_root}/pm64r-sethp.txt", "w+") as f:
                f.write("2")
        elif pm64_bit_values[bits] == "Add 10 Coins":
            print(f"[CC {datetime.now()}] Add 10 Coins")
            with open(f"{cc_root}/pm64r-addcoins.txt", "w+") as f:
                f.write("10")
        elif pm64_bit_values[bits] == "Subtract 10 Coins":
            print(f"[CC {datetime.now()}] Subtract 10 Coins")
            with open(f"{cc_root}/pm64r-addcoins.txt", "w+") as f:
                f.write("-10")
        elif pm64_bit_values[bits] == "Berserker":
            berserker_file = f"{cc_root}/pm64r-berserker.txt"
            berserker_queue += 60
            if not(os.path.isfile(berserker_file)):
                print(f"[CC {datetime.now()}] Berserker {berserker_queue} seconds")
                with open(berserker_file, "w+") as f:
                    f.write("who?")
        elif pm64_bit_values[bits] == "Slow Go":
            slowgo_file = f"{cc_root}/pm64r-slowgo.txt"
            slowgo_queue += 60
            if not(os.path.isfile(slowgo_file)):
                print(f"[CC {datetime.now()}] Slow Go {slowgo_queue} seconds")
                with open(slowgo_file, "w+") as f:
                    f.write("Of course")
        elif pm64_bit_values[bits] == "Random Pitch":
            pitch_file = f"{cc_root}/pm64r-random-pitch.txt"
            random_pitch_queue += 60
            if not(os.path.isfile(pitch_file)):
                print(f"[CC {datetime.now()}] Random Pitch enabled")
                with open(pitch_file, "w+") as f:
                    f.write("why??")
        elif pm64_bit_values[bits] == "Disable All Badges":
            print(f"[CC {datetime.now()}] Disable All Badges")
            with open(f"{cc_root}/pm64r-disablebadges.txt", "w+") as f:
                f.write("Rude af")
        elif pm64_bit_values[bits] == "Shuffle Current Seed":
            print(f"[CC {datetime.now()}] Shuffle Current Seed")
            with open(f"{cc_root}/cc-shuffle.txt", "w+") as f:
                f.write("Shuffle")
        elif pm64_bit_values[bits] == "Interval Swap":
            interval_swaps += 9 # 10 including the current one
            print(f"[CC {datetime.now()}] Adding Interval Swaps {interval_swaps}")
            with open(f"{cc_root}/cc-shuffle.txt", "w+") as f:
                f.write("Shuffle")
        elif pm64_bit_values[bits] == "Toggle Mirror Mode":
            print(f"[CC {datetime.now()}] Toggle Mirror Mode")
            with open(f"{cc_root}/pm64r-toggle-mirror.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Speedy Spin":
            print(f"[CC {datetime.now()}] Disable Speedy Spin")
            speedy_queue += 60
            with open(f"{cc_root}/pm64r-disable-speedy.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Heart Blocks":
            print(f"[CC {datetime.now()}] Disable Heart Blocks")
            heart_block_queue += 300
            with open(f"{cc_root}/pm64r-disable-heart-blocks.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Disable Save Blocks":
            print(f"[CC {datetime.now()}] Disable Save Blocks")
            save_block_queue += 300
            with open(f"{cc_root}/pm64r-disable-save-blocks.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "OHKO Mode":
            ohko_queue += 300
            print(f"[CC {datetime.now()}] OHKO Mode {ohko_queue}")
            with open(f"{cc_root}/pm64r-ohko.txt", "w+") as f:
                f.write("eww")
        elif pm64_bit_values[bits] == "Homeward Shroom":
            print(f"[CC {datetime.now()}] Homeward Shroom")
            with open(f"{cc_root}/pm64r-homeward-shroom.txt", "w+") as f:
                f.write("god dammit")
        elif pm64_bit_values[bits] == "Set Homeward Shroom":
            print(f"[CC {datetime.now()}] Set Homeward Shroom")
            with open(f"{cc_root}/pm64r-set-homeward-shroom.txt", "w+") as f:
                f.write("oh no")

'''
Handle periodic updates for effects that retrigger on a timer.
'''
def handle_cc_periodic_update(seconds: int):
    global slowgo_queue
    global berserker_queue
    global random_pitch_queue
    global speedy_queue
    global heart_block_queue
    global save_block_queue
    global ohko_queue
    global interval_swaps
    global hs_interval_swaps

    update_time = lambda a : max(a - seconds, 0)

    slowgo_queue = update_time(slowgo_queue)
    berserker_queue = update_time(berserker_queue)
    random_pitch_queue = update_time(random_pitch_queue)
    speedy_queue = update_time(speedy_queue)
    heart_block_queue = update_time(heart_block_queue)
    save_block_queue = update_time(save_block_queue)
    ohko_queue = update_time(ohko_queue)

    slowgo_file = f"{cc_root}/pm64r-slowgo.txt"
    berserker_file = f"{cc_root}/pm64r-berserker.txt"
    pitch_file = f"{cc_root}/pm64r-random-pitch.txt"
    speedy_file = f"{cc_root}/pm64r-disable-speedy.txt"
    heart_block_file = f"{cc_root}/pm64r-disable-heart-blocks.txt"
    save_block_file = f"{cc_root}/pm64r-disable-save-blocks.txt"
    ohko_file = f"{cc_root}/pm64r-ohko.txt"

    if slowgo_queue <= 0 and os.path.isfile(slowgo_file):
        print(f"[CC {datetime.now()}] Slow Go no longer enabled")
        os.remove(slowgo_file)

    if berserker_queue <= 0 and os.path.isfile(berserker_file):
        print(f"[CC {datetime.now()}] Berserker no longer enabled")
        os.remove(berserker_file)

    if random_pitch_queue <= 0 and os.path.isfile(pitch_file):
        print(f"[CC {datetime.now()}] Random Pitch no longer enabled")
        os.remove(pitch_file)

    if speedy_queue <= 0 and os.path.isfile(speedy_file):
        print(f"[CC {datetime.now()}] Speedy Spin is no longer disabled")
        os.remove(speedy_file)

    if heart_block_queue <= 0 and os.path.isfile(heart_block_file):
        print(f"[CC {datetime.now()}] Heart Blocks no longer disabled")
        os.remove(heart_block_file)

    if save_block_queue <= 0 and os.path.isfile(save_block_file):
        print(f"[CC {datetime.now()}] Save Blocks no longer disabled")
        os.remove(save_block_file)

    if ohko_queue <= 0 and os.path.isfile(ohko_file):
        print(f"[CC {datetime.now()}] OHKO Mode no longer enabled")
        os.remove(ohko_file)

    if interval_swaps > 0:
        with open(f"{cc_root}/cc-shuffle.txt", "w+") as f:
            f.write("Shuffle")
        interval_swaps -= 1

    if hs_interval_swaps > 0:
        hs_interval_swaps -= 1
        with open(f"{cc_root}/pm64r-set-homeward-shroom.txt", "w+") as f:
            f.write("oh no")

